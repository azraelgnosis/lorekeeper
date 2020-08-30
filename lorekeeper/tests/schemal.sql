DROP TABLE IF EXISTS color;
DROP TABLE IF EXISTS shape;

CREATE TABLE color (
    color_id INTEGER PRIMARY KEY AUTOINCREMENT,
    color_val TEXT NOT NULL UNIQUE,
    hex TEXT UNIQUE
);

CREATE TABLE shape (
    shape_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shape_val TEXT NOT NULL UNIQUE,
    sides INTEGER
);

CREATE TABLE person (
    person_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_val TEXT NOT NULL,
);

CREATE TABLE map_friend (
    
);