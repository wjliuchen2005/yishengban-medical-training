ALTER TABLE users ALTER COLUMN school SET DEFAULT '南京医科大学';
UPDATE users SET school = '南京医科大学' WHERE school IS NULL OR TRIM(school) = '';
