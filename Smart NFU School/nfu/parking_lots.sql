CREATE TABLE parking_lots(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    total_slots INTEGER,
    available_slots INTEGER,
    fee_per_hour INTEGER
);

INSERT  INTO parking_lots(name, address, lat, lng, total_slots, available_slots, fee_per_hour) VALUES
('第一停車場', '第一校區警衛室大門ATD與ASA旁', 23.70310, 120.43210, 120, 35, 30),
('第二停車場', '第一校區ATC與行政大樓後方', 23.70220, 120.43120, 80, 12, 25),
('第三停車場', '第一校區ATA後方', 23.70170, 120.43300, 60, 20, 20),
('第四停車場', '第一校區AGR後方', 23.70410, 120.43050, 100, 55, 35),
('第五停車場', '第三校區CPB與CPG旁', 23.70090, 120.43430, 150, 70, 40);