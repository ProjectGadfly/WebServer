# Select database gadlfy if it exists
DROP DATABASE IF EXISTS gadfly;

# Create initial database
CREATE DATABASE gadfly;

# Choose current database
USE gadfly;


# The call script table & fields
CREATE TABLE call_scripts (
  row_num INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  unique_id VARCHAR(255) NOT NULL UNIQUE,
  date_created TIMESTAMP NOT NULL,
  expiration_date DATETIME NOT NULL,
  scope VARCHAR(255) NULL,
  email_address VARCHAR(255) NULL
);
