from flask import Blueprint, render_template, flash, redirect, url_for, session, g, make_response, current_app, request
from app.auth.forms import RegistrationForm
from app import db
from app.models import User
from app.auth.forms import LoginForm
from werkzeug.local import LocalProxy
from itsdangerous.url_safe import URLSafeSerializer

auth = Blueprint("auth", __name__, template_folder="templates")

current_user = LocalProxy(lambda: get_current_user())

def login_user(user):
    session["user_id"] = user.id

@auth.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user:

            if user.check_password(password):
                #flash("You are successfully logged in.", "success")
                login_user(user)
                # Une fois l'utilisateur connecté on vérifie si remember est actif
                if form.remember_me.data:
                    resp = make_response(redirect(url_for("main.home")))
                    # Envoyer les cookies au navigateur
                    remember_token = user.get_remember_token()
                    db.session.commit()
                    # Stocker les cookies dans des variables
                    resp.set_cookie('remember_token', encrypt_cookie(remember_token), max_age=60*10)
                    resp.set_cookie('user_id', encrypt_cookie(user.id), max_age=60*10)
                    return resp
                return redirect(url_for("main.home"))
            else:
                form.password.errors.append("The password is not correct.")
        else:
            form.username.errors.append("The username is not correct.")

    return render_template("login.html", form=form)

@auth.route("/logout")
def logout():
    form = LoginForm()
    if current_user.is_authenticated():
        current_user.forget()
        db.session.commit()
        resp = make_response(redirect(url_for("main.home")))
        resp.set_cookie("remember_token", "", max_age=0)
        resp.set_cookie("user_id", "", max_age=0)
        logout_user()
        flash("You are logged out", "success")
        return render_template("login.html", form=form)
        #flash("You are logged out", "success")
    return redirect(url_for("main.home"))

def logout_user():
    session.pop("user_id")

@auth.app_context_processor
def inject_current_user():
    return dict(current_user=get_current_user())

def get_current_user():
    _current_user = getattr(g, "_current_user", None)
    if _current_user is None:
        if session.get("user_id"):
            user = User.query.get(session.get("user_id"))
            if user:
                _current_user = g._current_user = user
        elif request.cookies.get("user_id"):
            user = User.query.get(int(decrypt_cookie(request.cookies.get("user_id"))))
            if user and user.check_remember_token(decrypt_cookie(request.cookies.get("remember_token"))):
                login_user(user)
                _current_user = g._current_user = user

    if _current_user is None:
        _current_user = User()
    return _current_user

# Crypter nos cookies
def encrypt_cookie(content):
    s = URLSafeSerializer(current_app.config["SECRET_KEY"], salt="cookie")
    encrypted_content = s.dumps(content)
    return encrypted_content

# Decrypter nos cookies
def decrypt_cookie(encrypted_content):
    s = URLSafeSerializer(current_app.config["SECRET_KEY"], salt="cookie")
    try:
        content = s.loads(encrypted_content)
    except:
        content = "-1"
    return content

@auth.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        location = form.location.data
        description = form.description.data

        user = User(username, email, password, location, description)
        db.session.add(user)
        db.session.commit()
        flash("You are registered", "success")
        return redirect(url_for("main.home"))

    return render_template("register.html", form=form)
