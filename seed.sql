CREATE TABLE branches (
    branch_id INT PRIMARY KEY AUTO_INCREMENT,
    branch_name VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    phone_number VARCHAR(20)
);

INSERT INTO branches (branch_name, address, city, state, zip_code, phone_number) VALUES
('Downtown Central', '123 Main St', 'Metropolis', 'TX', '78701', '512-555-0101'),
('Northside Financial', '456 Oak Ave', 'Metropolis', 'TX', '78758', '512-555-0102'),
('West Lake Hills', '789 Pine Ln', 'West Lake', 'TX', '78746', '512-555-0103');

CREATE TABLE employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    branch_id INT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

INSERT INTO employees (branch_id, first_name, last_name, position, hire_date, email) VALUES
(1, 'Alice', 'Johnson', 'Branch Manager', '2018-05-20', 'alice.j@fakebank.com'),
(1, 'Bob', 'Williams', 'Teller', '2022-08-15', 'bob.w@fakebank.com'),
(2, 'Charlie', 'Brown', 'Loan Officer', '2020-02-10', 'charlie.b@fakebank.com'),
(3, 'Diana', 'Miller', 'Teller', '2023-01-30', 'diana.m@fakebank.com');

CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    phone_number VARCHAR(20),
    email VARCHAR(255) UNIQUE NOT NULL,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customers (first_name, last_name, date_of_birth, address, city, state, zip_code, phone_number, email) VALUES
('John', 'Smith', '1985-04-12', '101 Maple Dr', 'Metropolis', 'TX', '78704', '512-555-1122', 'john.smith@email.com'),
('Jane', 'Doe', '1992-08-22', '202 Birch Rd', 'Metropolis', 'TX', '78759', '512-555-3344', 'jane.doe@email.com'),
('Peter', 'Jones', '1978-11-30', '303 Cedar Blvd', 'West Lake', 'TX', '78746', '512-555-5566', 'peter.jones@email.com');

CREATE TABLE accounts (
    account_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    branch_id INT,
    account_type ENUM('Checking', 'Savings', 'Money Market', 'Certificate of Deposit') NOT NULL,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    open_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Active', 'Closed', 'Frozen') NOT NULL DEFAULT 'Active',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

INSERT INTO accounts (customer_id, branch_id, account_type, account_number, balance, status) VALUES
(1, 1, 'Checking', 'CHK000123456', 5450.75, 'Active'),
(1, 1, 'Savings', 'SAV000123457', 25300.00, 'Active'),
(2, 2, 'Checking', 'CHK000789012', 8210.50, 'Active'),
(3, 3, 'Money Market', 'MM000345678', 150250.20, 'Active');

CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT,
    transaction_type ENUM('Deposit', 'Withdrawal', 'Transfer', 'Fee', 'Interest') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR(255),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

INSERT INTO transactions (account_id, transaction_type, amount, transaction_date, description) VALUES
(1, 'Deposit', 1200.00, '2025-07-20 10:00:00', 'Paycheck'),
(2, 'Deposit', 5000.00, '2025-07-21 11:30:00', 'Initial Deposit'),
(1, 'Withdrawal', 50.00, '2025-07-22 15:45:00', 'ATM Withdrawal'),
(3, 'Withdrawal', 2500.00, '2025-07-23 09:15:00', 'Online Shopping'),
(1, 'Transfer', -200.00, '2025-07-25 14:00:00', 'Transfer to account SAV000123457'),
(2, 'Transfer', 200.00, '2025-07-25 14:00:00', 'Transfer from account CHK000123456'),
(4, 'Interest', 150.25, '2025-07-28 01:00:00', 'Monthly Interest Earned');

CREATE TABLE loans (
    loan_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    loan_type ENUM('Mortgage', 'Auto', 'Personal') NOT NULL,
    principal_amount DECIMAL(15, 2) NOT NULL,
    interest_rate DECIMAL(5, 4) NOT NULL,
    term_months INT NOT NULL,
    start_date DATE NOT NULL,
    status ENUM('Active', 'Paid Off', 'Default') NOT NULL DEFAULT 'Active',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

INSERT INTO loans (customer_id, loan_type, principal_amount, interest_rate, term_months, start_date, status) VALUES
(1, 'Auto', 25000.00, 0.0450, 60, '2023-06-15', 'Active'),
(3, 'Mortgage', 450000.00, 0.0625, 360, '2024-02-01', 'Active');

CREATE TABLE cards (
    card_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT,
    card_number VARCHAR(20) UNIQUE NOT NULL,
    card_type ENUM('Debit', 'Credit') NOT NULL,
    expiration_date VARCHAR(5) NOT NULL,
    cvv VARCHAR(4) NOT NULL,
    status ENUM('Active', 'Lost', 'Stolen', 'Expired') NOT NULL DEFAULT 'Active',
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

INSERT INTO cards (account_id, card_number, card_type, expiration_date, cvv) VALUES
(1, '4111222233334444', 'Debit', '08/28', '123'),
(3, '377788889999000', 'Credit', '11/27', '4567');