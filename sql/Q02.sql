SELECT
    Staff.Staff_AMKA,
    Staff.First_Name,
    Staff.Last_Name,
    IF(COUNT(DISTINCT Shift_Staff.Shift_Date) > 0, 'Ναι', 'Όχι') AS had_shift_this_year,
    COUNT(DISTINCT Surgery.Action_Code) AS total_surgeries
FROM Staff
JOIN Doctor
    ON Staff.Staff_AMKA = Doctor.Staff_AMKA
LEFT JOIN Shift_Staff
    ON Staff.Staff_AMKA = Shift_Staff.Staff_AMKA
    AND YEAR(Shift_Staff.Shift_Date) = YEAR(CURDATE())
LEFT JOIN Surgery
    ON Staff.Staff_AMKA = Surgery.Main_Surgeon_AMKA
WHERE Doctor.Specialty = 'Καρδιολογία'
GROUP BY Staff.Staff_AMKA, Staff.First_Name, Staff.Last_Name;
