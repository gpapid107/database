SELECT
    Staff.Staff_AMKA,
    Staff.First_Name,
    Staff.Last_Name,
    Staff.Age,
    COUNT(Surgery.Action_Code) AS surgery_count
FROM Staff
JOIN Doctor ON Staff.Staff_AMKA = Doctor.Staff_AMKA
JOIN Surgery ON Doctor.Staff_AMKA = Surgery.Main_Surgeon_AMKA
WHERE Staff.Age < 35
GROUP BY Staff.Staff_AMKA, Staff.First_Name, Staff.Last_Name, Staff.Age
ORDER BY surgery_count DESC;
