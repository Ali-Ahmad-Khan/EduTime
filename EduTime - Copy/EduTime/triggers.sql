-- ============================================
-- EduTime DBMS Project – Triggers
-- ============================================

USE edutime_final;

-- 1. Log user account creation
-- This trigger logs when a new user account is created
DELIMITER //
CREATE TRIGGER after_user_insert
AFTER INSERT ON UserAccount
FOR EACH ROW
BEGIN
    INSERT INTO UserActivityLog (User_ID, Activity, ActivityTime)
    VALUES (NEW.User_ID, CONCAT('New ', NEW.Role, ' account created'), NOW());
END//
DELIMITER ;

-- 2. Prevent scheduling conflicts for instructors
-- This trigger prevents an instructor from being scheduled at the same time
DELIMITER //
CREATE TRIGGER before_schedule_insert
BEFORE INSERT ON ClassSchedule
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT;
    
    -- Check if instructor is already scheduled at this time
    SELECT COUNT(*) INTO conflict_count
    FROM ClassSchedule
    WHERE Instructor_ID = NEW.Instructor_ID 
    AND TimeSlot_ID = NEW.TimeSlot_ID;
    
    IF conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Instructor already has a class at this time';
    END IF;
END//
DELIMITER ;

-- 3. Auto-update appointment status when counter-proposed
-- This trigger automatically updates appointment status when times are changed
DELIMITER //
CREATE TRIGGER before_appointment_update
BEFORE UPDATE ON Appointment
FOR EACH ROW
BEGIN
    -- If times are changed but status wasn't explicitly updated, set to counter-proposed
    IF (NEW.StartTime != OLD.StartTime OR NEW.EndTime != OLD.EndTime) 
       AND NEW.Status = OLD.Status AND OLD.Status = 'PENDING' THEN
        SET NEW.Status = 'COUNTER_PROPOSED';
    END IF;
END//
DELIMITER ;

-- Note: Before using these triggers, create the UserActivityLog table:
CREATE TABLE IF NOT EXISTS UserActivityLog (
    Log_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT,
    Activity VARCHAR(255) NOT NULL,
    ActivityTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID) REFERENCES UserAccount(User_ID) ON DELETE SET NULL
); 