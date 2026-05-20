# "Υγειόπολις" General Hospital


https://chatgpt.com/backend-api/estuary/content?id=file_00000000a32c71f4a7da1398d78b572d&ts=494246&p=fs&cid=1&sig=11a15977249af988aeced7d2a868f1633dce462d666a459556bee85a18e918bf&v=0
## Web UI

Η web εφαρμογή αναπτύχθηκε σε Python (Flask) και παρέχει γραφικό περιβάλλον
διαχείρισης της βάσης δεδομένων του Νοσοκομείου Υγειόπολης.

### Προαπαιτούμενα
- Python 3
- MySQL Server
- Η βάση mydb φορτωμένη (install.sql → load.sql → triggers.sql)

### Εγκατάσταση & Εκτέλεση

1. Ανοίξτε terminal και πηγαίνετε στον φάκελο ui:
   cd ui

2. Φτιάξτε εικονικό περιβάλλον και εγκαταστήστε τις βιβλιοθήκες:
   
   python3 -m venv venv

   source venv/bin/activate
   
   pip install -r requirements.txt

4. Ανοίξτε το αρχείο app.py και στη γραμμή 66 βάλτε τα στοιχεία
   σύνδεσης της δικής σας MySQL:

   DB_CONFIG = {
       'host': 'localhost',          # συνήθως δεν χρειάζεται αλλαγή
   
    'user': 'root',               # συνήθως δεν χρειάζεται αλλαγή
   
    'password': '',               # βάλτε τον κωδικό σας εδώ(εάν έχετε κωδικό για την MySQL αλλιώς κενό)
   
    'database': 'mydb',           # μην αλλάξετε
   
   'charset': 'utf8mb4'          # μην αλλάξετε
   }

5. Εκτελέστε:
   python app.py

6. Ανοίξτε στον browser τη διεύθυνση που εμφανίζεται στο terminal.

### Στοιχεία Σύνδεσης
- Admin: admin / admin123 (πλήρη δικαιώματα)
- Viewer: viewer / viewer123 (μόνο προβολή)
