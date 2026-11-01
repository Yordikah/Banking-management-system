-- Banking Management System - database schema (MySQL 8+)
-- Run with:  mysql -u root -p < sql/schema.sql

CREATE DATABASE IF NOT EXISTS banking_app;
USE banking_app;

CREATE TABLE IF NOT EXISTS users (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    age         INT          NOT NULL,
    occupation  VARCHAR(100),
    CONSTRAINT chk_users_age CHECK (age BETWEEN 18 AND 120)
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT            NOT NULL,
    account_type  VARCHAR(20)    NOT NULL,
    balance       DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_accounts_user FOREIGN KEY (user_id) REFERENCES users (user_id),
    CONSTRAINT chk_accounts_balance CHECK (balance >= 0),
    CONSTRAINT chk_accounts_type CHECK (account_type IN ('savings', 'checking', 'business'))
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id    INT AUTO_INCREMENT PRIMARY KEY,
    account_id        INT            NOT NULL,
    transaction_type  VARCHAR(10)    NOT NULL,
    amount            DECIMAL(15, 2) NOT NULL,
    created_at        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transactions_account FOREIGN KEY (account_id) REFERENCES accounts (account_id),
    CONSTRAINT chk_transactions_type CHECK (transaction_type IN ('credit', 'debit')),
    CONSTRAINT chk_transactions_amount CHECK (amount > 0),
    INDEX idx_transactions_account (account_id, created_at)
);
