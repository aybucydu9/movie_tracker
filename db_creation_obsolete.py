from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app import app, db

# Create Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    #email = db.Column(db.String(200), nullable=False, unique=True)
    #date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Movies(db.Model):
    movie_id = db.Column(db.String(200), primary_key=True)
    year = db.Column(db.Integer)
    genre = db.Column(db.String(200))
    director = db.Column(db.String(200))
    language = db.Column(db.String(200))

class Watch_history(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    movie_id = db.Column(db.String(200), db.ForeignKey("movies.movie_id"), primary_key=True)
    watch_date = db.Column(db.Date, primary_key=True) #TODO
    personal_rating = db.Column(db.Float)
    comments = db.Column(db.String(2000))
    imdb_rating = db.Column(db.Float)
    boxoffice = db.Column(db.String(200))

with app.app_context():
    db.create_all()