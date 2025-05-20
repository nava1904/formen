create database foremen;
use foremen;
-- Use a specific database (change 'chit_manager_db' to your desired database name)
-- CREATE DATABASE IF NOT EXISTS chit_manager_db;
-- USE chit_manager_db;

-- -------------------------------------------------------------------
-- Table: Subscribers
-- Represents a participant in a chit fund.
-- -------------------------------------------------------------------
CREATE TABLE Subscribers (
    id BINARY(16) PRIMARY KEY, -- Storing UUIDs as BINARY(16) is efficient for storage and indexing
    name VARCHAR(255) NOT NULL, -- Subscriber's full name
    phoneNumber VARCHAR(20) UNIQUE NOT NULL, -- Phone number, unique for each subscriber
    address TEXT, -- Optional address, using TEXT for potentially longer strings
    createdDate DATETIME NOT NULL, -- When the subscriber record was created
    isActive BOOLEAN NOT NULL DEFAULT TRUE -- Flag to indicate if the subscriber is active

    -- No direct relationships here in SQL; Many-to-Many is handled by the Enrollments table.
    -- One-to-Many to InstallmentPayments handled by FK in InstallmentPayments table.
);

-- -------------------------------------------------------------------
-- Table: ChitGroups
-- Represents a single chit scheme or group.
-- -------------------------------------------------------------------
CREATE TABLE ChitGroups (
    id BINARY(16) PRIMARY KEY, -- UUID for the group
    name VARCHAR(255) NOT NULL, -- Name of the group (e.g., "Evening Chit 10 Lakhs")
    value DOUBLE NOT NULL, -- Total value of the chit (use DECIMAL for precise currency if needed)
    numberOfSubscribers SMALLINT NOT NULL, -- Total number of slots in the group
    duration SMALLINT NOT NULL, -- Total number of installments (months)
    startDate DATE NOT NULL, -- The start date of the group
    foremanCommissionPercentage DOUBLE, -- Optional foreman commission percentage
    isActive BOOLEAN NOT NULL DEFAULT TRUE -- Flag to indicate if the group is active

    -- One-to-Many relationships to Installments and Enrollments handled by FKs in those tables.
);

-- -------------------------------------------------------------------
-- Table: Enrollments
-- Intermediary table for the Many-to-Many relationship between Subscribers and ChitGroups.
-- Represents a subscriber's specific slot/participation in a group.
-- -------------------------------------------------------------------
CREATE TABLE Enrollments (
    id BINARY(16) PRIMARY KEY, -- UUID for the enrollment record itself
    subscriberId BINARY(16) NOT NULL, -- Foreign Key referencing the Subscribers table
    groupId BINARY(16) NOT NULL, -- Foreign Key referencing the ChitGroups table
    assignedChitNumber SMALLINT NOT NULL, -- The unique slot number assigned to the subscriber in THIS group
    joinDate DATE NOT NULL, -- The date the subscriber was enrolled in this group

    -- Constraints to enforce the Many-to-Many logic and uniqueness:
    -- Ensure a subscriber can only have ONE enrollment record per group.
    UNIQUE KEY unique_enrollment_per_group (subscriberId, groupId),
    -- Ensure each assigned number is unique within a specific group.
    UNIQUE KEY unique_number_in_group (groupId, assignedChitNumber),

    -- Define Foreign Key constraints with ON DELETE rules:
    -- If a Subscriber is deleted, automatically delete their Enrollment records.
    FOREIGN KEY (subscriberId) REFERENCES Subscribers(id) ON DELETE CASCADE,
    -- If a ChitGroup is deleted, automatically delete all Enrollment records for that group.
    FOREIGN KEY (groupId) REFERENCES ChitGroups(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------------
-- Table: Installments
-- Represents each monthly cycle/period within a ChitGroup.
-- -------------------------------------------------------------------
CREATE TABLE Installments (
    id BINARY(16) PRIMARY KEY, -- UUID for the installment record
    groupId BINARY(16) NOT NULL, -- Foreign Key referencing the ChitGroups table (which group this installment belongs to)
    monthNumber SMALLINT NOT NULL, -- The sequential number of the installment (1, 2, ..., duration)
    dueDate DATE NOT NULL, -- The date the payment for this installment is due
    isAuctionConducted BOOLEAN NOT NULL DEFAULT FALSE, -- Flag if the auction for this month has occurred
    auctionPrizeAmount DOUBLE, -- Optional: The amount won in the auction for this installment
    auctionWinnerId BINARY(16), -- Optional Foreign Key referencing the Subscribers table (the winner)
    isCompleted BOOLEAN NOT NULL DEFAULT FALSE, -- Flag if this installment is considered fully collected/closed

    -- Constraint to ensure each month number is unique within a specific group.
    UNIQUE KEY unique_month_per_group (groupId, monthNumber),

    -- Define Foreign Key constraints with ON DELETE rules:
    -- If the parent ChitGroup is deleted, automatically delete all its Installments.
    FOREIGN KEY (groupId) REFERENCES ChitGroups(id) ON DELETE CASCADE,
    -- If a Subscriber who was an auction winner is deleted, set the auctionWinnerId to NULL.
    FOREIGN KEY (auctionWinnerId) REFERENCES Subscribers(id) ON DELETE SET NULL
);

-- -------------------------------------------------------------------
-- Table: InstallmentPayments
-- Represents a specific payment transaction made by a Subscriber for a specific Installment.
-- -------------------------------------------------------------------
CREATE TABLE InstallmentPayments (
    id BINARY(16) PRIMARY KEY, -- UUID for the payment transaction record
    installmentId BINARY(16) NOT NULL, -- Foreign Key referencing the Installments table (which month this payment is for)
    subscriberId BINARY(16) NOT NULL, -- Foreign Key referencing the Subscribers table (who made the payment)
    paymentDate DATETIME NOT NULL, -- The date and time the payment was recorded
    amountPaid DOUBLE NOT NULL, -- The amount paid in this transaction
    notes TEXT, -- Optional: Any notes about the payment (e.g., partial payment reason)

    -- Define Foreign Key constraints with ON DELETE rules:
    -- If the parent Installment is deleted, automatically delete its associated payment records.
    FOREIGN KEY (installmentId) REFERENCES Installments(id) ON DELETE CASCADE,
    -- If the parent Subscriber is deleted, automatically delete their payment records.
    FOREIGN KEY (subscriberId) REFERENCES Subscribers(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------------
-- Optional: Add Indexes for performance on frequently used foreign keys
-- -------------------------------------------------------------------

-- INDEX for quickly finding enrollments for a specific subscriber
-- CREATE INDEX idx_enrollments_subscriber ON Enrollments(subscriberId);
-- INDEX for quickly finding enrollments for a specific group
-- CREATE INDEX idx_enrollments_group ON Enrollments(groupId);

-- INDEX for quickly finding installments for a specific group
-- CREATE INDEX idx_installments_group ON Installments(groupId);

-- INDEX for quickly finding payments for a specific installment
-- CREATE INDEX idx_payments_installment ON InstallmentPayments(installmentId);
-- INDEX for quickly finding payments made by a specific subscriber
-- CREATE INDEX idx_payments_subscriber ON InstallmentPayments(subscriberId);
SELECT @@hostname;
ALTER USER 'foremen'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
SELECT hidost, user FROM mysql.user;
CREATE USER 'foremen'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON *.* TO 'foremen'@'localhost';
FLUSH PRIVILEGES;
select * from Subscribers;
SET innodb_lock_wait_timeout = 10;
