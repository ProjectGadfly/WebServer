
#  MAKE APPROPRIATE TABLES AND USER

# Select database gadlfy if it exists
DROP DATABASE IF EXISTS gadfly;


# Create initial database
CREATE DATABASE gadfly;


# Choose current database
USE gadfly;


# The call script table & fields
CREATE TABLE call_scripts (
  unique_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  ticket VARCHAR(255) NOT NULL UNIQUE,
  date_created TIMESTAMP NOT NULL,
  expiration_date DATETIME NOT NULL,
  scope VARCHAR(255) NULL
);


-- tags = federal, state, county, etc... should be unique since two tags with the same name will confuse users
# Create tags table
CREATE TABLE tags (
  unique_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tag_name VARCHAR(20) UNIQUE
);


-- CASCADE: Delete or update the row from the parent table, and automatically delete or update the matching rows in the child table.
# Creates the child table that points to the call_scripts and tags tables
CREATE TABLE link_callscripts_tags (
  -- may have to manually add indexs
  call_script_id INT REFERENCES call_scripts (unique_id) ON DELETE CASCADE,
  tag_id INT REFERENCES tags (unique_id) ON DELETE CASCADE
);


# Create default user
CREATE USER 'gadfly_user'@'127.0.0.1' IDENTIFIED BY 'gadfly_pw';
GRANT ALL PRIVILEGES ON * . * TO 'gadfly_user'@'127.0.0.1';
FLUSH PRIVILEGES;
