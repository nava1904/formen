-- Database Schema for Chitfund Foreman Ap
create database DHARMAREDDY;
use DHARMAREDDY;
-- Table to store details of each Chit Fund
CREATE TABLE Chits (
    chit_id VARCHAR(50) PRIMARY KEY,
    chit_value DECIMAL(10, 2) NOT NULL,
    duration INT NOT NULL,
    foreman_commission_percentage DECIMAL(5, 2) NOT NULL,
    start_date DATE NOT NULL,
    installment_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'Active'
);

-- Table to store details of each Member
CREATE TABLE Members (
    member_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(20) NOT NULL UNIQUE,
    chit_id VARCHAR(50) NOT NULL,
    join_date DATE NOT NULL,
    FOREIGN KEY (chit_id) REFERENCES Chits(chit_id)
);

-- Table to store details of each Auction
CREATE TABLE Auctions (
    auction_id INT PRIMARY KEY AUTO_INCREMENT,
    chit_id VARCHAR(50) NOT NULL,
    auction_date DATE NOT NULL,
    winner_id INT,
    winning_bid_discount_percentage DECIMAL(5, 2),
    prize_money DECIMAL(10, 2),
    FOREIGN KEY (chit_id) REFERENCES Chits(chit_id),
    FOREIGN KEY (winner_id) REFERENCES Members(member_id)
);

-- Table to store details of each Contribution made by members
CREATE TABLE Contributions (
    contribution_id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT NOT NULL,
    chit_id VARCHAR(50) NOT NULL,
    month_number INT NOT NULL,
    amount_paid DECIMAL(10, 2) NOT NULL,
    payment_date DATE NOT NULL,
    FOREIGN KEY (member_id) REFERENCES Members(member_id),
    FOREIGN KEY (chit_id) REFERENCES Chits(chit_id),
    UNIQUE KEY unique_contribution (member_id, chit_id, month_number) -- Ensure one contribution per member per month per chit
);

-- Table to store details of Dividends distributed to members
CREATE TABLE Dividends (
    dividend_id INT PRIMARY KEY AUTO_INCREMENT,
    chit_id VARCHAR(50) NOT NULL,
    member_id INT NOT NULL,
    auction_date DATE NOT NULL,
    dividend_amount DECIMAL(10, 2) NOT NULL,
    distribution_date DATE NOT NULL,
    FOREIGN KEY (chit_id) REFERENCES Chits(chit_id),
    FOREIGN KEY (member_id) REFERENCES Members(member_id)
);
SELECT @@hostname;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Vnr@2003';
FLUSH PRIVILEGES;
SELECT hidost, user FROM mysql.user;
CREATE USER 'root'@'localhost' IDENTIFIED BY 'Vnr@2003';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
select * from Subscribers;
SET innodb_lock_wait_timeout = 100;
