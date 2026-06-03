-- MySQL dump — Production users table
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255),
  password_hash VARCHAR(255),
  role VARCHAR(50)
);
INSERT INTO users VALUES (1,'ceo@corp.com','$2b$12$FakeHashAAAAAAAAAAAAAAAA','admin');
INSERT INTO users VALUES (2,'finance@corp.com','$2b$12$FakeHashBBBBBBBBBBBBBBBB','finance');
