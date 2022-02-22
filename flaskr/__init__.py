import os

from flask import Flask

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True) # this creates the Flask instance. '__name__' is the name of the current Python module. The app needs to know where it's location to set up some paths, and '__name__' is a convenient way to tell it that.
    #'instance_relative_config=True' tells the app that configuration files are relative to the instance folder. The instance folder is located outside the 'flaskr' package and can hold local data that shouldnt be committed to version control, such as configureation secrets and the database file.
    app.config.from_mapping( # this sets some default configureation that the app will use.              
        SECRET_KEY='dev',#this is used by Flask and extensions to keep data safe. It's set to 'dev' to provide a convenient value during development, but it should be overridden with a random value when deploying
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'), # this is the path where the SQLite database file will be saved. It's under 'app.instance_path' which is the path that Flask has chosen for the instance folder. 
    )
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True) # the overrides the default configureation with values taken from the config.py file in the instance folder if it exists. For example, when deploying, this can be used to set a real 'SECRET_KEY'. 
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
        
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    
    from . import db
    db.init_app(app)
    
    from . import auth
    app.register_blueprint(auth.bp)
    
    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')
    
    return app