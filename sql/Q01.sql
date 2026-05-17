SELECT
    Admission.Department_Name,
    YEAR(Admission.Release_Date) AS year,
    Admission.KEN_Code,
    Patient.Insurance_Provider,
    COUNT(Admission.AdmissionID) AS total_admissions,
    SUM(KEN.KEN_Cost) AS basic_cost,
    SUM(Admission.Total_Cost - KEN.KEN_Cost) AS extra_cost,
    SUM(Admission.Total_Cost) AS total_revenue
FROM Admission
JOIN KEN ON Admission.KEN_Code = KEN.KEN_Code
JOIN Patient ON Admission.Patient_AMKA = Patient.Patient_AMKA
WHERE Admission.Release_Date IS NOT NULL
GROUP BY Admission.Department_Name, YEAR(Admission.Release_Date), Admission.KEN_Code, Patient.Insurance_Provider
ORDER BY Admission.Department_Name, year, Admission.KEN_Code;
