SELECT 
    d.Staff_AMKA,
    COUNT(ma.Action_Code) AS num_surgeries
FROM Doctor d
LEFT JOIN Surgery 
ON Surgery.Main_Surgeon_AMKA = d.Staff_AMKA
LEFT JOIN Medical_Action ma
ON Surgery.Action_Code = ma.Action_Code
AND YEAR(ma.Action_Start) = YEAR(CURDATE())
GROUP BY d.Staff_AMKA
HAVING COUNT(ma.Action_Code) <= (
    SELECT MAX(num_surgeries)
    FROM (
        SELECT COUNT(*) AS num_surgeries
        FROM Surgery
        JOIN Medical_Action ON Surgery.Action_Code = Medical_Action.Action_Code
        WHERE YEAR(Medical_Action.Action_Start) = YEAR(CURDATE())
        GROUP 	BY Main_Surgeon_AMKA
    ) AS surgeon_counts
) - 5
ORDER BY num_surgeries DESC;
