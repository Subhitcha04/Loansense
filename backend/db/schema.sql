-- LoanSense Database Schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS loansense;
USE loansense;

CREATE TABLE IF NOT EXISTS applicants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    income DECIMAL(12,2) NOT NULL,
    employment_years FLOAT NOT NULL,
    existing_loans INT DEFAULT 0,
    debt_to_income FLOAT NOT NULL,
    credit_history_years FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    term_months INT NOT NULL,
    purpose ENUM('education','personal','medical','business') NOT NULL,
    risk_score FLOAT,
    risk_tier ENUM('low','medium','high'),
    interest_rate FLOAT,
    recommended_action VARCHAR(20),
    status ENUM('pending','approved','rejected') DEFAULT 'pending',
    idempotency_key VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (applicant_id) REFERENCES applicants(id)
);

CREATE TABLE IF NOT EXISTS loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    applicant_id INT NOT NULL,
    principal DECIMAL(12,2) NOT NULL,
    interest_rate FLOAT NOT NULL,
    term_months INT NOT NULL,
    emi_amount DECIMAL(10,2) NOT NULL,
    disbursed_on DATE NOT NULL,
    status ENUM('active','closed','defaulted') DEFAULT 'active',
    FOREIGN KEY (application_id) REFERENCES loan_applications(id),
    FOREIGN KEY (applicant_id) REFERENCES applicants(id)
);

CREATE TABLE IF NOT EXISTS repayment_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    instalment_no INT NOT NULL,
    due_date DATE NOT NULL,
    emi_amount DECIMAL(10,2) NOT NULL,
    principal_component DECIMAL(10,2) NOT NULL,
    interest_component DECIMAL(10,2) NOT NULL,
    outstanding_balance DECIMAL(12,2) NOT NULL,
    status ENUM('upcoming','paid','overdue') DEFAULT 'upcoming',
    paid_on DATE,
    FOREIGN KEY (loan_id) REFERENCES loans(id)
);

CREATE TABLE IF NOT EXISTS webhook_endpoints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(300) NOT NULL,
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS webhook_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    endpoint_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    status ENUM('delivered','failed') NOT NULL,
    http_status INT,
    attempt INT DEFAULT 1,
    fired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (endpoint_id) REFERENCES webhook_endpoints(id)
);

-- Risk assessments table (stores detailed scoring)
CREATE TABLE IF NOT EXISTS risk_assessments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    risk_score FLOAT NOT NULL,
    risk_tier ENUM('low','medium','high') NOT NULL,
    interest_rate FLOAT NOT NULL,
    recommended_action VARCHAR(20) NOT NULL,
    feature_importances JSON,
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES loan_applications(id)
);

-- Payments table (tracks individual EMI payments)
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    schedule_id INT NOT NULL,
    amount_paid DECIMAL(10,2) NOT NULL,
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(id),
    FOREIGN KEY (schedule_id) REFERENCES repayment_schedules(id)
);
