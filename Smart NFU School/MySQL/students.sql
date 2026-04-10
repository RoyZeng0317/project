-- create database(建立資料庫)
CREATE DATABASE IF NOT EXISTS school_parking;
USE school_parking;
-- creare basic profile of stdent(建立學生基本資料)
CREATE TABLE students(
    student_id VARCHAR(20) PRIMARY key,
    class_name VARCHAR(50) NOT NULL,
    name VARCHAR(50) NOT NULL
);

-- create table of parking lot logs(建立停車場表格)
CREATE TABLE parking_logs(
    id INT AUTO_INCREMENT PRIMARY key,
    student_id VARCHAR(20),
    recode_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    available_spaces INT,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
-- make sure the students profile are already saved(確保學生資料已存在)
INSERT INTO students(student_id, class_name, name)
VALUES('21414101', '二子一甲', '');
VALUES('21414102', '二子一甲', '');
VALUES('21414103', '二子一甲', '');
VALUES('21414104', '二子一甲', '');
VALUES('21414105', '二子一甲', '');
VALUES('21414106', '二子一甲', '');
VALUES('21414107', '二子一甲', '');
VALUES('21414108', '二子一甲', '');
VALUES('21414109', '二子一甲', '');
VALUES('21414110', '二子一甲', '');
VALUES('21414111', '二子一甲', '邱致綸');
VALUES('21414112', '二子一甲', '');
VALUES('21414113', '二子一甲', '');
VALUES('21414114', '二子一甲', '');
VALUES('21414115', '二子一甲', '');
VALUES('21414116', '二子一甲', '');
VALUES('21414117', '二子一甲', '');
VALUES('21414118', '二子一甲', '');
VALUES('21414119', '二子一甲', '');
VALUES('21414120', '二子一甲', '');
VALUES('21414121', '二子一甲', '');
VALUES('21414122', '二子一甲', '');
VALUES('21414123', '二子一甲', '');
VALUES('21414124', '二子一甲', '');
VALUES('21414125', '二子一甲', '');
VALUES('21414126', '二子一甲', '');
VALUES('21414127', '二子一甲', '');
VALUES('21414128', '二子一甲', '');
VALUES('21414129', '二子一甲', '');
VALUES('21414131', '二子一甲', '');
VALUES('21414132', '二子一甲', '');
VALUES('21414133', '二子一甲', '');
VALUES('21414134', '二子一甲', '');
VALUES('21414135', '二子一甲', '');
VALUES('21414136', '二子一甲', '');
VALUES('21414137', '二子一甲', '');
VALUES('21414138', '二子一甲', '');
VALUES('21414139', '二子一甲', '鐘奕其');
-- create when the parking infomation (紀錄停車當下的資訊)
INSERT INTO parking_logs (student_id, latitude, longitude, available_spaces)
VALUES('')

-- display the table of name, class id, time, place and available space(顯示姓名、班級、時間、地點及剩餘車位)
s.class_name,
s.student_id,
s.name,
p.recode_time,
p.latitude,
p.longitude,
p.available_spaces
FROM parking_logs p
JOIN students s ON p.student_id = s.student_id
ORDER BY p.recode_time DESC;

SELECT*FROM student;