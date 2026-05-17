WITH RECURSIVE hierarchy AS (
    SELECT 
        d.Staff_AMKA AS original_doctor,
        d.Staff_AMKA AS current_doctor,
        d.Supervisor_AMKA,
        1 AS Level
    FROM Doctor d
    WHERE d.Supervisor_AMKA IS NOT NULL

    UNION ALL

    SELECT 
        h.original_doctor,
        d_next.Staff_AMKA,
        d_next.Supervisor_AMKA,
        h.Level + 1
    FROM Doctor d_next
    JOIN hierarchy h ON d_next.Staff_AMKA = h.Supervisor_AMKA
    WHERE d_next.Supervisor_AMKA IS NOT NULL
)
SELECT DISTINCT
    hierarchy.original_doctor,
    s1.First_Name, s1.Last_Name,
    s2.First_Name AS Supervisor_First_Name,
    s2.Last_Name AS Supervisor_Last_Name,
    Level
FROM hierarchy
JOIN STAFF s1 ON hierarchy.current_doctor = s1.Staff_AMKA
JOIN STAFF s2 ON hierarchy.Supervisor_AMKA = s2.Staff_AMKA
ORDER BY original_doctor, Level
