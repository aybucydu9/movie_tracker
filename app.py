import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helper import apology, login_required, lookup#, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///movie.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/", methods=["GET"])
@login_required
def homepage():
    return render_template("layout.html")

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Enuser user name is unique
        if len(rows) != 0:
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
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"), hash)

        # log user in
        info = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = info[0]["id"]
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/add_movie", methods=["GET", "POST"])
@login_required
def add_movie():
    if request.method == "POST":

        # Ensure user input movie title
        if not request.form.get("title"):
            return apology("Title must not be null")

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

        # Update watch history
        db.execute("INSERT INTO watch_history (user_id, movie_id, personal_rating) VALUES(?, ?, ?)",
            session["user_id"], request.form.get("title"), rating)

        return redirect("/")

    else:
        return render_template("add_movie.html")

@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method == "POST":
        if "delete" in request.form:
            db.execute("DELETE FROM watch_history WHERE user_id = ? and movie_id = ? and watch_date = ?",
                session["user_id"], request.form.get("movie_id"), request.form.get("date"))

    """Show history of transactions"""
    history = list()
    rows = db.execute("SELECT watch_date, history.movie_id, year, genre, director, language, boxoffice, imdb_rating, personal_rating, comments FROM watch_history history join movies on history.movie_id = movies.movie_id where user_id = ? order by watch_date", session["user_id"])
    for i in range(len(rows)):
        history.append({"date": rows[i]["watch_date"], "movie_id": rows[i]["movie_id"], "year": rows[i]["year"],
            "genre": rows[i]["genre"],"director": rows[i]["director"],"language": rows[i]["language"],
            "boxoffice": rows[i]["boxoffice"],"imdb_rating": rows[i]["imdb_rating"],"personal_rating": rows[i]["personal_rating"],
            "comments": rows[i]["comments"]})
    return render_template("history.html", history=history)

@app.route("/wishlist", methods=["GET", "POST"])
@login_required
def wishlist():
    if request.method == "POST":
        if "delete" in request.form:
            db.execute("DELETE FROM wishlist WHERE user_id = ? and movie_id = ?",
                session["user_id"], request.form.get("movie_id"))
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
            record = db.execute("SELECT * FROM watch_history where user_id = ? and movie_id = ? and watch_date = ?",
            session["user_id"], request.form.get("movie_id"),  request.form.get("watchdate"))
            if len(record) == 1:
                return apology("This watch history already recorded")

            # Update watch history
            db.execute("INSERT INTO watch_history (user_id, movie_id, watch_date, personal_rating, comments, imdb_rating, boxoffice) VALUES(?, ?, ?, ?, ?, ?, ?)",
                session["user_id"], request.form.get("movie_id"), request.form.get("watchdate"), rating, request.form.get("comments"),request.form.get("imdb_rating"), request.form.get("boxoffice"))

            # Update movies table
            # check if movie already exist in movies table
            rows = db.execute("SELECT * FROM movies where movie_id = ?", request.form.get("movie_id"))
            if len(rows) != 1:
                # if not add the movie to movies table
                db.execute("INSERT INTO movies (movie_id, year, genre, director, language) VALUES(?, ?, ?, ?, ?)",
                    request.form.get("movie_id"), request.form.get("year"), request.form.get("genre"), request.form.get("director"), request.form.get("language"))

            # Update wishlist table
            db.execute("DELETE FROM wishlist WHERE user_id = ? and movie_id = ?",
                session["user_id"], request.form.get("movie_id"))

            #return redirect("/")
            return redirect("/wishlist")


    """Show record of wishlist"""
    wishlist = list()
    rows = db.execute("SELECT wishlist.movie_id, year, genre, director, language, boxoffice, imdb_rating, comments FROM wishlist join movies on wishlist.movie_id = movies.movie_id where user_id = ?", session["user_id"])
    for i in range(len(rows)):
        wishlist.append({"movie_id": rows[i]["movie_id"], "year": rows[i]["year"],"genre": rows[i]["genre"],
            "director": rows[i]["director"],"language": rows[i]["language"],"boxoffice": rows[i]["boxoffice"],
            "imdb_rating": rows[i]["imdb_rating"], "comments": rows[i]["comments"]})
    return render_template("wishlist.html", wishlist=wishlist)

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        # User request to search
        # TODO: check if there's a better way to write this
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
            record = db.execute("SELECT * FROM watch_history where user_id = ? movie_id = ? and watch_date = ?",
            session["user_id"], request.form.get("title"),  request.form.get("watchdate"))
            if len(record) == 1:
                return apology("This watch history already recorded")

            # Update watch history
            db.execute("INSERT INTO watch_history (user_id, movie_id, watch_date, personal_rating, comments, imdb_rating, boxoffice) VALUES(?, ?, ?, ?, ?, ?, ?)",
                session["user_id"], request.form.get("title"), request.form.get("watchdate"), rating, request.form.get("comments"),request.form.get("imdb_rating"), request.form.get("boxoffice"))

            # Update movies table
            # check if movie already exist in movies table
            rows = db.execute("SELECT * FROM movies where movie_id = ?", request.form.get("title"))
            if len(rows) != 1:
                # if not add the movie to movies table
                db.execute("INSERT INTO movies (movie_id, year, genre, director, language) VALUES(?, ?, ?, ?, ?)",
                    request.form.get("title"), request.form.get("year"), request.form.get("genre"), request.form.get("director"), request.form.get("language"))

            #return redirect("/")
            return redirect("/history")

        # User request to add the movie to wishlist
        if "add_to_wishlist" in request.form:
            # If movie already exist in wishlist
            rows = db.execute("SELECT * FROM wishlist where movie_id = ?", request.form.get("title"))
            if len(rows) == 1:
                return apology("movie already in wishlist")

            # Update wishlist
            db.execute("INSERT INTO wishlist (user_id, movie_id, comments, imdb_rating, boxoffice) VALUES(?, ?, ?, ?, ?)",
                session["user_id"], request.form.get("title"), request.form.get("wishlist_comment"),request.form.get("imdb_rating"), request.form.get("boxoffice"))

            # Update movies table
            # check if movie already exist in movies table
            rows = db.execute("SELECT * FROM movies where movie_id = ?", request.form.get("title"))
            if len(rows) != 1:
                # if not add the movie to movies table
                db.execute("INSERT INTO movies (movie_id, year, genre, director, language) VALUES(?, ?, ?, ?, ?)",
                    request.form.get("title"), request.form.get("year"), request.form.get("genre"), request.form.get("director"), request.form.get("language"))

            return redirect("/wishlist")
    else:
        return render_template("search.html")