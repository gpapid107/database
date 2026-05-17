WITH substance_given AS (
SELECT*
FROM Prescription p
INNER JOIN Medicine M USING (EMA_Code)
INNER JOIN Medicine_Composition MC USING (EMA_Code)
INNER JOIN Active_Substance AC USING (Substance_ID)
)
SELECT substance_A.Substance_Name AS Substance_A, substance_B.Substance_Name AS Substance_B, COUNT(*) AS Pair_Count
FROM substance_given substance_A
INNER JOIN substance_given substance_B ON substance_A.AdmissionID = substance_B.AdmissionID
WHERE substance_A.Substance_ID < substance_B.Substance_ID
AND substance_A.Start_Date <= substance_B.End_Date
AND substance_B.Start_Date <= substance_A.End_Date
GROUP BY substance_A.Substance_ID, substance_B.Substance_ID
ORDER BY Pair_Count DESC
LIMIT 3;
