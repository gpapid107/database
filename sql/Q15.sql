SELECT 
    stats.Urgency_Level,
    stats.Num_Triages,
    stats.Avg_Wait,
    stats.Pct_Admitted,
    refs.Department_Name,
    refs.Num_Referred
FROM (
    -- στατιστικά ανά Urgency Level
    SELECT 
        T.Urgency_Level,
        COUNT(*) AS Num_Triages,
        AVG(T.Waiting_Minutes) AS Avg_Wait,
        COUNT(A.AdmissionID) / COUNT(*) * 100 AS Pct_Admitted
    FROM Triage T
    LEFT JOIN Admission A ON T.Triage_ID = A.Triage_ID
    GROUP BY T.Urgency_Level
) AS stats
JOIN (
    -- κατανομή παραπομπών ανά Urgency + Department
    SELECT 
        T.Urgency_Level,
        A.Department_Name,
        COUNT(*) AS Num_Referred
    FROM Triage T
    JOIN Admission A ON T.Triage_ID = A.Triage_ID
    GROUP BY T.Urgency_Level, A.Department_Name
) AS refs
ON stats.Urgency_Level = refs.Urgency_Level
ORDER BY stats.Urgency_Level, refs.Department_Name
