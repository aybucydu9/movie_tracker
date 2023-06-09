import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def lookup(title):
    """Look up movie data for title."""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"http://www.omdbapi.com/?t={urllib.parse.quote_plus(title)}&apikey={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        data = response.json()
        return {
            "title": data["Title"],
            "year": int(data["Year"]),
            "imdb_rating": data["imdbRating"],
            "genre": data["Genre"],
            "director": data["Director"],
            "language": data["Language"],
            "boxoffice": data["BoxOffice"],
            "poster": data["Poster"],
        }
    except (KeyError, TypeError, ValueError):
        return None