-- Optional sample data. Run after schema.sql:
--   mysql -u root -p banking_app < sql/seed.sql

INSERT INTO users (first_name, last_name, age, occupation) VALUES
    ('Ayşe',  'Demir',   29, 'Engineer'),
    ('Mehmet','Kaya',    41, 'Teacher'),
    ('Elif',  'Yılmaz',  23, 'Student');

INSERT INTO accounts (user_id, account_type, balance) VALUES
    (1, 'checking', 1500.00),
    (1, 'savings',  5000.00),
    (2, 'checking',  800.00),
    (3, 'savings',   250.00);

INSERT INTO transactions (account_id, transaction_type, amount) VALUES
    (1, 'credit', 1500.00),
    (2, 'credit', 5000.00),
    (3, 'credit',  800.00),
    (4, 'credit',  250.00);
