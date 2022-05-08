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
    parent_id INTEGER REFERENCES posts ON DELETE CASCADE,
    ancestors INTEGER NOT NULL,
    sent_at TIMESTAMP NOT NULL
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    post_id INTEGER REFERENCES posts (id) ON DELETE CASCADE,
    UNIQUE(name, post_id)
);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts (id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users (id) ON DELETE CASCADE,
    sent_at TIMESTAMP NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users (id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts (id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES comments (id) ON DELETE CASCADE,
    liked_at TIMESTAMP NOT NULL,
    UNIQUE(user_id, post_id, comment_id)
);
