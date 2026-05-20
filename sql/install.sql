SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci ;
USE `mydb` ;

-- -----------------------------------------------------
-- Table `mydb`.`STAFF`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`STAFF` (
  `Staff_AMKA` VARCHAR(11) NOT NULL,
  `First_Name` VARCHAR(45) NOT NULL,
  `Last_Name` VARCHAR(45) NOT NULL,
  `Age` INT NOT NULL,
  `Email` VARCHAR(45) NOT NULL,
  `Phone_Number` VARCHAR(45) NOT NULL,
  `Hiring_Date` DATE NOT NULL,
  `Staff_Type` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`Staff_AMKA`),
  CONSTRAINT `chk_staff_age` CHECK (`Age` >= 18 AND `Age` <=70),
  CONSTRAINT `chk_staff_type` CHECK (`Staff_Type` IN ('Ιατρός', 'Νοσηλευτής', 'Διοικητικός'))
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Doctor`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Doctor` (
  `License_Number` VARCHAR(45) NOT NULL,
  `Specialty` VARCHAR(45) NOT NULL,
  `Rank` VARCHAR(45) NOT NULL,
  `Staff_AMKA` VARCHAR(11) NOT NULL,
  `Supervisor_AMKA` VARCHAR(11) NULL,
  PRIMARY KEY (`Staff_AMKA`),
  INDEX `fk_Doctor_STAFF_idx` (`Staff_AMKA` ASC),
  INDEX `fk_Doctor_Doctor1_idx` (`Supervisor_AMKA` ASC),
  CONSTRAINT `fk_Doctor_STAFF`
    FOREIGN KEY (`Staff_AMKA`)
    REFERENCES `mydb`.`STAFF` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Doctor_Doctor1`
    FOREIGN KEY (`Supervisor_AMKA`)
    REFERENCES `mydb`.`Doctor` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_doctor_rank` CHECK (`Rank` IN ('Ειδικευόμενος', 'Επιμελητής Β', 'Επιμελητής Α', 'Διευθυντής')),
  CONSTRAINT `chk_supervisor_rules` CHECK (
    (`Rank` = 'Ειδικευόμενος' AND `Supervisor_AMKA` IS NOT NULL) OR
    (`Rank` = 'Διευθυντής' AND `Supervisor_AMKA` IS NULL) OR
    (`Rank` NOT IN ('Ειδικευόμενος', 'Διευθυντής'))
  ),
  CONSTRAINT `chk_supervisor_is_different_person` CHECK((`Supervisor_AMKA` IS NULL) OR (`Supervisor_AMKA`<>`Staff_AMKA`))
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Department`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Department` (
  `Department_Name` VARCHAR(45) NOT NULL,
  `Description` VARCHAR(45) NOT NULL,
  `Num_of_Beds` INT NOT NULL,
  `Floor` INT NOT NULL,
  `Building` VARCHAR(45) NOT NULL,
  `DirectedBy` VARCHAR(11) NOT NULL,
  PRIMARY KEY (`Department_Name`),
  INDEX `fk_Department_Doctor1_idx` (`DirectedBy` ASC),
  CONSTRAINT `fk_Department_Doctor1`
    FOREIGN KEY (`DirectedBy`)
    REFERENCES `mydb`.`Doctor` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_dept_name` CHECK (`Department_Name` IN ('Καρδιολογία', 'Χειρουργική', 'ΜΕΘ', 'Επείγοντα', 'Νευρολογία', 'Παθολογία', 'Ορθοπεδική', 'Ουρολογία', 'Οφθαλμολογία', 'ΩΡΛ', 'Πνευμονολογία', 'Γαστρεντερολογία', 'Νεφρολογία', 'Αιματολογία', 'Ογκολογία')),
  CONSTRAINT `chk_num_of_beds` CHECK (`Num_of_Beds` >= 0)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Nurse`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Nurse` (
  `Nurse_Rank` VARCHAR(45) NOT NULL,
  `Staff_AMKA` VARCHAR(11) NOT NULL,
  `NurseBelongsDepartment` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`Staff_AMKA`),
  INDEX `fk_Nurse_STAFF1_idx` (`Staff_AMKA` ASC),
  INDEX `fk_Nurse_Department1_idx` (`NurseBelongsDepartment` ASC),
  CONSTRAINT `fk_Nurse_STAFF1`
    FOREIGN KEY (`Staff_AMKA`)
    REFERENCES `mydb`.`STAFF` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Nurse_Department1`
    FOREIGN KEY (`NurseBelongsDepartment`)
    REFERENCES `mydb`.`Department` (`Department_Name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_nurse_rank` CHECK (`Nurse_Rank` IN ('Βοηθός Νοσηλευτή', 'Νοσηλευτής', 'Προϊστάμενος'))
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Management`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Management` (
`Role` VARCHAR(45) NOT NULL,
`Office` VARCHAR(45) NOT NULL,
`Staff_AMKA` VARCHAR(11) NOT NULL,
`ManagerBelongsDepartment` VARCHAR(45) NOT NULL,
PRIMARY KEY (`Staff_AMKA`),
INDEX `fk_Management_STAFF1_idx` (`Staff_AMKA` ASC),
INDEX `fk_Management_Department1_idx` (`ManagerBelongsDepartment` ASC),
CONSTRAINT `fk_Management_STAFF1`
  FOREIGN KEY (`Staff_AMKA`)
  REFERENCES `mydb`.`STAFF` (`Staff_AMKA`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION,
CONSTRAINT `fk_Management_Department1`
  FOREIGN KEY (`ManagerBelongsDepartment`)
  REFERENCES `mydb`.`Department` (`Department_Name`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION,
CONSTRAINT `chk_management_role` CHECK (`Role` IN ('Γραμματέας', 'Λογιστής', 'Ανθρώπινο Δυναμικό'))  
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Belongs_Doctor`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Belongs_Doctor` (
  `Doctor_AMKA` VARCHAR(11) NOT NULL,
  `Department_Name` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`Doctor_AMKA`, `Department_Name`),
  INDEX `fk_Doctor_has_Department_Department1_idx` (`Department_Name` ASC),
  INDEX `fk_Doctor_has_Department_Doctor1_idx` (`Doctor_AMKA` ASC),
  CONSTRAINT `fk_Doctor_has_Department_Doctor1`
    FOREIGN KEY (`Doctor_AMKA`)
    REFERENCES `mydb`.`Doctor` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Doctor_has_Department_Department1`
    FOREIGN KEY (`Department_Name`)
    REFERENCES `mydb`.`Department` (`Department_Name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Bed`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Bed` (
  `Department_Name` VARCHAR(45) NOT NULL,
  `Bed_Number` INT NOT NULL,
  `Bed_Type` VARCHAR(45) NOT NULL,
  `Status` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`Department_Name`, `Bed_Number`),
  CONSTRAINT `fk_Bed_Department1`
    FOREIGN KEY (`Department_Name`)
    REFERENCES `mydb`.`Department` (`Department_Name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_bed_number` CHECK (`Bed_Number` > 0),
  CONSTRAINT `chk_bed_type` CHECK (`Bed_Type` IN ('ΜΕΘ', 'Μονόκλινο', 'Πολύκλινο')),
  CONSTRAINT `chk_bed_status` CHECK (`Status` IN ('Διαθέσιμη', 'Κατειλημμένη', 'Υπό Συντήρηση'))
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Insurance`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Insurance` (
  `Provider` VARCHAR(45) NOT NULL,
  `Provider_Phone` VARCHAR(45) NULL,
  PRIMARY KEY (`Provider`),
CONSTRAINT `chk_provider_name`CHECK (`Provider` IN ('ΕΦΚΑ', 'ΕΟΠΥΥ', 'Ιδιωτική Ασφάλεια', 'Ανασφάλιστος'))
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Patient`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Patient` (
  `Patient_AMKA` VARCHAR(11) NOT NULL,
  `Patient_First_Name` VARCHAR(45) NOT NULL,
  `Patient_Last_Name` VARCHAR(45) NOT NULL,
  `Patient_Father_Name` VARCHAR(45) NOT NULL,
  `Patient_Age` INT NOT NULL,
  `Age_Month` INT NULL,
  `Patient_Gender` VARCHAR(45) NOT NULL,
  `Patient_Weight` DECIMAL(10,2) NOT NULL,
  `Patient_Height` DECIMAL(10,2) NOT NULL,
  `Patient_Address` VARCHAR(45) NOT NULL,
  `Patient_Phone_Number` VARCHAR(45) NOT NULL,
  `Patient_Email` VARCHAR(45) NOT NULL,
  `Patient_Profession` VARCHAR(45) NOT NULL,
  `Patient_Nationality` VARCHAR(45) NOT NULL,
  `Insurance_Provider` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`Patient_AMKA`),
  INDEX `fk_Patient_Insurance1_idx` (`Insurance_Provider` ASC),
  CONSTRAINT `fk_Patient_Insurance1`
    FOREIGN KEY (`Insurance_Provider`)
    REFERENCES `mydb`.`Insurance` (`Provider`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_age` CHECK ((`Patient_Age` > 0 AND (Age_Month IS NULL OR Age_Month = 0)) OR (`Patient_Age` = 0 AND `Age_Month` >= 0)),
  CONSTRAINT `chk_gender` CHECK (`Patient_Gender` IN ('Άρρεν', 'Θήλυ')),
  CONSTRAINT `chk_weight` CHECK (`Patient_Weight` > 0),
  CONSTRAINT `chk_height` CHECK (`Patient_Height` > 0)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Triage`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Triage` (
  `Triage_ID` INT NOT NULL,
  `Symptoms` VARCHAR(45) NOT NULL,
  `Urgency_Level` INT NOT NULL,
  `Arrival_DateTime` DATETIME NOT NULL,
  `Waiting_Minutes` INT NULL,
  `Patient_AMKA` VARCHAR(11) NOT NULL,
  `Nurse_AMKA` VARCHAR(11) NOT NULL,
  PRIMARY KEY (`Triage_ID`),
  INDEX `fk_Triage_Patient1_idx` (`Patient_AMKA` ASC),
  INDEX `fk_Triage_Nurse1_idx` (`Nurse_AMKA` ASC),
  CONSTRAINT `fk_Triage_Patient1`
    FOREIGN KEY (`Patient_AMKA`)
    REFERENCES `mydb`.`Patient` (`Patient_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Triage_Nurse1`
    FOREIGN KEY (`Nurse_AMKA`)
    REFERENCES `mydb`.`Nurse` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_triage_id` CHECK (`Triage_ID` >= 0),
  CONSTRAINT `chk_urgency_level` CHECK (`Urgency_Level` IN (1, 2, 3, 4, 5)),
  CONSTRAINT `chk_waiting_minutes` CHECK (`Waiting_Minutes` IS NULL OR `Waiting_Minutes` >= 0)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`KEN`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`KEN` (
  `KEN_Code` VARCHAR(10) NOT NULL,
  `KEN_Cost` DECIMAL(10,2) NOT NULL,
  `MDN` INT NOT NULL,
  PRIMARY KEY (`KEN_Code`),
  CONSTRAINT `chk_KEN_cost` CHECK (`KEN_Cost` >= 0),
  CONSTRAINT `chk_MDN` CHECK (`MDN` > 0)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Diagnosis`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Diagnosis` (
  `ICD_10_Code` VARCHAR(10) NOT NULL,
  `Description` VARCHAR(200) NOT NULL,
  PRIMARY KEY (`ICD_10_Code`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Admission`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Admission` (
  `AdmissionID` INT NOT NULL,
  `Admission_Date` DATE NOT NULL,
  `Release_Date` DATE NULL,
  `Total_Cost` DECIMAL(10,2) NULL,
  `Department_Name` VARCHAR(45) NOT NULL,
  `Bed_Number` INT NOT NULL,
  `Patient_AMKA` VARCHAR(11) NOT NULL,
  `Triage_ID` INT NOT NULL,
  `KEN_Code` VARCHAR(10) NOT NULL,
  `Admission_Diagnosis_ICD_10_Code` VARCHAR(10) NOT NULL,
  `Release_Diagnosis_ICD_10_Code` VARCHAR(10) NULL,
  PRIMARY KEY (`AdmissionID`),
  INDEX `fk_Admission_Bed1_idx` (`Department_Name` ASC, `Bed_Number` ASC),
  INDEX `fk_Admission_Patient1_idx` (`Patient_AMKA` ASC),
  INDEX `fk_Admission_Triage1_idx` (`Triage_ID` ASC),
  INDEX `fk_Admission_KEN1_idx` (`KEN_Code` ASC),
  INDEX `fk_Admission_Diagnosis1_idx` (`Admission_Diagnosis_ICD_10_Code` ASC),
  INDEX `fk_Admission_Diagnosis2_idx` (`Release_Diagnosis_ICD_10_Code` ASC),
  CONSTRAINT `fk_Admission_Bed1`
    FOREIGN KEY (`Department_Name` , `Bed_Number`)
    REFERENCES `mydb`.`Bed` (`Department_Name` , `Bed_Number`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Admission_Patient1`
    FOREIGN KEY (`Patient_AMKA`)
    REFERENCES `mydb`.`Patient` (`Patient_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Admission_Triage1`
    FOREIGN KEY (`Triage_ID`)
    REFERENCES `mydb`.`Triage` (`Triage_ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Admission_KEN1`
    FOREIGN KEY (`KEN_Code`)
    REFERENCES `mydb`.`KEN` (`KEN_Code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Admission_Diagnosis1`
    FOREIGN KEY (`Admission_Diagnosis_ICD_10_Code`)
    REFERENCES `mydb`.`Diagnosis` (`ICD_10_Code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Admission_Diagnosis2`
    FOREIGN KEY (`Release_Diagnosis_ICD_10_Code`)
    REFERENCES `mydb`.`Diagnosis` (`ICD_10_Code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_admission_id` CHECK (`AdmissionID` >= 0),
  CONSTRAINT `chk_total_cost` CHECK (`Total_Cost` >= 0),
  CONSTRAINT `chk_admission_time_logic` CHECK ((`Release_Date` IS NULL) OR (`Admission_Date` <= `Release_Date`))

)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Shift`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Shift` (
  `Shift_Date` DATE NOT NULL,
  `Shift_Type` VARCHAR(45) NOT NULL,
  `Start_Time` DATETIME NOT NULL,
  `End_Time` DATETIME NOT NULL,
  `Department_Name` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`Shift_Date`, `Shift_Type`, `Department_Name`),
  INDEX `fk_Shift_Department1_idx` (`Department_Name` ASC),
  CONSTRAINT `fk_Shift_Department1`
    FOREIGN KEY (`Department_Name`)
    REFERENCES `mydb`.`Department` (`Department_Name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_shift_type` CHECK (`Shift_Type` IN ('Πρωινή', 'Απογευματινή', 'Νυχτερινή')),
  CONSTRAINT `chk_shift_time_logic` CHECK (`End_Time` >= `Start_Time`)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Shift_Staff`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Shift_Staff` (
  `Shift_Date` DATE NOT NULL,
  `Shift_Type` VARCHAR(45) NOT NULL,
  `Department_Name` VARCHAR(45) NOT NULL,
  `Staff_AMKA` VARCHAR(11) NOT NULL,
  PRIMARY KEY (`Shift_Date`, `Shift_Type`, `Department_Name`, `Staff_AMKA`),
  INDEX `fk_Shift_has_STAFF_STAFF1_idx` (`Staff_AMKA` ASC),
  INDEX `fk_Shift_has_STAFF_Shift1_idx` (`Shift_Date` ASC, `Shift_Type` ASC, `Department_Name` ASC),
  CONSTRAINT `fk_Shift_has_STAFF_Shift1`
    FOREIGN KEY (`Shift_Date` , `Shift_Type` , `Department_Name`)
    REFERENCES `mydb`.`Shift` (`Shift_Date` , `Shift_Type` , `Department_Name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Shift_has_STAFF_STAFF1`
    FOREIGN KEY (`Staff_AMKA`)
    REFERENCES `mydb`.`STAFF` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Exam`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Exam` (
  `Exam_Code` INT NOT NULL,
  `Exam_Type` VARCHAR(45) NOT NULL,
  `Exam_Date` DATE NOT NULL,
  `Exam_Result` VARCHAR(45) NOT NULL,
  `Measurement_Unit` VARCHAR(45) NULL,
  `Exam_Cost` DECIMAL(10,2) NOT NULL,
  `AdmissionID` INT NOT NULL,
  `Doctor_AMKA` VARCHAR(11) NOT NULL,
  INDEX `fk_Exam_Admission1_idx` (`AdmissionID` ASC),
  INDEX `fk_Exam_Doctor1_idx` (`Doctor_AMKA` ASC),
  PRIMARY KEY (`Exam_Code`),
  CONSTRAINT `fk_Exam_Admission1`
    FOREIGN KEY (`AdmissionID`)
    REFERENCES `mydb`.`Admission` (`AdmissionID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Exam_Doctor1`
    FOREIGN KEY (`Doctor_AMKA`)
    REFERENCES `mydb`.`Doctor` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_exam_code` CHECK (`Exam_Code` >= 0),
  CONSTRAINT `chk_exam_cost` CHECK (`Exam_Cost` >= 0)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Operating_Room`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Operating_Room` (
  `Room_Code` INT NOT NULL,
  `Room_Type` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`Room_Code`),
  CONSTRAINT `chk_room_code` CHECK (`Room_Code` >= 0)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Medical_Action`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Medical_Action` (
  `Action_Code` INT NOT NULL,
  `Action_Name` VARCHAR(400) NOT NULL,
  `Action_Type` VARCHAR(45) NOT NULL,
  `Action_Start` DATETIME NOT NULL,
  `Action_Duration` INT NOT NULL,     -- in minutes
  `Action_Cost` DECIMAL(10,2) NOT NULL,
  `AdmissionID` INT NOT NULL,
  `Operating_Room_Code` INT NOT NULL,
  PRIMARY KEY (`Action_Code`),
  INDEX `fk_Medical_Action_Admission1_idx` (`AdmissionID` ASC),
  INDEX `fk_Medical_Action_Operating_Room1_idx` (`Operating_Room_Code` ASC),
  CONSTRAINT `fk_Medical_Action_Admission1`
    FOREIGN KEY (`AdmissionID`)
    REFERENCES `mydb`.`Admission` (`AdmissionID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Medical_Action_Operating_Room1`
    FOREIGN KEY (`Operating_Room_Code`)
    REFERENCES `mydb`.`Operating_Room` (`Room_Code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_action_code` CHECK (`Action_Code` >= 0),
  CONSTRAINT `chk_action_type` CHECK (`Action_Type` IN ('Χειρουργική', 'Διαγνωστική', 'Θεραπευτική')),
  CONSTRAINT `chk_action_cost` CHECK (`Action_Cost` >= 0)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Surgery`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Surgery` (
  `Surgery_Type` VARCHAR(45) NOT NULL,
  `Action_Code` INT NOT NULL,
  `Main_Surgeon_AMKA` VARCHAR(11) NOT NULL,
  PRIMARY KEY (`Action_Code`),
  INDEX `fk_Surgery_Medical_Action1_idx` (`Action_Code` ASC),
  INDEX `fk_Surgery_Doctor1_idx` (`Main_Surgeon_AMKA` ASC),
  CONSTRAINT `fk_Surgery_Medical_Action1`
    FOREIGN KEY (`Action_Code`)
    REFERENCES `mydb`.`Medical_Action` (`Action_Code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Surgery_Doctor1`
    FOREIGN KEY (`Main_Surgeon_AMKA`)
    REFERENCES `mydb`.`Doctor` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_surgery_action_code` CHECK (`Action_Code` >= 0)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Surgery_Assistant`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Surgery_Assistant` (
  `Surgery_Action_Code` INT NOT NULL,
  `Assistant_AMKA` VARCHAR(11) NOT NULL,
  PRIMARY KEY (`Surgery_Action_Code`, `Assistant_AMKA`),
  INDEX `fk_Surgery_has_STAFF_STAFF1_idx` (`Assistant_AMKA` ASC),
  INDEX `fk_Surgery_has_STAFF_Surgery1_idx` (`Surgery_Action_Code` ASC),
  CONSTRAINT `fk_Surgery_has_STAFF_Surgery1`
    FOREIGN KEY (`Surgery_Action_Code`)
    REFERENCES `mydb`.`Surgery` (`Action_Code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Surgery_has_STAFF_STAFF1`
    FOREIGN KEY (`Assistant_AMKA`)
    REFERENCES `mydb`.`STAFF` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Evaluation`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Evaluation` (
  `Nursing_Quality` INT NOT NULL,
  `Cleanliness` INT NOT NULL,
  `Food` INT NOT NULL,
  `Overall_Experience` INT NOT NULL,
  `AdmissionID` INT NOT NULL,
  PRIMARY KEY (`AdmissionID`),
  INDEX `fk_Evaluation_Admission1_idx` (`AdmissionID` ASC),
  CONSTRAINT `fk_Evaluation_Admission1`
    FOREIGN KEY (`AdmissionID`)
    REFERENCES `mydb`.`Admission` (`AdmissionID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  -- 1 : Very Bad , 2 : Bad , 3 : Acceptable , 4 : Good , 5 : Excellent
  CONSTRAINT `chk_nursing_quality` CHECK (`Nursing_Quality` IN (1, 2, 3, 4, 5)),
  CONSTRAINT `chk_cleanliness` CHECK (`Cleanliness` IN (1, 2, 3, 4, 5)),
  CONSTRAINT `chk_food` CHECK (`Food` IN (1, 2, 3, 4, 5)),
  CONSTRAINT `chk_overall_experience` CHECK (`Overall_Experience` IN (1, 2, 3, 4, 5))
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Doctor_Evaluation`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Doctor_Evaluation` (
  `AdmissionID` INT NOT NULL,
  `Doctor_AMKA` VARCHAR(11) NOT NULL,
  `Doctor_Quality` INT NOT NULL,
  PRIMARY KEY (`AdmissionID`, `Doctor_AMKA`),
  INDEX `fk_Doctor_Evaluation_Doctor1_idx` (`Doctor_AMKA` ASC),
  CONSTRAINT `fk_Doctor_Evaluation_Evaluation1`
    FOREIGN KEY (`AdmissionID`)
    REFERENCES `mydb`.`Evaluation` (`AdmissionID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Doctor_Evaluation_Doctor1`
    FOREIGN KEY (`Doctor_AMKA`)
    REFERENCES `mydb`.`Doctor` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  -- 1 : Very Bad , 2 : Bad , 3 : Acceptable , 4 : Good , 5 : Excellent
  CONSTRAINT `chk_doctor_quality` CHECK (`Doctor_Quality` IN (1, 2, 3, 4, 5))
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Medicine`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Medicine` (
  `EMA_Code` VARCHAR(45) NOT NULL,
  `Medicine_Name` VARCHAR(200) NULL,
  PRIMARY KEY (`EMA_Code`)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Prescription`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Prescription` (
  `Prescription_ID` INT NOT NULL,
  `Start_Date` DATE NOT NULL,
  `End_Date` DATE NOT NULL,
  `Dosage` INT NOT NULL,
  `Frequency` INT NOT NULL,
  `Doctor_AMKA` VARCHAR(11) NOT NULL,
  `EMA_Code` VARCHAR(45) NOT NULL,
  `AdmissionID` INT NOT NULL,
  PRIMARY KEY (`Prescription_ID`),
  INDEX `fk_Prescription_Doctor1_idx` (`Doctor_AMKA` ASC),
  INDEX `fk_Prescription_Medicine1_idx` (`EMA_Code` ASC),
  INDEX `fk_Prescription_Admission1_idx` (`AdmissionID` ASC),
  CONSTRAINT `fk_Prescription_Doctor1`
    FOREIGN KEY (`Doctor_AMKA`)
    REFERENCES `mydb`.`Doctor` (`Staff_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Prescription_Medicine1`
    FOREIGN KEY (`EMA_Code`)
    REFERENCES `mydb`.`Medicine` (`EMA_Code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Prescription_Admission1`
    FOREIGN KEY (`AdmissionID`)
    REFERENCES `mydb`.`Admission` (`AdmissionID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_prescription_id` CHECK (`Prescription_ID` >= 0),
  CONSTRAINT `chk_prescription_time_logic` CHECK (`Start_Date` <= `End_Date`),
  CONSTRAINT `chk_dosage` CHECK (`Dosage` >= 0),
  CONSTRAINT `chk_frequency` CHECK (`Frequency` >= 0),
  CONSTRAINT `unique_prescription_combo` UNIQUE (`Doctor_AMKA`, `AdmissionID`, `EMA_Code`, `Start_Date`)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Active_Substance`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Active_Substance` (
  `Substance_ID` VARCHAR(45) NOT NULL,
  `Substance_Name` VARCHAR(200) NOT NULL,
  PRIMARY KEY (`Substance_ID`)
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Medicine_Composition`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Medicine_Composition` (
  `EMA_Code` VARCHAR(45) NOT NULL,
  `Substance_ID` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`EMA_Code`, `Substance_ID`),
  INDEX `fk_Medicine_has_Active_Substance_Active_Substance1_idx` (`Substance_ID` ASC),
  INDEX `fk_Medicine_has_Active_Substance_Medicine1_idx` (`EMA_Code` ASC),
  CONSTRAINT `fk_Medicine_has_Active_Substance_Medicine1`
    FOREIGN KEY (`EMA_Code`)
    REFERENCES `mydb`.`Medicine` (`EMA_Code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Medicine_has_Active_Substance_Active_Substance1`
    FOREIGN KEY (`Substance_ID`)
    REFERENCES `mydb`.`Active_Substance` (`Substance_ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Patient_Allergy`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Patient_Allergy` (
  `Patient_AMKA` VARCHAR(11) NOT NULL,
  `Substance_ID` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`Patient_AMKA`, `Substance_ID`),
  INDEX `fk_Patient_has_Active_Substance_Active_Substance1_idx` (`Substance_ID` ASC),
  INDEX `fk_Patient_has_Active_Substance_Patient1_idx` (`Patient_AMKA` ASC),
  CONSTRAINT `fk_Patient_has_Active_Substance_Patient1`
    FOREIGN KEY (`Patient_AMKA`)
    REFERENCES `mydb`.`Patient` (`Patient_AMKA`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Patient_has_Active_Substance_Active_Substance1`
    FOREIGN KEY (`Substance_ID`)
    REFERENCES `mydb`.`Active_Substance` (`Substance_ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Entity_Image`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Entity_Image` (
  `Image_ID` INT NOT NULL AUTO_INCREMENT,
  `Entity_Type` VARCHAR(45) NOT NULL,
  `Entity_Key` VARCHAR(100) NOT NULL,
  `Image_URL` VARCHAR(255) NOT NULL,
  `Description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`Image_ID`),
  CONSTRAINT `chk_entity_type` CHECK (`Entity_Type` IN (
    'Department', 'Doctor', 'Nurse', 'Management', 'Patient',
    'Medicine', 'Operating_Room', 'Bed', 'Medical_Action',
    'Exam', 'Surgery', 'Diagnosis', 'KEN'
  ))
)ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Emergency_Contact`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`Emergency_Contact` (
  `Contact_AMKA` VARCHAR(11) NOT NULL,
  `Patient_AMKA` VARCHAR(11) NOT NULL,
  `Contact_Phone_Number` VARCHAR(45) NOT NULL,
  `Contact_First_Name` VARCHAR(45) NOT NULL,
  `Contact_Last_Name` VARCHAR(45) NOT NULL,
  `Contact_Email` VARCHAR(45) NULL,
  PRIMARY KEY (`Contact_AMKA`, `Patient_AMKA`),
  CONSTRAINT `fk_emergency_contact_for_patient`
    FOREIGN KEY (`Patient_AMKA`)
    REFERENCES `mydb`.`Patient` (`Patient_AMKA`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
)ENGINE = InnoDB;

CREATE INDEX idx_admission_department_release
ON Admission (Department_Name, Release_Date);

CREATE INDEX idx_triage_urgency_arrival
ON Triage (Urgency_Level, Arrival_DateTime);



SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
