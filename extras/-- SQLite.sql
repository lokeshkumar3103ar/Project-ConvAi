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
