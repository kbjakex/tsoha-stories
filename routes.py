from app import app
from db import db
from flask import redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
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

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password
        self.sort_mode = "newest"

class Post:
    def __init__(self, id, title, content, sent_at, author, tags):
        self.id = id
        self.title = title
        self.content = content
        self.author = author
        self.sent_at = sent_at
        self.tags = tags
        self.num_likes = 0
        self.num_comments = 0

@login_manager.user_loader
def load_user(user_id):
    sql = "SELECT * FROM users WHERE id = :id"
    user = db.session.execute(sql, {"id": user_id}).fetchone()
    if user is None:
        return None
    
    return User(user[0], user[1], user[2])

@app.route("/")
def index():
    sort = request.args.get("sort")
    if not current_user is None:
        current_user.sort_mode = sort

    sql = "SELECT P.id, P.title, P.content, P.sent_at, U.username, T.name FROM users U, posts P LEFT JOIN tags T ON P.id = T.post_id WHERE U.id = P.user_id"
    result = db.session.execute(sql)
    posts_raw = result.fetchall()

    posts = []
    last_post_id = None
    for post in posts_raw:
        if last_post_id != post[0]:
            posts.append(Post(post[0], post[1], post[2], post[3], post[4], []))
            last_post_id = post[0]
        if post[5] is not None:
            posts[-1].tags.append(post[5])

    sql = "SELECT P.id, COUNT(L), COUNT(C) FROM likes L, posts P LEFT JOIN comments C ON  P.id = C.post_id WHERE L.post_id = P.id GROUP BY P.id"
    likes_and_comments = db.session.execute(sql).fetchall()

    for stats in likes_and_comments:
        for post in posts:
            if post.id == stats[0]:
                post.num_likes = stats[1]
                post.num_comments = stats[2]

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
        
        sql = "SELECT * FROM users WHERE username = :username"
        user = db.session.execute(sql, {"username": username}).fetchone()

        if not user is None and check_password_hash(user["password"], password):
            # lets see if it can just accept the user like this 
            login_user(User(user[0], user[1], user[2]))
            return redirect(next or "/")
        else:
            last_error = "Invalid username or password"

    return render_template("login.html", last_form_error=last_error)


@app.route("/register",methods=["GET","POST"])
def register():
    last_error = None

    if request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if password1 != password2:
            last_error = "Passwords do not match"
        else:
            sql = "SELECT * FROM users WHERE username = :username"
            user = db.session.execute(sql, {"username": username}).fetchone()

            if not user is None:
                last_error = "Username is taken"
            else:
                password = generate_password_hash(password1)
                sql = "INSERT INTO users (username, password) VALUES (:username, :password)"
                db.session.execute(sql, {"username": username, "password": password })
                db.session.commit()

                return redirect("/login")

    return render_template("register.html", last_form_error=last_error)
    

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/new",methods=["GET", "POST"])
@login_required
def addstory():
    if request.method == "POST":
        username = current_user.username
        title = request.form["title"]
        contents = request.form["content"]

        result = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":username}).fetchone()
        if not result:
            abort(401) # Access denied: cannot happen without intentionally malicious use of the website...
            return

        user_id = result[0]

        rowid = db.session.execute("INSERT INTO posts (title, content, user_id, parent_id, sent_at) VALUES (:title, :content, :user_id, NULL, NOW()) RETURNING posts.id", {"title":title, "content":contents, "user_id":user_id}).fetchone()[0]
        db.session.commit()

        # tagify outputs the tags in json format.
        json_tags = json.loads(request.form["tags"])
        for json_tag in json_tags:
            tagname = json_tag['value'] 
            db.session.execute("INSERT INTO tags (name, post_id) VALUES (:name, :post_id)", {"post_id":rowid, "name":tagname})
            db.session.commit()

        return redirect(f"/posts/{rowid}")

    return render_template("newstory.html")

@app.route("/posts/<int:id>")
def page(id):
    sql = "SELECT U.username, P.id, P.title, P.content, P.sent_at FROM posts P, users U WHERE P.user_id = U.id AND P.id = :id"
    result = db.session.execute(sql, {"id":id})
    post = result.fetchone()
    return render_template("storypage.html", post = post) 