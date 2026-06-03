CREATE DATABASE IF NOT EXISTS nfu_school
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE nfu_school;

CREATE TABLE IF NOT EXISTS parking_lots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    lat DOUBLE NOT NULL,
    lng DOUBLE NOT NULL,
    total_slots INT,
    available_slots INT,
    fee_per_hour INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO parking_lots (name, address, lat, lng, total_slots, available_slots, fee_per_hour) VALUES
('第一停車場', '第一校區警衛室大門ATD與ASA旁', 23.70310, 120.43210, 120, 35, 30),
('第二停車場', '第一校區ATC與行政大樓後方', 23.70220, 120.43120, 80, 12, 25),
('第三停車場', '第一校區ATA後方', 23.70170, 120.43300, 60, 20, 20),
('第四停車場', '第一校區AGR後方', 23.70410, 120.43050, 100, 55, 35),
('第五停車場', '第三校區CPB與CPG旁', 23.70090, 120.43430, 150, 70, 40);

CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
