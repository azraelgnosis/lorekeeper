DROP TABLE IF EXISTS user;

CREATE TABLE user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_val TEXT NOT NULL,
    password TEXT NOT NULL
);

INSERT INTO user (user_id, user_val, password) VALUES (1, "admin", "admin");