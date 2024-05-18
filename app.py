from flask import Flask, render_template, redirect, url_for, request
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'QWERTYUIOP'
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///db.sqlite'

db = SQLAlchemy()
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(128), unique = True, nullable = False)
    password = db.Column(db.String(128), nullable = False)

class Wiki(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), unique = True, nullable = False)
    pages = db.relationship('Page', backref='wiki', lazy=True)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    wiki_id = db.Column(db.Integer, db.ForeignKey('wiki.id'), nullable=False) 

db.init_app(app)
 
with app.app_context():
    db.create_all()

class SignUpForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    password = PasswordField('Password', validators = [DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    password = PasswordField('Password', validators = [DataRequired()])
    submit = SubmitField('Log In')

class CreateWikiForm(FlaskForm):
    name = StringField('Wiki Name', validators=[DataRequired()])
    home = TextAreaField('Home Page Content', validators=[DataRequired()])
    submit = SubmitField('Create Wiki')

@app.route('/signup', methods=["GET", "POST"])
def sign_up():
    form = SignUpForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    elif form.validate_on_submit():
        password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, password = password_hash)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html', signup_form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    elif form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html', login_form=form)

@app.route('/createwiki', methods=["GET", "POST"])
def createwiki():
    form = CreateWikiForm()
    if form.validate_on_submit():
        wiki_name = form.name.data.strip().lower()
        wiki = Wiki(name = wiki_name)
        path = f'./wiki/{wiki_name}'
        if not os.path.exists(path):
            os.makedirs(path)
        db.session.add(wiki)
        db.session.commit()
        home_content = Page(content=form.home.data, name='home', wiki=wiki)
        db.session.add(home_content)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('createwiki.html', createwiki_form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))
    
@app.route("/")
def index():
    return render_template("index.html")