CREATE DATABASE school;
USE school;
CREATE TABLE student(
id INt PRIMARY KEY,
name VARCHAR(50),
age INt,
class VARCHAR(20),
time TIMESTAMP DEFAULT 
CURRENT_TIMESTAMP
);
INSERT INTO student(name,age,class) VALUES
(1,'Tom',18,'二專電子一甲');
(2,'Amy',17,'二專電子一甲');
SELECT*FROM student;
SELECT*FROM student
WHERE class ='二專電子一甲';
UPDATE student 
SET age =19
where name='Tom';
DELETE FROM sutdent 
WHERE name ='Amy';

SELECT*FROM student;