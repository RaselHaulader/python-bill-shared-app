from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    due = db.Column(db.Float)
    name = db.Column(db.String(100))

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_amount = db.Column(db.Float)
    deu_amount = db.Column(db.Float)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    bill_type = db.Column(db.String(100))
    date = db.Column(db.String(20))
