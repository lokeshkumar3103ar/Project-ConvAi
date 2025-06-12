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
