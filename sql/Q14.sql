SELECT 
    counts_a.ICD10_Category AS ICD10_Category,
    counts_a.admission_year AS Year_1,
    counts_b.admission_year AS Year_2,
    counts_a.Num_Admissions
FROM (
    SELECT LEFT(Admission_Diagnosis_ICD_10_Code, 1) AS ICD10_Category, YEAR(Admission_Date) AS admission_year,
    COUNT(*) AS Num_Admissions
    FROM Admission A1
    GROUP BY LEFT(A1.Admission_Diagnosis_ICD_10_Code, 1), YEAR(Admission_Date)
    HAVING COUNT(*) >= 5
) AS counts_a
JOIN (
    SELECT LEFT(Admission_Diagnosis_ICD_10_Code, 1) AS ICD10_Category, YEAR(Admission_Date) AS admission_year,
    COUNT(*) AS Num_Admissions
    FROM Admission A2
    GROUP BY LEFT(A2.Admission_Diagnosis_ICD_10_Code, 1), YEAR(Admission_Date)
    HAVING COUNT(*) >= 5
) AS counts_b
ON counts_a.ICD10_Category = counts_b.ICD10_Category
AND counts_b.admission_year = counts_a.admission_year + 1
AND counts_a.Num_Admissions = counts_b.Num_Admissions
