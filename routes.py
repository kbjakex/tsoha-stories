from app import app
from db import db
from flask import redirect, render_template, request, session, flash, abort
from werkzeug.security import check_password_hash, generate_password_hash

@app.route("/")
def index():
    error = request.args.get("e")

    sql = "SELECT U.username, P.id, P.title, P.content, P.sent_at FROM posts P, users U WHERE P.user_id = U.id"
    result = db.session.execute(sql)
    posts = result.fetchall()
    return render_template("index.html", posts = posts, login_error = error) 

@app.route("/login",methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    register = "register" in request.form
    
    print(f"LOGIN: username {username}")

    sql = "SELECT id, password FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()    
    if not user:
        if not register:
            posts = db.session.execute("SELECT U.username, P.id, P.title, P.content, P.sent_at FROM posts P, users U WHERE P.user_id = U.id").fetchall()
            return redirect("/?e=credentials") 

        db.session.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username":username, "password":generate_password_hash(password)})
        db.session.commit()
        print(f"Username: {username}, password: {password} was NOT in database. PWHash: {generate_password_hash(password)}")
    elif register:
        posts = db.session.execute("SELECT U.username, P.id, P.title, P.content, P.sent_at FROM posts P, users U WHERE P.user_id = U.id").fetchall()
        return redirect("/?e=username") 
    session["username"] = username
    return redirect("/")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/addstory",methods=["POST"])
def addstory():
    username = session["username"]
    title = request.form["title"]
    contents = request.form["contents"]

    print(f"username: {username}")

    result = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":username}).fetchone()
    if not result:
        abort(401) # Access denied: cannot happen without intentionally malicious use of the website...
        return

    user_id = result[0]

    db.session.execute("INSERT INTO posts (title, content, user_id, parent_id, sent_at) VALUES (:title, :content, :user_id, NULL, NOW())", {"title":title, "content":contents, "user_id":user_id})
    db.session.commit()
    return redirect("/")

@app.route("/posts/<int:id>")
def page(id):
    sql = "SELECT U.username, P.id, P.title, P.content, P.sent_at FROM posts P, users U WHERE P.user_id = U.id AND P.id = :id"
    result = db.session.execute(sql, {"id":id})
    post = result.fetchone()
    return render_template("storypage.html", post = post) 