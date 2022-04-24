CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title TEXT,
    content TEXT NOT NULL,
    user_id INTEGER REFERENCES users,
    parent_id INTEGER REFERENCES posts,
    sent_at TIMESTAMP NOT NULL
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    post_id INTEGER REFERENCES posts,
    UNIQUE(name, post_id)
);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts,
    user_id INTEGER REFERENCES users,
    sent_at TIMESTAMP NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    post_id INTEGER REFERENCES posts,
    comment_id INTEGER REFERENCES comments,
    liked_at TIMESTAMP NOT NULL,
    UNIQUE(user_id, post_id, comment_id)
);
