CREATE DATABASE IF NOT EXISTS tibia2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tibia2;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(30) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE villages (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  name VARCHAR(80) NOT NULL,
  coord_x SMALLINT NOT NULL,
  coord_y SMALLINT NOT NULL,
  wood INT NOT NULL DEFAULT 500,
  clay INT NOT NULL DEFAULT 500,
  iron INT NOT NULL DEFAULT 500,
  points INT NOT NULL DEFAULT 0,
  last_resource_update TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_village_coords (coord_x, coord_y),
  CONSTRAINT fk_villages_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE buildings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  village_id INT NOT NULL,
  building_key VARCHAR(30) NOT NULL,
  level INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_village_building (village_id, building_key),
  CONSTRAINT fk_buildings_village FOREIGN KEY (village_id) REFERENCES villages(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE troops (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(30) NOT NULL UNIQUE,
  name VARCHAR(50) NOT NULL,
  attack INT NOT NULL,
  defense INT NOT NULL,
  speed INT NOT NULL,
  cost_wood INT NOT NULL,
  cost_clay INT NOT NULL,
  cost_iron INT NOT NULL,
  train_time INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE village_troops (
  village_id INT NOT NULL,
  troop_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (village_id, troop_id),
  CONSTRAINT fk_vt_village FOREIGN KEY (village_id) REFERENCES villages(id) ON DELETE CASCADE,
  CONSTRAINT fk_vt_troop FOREIGN KEY (troop_id) REFERENCES troops(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE construction_queue (
  id INT AUTO_INCREMENT PRIMARY KEY,
  village_id INT NOT NULL,
  building_key VARCHAR(30) NOT NULL,
  target_level INT NOT NULL,
  cost_wood INT NOT NULL,
  cost_clay INT NOT NULL,
  cost_iron INT NOT NULL,
  start_at TIMESTAMP NULL,
  finish_at TIMESTAMP NULL,
  status ENUM('running','done','canceled') NOT NULL DEFAULT 'running',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_construction_status (village_id, status, finish_at),
  CONSTRAINT fk_cq_village FOREIGN KEY (village_id) REFERENCES villages(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE training_queue (
  id INT AUTO_INCREMENT PRIMARY KEY,
  village_id INT NOT NULL,
  troop_id INT NOT NULL,
  quantity INT NOT NULL,
  start_at TIMESTAMP NULL,
  finish_at TIMESTAMP NULL,
  status ENUM('running','done','canceled') NOT NULL DEFAULT 'running',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_training_status (village_id, status, finish_at),
  CONSTRAINT fk_tq_village FOREIGN KEY (village_id) REFERENCES villages(id) ON DELETE CASCADE,
  CONSTRAINT fk_tq_troop FOREIGN KEY (troop_id) REFERENCES troops(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE attacks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  attacker_user_id INT NOT NULL,
  from_village_id INT NOT NULL,
  to_village_id INT NOT NULL,
  units_json JSON NOT NULL,
  depart_at TIMESTAMP NULL,
  arrival_at TIMESTAMP NULL,
  resolved_at TIMESTAMP NULL,
  winner_user_id INT NULL,
  loot_wood INT NOT NULL DEFAULT 0,
  loot_clay INT NOT NULL DEFAULT 0,
  loot_iron INT NOT NULL DEFAULT 0,
  status ENUM('traveling','arrived','resolved') NOT NULL DEFAULT 'traveling',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_attack_timing (status, arrival_at),
  CONSTRAINT fk_attacker_user FOREIGN KEY (attacker_user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_attack_from FOREIGN KEY (from_village_id) REFERENCES villages(id) ON DELETE CASCADE,
  CONSTRAINT fk_attack_to FOREIGN KEY (to_village_id) REFERENCES villages(id) ON DELETE CASCADE,
  CONSTRAINT fk_attack_winner FOREIGN KEY (winner_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE reports (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(150) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_reports_user (user_id, created_at),
  CONSTRAINT fk_reports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE tribes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE,
  tag VARCHAR(8) NOT NULL UNIQUE,
  owner_user_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tribes_owner FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE tribe_members (
  tribe_id INT NOT NULL,
  user_id INT NOT NULL,
  role ENUM('leader','member') NOT NULL DEFAULT 'member',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (tribe_id, user_id),
  UNIQUE KEY uniq_user_tribe (user_id),
  CONSTRAINT fk_tm_tribe FOREIGN KEY (tribe_id) REFERENCES tribes(id) ON DELETE CASCADE,
  CONSTRAINT fk_tm_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE tribe_chat (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tribe_id INT NOT NULL,
  user_id INT NOT NULL,
  message VARCHAR(500) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_tribe_chat (tribe_id, created_at),
  CONSTRAINT fk_tc_tribe FOREIGN KEY (tribe_id) REFERENCES tribes(id) ON DELETE CASCADE,
  CONSTRAINT fk_tc_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

INSERT INTO troops (code,name,attack,defense,speed,cost_wood,cost_clay,cost_iron,train_time) VALUES
('spear','Lanceiro',10,25,18,50,30,10,40),
('sword','Espadachim',25,50,22,30,50,20,55),
('scout','Batedor',0,2,9,60,50,40,70),
('light','Cavalaria Leve',130,40,10,125,100,250,180),
('ram','Ariete',2,20,30,300,200,200,260);
