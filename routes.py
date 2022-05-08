from app import app
import db
from flask import redirect, render_template, request, abort, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
import json

from urllib.parse import urlparse, urljoin

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return db.get_user_by_id(user_id)

@app.route("/")
def index():
    sort = request.args.get("sort")
    if sort is None:
        sort = "newest"
    if not current_user is None:
        current_user.sort_mode = sort

    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id

    posts = db.get_all_posts(user_id)

    if not sort is None:
        if current_user.sort_mode == "newest":
            posts.sort(key=lambda x: x.sent_at, reverse=True)
        elif current_user.sort_mode == "oldest":
            posts.sort(key=lambda x: x.sent_at, reverse=False)
        elif current_user.sort_mode == "most_liked":
            posts.sort(key=lambda x: x.num_likes, reverse=True) 
    
    return render_template("index.html", posts = posts)

@app.route("/login",methods=["GET","POST"])
def login():
    last_error = None

    if request.method == "POST":
        next = request.args.get("next")
        if not next is None and not is_safe_url(next):
            return abort(400)
        
        username = request.form["username"]
        password = request.form["password"]
        
        user = db.get_user_by_username(username)

        if not user is None and check_password_hash(user.password, password):
            # lets see if it can just accept the user like this 
            login_user(user)
            session["csrf_token"] = secrets.token_hex(16)
            return redirect(next or "/")
        else:
            last_error = "Invalid username or password"

    return render_template("login.html", last_form_error=last_error)


@app.route("/register",methods=["GET","POST"])
def register():
    last_error = None

    if request.method == "POST":
        next = request.args.get("next")
        if not next is None and not is_safe_url(next):
            return abort(400)

        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if password1 != password2:
            return render_template("register.html", last_form_error = "Passwords do not match")

        if len(password1) < 3:
            return render_template("register.html", last_form_error = "Password must be at least 3 characters")

        user = db.get_user_by_username(username)

        if not user is None:
            return render_template("register.html", last_form_error = "Username is taken")

        password = generate_password_hash(password1)

        user = db.create_user(username, password)
        login_user(user)
        session["csrf_token"] = secrets.token_hex(16)

        return redirect(next or "/")

    return render_template("register.html", last_form_error=last_error)
    

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/new",methods=["GET", "POST"])
@login_required
def addstory():
    if request.method != "POST":
        return render_template("newstory.html")

    if session["csrf_token"] != request.form["csrf_token"]:
        return abort(403)

    title = request.form["title"]
    contents = request.form["content"]
    tags = request.form["tags"]

    if tags is not None and len(tags) > 0:
        tags = [tag['value'] for tag in json.loads(tags)]

    post_id = db.create_post(title, contents, current_user.id, tags)

    return redirect(f"/posts/{post_id}")

@app.route("/extend/<int:id>", methods=["GET", "POST"])
@login_required
def extend(id):
    parent = db.get_post_title_and_content(id)
    if parent is None:
        return abort(404)

    if request.method != "POST":
        return render_template("extend.html", parent_title=parent.title, parent_content=parent.content)

    if session["csrf_token"] != request.form["csrf_token"]:
        return abort(403)

    contents = request.form["content"]

    post_id = db.create_post(parent.title, contents, current_user.id, None, id)

    return redirect(f"/continuations/{post_id}")

@app.route("/posts/<int:id>", methods=["GET", "POST"])
def page(id):
    if request.method == "POST":
        if not current_user.is_authenticated:
            abort(401)
        if session["csrf_token"] != request.form["csrf_token"]:
            return abort(403)

        comment = request.form.get("content")
        if not comment is None and len(comment) > 0:
            db.create_comment(id, comment, current_user.id)
            return redirect('#')

    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id

    post = db.get_post_by_id(id, user_id)
    if post is None:
        return abort(404)

    return render_template("storypage.html", post = post) 

@app.route("/continuations/<int:id>", methods=["GET", "POST"])
def continuation(id):
    if request.method == "POST":
        if not current_user.is_authenticated:
            abort(401)
        if session["csrf_token"] != request.form["csrf_token"]:
            return abort(403)

        comment = request.form.get("content")
        if not comment is None and len(comment) > 0:
            db.create_comment(id, comment, current_user.id)
            return redirect('#')

    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id

    post = db.get_post_by_id(id, user_id)
    if post is None:
        return abort(404)

    return render_template("continuation.html", post = post) 

@app.route("/api/posts/<int:id>/like", methods=["POST"])
@login_required
def like(id):
    print(request)
    print(request.data)
    if session["csrf_token"] != json.loads(request.data)["token"]:
        return abort(403)

    liked = db.like_post(id, current_user.id)
    liked = "true" if liked else "false"

    likes = db.get_like_count_for_post(id)

    return f"{{ \"liked\": {liked}, \"num_likes\": {likes} }}"

@app.route("/api/posts/<int:id>/delete", methods=["GET", "POST"])
@login_required
def delete(id):
    db.delete_post(id, current_user.id)
    return redirect("/")
