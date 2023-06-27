import os

from flask import Flask, flash, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
from sqlalchemy import func, extract

from helper import apology, login_required, lookup

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# v1: Configure SQLlite DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies_sqlite.db"

# v2: Config for Heroku
#app.config["SQLALCHEMY_DATABASE_URI"] = os.environ['POSTGRESQL_URL']

db = SQLAlchemy(app)

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
    poster_url = db.Column(db.String(300))

class Watch_history(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    movie_id = db.Column(db.String(200), db.ForeignKey("movies.movie_id"), primary_key=True)
    watch_date = db.Column(db.Date, primary_key=True)
    personal_rating = db.Column(db.Float)
    comments = db.Column(db.Text())
    imdb_rating = db.Column(db.Float)
    boxoffice = db.Column(db.String(200))

class Wishlist(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    movie_id = db.Column(db.String(200), db.ForeignKey("movies.movie_id"), primary_key=True)
    comments = db.Column(db.Text())
    imdb_rating = db.Column(db.Float)
    boxoffice = db.Column(db.String(200))

# v1: SQLlite DB create tables
with app.app_context():
    db.create_all()

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/", methods=["GET"])
@login_required
def homepage():
    # result = Movies.query.first()
    # poster = result.poster_url
    return render_template("homepage.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = Users.query.filter_by(username=request.form.get("username")).first()

        # Ensure username exists and password is correct
        if rows is None or not check_password_hash(rows.password, request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows.id

        # Redirect user to home page
        return redirect("/search")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)

        # Query database for username
        rows = Users.query.filter_by(username=request.form.get("username")).first()

        # Enuser user name is unique
        if rows is not None:
            return apology("username already exist", 400)

        # Ensure password and confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password do not match", 400)

        # Ensure password at least have 8 characters
        if len(request.form.get("password")) < 8:
            return apology("Password not long enough", 400)

        # Hash password
        hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # Insert into db
        user = Users(username=request.form.get("username"), password=hash)
        db.session.add(user)
        db.session.commit()

        # log user in
        info = Users.query.filter_by(username=request.form.get("username")).first()
        session["user_id"] = info.id
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method == "POST":
        if "delete" in request.form:
            query = Watch_history.query.filter_by(user_id=session["user_id"], movie_id=request.form.get("movie_id"), watch_date=request.form.get("date")).first()
            db.session.delete(query)
            db.session.commit()

    """Show history of transactions"""
    history = list()
    results = db.session.query(Movies, Watch_history).join(Watch_history).filter(Watch_history.user_id==session["user_id"]).order_by(Watch_history.watch_date.desc()).all()
    for movies, watch_history in results:
        history.append({"date": watch_history.watch_date, 
                        "movie_id": watch_history.movie_id, 
                        "year": movies.year,
                        "genre": movies.genre,
                        "director": movies.director,
                        "language": movies.language,
                        "boxoffice": watch_history.boxoffice,
                        "imdb_rating": watch_history.imdb_rating,
                        "personal_rating": watch_history.personal_rating,
                        "comments": watch_history.comments})
    return render_template("history.html", history=history)

@app.route("/wishlist", methods=["GET", "POST"])
@login_required
def wishlist():
    if request.method == "POST":
        if "delete" in request.form:
            query = Wishlist.query.filter_by(user_id=session["user_id"], 
                                             movie_id=request.form.get("movie_id")).first()
            db.session.delete(query)
            db.session.commit()
        if "add_to_history" in request.form:
            # Ensure watch date is not null
            if not request.form.get("watchdate"):
                return apology("Watch date must not be null")

            # Ensure rating is float
            try:
                rating = float(request.form.get("personal_rating"))
            except ValueError:
                return apology("Rating must be numerical")

            # Ensure rating within rating range
            if rating < 0:
                return apology("Rating can not be negative")
            elif rating > 10:
                return apology("Rating can't exceed 10")

            # Check whether this movie has been added for that day already
            record = Watch_history.query.filter_by(user_id=session["user_id"], movie_id=request.form.get("movie_name"), watch_date=request.form.get("watchdate")).first()
            if record is not None:
                return apology("This watch history has already been recorded")

            # Update movies table
            # check if movie already exist in movies table
            rows = Movies.query.filter_by(movie_id=request.form.get("movie_id")).first()
            if rows is None:
                # if not add the movie to movies table
                # movies = Movies(movie_id=request.form.get("movie_id"),
                #                 year = request.form.get("year"), 
                #                 genre=request.form.get("genre"),
                #                 director = request.form.get("director"),
                #                 language = request.form.get("language"))
                # db.session.add(movies)
                # db.session.commit()
                return apology("Please don't modify Movie Name")

            # Update watch history
            movie_watched = Watch_history(user_id=session["user_id"], 
                                          movie_id = request.form.get("movie_name"), 
                                          watch_date=datetime.strptime(request.form.get("watchdate"), '%Y-%m-%d').date(), 
                                          personal_rating=rating, 
                                          comments=request.form.get("comments"),
                                          imdb_rating=request.form.get("imdb_correct"),
                                          boxoffice=request.form.get("box_office_correct"))
            db.session.add(movie_watched)
            db.session.commit()

            
            # Update wishlist table
            query = Wishlist.query.filter_by(user_id=session["user_id"], 
                                             movie_id=request.form.get("movie_name")).first()
            db.session.delete(query)
            db.session.commit()

            #return redirect("/")
            return redirect("/wishlist")


    """Show record of wishlist"""
    wishlist_list = list()
    results = db.session.query(Movies, Wishlist).join(Wishlist).filter(Wishlist.user_id==session["user_id"]).all()
    for movies, wishlist in results:
        wishlist_list.append({"movie_id": wishlist.movie_id, 
                        "year": movies.year,
                        "genre": movies.genre,
                        "director": movies.director,
                        "language": movies.language,
                        "boxoffice": wishlist.boxoffice,
                        "imdb_rating": wishlist.imdb_rating,
                        "comments": wishlist.comments})
    return render_template("wishlist.html", wishlist=wishlist_list)

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        # User request to search
        if "search_movie" in request.form:
            # Ensure user input movie title
            if not request.form.get("title"):
                return apology("Title must not be null")

            result = lookup(request.form.get("title"))

            # movie title doesn't exist
            if not result:
                return apology("Can't find the movie", 400)
            else:
                return render_template("search_results.html", title=result["title"], year=result["year"],
                    genre=result["genre"], director=result["director"], language=result["language"],
                    imdb_rating=result["imdb_rating"], boxoffice=result["boxoffice"], poster=result["poster"])

        # User request to search for another movie
        if "search_again" in request.form:
            return render_template("search.html")

        # User request to add the movie to watch history
        if "add_to_history" in request.form:
            result = lookup(request.form.get("title"))

            # Ensure watch date is not null
            if not request.form.get("watchdate"):
                return apology("Watch date must not be null")

            # Ensure rating is float
            try:
                rating = float(request.form.get("personal_rating"))
            except ValueError:
                return apology("Rating must be numerical")

            # Ensure rating within rating range
            if rating < 0:
                return apology("Rating can not be negative")
            elif rating > 10:
                return apology("Rating can't exceed 10")

            # Check whether this movie has been added for that day already
            record = Watch_history.query.filter_by(user_id=session["user_id"], movie_id=request.form.get("title"), watch_date=request.form.get("watchdate")).first()
            if record is not None:
                return apology("This watch history has already been recorded")

            # Update movies table
            # check if movie already exist in movies table
            rows = Movies.query.filter_by(movie_id=request.form.get("title")).first()
            if rows is None:
                # if not add the movie to movies table
                movies = Movies(movie_id=request.form.get("title"),
                                year = request.form.get("year"), 
                                genre=request.form.get("genre"),
                                director = request.form.get("director"),
                                language = request.form.get("language"),
                                poster_url = result["poster"])
                db.session.add(movies)
                db.session.commit()

            # Update watch history
            movie_watched = Watch_history(user_id=session["user_id"], 
                                          movie_id = request.form.get("title"), 
                                          watch_date=datetime.strptime(request.form.get("watchdate"), '%Y-%m-%d').date(), 
                                          personal_rating=rating, 
                                          comments=request.form.get("comments"),
                                          imdb_rating=request.form.get("imdb_rating"),
                                          boxoffice=request.form.get("boxoffice"))
            db.session.add(movie_watched)
            db.session.commit()

            #return redirect("/")
            return redirect("/history")

        # User request to add the movie to wishlist
        if "add_to_wishlist" in request.form:
            result = lookup(request.form.get("title"))
            # If movie already exist in wishlist
            rows = Wishlist.query.filter_by(user_id=session["user_id"], movie_id=request.form.get("title")).first()
            if rows is not None:
                return apology("movie already in wishlist")

            # Update movies table
            # check if movie already exist in movies table
            rows = Movies.query.filter_by(movie_id=request.form.get("title")).first()
            if rows is None:
                # if not add the movie to movies table
                movies = Movies(movie_id=request.form.get("title"),
                                year = request.form.get("year"), 
                                genre=request.form.get("genre"),
                                director = request.form.get("director"),
                                language = request.form.get("language"),
                                poster_url = result["poster"])
                db.session.add(movies)
                db.session.commit()

            # Update wishlist
            # Future enhancement: get rid of imdb_rating and boxoffice in wishlist table
            add_to_wishlist = Wishlist(user_id=session["user_id"], 
                                       movie_id = request.form.get("title"), 
                                       comments=request.form.get("comments"),
                                       imdb_rating=request.form.get("imdb_rating"),
                                       boxoffice=request.form.get("boxoffice"))
            db.session.add(add_to_wishlist)
            db.session.commit()
            
            return redirect("/wishlist")
    else:
        return render_template("search.html")
    
@app.route("/posterwall", methods=["GET"])
@login_required
def poster_wall():
    poster_list = []
    # # Retrieve the image data from the database

    all_movies = db.session.query(
        Movies, Watch_history
    ).join(
        Watch_history
    ).filter(
        Watch_history.user_id==session["user_id"]
    ).order_by(
        Watch_history.watch_date
    ).all()


    for movie, watch_history in all_movies:
        poster = movie.poster_url
        if poster not in poster_list:
            poster_list.append(poster)

    return render_template("poster_wall.html", poster_list=poster_list)

@app.route("/stats", methods=["GET"])
@login_required
def stats():
    basic_stats = []
    favorite = []
    favorite_with_img = []
    others = []
    others_with_img = []
    watch_next = []
    watch_next_with_img = []
    stats_list = list()
    stats_list_with_image = list()
    stats_list_with_image_2 = list()
    # Basic stats
    # total movies watched
    results = db.session.query(Watch_history).filter_by(user_id=session["user_id"]).count()
    basic_stats.append({"question": "Movies in your Watch History", 
                        "answer": results})
    
    # number of movies you watched this year
    current_year = datetime.now().year
    results = Watch_history.query.filter(Watch_history.user_id==session["user_id"],
                               extract('year', Watch_history.watch_date) == current_year).count()
    basic_stats.append({"question": "Movies you Watched This Year", 
                        "answer": results})
    
    # days since you last watched a movie
    results = find_most_recent_watch()
    basic_stats.append({"question": "since you last watched a movie", 
                        "answer": results + " Days"})
    
    # number of wishlist items
    results = db.session.query(Wishlist).filter_by(user_id=session["user_id"]).count()
    basic_stats.append({"question": "Movies you want to watch", 
                        "answer": results})

    # Personal Favorites
    # movies with the highest personal rating
    results = find_highest(Watch_history, "personal_rating")
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        favorite_with_img.append({"question": "Your Favorite Movie",  
                                    "answer": results,
                                    "poster": poster[0]})
    else:
        favorite.append({"question": "Your Favorite Movie",  
                                  "answer": results})

    # movies you watched the most times
    results = most_watch()
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        favorite_with_img.append({"question": "You can't stop re-watching", 
                        "answer": results,
                        "poster": poster[0]})
    else:
        favorite.append({"question": "You can't stop re-watching",  
                                  "answer": results})
    
    # favorite genre
    results = find_favorite("genre")
    favorite.append({"question": "Your favorite genre", 
                        "answer": results})
    
    # favorite director
    results = find_favorite("director")
    favorite.append({"question": "Your favorite director", 
                        "answer": results})
    
    # unique movies watched
    # results = db.session.query(Watch_history.movie_id).filter_by(user_id=session["user_id"]).distinct().count()
    # stats_list.append({"question": "Number of unique movies you have watched", 
    #                     "answer": results})
    
    # Comparing to others
    # watch history with the highest box office 
    results = find_highest_box_office(Watch_history)
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        others_with_img.append({"question": "Most popular movie you have watched",  
                                    "answer": results,
                                    "poster": poster[0]})
    else:
        others.append({"question": "Most popular movie you have watched",  
                                  "answer": results})
    
    # watch history with the highest IMDB rating
    results = find_highest(Watch_history, "imdb_rating")
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        others_with_img.append({"question": "Highest IMDb rating movie you have watched",  
                                    "answer": results,
                                    "poster": poster[0]})
    else:
        others.append({"question": "Highest IMDb rating movie you have watched",  
                                  "answer": results})

    # movies you love more than imdb
    results = compare_personal_rating_with_imdb("rate higher")
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        others_with_img.append({"question": "Movie you love way more than other people",  
                                    "answer": results,
                                    "poster": poster[0]})
    else:
        others.append({"question": "Movie you love way more than other people",  
                                  "answer": results})

    # movies you under-rate
    results = compare_personal_rating_with_imdb("rate lower")
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        others_with_img.append({"question": "The most overrated movie you think",  
                                    "answer": results,
                                    "poster": poster[0]})
    else:
        others.append({"question": "The most overrated movie you think",  
                                  "answer": results})


    # Watch next
    # oldest movie you have watched
    results = find_oldest_or_newest_movie("old", Wishlist)
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        watch_next_with_img.append({"question": "Some old fashion",  
                                    "answer": results,
                                    "poster": poster[0]})
    else:
        watch_next.append({"question": "Some old fashion",  
                                  "answer": results})

    # movies with the highest IMDB rating in your wishlist
    results = find_highest(Wishlist, "imdb_rating")
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        watch_next_with_img.append({"question": "Highest rating",  
                                    "answer": results,
                                    "poster": poster[0]})
    else:
        watch_next.append({"question": "Highest rating",  
                                  "answer": results})
        
    # wishlist with the highest box office
    results = find_highest_box_office(Wishlist)
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        watch_next_with_img.append({"question": "Most popular",  
                                    "answer": results,
                                    "poster": poster[0]})
    else:
        watch_next.append({"question": "Most popular",  
                                  "answer": results})    
    
    results = find_oldest_or_newest_movie("new", Wishlist)
    poster = find_poster_url(results)
    if type(poster)== list and len(poster)==1:
        watch_next_with_img.append({"question": "Something new",  
                                    "answer": results,
                                    "poster": poster[0]})
    else:
        watch_next.append({"question": "Something new",  
                                  "answer": results})
    
    return render_template("dashboard_cards.html", basic_stats=basic_stats, favorite=favorite, favorite_with_img=favorite_with_img, others=others, others_with_img=others_with_img, watch_next=watch_next, watch_next_with_img=watch_next_with_img, stats=stats_list, stats_img=stats_list_with_image, stats_img_2=stats_list_with_image_2)

def find_highest(table, metric):
    results = list()

    subquery = db.session.query(
        table,
        func.rank().over(
            order_by=getattr(table, metric).desc(),
            partition_by=table.user_id
        ).label('rnk')
    ).subquery()

    query = db.session.query(subquery).filter(
        subquery.c.rnk==1,
        subquery.c.user_id==session["user_id"]
    ).all()

    for movie in query:
        if movie.movie_id not in results:
            results.append(movie.movie_id)

    if not results:
        if table == Wishlist:
            return "You don't have any record in your Wish List"
        elif table == Watch_history:
            return "You don't have any record in your Watch History"
    else:
        return results

def find_highest_box_office(table):
    movie_pairs = {}

    all_movies = table.query.filter(table.user_id==session["user_id"]).all()

    for movie in all_movies:
        if movie.boxoffice == "N/A":
            movie_pairs[movie.movie_id] = 0
        elif movie.movie_id not in movie_pairs:
            box_office_num = int(movie.boxoffice[1:].replace(",", ""))
            movie_pairs[movie.movie_id] = box_office_num
    
    if movie_pairs == {}:
        if table == Wishlist:
            return "You don't have any record in your Wish List"
        elif table == Watch_history:
            return "You don't have any record in your Watch History"

    max_box_office = max(movie_pairs.values())

    if max_box_office == 0:
        if table == Wishlist:
            return "You don't have any record with valid box office in your Wish List"
        elif table == Watch_history:
            return "You don't have any record with valid box office in your Watch History"
    
    results = [k for k, v in movie_pairs.items() if v == max_box_office]

    return results

def compare_personal_rating_with_imdb(option):
    if option not in ["rate higher", "rate lower"]:
        raise ValueError('option input should be either "rate higher" or "rate lower"')
    movie_pairs = {}

    all_movies = Watch_history.query.filter(Watch_history.user_id==session["user_id"]).all()

    for movie in all_movies:
        personal_minus_imdb = movie.personal_rating - movie.imdb_rating
        if movie.movie_id not in movie_pairs:
            movie_pairs[movie.movie_id] = personal_minus_imdb
        # if user has multiple record of the same movie and different rating each time
        elif movie.movie_id in movie_pairs:
            if option == "rate higher": #keep the one you over-rate the highest
                if personal_minus_imdb > movie_pairs[movie.movie_id]:
                    movie_pairs[movie.movie_id] = personal_minus_imdb
            elif option == "rate lower": #keep the one you under-rate the highest
                if personal_minus_imdb < movie_pairs[movie.movie_id]:
                    movie_pairs[movie.movie_id] = personal_minus_imdb

    if movie_pairs == {}:
        return "You don't have any record in your Watch History"
    
    if option == "rate higher":
        diff = max(movie_pairs.values(), default=0)
    if option == "rate lower":
        diff = min(movie_pairs.values(), default=0)

    results = [k for k, v in movie_pairs.items() if v == diff]

    if option == "rate higher" and diff <= 0:
        return "You don't have any record in your Watch History you " + option + " than IMDB"
    elif option == "rate lower" and diff >=0:
        return "You don't have any record in your Watch History you " + option + " than IMDB"
    else:
        return results
    
def most_watch():
    movie_pairs = {}

    all_movies = Watch_history.query.filter(Watch_history.user_id==session["user_id"]).all()

    for movie in all_movies:
        if movie.movie_id not in movie_pairs:
            movie_pairs[movie.movie_id] = 1
        # if user has multiple record of the same movie and different rating each time
        elif movie.movie_id in movie_pairs:
            movie_pairs[movie.movie_id] = movie_pairs[movie.movie_id] + 1

    if movie_pairs == {}:
        return "You don't have any record in your Watch History"
    
    most_watch = max(movie_pairs.values(), default=0)

    results = [k for k, v in movie_pairs.items() if v == most_watch]

    if len(results) > 3:
        return "Too many movies tie as the most watched movie"
    else:
        return results
    
def find_oldest_or_newest_movie(option, table):
    if option not in ["old", "new"]:
        raise ValueError('option input should be either "old" or "new"')
    movie_pairs = {}

    all_movies = db.session.query(
        Movies, table
    ).join(
        table
    ).filter(
        table.user_id==session["user_id"]
    ).all()

    for movie, list in all_movies:
        if movie.movie_id not in movie_pairs:
            movie_pairs[movie.movie_id] = movie.year
    
    if movie_pairs == {}:
        if table == Watch_history:
            return "You don't have any record in your Watch History"
        elif table == Wishlist:
            return "You don't have any record in your Wishlist"

    if option == "old":
        year = min(movie_pairs.values())
    elif option == "new":
        year = max(movie_pairs.values())

    results = [k for k, v in movie_pairs.items() if v == year]

    return results

def find_favorite(option):
    if option not in ["genre", "director"]:
        raise ValueError('option input should be either "genre" or "director"')
    movie_pairs = {}

    all_movies = db.session.query(
        Movies, Watch_history
    ).join(
        Watch_history
    ).filter(
        Watch_history.user_id==session["user_id"]
    ).all()

    for movie, watch_history in all_movies:
        list = getattr(movie, option).split(", ")
        for item in list:
            if item not in movie_pairs:
                movie_pairs[item] = 1
            elif item in movie_pairs:
                movie_pairs[item] = movie_pairs[item] + 1

    if movie_pairs == {}:
        return "You don't have any record in your Watch History"
    
    favorite = max(movie_pairs.values(), default=0)

    results = [k for k, v in movie_pairs.items() if v == favorite]

    if len(results) > 5:
        return "Too many "+ option + " tie as your favorite "+ option
    else:
        return results
    
def find_most_recent_watch():
    most_recent_movie = Watch_history.query.filter(
        Watch_history.user_id==session["user_id"],
        Watch_history.watch_date <= datetime.now()
    ).order_by(
        Watch_history.watch_date.desc()
    ).first()
    
    if most_recent_movie is None:
        return "You don't have any record in your Watch History"

    date_diff = date.today() - most_recent_movie.watch_date
    date_diff = str(date_diff.days)
    return date_diff

def find_poster_url(results):
    if type(results) == list:
        url_list = []
        for movie in results:
            movie_info = Movies.query.filter(Movies.movie_id==movie).first()
            url_list.append(movie_info.poster_url)
        return url_list
    else:
        return 0

# @app.route("/add_movie", methods=["GET", "POST"])
# @login_required
# def add_movie():
#     if request.method == "POST":

#         # Ensure user input movie title
#         if not request.form.get("title"):
#             return apology("Title must not be null")

#         # Ensure rating is float
#         try:
#             rating = float(request.form.get("personal_rating"))
#         except ValueError:
#             return apology("Rating must be numerical")

#         # Ensure rating within rating range
#         if rating < 0:
#             return apology("Rating can not be negative")
#         elif rating > 10:
#             return apology("Rating can't exceed 10")

#         # Update watch history
#         movie_watched = Watch_history(user_id=session["user_id"], movie_id = request.form.get("title"), personal_rating=rating)
#         db.session.add(movie_watched)
#         db.session.commit()

#         return redirect("/")

#     else:
#         return render_template("add_movie.html")
