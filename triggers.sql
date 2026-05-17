USE `mydb` ;

DROP PROCEDURE IF EXISTS circular_supervision;
DROP PROCEDURE IF EXISTS surgery_constraints;
DROP PROCEDURE IF EXISTS validate_shift_staffing;

DROP TRIGGER IF EXISTS ins_doctor;
DROP TRIGGER IF EXISTS upd_doctor;
DROP TRIGGER IF EXISTS ins_admission_cost_calculation;
DROP TRIGGER IF EXISTS upd_admission_cost_calculation;
DROP TRIGGER IF EXISTS ins_surgery;
DROP TRIGGER IF EXISTS upd_surgery;
DROP TRIGGER IF EXISTS ins_prescription_allergy_check;
DROP TRIGGER IF EXISTS upd_prescription_allergy_check;
DROP TRIGGER IF EXISTS ins_evaluation_completed_admission;
DROP TRIGGER IF EXISTS upd_evaluation_completed_admission;
DROP TRIGGER IF EXISTS ins_doctor_eval_prescribed;
DROP TRIGGER IF EXISTS upd_doctor_eval_prescribed;
DROP TRIGGER IF EXISTS chk_shift_staff_constraints;
DROP TRIGGER IF EXISTS chk_delete_senior_from_shift;
DROP TRIGGER IF EXISTS chk_min_staff_on_delete;
DROP TRIGGER IF EXISTS chk_min_staff_on_update;
DROP TRIGGER IF EXISTS department_director_ins;
DROP TRIGGER IF EXISTS department_director_upd;
DROP TRIGGER IF EXISTS staff_doctor_ins;
DROP TRIGGER IF EXISTS staff_doctor_upd;
DROP TRIGGER IF EXISTS staff_nurse_ins;
DROP TRIGGER IF EXISTS staff_nurse_upd;
DROP TRIGGER IF EXISTS staff_management_ins;
DROP TRIGGER IF EXISTS staff_management_upd;

DELIMITER //
CREATE PROCEDURE `circular_supervision` (IN supervisor_AMKA VARCHAR(11), IN supervisee_AMKA VARCHAR(11))
BEGIN
    DECLARE next_supervisor_AMKA VARCHAR(11);

    IF supervisor_AMKA IS NOT NULL THEN
      SELECT Supervisor_AMKA
      INTO next_supervisor_AMKA
      FROM Doctor
      WHERE Staff_AMKA = supervisor_AMKA;

      WHILE ((next_supervisor_amka IS NOT NULL) AND (next_supervisor_AMKA <> supervisee_AMKA))DO
          SELECT Supervisor_AMKA
          INTO next_supervisor_AMKA
          FROM Doctor
          WHERE Staff_AMKA = next_supervisor_AMKA;
      END WHILE;

      IF (next_supervisor_AMKA = supervisee_AMKA) THEN
          SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Κυκλική αλυσίδα εποπτείας.';
      END IF;
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER `ins_doctor` BEFORE INSERT ON `Doctor` FOR EACH ROW
BEGIN
    CALL circular_supervision(new.Supervisor_AMKA, new.Staff_AMKA);
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `upd_doctor` BEFORE UPDATE ON `Doctor` FOR EACH ROW
BEGIN
    CALL circular_supervision(new.Supervisor_AMKA, new.Staff_AMKA);
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `ins_admission_cost_calculation` BEFORE INSERT ON `Admission` FOR EACH ROW
BEGIN
    DECLARE ken_cost DECIMAL(10,2);
    DECLARE mdn INT;
    DECLARE days_stayed INT;
    DECLARE daily_extra_charge DECIMAL(10,2);

    IF NEW.Release_Date IS NOT NULL THEN

        SELECT KEN_Cost, MDN
        INTO ken_cost, mdn
        FROM KEN
        WHERE KEN_Code = NEW.KEN_Code;

        SET days_stayed = DATEDIFF(NEW.Release_Date, NEW.Admission_Date);

        IF days_stayed <= mdn THEN
            SET NEW.Total_Cost = ken_cost;
        ELSE
            SET daily_extra_charge = ken_cost / mdn;
            SET NEW.Total_Cost = ken_cost + ((days_stayed - mdn) * daily_extra_charge);
        END IF;

    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `upd_admission_cost_calculation` BEFORE UPDATE ON `Admission` FOR EACH ROW
BEGIN
    DECLARE ken_cost DECIMAL(10,2);
    DECLARE mdn INT;
    DECLARE days_stayed INT;
    DECLARE daily_extra_charge DECIMAL(10,2);

    IF NEW.Release_Date IS NOT NULL THEN

        SELECT KEN_Cost, MDN
        INTO ken_cost, mdn
        FROM KEN
        WHERE KEN_Code = NEW.KEN_Code;

        SET days_stayed = DATEDIFF(NEW.Release_Date, NEW.Admission_Date);

        IF days_stayed <= mdn THEN
            SET NEW.Total_Cost = ken_cost;
        ELSE
            SET daily_extra_charge = ken_cost / mdn;
            SET NEW.Total_Cost = ken_cost + ((days_stayed - mdn) * daily_extra_charge);
        END IF;

    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE PROCEDURE `surgery_constraints` (IN new_action_code INT, IN new_main_surgeon_amka VARCHAR(11))
BEGIN
    DECLARE room_code INT;
    DECLARE new_start_time DATETIME;
    DECLARE new_surgery_duration INT;
    DECLARE new_end_time DATETIME;

    SELECT Operating_Room_Code, Action_Start, Action_Duration
    INTO room_code, new_start_time, new_surgery_duration
    FROM Medical_Action
    WHERE Action_Code = new_action_code;

    SET new_end_time = DATE_ADD(new_start_time, INTERVAL new_surgery_duration MINUTE);

    IF EXISTS(
      SELECT 1
      FROM Medical_Action
      WHERE Operating_Room_Code = room_code
        AND Action_Code <> new_action_code
        AND new_start_time < DATE_ADD(Action_Start, INTERVAL Action_Duration MINUTE)
        AND new_end_time > Action_Start
    ) THEN 
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Κατειλλημένος χώρος επέμβασης.';
    END IF;

    IF EXISTS(
      SELECT 1
      FROM Surgery s
      INNER JOIN Medical_Action ma ON ma.Action_Code = s.Action_Code
      WHERE s.Main_Surgeon_AMKA = new_main_surgeon_amka
        AND s.Action_Code <> new_Action_Code
        AND new_start_time < DATE_ADD(Action_Start, INTERVAL Action_Duration MINUTE)
        AND new_end_time > Action_Start
    ) THEN 
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Κατειλλημένος βασικός χειρουργός.';
    END IF;

END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `ins_surgery` BEFORE INSERT ON `Surgery` FOR EACH ROW
BEGIN
    CALL surgery_constraints(new.Action_Code, new.Main_Surgeon_AMKA);
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `upd_surgery` BEFORE UPDATE ON `Surgery` FOR EACH ROW
BEGIN
    CALL surgery_constraints(new.Action_Code, new.Main_Surgeon_AMKA);
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER ins_prescription_allergy_check BEFORE INSERT ON Prescription FOR EACH ROW
BEGIN
    IF EXISTS(
      SELECT 1
      FROM Medicine_Composition
      JOIN Patient_Allergy ON Medicine_Composition.Substance_ID = Patient_Allergy.Substance_ID
      JOIN Admission ON Admission.AdmissionID = new.AdmissionID
      WHERE Medicine_Composition.EMA_Code = new.EMA_Code
        AND Patient_Allergy.Patient_AMKA = Admission.Patient_AMKA
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ο ασθενής έχει αλλεργία σε δραστική ουσία του συγκεκριμένου φαρμάκου.';
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER upd_prescription_allergy_check BEFORE UPDATE ON Prescription FOR EACH ROW
BEGIN
    IF EXISTS(
      SELECT 1
      FROM Medicine_Composition
      JOIN Patient_Allergy ON Medicine_Composition.Substance_ID = Patient_Allergy.Substance_ID
      JOIN Admission ON Admission.AdmissionID = new.AdmissionID
      WHERE Medicine_Composition.EMA_Code = new.EMA_Code
        AND Patient_Allergy.Patient_AMKA = Admission.Patient_AMKA
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ο ασθενής έχει αλλεργία σε δραστική ουσία του συγκεκριμένου φαρμάκου.';
    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER ins_evaluation_completed_admission BEFORE INSERT ON Evaluation FOR EACH ROW
BEGIN
    DECLARE release_date DATE;

    SELECT Release_Date 
    INTO release_date 
    FROM Admission
    WHERE AdmissionID = NEW.AdmissionID;

    IF release_date IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Η νοσηλεία δεν έχει ολοκληρωθεί ακόμη.';
    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER upd_evaluation_completed_admission BEFORE UPDATE ON Evaluation FOR EACH ROW
BEGIN
    DECLARE release_date DATE;

    SELECT Release_Date 
    INTO release_date 
    FROM Admission
    WHERE AdmissionID = NEW.AdmissionID;

    IF release_date IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Η νοσηλεία δεν έχει ολοκληρωθεί ακόμη.';
    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `ins_doctor_eval_prescribed` BEFORE INSERT ON Doctor_Evaluation
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM Prescription
        WHERE Prescription.AdmissionID = NEW.AdmissionID
          AND Prescription.Doctor_AMKA = NEW.Doctor_AMKA
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ο ιατρός δεν συνταγογράφησε σε αυτή τη νοσηλεία.';
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER `upd_doctor_eval_prescribed` BEFORE UPDATE ON Doctor_Evaluation
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM Prescription
        WHERE Prescription.AdmissionID = NEW.AdmissionID
          AND Prescription.Doctor_AMKA = NEW.Doctor_AMKA
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ο ιατρός δεν συνταγογράφησε σε αυτή τη νοσηλεία.';
    END IF;
END //
DELIMITER ;


-- ============================================
-- Trigger: Comprehensive shift staff constraints
-- Enforces: monthly limits, 8-hour rest, max 3 consecutive night shifts
-- ============================================
DELIMITER //
CREATE TRIGGER `chk_shift_staff_constraints` BEFORE INSERT ON `Shift_Staff` FOR EACH ROW
BEGIN
    DECLARE v_staff_type VARCHAR(45);
    DECLARE v_shift_count INT;
    DECLARE v_new_start DATETIME;
    DECLARE v_new_end DATETIME;
    DECLARE v_back INT DEFAULT 0;
    DECLARE v_fwd INT DEFAULT 0;

    -- Get staff type
    SELECT Staff_Type INTO v_staff_type
    FROM STAFF WHERE Staff_AMKA = NEW.Staff_AMKA;

    -- Get new shift start/end times
    SELECT Start_Time, End_Time
    INTO v_new_start, v_new_end
    FROM Shift
    WHERE Shift_Date = NEW.Shift_Date
      AND Shift_Type = NEW.Shift_Type
      AND Department_Name = NEW.Department_Name;

    -- ============================================
    -- 1. Monthly shift limits per staff type
    -- ============================================
    SELECT COUNT(*) INTO v_shift_count
    FROM Shift_Staff
    WHERE Staff_AMKA = NEW.Staff_AMKA
      AND MONTH(Shift_Date) = MONTH(NEW.Shift_Date)
      AND YEAR(Shift_Date) = YEAR(NEW.Shift_Date);

    IF v_staff_type = 'Ιατρός' AND v_shift_count >= 15 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Υπέρβαση ορίου: Ιατροί έως 15 βάρδιες/μήνα.';
    ELSEIF v_staff_type = 'Νοσηλευτής' AND v_shift_count >= 20 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Υπέρβαση ορίου: Νοσηλευτές έως 20 βάρδιες/μήνα.';
    ELSEIF v_staff_type = 'Διοικητικός' AND v_shift_count >= 25 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Υπέρβαση ορίου: Διοικητικοί έως 25 βάρδιες/μήνα.';
    END IF;

    -- ============================================
    -- 2. Minimum 8-hour rest between shifts
    -- ============================================
    IF v_new_start IS NOT NULL AND v_new_end IS NOT NULL THEN
        IF EXISTS (
            SELECT 1
            FROM Shift_Staff ss
            JOIN Shift s ON ss.Shift_Date = s.Shift_Date
                        AND ss.Shift_Type = s.Shift_Type
                        AND ss.Department_Name = s.Department_Name
            WHERE ss.Staff_AMKA = NEW.Staff_AMKA
              AND NOT (ss.Shift_Date = NEW.Shift_Date
                       AND ss.Shift_Type = NEW.Shift_Type
                       AND ss.Department_Name = NEW.Department_Name)
              AND (
                  s.End_Time > DATE_SUB(v_new_start, INTERVAL 8 HOUR)
                  AND s.Start_Time < DATE_ADD(v_new_end, INTERVAL 8 HOUR)
              )
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Ελάχιστο 8ωρο ανάπαυσης μεταξύ διαδοχικών βαρδιών.';
        END IF;
    END IF;

    -- ============================================
    -- 3. Max 3 consecutive night shifts
    -- ============================================
    IF NEW.Shift_Type = 'Νυχτερινή' THEN
        -- Count consecutive nights before this date
        IF EXISTS (SELECT 1 FROM Shift_Staff WHERE Staff_AMKA = NEW.Staff_AMKA
                   AND Shift_Type = 'Νυχτερινή' AND Shift_Date = DATE_SUB(NEW.Shift_Date, INTERVAL 1 DAY)) THEN
            SET v_back = 1;
            IF EXISTS (SELECT 1 FROM Shift_Staff WHERE Staff_AMKA = NEW.Staff_AMKA
                       AND Shift_Type = 'Νυχτερινή' AND Shift_Date = DATE_SUB(NEW.Shift_Date, INTERVAL 2 DAY)) THEN
                SET v_back = 2;
                IF EXISTS (SELECT 1 FROM Shift_Staff WHERE Staff_AMKA = NEW.Staff_AMKA
                           AND Shift_Type = 'Νυχτερινή' AND Shift_Date = DATE_SUB(NEW.Shift_Date, INTERVAL 3 DAY)) THEN
                    SET v_back = 3;
                END IF;
            END IF;
        END IF;

        -- Count consecutive nights after this date
        IF EXISTS (SELECT 1 FROM Shift_Staff WHERE Staff_AMKA = NEW.Staff_AMKA
                   AND Shift_Type = 'Νυχτερινή' AND Shift_Date = DATE_ADD(NEW.Shift_Date, INTERVAL 1 DAY)) THEN
            SET v_fwd = 1;
            IF EXISTS (SELECT 1 FROM Shift_Staff WHERE Staff_AMKA = NEW.Staff_AMKA
                       AND Shift_Type = 'Νυχτερινή' AND Shift_Date = DATE_ADD(NEW.Shift_Date, INTERVAL 2 DAY)) THEN
                SET v_fwd = 2;
                IF EXISTS (SELECT 1 FROM Shift_Staff WHERE Staff_AMKA = NEW.Staff_AMKA
                           AND Shift_Type = 'Νυχτερινή' AND Shift_Date = DATE_ADD(NEW.Shift_Date, INTERVAL 3 DAY)) THEN
                    SET v_fwd = 3;
                END IF;
            END IF;
        END IF;

        -- Total chain = backwards + 1 (new) + forwards; must not exceed 3
        IF (v_back + 1 + v_fwd) > 3 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Υπέρβαση ορίου 3 συνεχόμενων νυχτερινών βαρδιών.';
        END IF;
    END IF;
END //
DELIMITER ;


-- ============================================
-- Stored Procedure: Validate shift staffing levels
-- Checks minimum personnel (3 doctors, 6 nurses, 2 admin)
-- and supervisor presence when residents are assigned
-- Call after inserting all staff for a shift:
--   CALL validate_shift_staffing('2026-03-01', 'Πρωινή', 'Καρδιολογία');
-- ============================================
DELIMITER //
CREATE PROCEDURE `validate_shift_staffing` (
    IN p_shift_date DATE,
    IN p_shift_type VARCHAR(45),
    IN p_department_name VARCHAR(45)
)
BEGIN
    DECLARE v_doctors INT DEFAULT 0;
    DECLARE v_nurses INT DEFAULT 0;
    DECLARE v_admin INT DEFAULT 0;
    DECLARE v_has_resident INT DEFAULT 0;
    DECLARE v_has_supervisor INT DEFAULT 0;

    SELECT COUNT(*) INTO v_doctors
    FROM Shift_Staff ss
    JOIN STAFF s ON ss.Staff_AMKA = s.Staff_AMKA
    WHERE ss.Shift_Date = p_shift_date
      AND ss.Shift_Type = p_shift_type
      AND ss.Department_Name = p_department_name
      AND s.Staff_Type = 'Ιατρός';

    SELECT COUNT(*) INTO v_nurses
    FROM Shift_Staff ss
    JOIN STAFF s ON ss.Staff_AMKA = s.Staff_AMKA
    WHERE ss.Shift_Date = p_shift_date
      AND ss.Shift_Type = p_shift_type
      AND ss.Department_Name = p_department_name
      AND s.Staff_Type = 'Νοσηλευτής';

    SELECT COUNT(*) INTO v_admin
    FROM Shift_Staff ss
    JOIN STAFF s ON ss.Staff_AMKA = s.Staff_AMKA
    WHERE ss.Shift_Date = p_shift_date
      AND ss.Shift_Type = p_shift_type
      AND ss.Department_Name = p_department_name
      AND s.Staff_Type = 'Διοικητικός';

    SELECT COUNT(*) INTO v_has_resident
    FROM Shift_Staff ss
    JOIN Doctor d ON ss.Staff_AMKA = d.Staff_AMKA
    WHERE ss.Shift_Date = p_shift_date
      AND ss.Shift_Type = p_shift_type
      AND ss.Department_Name = p_department_name
      AND d.`Rank` = 'Ειδικευόμενος';

    SELECT COUNT(*) INTO v_has_supervisor
    FROM Shift_Staff ss
    JOIN Doctor d ON ss.Staff_AMKA = d.Staff_AMKA
    WHERE ss.Shift_Date = p_shift_date
      AND ss.Shift_Type = p_shift_type
      AND ss.Department_Name = p_department_name
      AND d.`Rank` IN ('Επιμελητής Α', 'Διευθυντής');

    IF v_doctors < 3 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Η βάρδια απαιτεί τουλάχιστον 3 ιατρούς.';
    END IF;

    IF v_nurses < 6 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Η βάρδια απαιτεί τουλάχιστον 6 νοσηλευτές.';
    END IF;

    IF v_admin < 2 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Η βάρδια απαιτεί τουλάχιστον 2 διοικητικούς υπαλλήλους.';
    END IF;

    IF v_has_resident > 0 AND v_has_supervisor = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Σε βάρδια με ειδικευόμενο πρέπει να παρίσταται Επιμελητής Α ή Διευθυντής.';
    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `chk_delete_senior_from_shift` BEFORE DELETE ON `Shift_Staff` FOR EACH ROW
BEGIN
    DECLARE v_rank VARCHAR(45);
    DECLARE has_resident INT DEFAULT 0;

    SELECT `Rank` INTO v_rank
    FROM Doctor
    WHERE Staff_AMKA = OLD.Staff_AMKA;

    IF v_rank IN ('Επιμελητής Α', 'Διευθυντής') THEN

        SELECT COUNT(*) INTO has_resident
        FROM Shift_Staff ss
        JOIN Doctor d ON ss.Staff_AMKA = d.Staff_AMKA
        WHERE ss.Shift_Date = OLD.Shift_Date
          AND ss.Shift_Type = OLD.Shift_Type
          AND ss.Department_Name = OLD.Department_Name
          AND d.`Rank` = 'Ειδικευόμενος'
          AND ss.Staff_AMKA <> OLD.Staff_AMKA;

        IF has_resident > 0 THEN
            
            IF (
                SELECT COUNT(*)
                FROM Shift_Staff ss
                JOIN Doctor d ON ss.Staff_AMKA = d.Staff_AMKA
                WHERE ss.Shift_Date = OLD.Shift_Date
                  AND ss.Shift_Type = OLD.Shift_Type
                  AND ss.Department_Name = OLD.Department_Name
                  AND d.`Rank` IN ('Επιμελητής Α', 'Διευθυντής')
                  AND ss.Staff_AMKA <> OLD.Staff_AMKA
            ) = 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Απαγορεύεται: Δεν μπορεί να αφαιρεθεί ο τελευταίος Επιμελητής Α/Διευθυντής ενώ υπάρχει Ειδικευόμενος στη βάρδια.';
            END IF;
        END IF;
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER `chk_min_staff_on_delete` BEFORE DELETE ON `Shift_Staff` FOR EACH ROW
BEGIN
    DECLARE v_staff_type VARCHAR(45);
    DECLARE v_count_after INT;

    SELECT Staff_Type INTO v_staff_type
    FROM STAFF
    WHERE Staff_AMKA = OLD.Staff_AMKA;

    SELECT COUNT(*) INTO v_count_after
    FROM Shift_Staff ss
    JOIN STAFF s ON ss.Staff_AMKA = s.Staff_AMKA
    WHERE ss.Shift_Date = OLD.Shift_Date
      AND ss.Shift_Type = OLD.Shift_Type
      AND ss.Department_Name = OLD.Department_Name
      AND s.Staff_Type = v_staff_type
      AND ss.Staff_AMKA <> OLD.Staff_AMKA;  

    IF v_staff_type = 'Ιατρός' AND v_count_after < 3 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Απαγορεύεται: Η βάρδια πρέπει να έχει τουλάχιστον 3 ιατρούς.';

    ELSEIF v_staff_type = 'Νοσηλευτής' AND v_count_after < 6 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Απαγορεύεται: Η βάρδια πρέπει να έχει τουλάχιστον 6 νοσηλευτές.';

    ELSEIF v_staff_type = 'Διοικητικός' AND v_count_after < 2 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Απαγορεύεται: Η βάρδια πρέπει να έχει τουλάχιστον 2 διοικητικούς υπαλλήλους.';
    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `chk_min_staff_on_update` BEFORE UPDATE ON `Shift_Staff` FOR EACH ROW
BEGIN
    DECLARE v_staff_type VARCHAR(45);
    DECLARE v_count_after INT;

    SELECT Staff_Type INTO v_staff_type
    FROM STAFF
    WHERE Staff_AMKA = OLD.Staff_AMKA;

    SELECT COUNT(*) INTO v_count_after
    FROM Shift_Staff ss
    JOIN STAFF s ON ss.Staff_AMKA = s.Staff_AMKA
    WHERE ss.Shift_Date = OLD.Shift_Date
      AND ss.Shift_Type = OLD.Shift_Type
      AND ss.Department_Name = OLD.Department_Name
      AND s.Staff_Type = v_staff_type
      AND ss.Staff_AMKA <> OLD.Staff_AMKA;  

    IF v_staff_type = 'Ιατρός' AND v_count_after < 3 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Απαγορεύεται: Η βάρδια πρέπει να έχει τουλάχιστον 3 ιατρούς.';

    ELSEIF v_staff_type = 'Νοσηλευτής' AND v_count_after < 6 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Απαγορεύεται: Η βάρδια πρέπει να έχει τουλάχιστον 6 νοσηλευτές.';

    ELSEIF v_staff_type = 'Διοικητικός' AND v_count_after < 2 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Απαγορεύεται: Η βάρδια πρέπει να έχει τουλάχιστον 2 διοικητικούς υπαλλήλους.';
    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `department_director_ins` BEFORE INSERT ON `Department` FOR EACH ROW
BEGIN 
    DECLARE director_rank VARCHAR(45);

    SELECT d.Rank
    INTO director_rank
    FROM Doctor d
    WHERE d.Staff_AMKA = new.DirectedBy;

    IF director_rank <> 'Διευθυντής'
    OR NOT EXISTS(
        SELECT 1
        FROM Doctor D
        JOIN Belongs_Doctor bd ON bd.Doctor_AMKA = D.Staff_AMKA
        WHERE bd.Department_Name = new.Department_Name AND D.Staff_AMKA = new.DirectedBy
      )THEN 
          SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Απαγορεύεται: Ο συγκεκριμένος γιατρός δεν έχει βαθμίδα διευθυντή.';
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER `department_director_upd` BEFORE UPDATE ON `Department` FOR EACH ROW
BEGIN 
    DECLARE director_rank VARCHAR(45);

    SELECT d.Rank
    INTO director_rank
    FROM Doctor d
    WHERE d.Staff_AMKA = new.DirectedBy;

    IF director_rank <> 'Διευθυντής'
    OR NOT EXISTS(
        SELECT 1
        FROM Doctor D
        JOIN Belongs_Doctor bd ON bd.Doctor_AMKA = D.Staff_AMKA
        WHERE bd.Department_Name = new.Department_Name AND D.Staff_AMKA = new.DirectedBy
      )THEN 
          SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Απαγορεύεται: Ο συγκεκριμένος γιατρός δεν έχει βαθμίδα διευθυντή.';
    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `staff_doctor_ins` BEFORE INSERT ON `Doctor` FOR EACH ROW
BEGIN 
    DECLARE staff_type VARCHAR(45); 

    SELECT Staff_Type
    INTO staff_type
    FROM STAFF s
    WHERE s.Staff_AMKA = NEW.Staff_AMKA;

    IF staff_type <> 'Ιατρός' THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Απαγορεύεται: Το μέλος προσωπικού δεν είναι ιατρός.';
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER `staff_doctor_upd` BEFORE UPDATE ON `Doctor` FOR EACH ROW
BEGIN 
    DECLARE staff_type VARCHAR(45); 

    SELECT Staff_Type
    INTO staff_type
    FROM STAFF s
    WHERE s.Staff_AMKA = NEW.Staff_AMKA;

    IF staff_type <> 'Ιατρός' THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Απαγορεύεται: Το μέλος προσωπικού δεν είναι ιατρός.';
    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `staff_nurse_ins` BEFORE INSERT ON `Nurse` FOR EACH ROW
BEGIN 
    DECLARE staff_type VARCHAR(45); 

    SELECT Staff_Type
    INTO staff_type
    FROM STAFF s
    WHERE s.Staff_AMKA = NEW.Staff_AMKA;

    IF staff_type <> 'Νοσηλευτής' THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Απαγορεύεται: Το μέλος προσωπικού δεν είναι νοσηλευτής.';
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER `staff_nurse_upd` BEFORE UPDATE ON `Nurse` FOR EACH ROW
BEGIN 
    DECLARE staff_type VARCHAR(45); 

    SELECT Staff_Type
    INTO staff_type
    FROM STAFF s
    WHERE s.Staff_AMKA = NEW.Staff_AMKA;

    IF staff_type <> 'Νοσηλευτής' THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Απαγορεύεται: Το μέλος προσωπικού δεν είναι νοσηλευτής.';
    END IF;
END //
DELIMITER ;


DELIMITER //
CREATE TRIGGER `staff_management_ins` BEFORE INSERT ON `Management` FOR EACH ROW
BEGIN 
    DECLARE staff_type VARCHAR(45); 

    SELECT Staff_Type
    INTO staff_type
    FROM STAFF s
    WHERE s.Staff_AMKA = NEW.Staff_AMKA;

    IF staff_type <> 'Διοικητικός' THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Απαγορεύεται: Το μέλος προσωπικού δεν είναι διοικητικός.';
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER `staff_management_upd` BEFORE UPDATE ON `Management` FOR EACH ROW
BEGIN 
    DECLARE staff_type VARCHAR(45); 

    SELECT Staff_Type
    INTO staff_type
    FROM STAFF s
    WHERE s.Staff_AMKA = NEW.Staff_AMKA;

    IF staff_type <> 'Διοικητικός' THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Απαγορεύεται: Το μέλος προσωπικού δεν είναι διοικητικός.';
    END IF;
END //
DELIMITER ;