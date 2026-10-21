ALTER TABLE Users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0;
UPDATE Users SET is_admin = 1 WHERE email = 'ravigovani16@gmail.com';
