CREATE SCHEMA files;

CREATE TABLE `files`.`services` (
  `pk_id_service` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `service` varchar(45) NOT NULL,
  PRIMARY KEY (`pk_id_service`),
  UNIQUE KEY `pk_id_service_UNIQUE` (`pk_id_service`),
  UNIQUE KEY `service_UNIQUE` (`service`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `files`.`file_log` (
  `pk_id_file_log` int NOT NULL AUTO_INCREMENT,
  `old_file` varchar(255) NOT NULL,
  `new_file` varchar(255) NOT NULL,
  `fk_id_service` int NOT NULL,
  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`pk_id_file_log`,`old_file`,`fk_id_service`),
  KEY `fk_id_service_idx` (`fk_id_service`),
  CONSTRAINT `fk_id_service` FOREIGN KEY (`fk_id_service`) REFERENCES `services` (`pk_id_service`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE USER 'fileapp'@'localhost' IDENTIFIED BY '12345678';

GRANT SELECT, INSERT, DELETE, UPDATE ON files.* TO 'fileapp';

commit;