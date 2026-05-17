SET @target_date = '2026-03-01';
SET @target_department = _utf8mb4'Καρδιολογία' COLLATE utf8mb4_unicode_ci;

SELECT staff.Staff_AMKA, staff.First_Name, staff.Last_Name, staff.Staff_Type
FROM STAFF staff
WHERE NOT EXISTS(
	SELECT 1
    FROM Shift shift
    INNER JOIN Shift_Staff shift_staff USING (Shift_Date, Shift_Type, Department_Name)
    WHERE shift.Department_Name = @target_department
    AND shift_staff.Staff_AMKA = staff.Staff_AMKA
    AND DATE(shift.Start_Time) <= @target_date
    AND DATE(shift.End_Time) >= @target_date
);
