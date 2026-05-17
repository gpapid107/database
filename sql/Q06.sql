SELECT A.Admission_Date, A.Release_Date, A.Total_Cost, A.Department_Name, A.Admission_Diagnosis_ICD_10_Code, 
A.Release_Diagnosis_ICD_10_Code, (E.Nursing_Quality+E.Cleanliness+E.Food+E.Overall_Experience)/4.0 AS Average_Evaluation 
FROM Admission A 
LEFT OUTER JOIN Evaluation E ON A.AdmissionID = E.AdmissionID 
WHERE A.Patient_AMKA = '55799802841' ORDER BY A.Admission_Date;
