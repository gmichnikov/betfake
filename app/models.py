from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import enum

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))
    time_zone = db.Column(db.String(50), nullable=False, default='UTC')
    is_admin = db.Column(db.Boolean, default=False)
    balance = db.Column(db.Float, nullable=False, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    actor = db.relationship('User', backref=db.backref('log_entries', lazy=True))

    def __repr__(self):
        return f'<LogEntry {self.timestamp} - {self.category}>'
    
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String, nullable=False, unique=True)
    category = db.Column(db.String)
    sport_key = db.Column(db.String)
    sport_title = db.Column(db.String)
    commence_time = db.Column(db.DateTime)
    home_team = db.Column(db.String)
    away_team = db.Column(db.String)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    home_team_score = db.Column(db.Integer)
    away_team_score = db.Column(db.Integer)
    last_updated_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Event {self.event_id}>'

class MarketStatus(enum.Enum):
    win = 'win'
    lose = 'lose'
    push = 'push'
    tbd = 'tbd'

class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float)
    point = db.Column(db.Float)
    last_updated_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Enum(MarketStatus), default=MarketStatus.tbd, nullable=False)

    event = db.relationship('Event', backref=db.backref('markets', lazy='dynamic'))

    def __repr__(self):
        return f'<Market {self.name} - Price: {self.price} - Point: {self.point} - Status: {self.status}>'

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    included_in_balance = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('bets', lazy='dynamic'))
    market = db.relationship('Market', backref=db.backref('bets', lazy='dynamic'))

    def __repr__(self):
        return f'<Bet {self.id} - User {self.user_id} - Market {self.market_id} - Amount {self.amount}>'

class TransactionType(enum.Enum):
    deposit = 'deposit'
    withdrawal = 'withdrawal'
    bet_placed = 'bet_placed'
    bet_win = 'bet_win'
    bet_push = 'bet_push'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.Enum(TransactionType), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    bet_id = db.Column(db.Integer, db.ForeignKey('bet.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('transactions', lazy='dynamic'))
    bet = db.relationship('Bet', backref=db.backref('transactions', uselist=False))

    def __repr__(self):
        return f'<Transaction {self.id} - Type: {self.type} - Amount: {self.amount}>'

    def is_bet(self):
        """Check if the transaction is bet related."""
        return self.type in [TransactionType.bet_placed, TransactionType.bet_win, TransactionType.bet_push]