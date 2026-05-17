WITH ppl AS (
SELECT p.Patient_AMKA, p.Patient_First_Name, p.Patient_Last_Name, SUM(DATEDIFF(COALESCE(a.Release_Date, CURDATE()), a.Admission_Date)) AS Total_Days_Stayed
FROM Patient p
INNER JOIN Admission a
USING (Patient_AMKA)
WHERE a.Admission_Date > DATE_SUB(CURDATE(), INTERVAL 365 DAY) 
GROUP BY p.Patient_AMKA
HAVING Total_Days_Stayed > 15 
)
SELECT*
FROM ppl X
WHERE EXISTS(
	SELECT 1
    FROM ppl Y
    WHERE Y.Total_Days_Stayed = X.Total_Days_Stayed
    AND Y.Patient_AMKA <> X.Patient_AMKA
)
ORDER BY Total_Days_Stayed DESC;
