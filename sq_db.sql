CREATE TABLE IF NOT EXISTS mainmenu (
    id integer PRIMARY KEY AUTOINCREMENT,
    title text NOT NULL,
    url text NOT NULL
);

create table if not exists posts (
    id integer primary key autoincrement,
    title text not null,
    text text not null,
    url text not null,
    time integer not null
);

create table if not exists users (
    id integer primary key autoincrement,
    name text not null,
    email text not null,
    psw text not null,
    time integer not null
);