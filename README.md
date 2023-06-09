# My Movies
### Video Demo:  <URL HERE>
## Description:
This is a website to help user record the movies they have watched (watch history) and the ones they want to watch (wishlist).

Users will be able to add movies to the record by searching for the movie and decide whether they want to add it to the watch history or wishlist.

## Files Description
### app.py:
This is the main file that controls the behaviour of the application. It contains 8 different app.route including `homepage`, `login`, `logout`, `register`, `search`, `watch_history`, `wishlist`, and `add_movei` (retired).
- `homepage`: doesn't do much right now. Can add a dashboard with interesting stats in the future.
- `login`: allow users to log in to their account by checking whether their input matches with records in the `users` database. Log user in, remember the user_id for the session and redirect to homepage if there's a match.
- `logout`: allow users to log out of their account
- `register`: allow users to register for an account. Perform basic checks on the user input (valid username, password, confirmation matches the password, username was not registered before, and password is at least 8 character long). After confirming input is valid, log user into the platform and redirect to homepage. Hash user password and add the user to users table in database in the backend.
- `search`: This function allows users to search for any movie they want. From the backend the function pass user input to the OMDb API (https://www.omdbapi.com/) to retrieve movie informations including poster, movie name, release year, genre, director, language, imdb_rating and box office number and display these information to the user. User can then decide whether they want to
    1. search for another movie (maybe the returned results is not the right movie because they entered the wrong name)
    2. add movie to the watch history: the system will then prompt the user for watch date (mandatory), personal rating (optional) and comments (optional). the backend logic then update the movies and watch_history tables in the backend with respective data and then redirect the user to the watch history page
    3. add movie to the wishlist: the system will then prompt the user for comments (optional). The backend logic then check if the movie is already in wishlist and throws an error if it does. If not then the logic will update the movies and wishlist table in the backend with respective data and then redirect the user to the wishlist page
- `history`: Display the full watch history for that specific user. Allow users to delete the record from the page.
- `wishlist`: Display the full wishlist for that specific user. Allow users to delete the record or add the movie to watch history from the page.
- `add_movie` (retired): allow users to directly add movie to watch history without needing to search for the movie first. But users will only input Movie name and personal rating and the records will not be as informative when we look at the watch history page. Also we will not be able to check for potential typo in the movie name.

I had a design debate regarding on whether we should keep the add_movie function to co-exist with the search and add from search result to watch history function. On one hand this is a simple function to allow user to esily log the movies, but on the other hand there wouldn't be a lot of useful information to compare across records, and we will not be able to check for potential typo in the movie name. It will also create a inconsistent user experience that the records added from search has a lot of information but the records added manually has very few info. In the end I decided to keep the user experience simple and consistent by retiring the manually add movie function.

### helper.py:
Helper file contains useful functions for web developement including `apology`, `login_required`, and `lookup`
- `apology`: to signal error and display error message to user
- `login_required`: to redirect user to the login page before they can access the other functions within the application
- `lookup`: the function to handle and parse the OMDb API to extract only the informations we want to use for the application

### movie.db:
Database file including 4 main tables: `users`, `movies`, `watch_history`, `wishlist`.
- `users`: record the username and hashed password for each user so that they can login to the application.
- `movies`: store basic movie info extracted from the OMDb database including movie name, release year, genre, director, language.
- `watch_history`: record user's watch history. Primary key is the user_id, movie_id and watch_date. (User can watch the same movie many times but across different dates) User can also add personal rating for the movie and comments to record their takeaways, but these inputs are optional. This table also includes the movie's imdb rating and box office number at the time when user input the record.
- `wishlist`: record user's wishlist that they want to watch in the future. A Movie can only have one record in wishlist, but can exist in both wishlist and watch history. (If the user want to remind himself/herself to watch the movie again) Primary key is user_id and movie_id. Can also add optiomal comment to record things like who recommended the movie to them/who they want to watch the movie with.

I had a debate whether imdb rating and box office number should be put in `movies` table or `watch_history` table. They are movie attributes that doesn't differ based on user_id so it makes sense to put them in movies table, but they are time-dependent attributes that the value might change based on when the user called the API. And if all users share the same record of the movie from the movies table, then then number might get updated for user A when user B called the API at a later time, creating confusing user experience. (numbers get updated sometimes but not all the time) So I decided to put these 2 attributes as column in the watch_history/wishlist tables and the value will be fixed to the value which was captured on the day the user key in the record. If the user watched the same movie multiple times, they will also get to observe whether their IMDb rating and box office has changed in between.

### templates folder:
Contains all the html file that controls what shows up on each webpage.
- `add_movie.html` (retired): correspond to the `add_movie` function. Contains a form for users to input movie name and personal rating and submit to the system to add to watch history.
- `apology.html`: correspond to the `apology` function in `helper.py`, shows the image with error message
- `hisotry.html`: correspond to the `history` function. Contains jinja syntax to loop through entries in the watch_history table and display them in a table. Contains a delete button to remove the record.
- `wishlist.html`: correspond to the `wishlist` function. Contains jinja syntax to loop through entries in the wishlist table and display them in a table. Contains a delete button to remove the record. Contains a add to watch history button to directly add the record to watch history
- `layout.html`: backbone template for all the other html files. Defines tha basic layout of the webpage and the linkage between different pages
- `login.html`: correspond to the `login` function. Contains a form for users to input username and password and submit to the application
- `register.html`: correspond to the `register` function. Contains a form for users to input username, password and password confirmation and submit to the application
- `search_results.html`: correspond to the `search` function. Contains
    1. jinja syntax to display the API response in a table
    2. button to search for another movie
    3. button to add the movie to watch history. Once clicked a Modal will be displayed to ask for additional information form users (watch date, personal rating and comments) and allow users to submit the data to the application. (also contains the hidden inputs to pass the movie basic info we got from the API response to the application)
    4. button to add the movie to wishlist. Once clicked a Modal will be displayed to ask for additional information form users (optional comments) and allow users to submit the data to the application. (also contains the hidden inputs to pass the movie basic info we got from the API response to the application)
- `search.html`: correspond to the `search` function. Contains a form for users to input movie name to search for and submit to the application

## Potential enhancements for Future:
- edit record (for both wishlist and watch history, watch_date, comment and personal_rating) (prepopulate the existing content to the modal)
- including the movie's poster in the wishlist and the watch history list
- Upgrade the general UI (especially for the tables)
- change cat meme to hamster (this is purely personal preference)
- what to display on homepage (right now homepage doesn't really do much) (consider the stats dashboard or poster of most recent watched movies)
- add in indicator in page to show if it's watch history or wishlist
- check box to copy the comment from wishlist to watch history
- add date info for wishlist (automatically generate on the moment you add to the list)
- Sort history by different metrics / ability to rank by different properties (eg imdb ranking, personal ranking)
- filter for specific property for history and wishlist
- watch history and wishlist add multiple pages (bootstrap pagination: https://getbootstrap.com/docs/5.1/components/pagination/)
- add data tag whether you rate the movie higher or lower than imdb rating
- stats dashboard (consider making this the homepage): total number of movies you have watched, highest rated movie, number of countries, lowest rated movie, most common genre...
- use the search function for the API to return more than 1 results. This could enable a much better user experience but would requrie major architecture changes.
- make friends. See each other's list. Add who you watched the movie with/ who you want to watch the wishlist with
- email function to confirm address and reset password

## Formatting guide for future reference:
- https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax