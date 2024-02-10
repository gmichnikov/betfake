from flask import render_template, redirect, url_for, flash, request
from app import app, db
from app.models import User, LogEntry, Market, Bet, Event, MarketStatus, MarketType, Transaction, TransactionType
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app.forms import RegistrationForm, LoginForm, AdminPasswordResetForm, FetchOddsForm
from functools import wraps
import os
import requests
import json
from datetime import datetime

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def index():
    if current_user.is_authenticated:
        email = current_user.email
        return render_template('index.html', logged_in=True, email=email)
    else:
        return render_template('index.html', logged_in=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered.')
            return redirect(url_for('register'))
        
        new_user = User(
            email=form.email.data,
            time_zone=form.time_zone.data,
        )
        new_user.set_password(form.password.data)
        # Automatically make user with ADMIN_EMAIL an admin
        if form.email.data == ADMIN_EMAIL:
            new_user.is_admin = True

        db.session.add(new_user)
        db.session.commit()

        log_entry = LogEntry(category='Register', actor_id=new_user.id, description=f"Email: {new_user.email}")
        db.session.add(log_entry)
        db.session.commit()

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/reset_password', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_reset_password():
    form = AdminPasswordResetForm()
    form.email.choices = [(user.email, user.email) for user in User.query.all()]

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password reset successfully.')

            log_entry = LogEntry(category='Reset Password', actor_id=current_user.id, description=f"{current_user.email} reset password of {user.email}")
            db.session.add(log_entry)
            db.session.commit()

        else:
            flash('User not found.')

    return render_template('admin/reset_password.html', form=form)

@app.route('/admin/fetch_odds', methods=['GET', 'POST'])
@admin_required
@login_required
def admin_fetch_odds():
    form = FetchOddsForm()
    if form.validate_on_submit():
        sport_name = form.sport.data
        market_name = form.market.data
        print(sport_name, market_name)
        make_odds_api_call(sport_name, market_name)
        flash('Odds fetched successfully.', 'success')
    return render_template('admin/fetch_odds.html', form=form)


def make_odds_api_call(sport_name, market_name):
    api_url = f"https://api.the-odds-api.com/v4/sports/{sport_name}/odds"
    params = {
        'regions': 'us',
        'markets': market_name,
        'oddsFormat': 'american',
        'dateFormat': 'unix',
        'api_key': ODDS_API_KEY
    }
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        odds_data = response.json()
        process_odds_response(odds_data, sport_name, market_name)
        # Process the odds data here
    else:
        flash('Failed to fetch odds from the API.', 'danger')

def process_odds_response(odds_data, sport_name, market_name):
    update_existing_markets(sport_name, market_name)

    for event in odds_data:
        existing_event = Event.query.filter_by(event_id=event['id']).first()
        db_event = existing_event
        if not existing_event:
            # Convert epoch to datetime
            commence_time = datetime.utcfromtimestamp(event['commence_time'])
            new_event = Event(
                event_id=event['id'],
                category="sports",
                sport_key=event['sport_key'],
                sport_title=event['sport_title'],
                commence_time=commence_time,
                home_team=event['home_team'],
                away_team=event['away_team'],
                completed=False
            )
            db.session.add(new_event)
            db_event = new_event
        else:
            existing_event.commence_time = datetime.utcfromtimestamp(event['commence_time'])
            existing_event.last_updated_time = datetime.utcnow()
        db.session.commit()

        best_prices = {}
        for bookmaker in event['bookmakers']:
            for market in bookmaker['markets']:
                for outcome in market['outcomes']:
                    key = (outcome['name'], outcome.get('point'))
                    if key not in best_prices or outcome['price'] > best_prices[key]['price']:
                        best_prices[key] = {
                            'price': outcome['price'],
                            'point': outcome.get('point'),
                            'type': market['key']
                        }

        # After determining the best prices, update or create markets in the database
        for (name, point), details in best_prices.items():
            new_market = Market(
                event_id=db_event.id,
                name=name,
                price=details['price'],
                point=point,
                type=details['type']
            )
            db.session.add(new_market)

        db.session.commit()

def update_existing_markets(sport_name, market_name):
    market_ids = db.session.query(Market.id).join(Event).filter(
        Event.sport_key == sport_name,
        Market.available == True,
        Market.type == market_name
    ).all()
    market_ids = [mid[0] for mid in market_ids]

    # Then, perform the update operation only on those IDs
    if market_ids:
        db.session.query(Market).filter(Market.id.in_(market_ids)).update({
            Market.available: False,
            Market.marked_unavailable_time: datetime.utcnow(),
            Market.last_updated_time: datetime.utcnow()
        }, synchronize_session=False)
        db.session.commit()
