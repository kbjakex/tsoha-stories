from app import app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from os import getenv

def _get_db_uri():
    db_uri = getenv("DATABASE_URL")
    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    return db_uri

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = _get_db_uri()
db = SQLAlchemy(app)

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
        self.liked = False
        self.num_comments = 0
        self.comments = []

def get_user_by_id(user_id):
    sql = "SELECT * FROM users WHERE id = :id"
    user = db.session.execute(sql, {"id": user_id}).fetchone()
    if user is None:
        return None
    
    return User(user[0], user[1], user[2])

def get_user_by_username(username):
    sql = "SELECT * FROM users WHERE username = :username"
    user = db.session.execute(sql, {"username": username}).fetchone()
    if user is None:
        return None

    return User(user[0], user[1], user[2])

def create_user(username, password):
    sql = "INSERT INTO users (username, password) VALUES (:username, :password) RETURNING id"
    id = db.session.execute(sql, {"username": username, "password": password }).fetchone()[0]
    db.session.commit()

    return User(id, username, password)


def get_all_posts(user_id = None):
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

    sql = "SELECT P.id, (SELECT COUNT(*) FROM Likes L WHERE L.post_id = P.id), (SELECT COUNT(*) FROM Comments C WHERE C.post_id = P.id) FROM posts P GROUP BY P.id"
    likes_and_comments = db.session.execute(sql).fetchall()

    for stats in likes_and_comments:
        for post in posts:
            if post.id == stats[0]:
                post.num_likes = stats[1]
                post.num_comments = stats[2]

    if not user_id is None:
        sql = "SELECT P.id FROM posts P, likes L WHERE L.user_id = :user_id AND L.post_id = P.id"
        liked_posts = db.session.execute(sql, {"user_id": user_id}).fetchall()
        for post in posts:
            if post.id in [p[0] for p in liked_posts]:
                post.liked = True

    return posts

def get_post_by_id(post_id: int, current_user_id: int = None) -> Post:
    sql = "SELECT P.id, P.title, P.content, P.sent_at, U.username, U.id, T.name FROM users U, posts P LEFT JOIN tags T ON P.id = T.post_id WHERE U.id = P.user_id AND P.id = :post_id"
    post_raw_all = db.session.execute(sql, {"post_id": post_id}).fetchall()

    if post_raw_all is None or len(post_raw_all) == 0:
        return None
    
    post_raw = post_raw_all[0]
    post = Post(post_raw[0], post_raw[1], post_raw[2], post_raw[3], post_raw[4], [])
    for tuple in post_raw_all:
        if tuple[6] is not None:
            post.tags.append(tuple[6])

    # Check if user has liked the post
    if not current_user_id is None:
        sql = "SELECT COUNT(*), SUM(CASE WHEN U.id = :user_id THEN 1 ELSE 0 END) FROM users U, likes L WHERE U.id = L.user_id AND L.post_id = :post_id"
        likes = db.session.execute(sql, {"post_id": post_id, "user_id": current_user_id}).fetchone()
        if not likes[1] is None and likes[1] > 0:
            post.liked = True

        post.num_likes = likes[0]
        post.can_delete = current_user_id == post_raw[5]
        post.can_edit = post.can_delete and not post.sent_at < datetime.now() - timedelta(minutes=30)

    sql = "SELECT P.id, U.username FROM users U, posts P WHERE U.id = P.user_id AND P.parent_id = :post_id"
    post.continuations = db.session.execute(sql, {"post_id": post_id}).fetchall()

    sql = "SELECT U.username, C.content, C.sent_at, COUNT(L.id) FROM users U, comments C LEFT JOIN Likes L ON L.comment_id = C.id WHERE C.post_id = :post_id AND U.id = C.user_id GROUP BY C.id, U.id ORDER BY C.sent_at DESC"
    post.comments = db.session.execute(sql, {"post_id":post_id}).fetchall()

    return post

def create_post(title: str, content: str, author_id: int, tags: list = None) -> int:
    rowid = db.session.execute(
        "INSERT INTO posts (title, content, user_id, parent_id, sent_at) VALUES (:title, :content, :user_id, NULL, NOW()) RETURNING posts.id", 
        { "title": title, "content": content, "user_id": author_id }
    ).fetchone()[0]

    db.session.commit()
    
    if not tags is None and len(tags) > 0:
        for tag in tags:
            db.session.execute("INSERT INTO tags (name, post_id) VALUES (:name, :post_id)", {"post_id":rowid, "name":tag})
            db.session.commit()

    return rowid

def edit_post(post_id: int, title: str, content: str, tags: list = None) -> bool:
    sql = "UPDATE posts SET title = :title, content = :content WHERE id = :post_id"
    db.session.execute(sql, {"title": title, "content": content, "post_id": post_id})
    db.session.commit()

    if not tags is None and len(tags) > 0:
        sql = "DELETE FROM tags WHERE post_id = :post_id"
        db.session.execute(sql, {"post_id": post_id})
        db.session.commit()

        for tag in tags:
            db.session.execute("INSERT INTO tags (name, post_id) VALUES (:name, :post_id)", {"post_id":post_id, "name":tag})
            db.session.commit()

    return True

def delete_post(post_id: int, user_id: int):
    sql = "DELETE FROM posts WHERE id = :post_id AND user_id = :user_id"
    db.session.execute(sql, {"post_id": post_id, "user_id": user_id })
    db.session.commit()

def create_comment(post_id: int, content: str, author_id: int) -> int:
    db.session.execute(
        "INSERT INTO comments (post_id, content, user_id, sent_at) VALUES (:post_id, :content, :user_id, NOW())",
        { "post_id": post_id, "content": content, "user_id": author_id }
    )

    db.session.commit()

def like_post(post_id: int, user_id: int) -> bool:
    sql = "SELECT * FROM likes WHERE user_id = :user_id AND post_id = :post_id"
    result = db.session.execute(sql, {"user_id": user_id, "post_id": post_id})
    liked = False
    if result.fetchone() is None:
        liked = True
        db.session.execute("INSERT INTO likes (user_id, post_id, liked_at) VALUES (:user_id, :post_id, NOW())", {"user_id": user_id, "post_id": post_id})
    else:
        db.session.execute("DELETE FROM likes WHERE user_id = :user_id AND post_id = :post_id", {"user_id": user_id, "post_id": post_id})

    db.session.commit()
    return liked

def get_like_count_for_post(post_id: int) -> int:
    sql = "SELECT COUNT(*) FROM likes WHERE post_id = :post_id"
    return db.session.execute(sql, {"post_id": post_id}).fetchone()[0]