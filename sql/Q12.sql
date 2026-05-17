SET @week_start = '2026-03-01';
SET @week_end = DATE_ADD(@week_start, INTERVAL 6 DAY);

SELECT
    ss.Shift_Date,
    ss.Shift_Type,
    ss.Department_Name,
    s.Staff_Type,
    CASE
        WHEN s.Staff_Type = 'Ιατρός'       THEN d.Specialty
        WHEN s.Staff_Type = 'Νοσηλευτής'   THEN n.Nurse_Rank
        WHEN s.Staff_Type = 'Διοικητικός'  THEN m.Role
    END AS Subcategory,
    COUNT(*) AS Num_Staff
FROM Shift_Staff ss
JOIN STAFF s ON ss.Staff_AMKA = s.Staff_AMKA
LEFT JOIN Doctor d     ON ss.Staff_AMKA = d.Staff_AMKA
LEFT JOIN Nurse n      ON ss.Staff_AMKA = n.Staff_AMKA
LEFT JOIN Management m ON ss.Staff_AMKA = m.Staff_AMKA
WHERE ss.Shift_Date BETWEEN @week_start AND @week_end
GROUP BY
    ss.Shift_Date,
    ss.Shift_Type,
    ss.Department_Name,
    s.Staff_Type,
    Subcategory
ORDER BY
    ss.Shift_Date,
    ss.Shift_Type,
    ss.Department_Name,
    s.Staff_Type;
