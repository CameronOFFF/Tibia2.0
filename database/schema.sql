CREATE DATABASE IF NOT EXISTS never_duality CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE never_duality;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('OWNER','ADMIN','LEADER','MEMBER') NOT NULL DEFAULT 'MEMBER',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NULL,
  action VARCHAR(100) NOT NULL,
  details TEXT,
  created_at DATETIME NOT NULL,
  INDEX(user_id)
);

CREATE TABLE guild_members (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  vocation VARCHAR(100) DEFAULT '',
  level INT NOT NULL DEFAULT 0,
  online_status ENUM('online','offline') NOT NULL DEFAULT 'offline',
  last_update DATETIME NOT NULL
);

CREATE TABLE member_level_tracking (
  id INT AUTO_INCREMENT PRIMARY KEY,
  character_name VARCHAR(120) NOT NULL UNIQUE,
  vocation VARCHAR(100) DEFAULT '',
  level_start_week INT NOT NULL DEFAULT 0,
  level_current INT NOT NULL DEFAULT 0,
  level_gain INT NOT NULL DEFAULT 0,
  week_start_date DATE NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE character_scans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  vocation VARCHAR(100) DEFAULT '',
  level INT NOT NULL DEFAULT 0,
  guild_name VARCHAR(120) DEFAULT '',
  status ENUM('online','offline') NOT NULL DEFAULT 'offline',
  scanned_at DATETIME NOT NULL
);

CREATE TABLE hunted_list (
  id INT AUTO_INCREMENT PRIMARY KEY,
  character_name VARCHAR(120) NOT NULL,
  guild VARCHAR(120) DEFAULT '',
  reason VARCHAR(255) DEFAULT '',
  notes VARCHAR(255) DEFAULT '',
  added_by VARCHAR(50) DEFAULT '',
  created_at DATETIME NOT NULL
);

CREATE TABLE friend_list LIKE hunted_list;
CREATE TABLE neutral_list LIKE hunted_list;
CREATE TABLE ally_list LIKE hunted_list;

CREATE TABLE guild_watch (
  id INT AUTO_INCREMENT PRIMARY KEY,
  guild_name VARCHAR(120) NOT NULL,
  world VARCHAR(80) DEFAULT '',
  notes VARCHAR(255) DEFAULT '',
  added_by VARCHAR(50) DEFAULT '',
  created_at DATETIME NOT NULL
);

INSERT INTO users (username, password_hash, role) VALUES
('owner', '$2y$10$u7I8YhlhL.0J8Ff6ipRDjOO0nUxwJ4WQ5d8nJzW0E20JvokJ2Qj6W', 'OWNER');
-- senha padrão: owner123
