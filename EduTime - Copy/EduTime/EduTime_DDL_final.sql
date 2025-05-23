-- ============================================
-- EduTime DBMS Project
-- ============================================

-- 1. Create Database
CREATE DATABASE IF NOT EXISTS edutime_final;
USE edutime_final;


CREATE TABLE Department (
    Department_ID INT AUTO_INCREMENT PRIMARY KEY,
    Prefix  VARCHAR(5)  NOT NULL UNIQUE,
    Name    VARCHAR(60) NOT NULL UNIQUE
);



-- 2. User & Roles Tables
-- -----------------------

-- 2.1 UserAccount: All user roles
CREATE TABLE UserAccount (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(80) NOT NULL,
    Email VARCHAR(120) NOT NULL UNIQUE,
    Role ENUM('ADMIN', 'INSTRUCTOR', 'STUDENT') NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 Administrator
CREATE TABLE Administrator (
    Admin_ID INT PRIMARY KEY,
    User_ID INT NOT NULL UNIQUE,
    FOREIGN KEY (User_ID) REFERENCES UserAccount(User_ID) ON DELETE CASCADE
);

-- 2.3 Instructor
CREATE TABLE Instructor (
    Instructor_ID INT PRIMARY KEY,
    User_ID INT NOT NULL UNIQUE,
    Department_ID INT NOT NULL,
    FOREIGN KEY (User_ID) REFERENCES UserAccount(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Department_ID) REFERENCES Department(Department_ID) ON DELETE CASCADE
);

-- 2.4 Student
CREATE TABLE Student (
    Student_ID INT PRIMARY KEY,
    User_ID INT NOT NULL UNIQUE,
    CMS_ID VARCHAR(20) NOT NULL,
    Department_ID INT NOT NULL,
    FOREIGN KEY (User_ID) REFERENCES UserAccount(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Department_ID) REFERENCES Department(Department_ID) ON DELETE CASCADE
);


-- 3. Program Structure Tables
-- ---------------------------

-- 3.1 Degree
CREATE TABLE Degree (
    Degree_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(60) NOT NULL UNIQUE,
    Department_ID INT NOT NULL,
    FOREIGN KEY (Department_ID) REFERENCES Department(Department_ID) ON DELETE CASCADE
);

-- 3.2 Semester
CREATE TABLE Semester (
    Semester_ID INT AUTO_INCREMENT PRIMARY KEY,
    Degree_ID INT NOT NULL,
    Semester_No TINYINT UNSIGNED NOT NULL,
    UNIQUE (Degree_ID, Semester_No),
    FOREIGN KEY (Degree_ID) REFERENCES Degree(Degree_ID) ON DELETE CASCADE
);

-- 3.3 Course
CREATE TABLE Course (
    Course_ID INT AUTO_INCREMENT PRIMARY KEY,
    Degree_ID INT NOT NULL,
    Semester_ID INT NOT NULL,
    Name VARCHAR(120) NOT NULL,
    CreditHours TINYINT UNSIGNED NOT NULL,
    IsLab BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (Semester_ID, Name),
    FOREIGN KEY (Degree_ID) REFERENCES Degree(Degree_ID) ON DELETE CASCADE,
    FOREIGN KEY (Semester_ID) REFERENCES Semester(Semester_ID) ON DELETE CASCADE
);

/* =========================================================
   4.  RESOURCE TABLES
   ========================================================= */

-- 4.1 Classroom: both lecture rooms and labs
CREATE TABLE Classroom (
    Room_ID     INT AUTO_INCREMENT PRIMARY KEY,
    RoomNumber  VARCHAR(20) NOT NULL UNIQUE,
    RoomType    ENUM('CLASSROOM', 'LAB') NOT NULL,
    Department_ID INT NOT NULL,
    FOREIGN KEY (Department_ID) REFERENCES Department(Department_ID) ON DELETE CASCADE
    -- Capacity can be added later if needed
);

-- 4.2 TimeSlot: 7 usable 50-min slots per weekday (break hour excluded)
CREATE TABLE TimeSlot (
    TimeSlot_ID INT AUTO_INCREMENT PRIMARY KEY,
    Day ENUM('MON','TUE','WED','THU','FRI') NOT NULL,
    Slot_No  TINYINT UNSIGNED NOT NULL,          -- 1 … 7
    StartTime TIME NOT NULL,
    EndTime   TIME NOT NULL,
    UNIQUE (Day, Slot_No)                        -- prevents duplicates
    /* example data:
       ('MON',1,'09:00','09:50'), ('MON',2,'10:00','10:50'), ...,
       skip slot 5 ('12:50'–'14:00' break), up to slot 7 ending 16:50
    */
);


/* =========================================================
   5.  RELATIONSHIP / JUNCTION TABLES
   ========================================================= */

-- 5.1 Teaches: which instructor can teach which course
CREATE TABLE Teaches (
    Instructor_ID INT NOT NULL,
    Course_ID     INT NOT NULL,
    PRIMARY KEY (Instructor_ID, Course_ID),
    FOREIGN KEY (Instructor_ID) REFERENCES Instructor(Instructor_ID) ON DELETE CASCADE,
    FOREIGN KEY (Course_ID)     REFERENCES Course(Course_ID)         ON DELETE CASCADE
);


/* =========================================================
   6.  CORE SCHEDULING TABLE
   ========================================================= */

CREATE TABLE ClassSchedule (
    Schedule_ID   INT AUTO_INCREMENT PRIMARY KEY,
    Course_ID     INT NOT NULL,
    Instructor_ID INT NOT NULL,
    Semester_ID   INT NOT NULL,
    Room_ID       INT NOT NULL,
    TimeSlot_ID   INT NOT NULL,
    Duration      TINYINT UNSIGNED NOT NULL DEFAULT 1,  -- 1 = standard lecture, 3 = 3-slot lab
    -- ------------------------------------------------------
    FOREIGN KEY (Course_ID)     REFERENCES Course(Course_ID)         ON DELETE CASCADE,
    FOREIGN KEY (Instructor_ID) REFERENCES Instructor(Instructor_ID) ON DELETE CASCADE,
    FOREIGN KEY (Semester_ID)   REFERENCES Semester(Semester_ID)     ON DELETE CASCADE,
    FOREIGN KEY (Room_ID)       REFERENCES Classroom(Room_ID)        ON DELETE CASCADE,
    FOREIGN KEY (TimeSlot_ID)   REFERENCES TimeSlot(TimeSlot_ID)     ON DELETE CASCADE,
    -- Unique constraints to enforce NO conflicts
    UNIQUE KEY uk_room_slot        (Room_ID, TimeSlot_ID),
    UNIQUE KEY uk_instructor_slot  (Instructor_ID, TimeSlot_ID),
    UNIQUE KEY uk_semester_slot    (Semester_ID, TimeSlot_ID),
    CHECK (Duration IN (1,3))
);


/* =========================================================
   7.  SIMPLE APPOINTMENT TABLE (optional enhancement)
   ========================================================= */

CREATE TABLE Appointment (
    Appointment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Student_ID     INT NOT NULL,
    Instructor_ID  INT NOT NULL,
    ApptDate       DATE NOT NULL,
    StartTime      TIME NOT NULL,
    EndTime        TIME NOT NULL,
    Purpose        VARCHAR(255),
    Status         ENUM('PENDING', 'CONFIRMED', 'REJECTED', 'COUNTER_PROPOSED') NOT NULL DEFAULT 'PENDING',
    CreatedAt      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Student_ID)    REFERENCES Student(Student_ID)       ON DELETE CASCADE,
    FOREIGN KEY (Instructor_ID) REFERENCES Instructor(Instructor_ID) ON DELETE CASCADE
);

/* =========================================================
   END OF DDL
   ========================================================= */
