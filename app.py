from flask import Flask, render_template, redirect, url_for, request
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import markdown 
import markdown.extensions.fenced_code
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
    name = db.Column(db.String(128), nullable = False)
    pages = db.relationship('Page', backref='wiki', lazy=True)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    wiki_id = db.Column(db.Integer, db.ForeignKey('wiki.id'), nullable=False) 

db.init_app(app)
 
app.app_context().push()
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

class CreatePageForm(FlaskForm):
    name = StringField('Page Name', validators=[DataRequired()])
    page = TextAreaField('Page Content', validators=[DataRequired()])
    submit = SubmitField('Create Page')

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
        home_page_name = f'home_{wiki.id}'
        home_content = Page(content=form.home.data, name=home_page_name, wiki=wiki)
        db.session.add(home_content)
        db.session.commit()
        f = open(f"./wiki/{wiki_name}/home.md", "x")
        f.write(form.home.data)
        f.close()
        return redirect(url_for('index'))
    return render_template('createwiki.html', createwiki_form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/wikilist")
def wikilist():
    wikis = Wiki.query.all()
    wiki_names = [wiki.name for wiki in wikis]
    return render_template("wikilist.html", wiki_names=wiki_names)

@app.route("/wiki/<wikiname>")
def homepage(wikiname):
    file = open(f"./wiki/{wikiname}/home.md", "r")
    md_template_string = markdown.markdown(
        file.read(), extensions=["fenced_code"]
    )

    return md_template_string

@app.route("/wiki/<wikiname>/<pagename>")
def page(wikiname, pagename):
    file = open(f"./wiki/{wikiname}/{pagename}", "r")
    md_template_string = markdown.markdown(
        file.read(), extensions=["fenced_code"]
    )

    return md_template_string

@app.route("/wiki/<wikiname>/createpage", methods=["GET", "POST"])
def pagecreate(wikiname):
    form = CreatePageForm()
    if form.validate_on_submit():
        page_name = form.name.data
        wiki = Wiki.query.filter_by(name=wikiname).one_or_none()
        if wiki is None:
            return "Wiki not found.", 404
        page_content = Page(content=form.page.data, name=page_name, wiki=wiki)
        db.session.add(page_content)
        db.session.commit()
        f = open(f"./wiki/{wikiname}/{page_name}.md", "x")
        f.write(form.page.data)
        f.close()
        return redirect(url_for('index'))
    return render_template('createpage.html', createpage_form=form)

@app.route("/")
def index():
    return render_template("index.html")