SELECT
    Patient.Patient_AMKA,
    Patient.Patient_First_Name,
    Patient.Patient_Last_Name,
    Admission.Department_Name,
    COUNT(Admission.AdmissionID) AS times_admitted,
    SUM(Admission.Total_Cost) AS total_cost
FROM Patient
JOIN Admission ON Patient.Patient_AMKA = Admission.Patient_AMKA
GROUP BY Patient.Patient_AMKA, Patient.Patient_First_Name, Patient.Patient_Last_Name, Admission.Department_Name
HAVING COUNT(Admission.AdmissionID) > 3
ORDER BY total_cost DESC;



