SELECT 
substance.Substance_Name, 
	(SELECT COUNT(*) 
    FROM Patient_Allergy PA 
    WHERE PA.Substance_ID = substance.Substance_ID 
) AS Allergy_Count, 
	(SELECT COUNT(*) 
    FROM Medicine_Composition MC 
    WHERE MC.Substance_ID = substance.Substance_ID 
) AS Medicine_Count 
FROM Active_Substance substance 
ORDER BY Allergy_Count DESC;
