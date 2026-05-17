SELECT
    Doctor_Evaluation.Doctor_AMKA,
    AVG(Doctor_Evaluation.Doctor_Quality) AS avg_medical_care_quality,
    AVG(Evaluation.Overall_Experience) AS avg_overall_hospitalization_experience
FROM Doctor_Evaluation
JOIN Evaluation ON Doctor_Evaluation.AdmissionID = Evaluation.AdmissionID
WHERE Doctor_Evaluation.Doctor_AMKA = '98182992299'
GROUP BY Doctor_Evaluation.Doctor_AMKA;
