from crypt import methods
import functools
from tkinter.messagebox import NO

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# This creates a Blueprint named 'auth'. Like the application object, the blueprint needs to know where it's defined, so '__name__' is passed as the second argument.
# The 'url_prefix' will be prepended to all the URLs associated with the blueprint.

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
            
        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))
            
        flash(error)
        
    return render_template('auth/register.html')

# Here's what the register view function is doing:

# 1. '@bp.route' associate the URL '/register' with the 'register' view function. When Flask receives a request to '/auth/register', it will call the 
# 'register' view and use the return value as the response.

# 2. If the user submitted the form, 'request.method' will be POST. In this case, start validating the input.

# 3. 'request.form' is a special type of dict mapping submitted form keys and values. The user will input their 'username' and 'password'

# 4.  Validate that 'username' and 'password' are not empty

# 5. If validation succeeds, insert the new user data into the database.
# -- 'db.execute' takes a SQL query with '?' placeholders for any user input, and a tuple of values to replace the placeholders with. The database library will take care of escaping the values so you are not vulnerable to a SQL injection attack.
# -- For security, passwords should never be stored in the database directly. Instead, 'generate_password_hash()' is used to securely hash the password, and that hash is stored. Since this query modifies data, 'db.commit()' needs to be called afterwards to save the changes.
# -- An 'sqlite3.IntegrityError' will occur if the username already exists, which should be shown to the user as another validation error.

# 6. After storing the user, they are redirected to the login page. 'url_for()' generates the URL for the login view based on its name. This is perferable to writing the URL directly as it allows you to change the URL later without changing all code that links to it. 'redirect()' generates a response to the generated URL.

# 7. If validation fails, the error is shown to the user. 'flash()' stores message that can be strieved when redering the template. 

# 8. When the user initially navigates to 'auth/register', or there was a validation error, and HTML page with the registration form should be shown. 'render_template()' will render a template containing the HTML.


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()
        
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
            
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        
        flash(error)
        
    return render_template('auth/login.html')


# There are a few differences from the register view:

# 1. the user is queried first and stored in a variable for later use.
# -- 'fetchone()' returns one row from the query. If the query returned no results, it returns 'None'. Later, 'fetchall()' will be used, which returns a list of all results.

# 2. 'check_password_hash()' hashes the submitted password in the same way as the stored hash and securely compares them. If the match , the password is valid.

# 3. 'session' is a 'dict' that stores data across requests. When validation succeeds, the user's 'id' is stored in a new session. The data is stored in a cookie that is sent to the browser, and the browser then sends it back with subsequent requests. Flask securely signs the data so that it can't be tampered with.

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
        

# bp.before_app_request() registers a function that runs before the view function, no matter what URL is requested. 'load_logged_in_user' checks if a user id is stored in the session and gets teh user's data from the database, storing it on 'g.user', which last for the length of the request. If there is no user id, or if the id doesn't exist, 'g.user' will be 'None'


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# To log out, you need to remove the user id from the session. Then 'load_logged_in_user' won't load a user on subsequent requests.

 
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)
    
    return wrapped_view

# This decorator returns a new view function that wraps the original view it's applied to. The new function checks if a user is loaded and redirects to the login page otherwise. If a user is loaded the original view is called and continues normally. 

# THe 'url_for()' function generates the URL to a view based on a name and arguments. The name associated with a view is also called the endpoint, and by default it's the same as the name of the view function.
# For example, the 'hello()' view that was added to the app factory earlier in the tutorial has the name 'hello' and can be linked to with 'url_for('hello')'. If it took an argument it would be linked to using 'url_for('hello', who='World')'.
# When using a blueprint, the name of the blueprint is prepended to the name of the function, so the endpoint for the login function you wrote above is 'auth.login' because you added it to the 'auth' blueprint.