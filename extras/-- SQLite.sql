-- SQLite

ALTER TABLE users
ADD COLUMN name Text;


PRAGMA table_info(users);

DELETE FROM users
WHERE name="Thamil";

UPDATE users
SET name='Thamil'
WHERE roll_number=23112011 AND username=23112011;

UPDATE users
SET name='Lokesh Kumar A R', username='23112067'
WHERE roll_number=23112067;

UPDATE users
SET name='Aravindakshan R R'
WHERE username=23112064;

SELECT * FROM users;

ALTER TABLE users
ADD COLUMN email Text NOT NULL DEFAULT '';

ALTER TABLE users RENAME TO users2;

SELECT * FROM users2;

PRAGMA table_info(users);

SELECT * FROM teachers;

INSERT INTO teachers VALUES(1,'dr_teacher','$argon2id$v=19$m=65536,t=3,p=4$VvkyIPy+pYydMEFhgennQg$9XiHnhvaH4LmI7yX74x+lgdqxtikAVxoNhuVF5uYZa4',NULL);

UPDATE users
SET email="mthamilelelan@gmail.com"
WHERE roll_number=23112011;

SELECT * FROM users;

UPDATE users
SET email="lokeshkumar3103ar@gmail.com"
WHERE roll_number=23112067;

SELECT * FROM users;

SELECT * FROM password_reset_tokens;

ALTER TABLE users
ADD COLUMN classname Varchar(20);

DELETE FROM users
WHERE roll_number=23112001;

UPDATE users 
SET classname="CSE5A"
WHERE roll_number LIKE '2311%';

UPDATE users
SET classname="CSE4A"
WHERE roll_number=23112023;