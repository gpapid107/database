from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
import mysql.connector
from mysql.connector import Error
from decimal import Decimal
from datetime import date, datetime
import json

app = Flask(__name__)
app.secret_key = 'hospital_ygioupolis_2026'

# ======================== AUTH ========================

USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'Διαχειριστής'},
    'viewer': {'password': 'viewer123', 'role': 'viewer', 'name': 'Προβολή Μόνο'},
}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('Παρακαλώ συνδεθείτε.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('Παρακαλώ συνδεθείτε.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Δεν έχετε δικαίωμα για αυτή την ενέργεια.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = USERS.get(username)
        if user and user['password'] == password:
            session['user'] = username
            session['role'] = user['role']
            session['display_name'] = user['name']
            flash(f'Καλώς ήρθατε, {user["name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Λάθος στοιχεία σύνδεσης.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Αποσυνδεθήκατε επιτυχώς.', 'success')
    return redirect(url_for('login'))

# ======================== DATABASE ========================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'mydb',
    'charset': 'utf8mb4'
}

ALL_TABLES = [
    'Patient', 'Admission', 'Prescription', 'Surgery', 'Doctor',
    'STAFF', 'Nurse', 'Department', 'Shift', 'Shift_Staff',
    'Evaluation', 'Doctor_Evaluation', 'Medicine', 'KEN',
    'Insurance', 'Triage', 'Bed', 'Diagnosis', 'Operating_Room',
    'Medical_Action', 'Active_Substance', 'Patient_Allergy',
    'Surgery_Assistant', 'Belongs_Doctor', 'Exam', 'Management',
    'Entity_Image', 'Medicine_Composition', 'Emergency_Contact'
]

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def run_query(sql, params=None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    if cursor.description:
        results = cursor.fetchall()
        columns = [d[0] for d in cursor.description]
    else:
        results = []
        columns = []
    cursor.close()
    conn.close()
    return results, columns

def run_multi_query(sql, params=None):
    """Run multiple statements (SET + SELECT) and return last result."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    for result in cursor.execute(sql, params or (), multi=True):
        if result.with_rows:
            results = result.fetchall()
            columns = [d[0] for d in result.description]
    cursor.close()
    conn.close()
    return results, columns

def run_modify(sql, params=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return str(obj)
        return super().default(obj)

app.json_encoder = CustomEncoder

# ======================== ROUTES ========================

@app.route('/')
@login_required
def index():
    tables_info = []
    for t in ALL_TABLES:
        try:
            rows, _ = run_query(f"SELECT COUNT(*) AS cnt FROM `{t}`")
            tables_info.append({'name': t, 'count': rows[0]['cnt']})
        except:
            tables_info.append({'name': t, 'count': 0})
    total = sum(t['count'] for t in tables_info)

    try:
        dept_stats, _ = run_query("""
            SELECT Department_Name, COUNT(*) AS cnt
            FROM Admission GROUP BY Department_Name ORDER BY cnt DESC LIMIT 5
        """)
    except:
        dept_stats = []

    try:
        recent, _ = run_query("""
            SELECT A.AdmissionID, P.Patient_First_Name, P.Patient_Last_Name,
                   A.Department_Name, A.Admission_Date, A.Total_Cost
            FROM Admission A JOIN Patient P ON A.Patient_AMKA = P.Patient_AMKA
            ORDER BY A.Admission_Date DESC LIMIT 5
        """)
    except:
        recent = []

    try:
        insurance_stats, _ = run_query("""
            SELECT P.Insurance_Provider, COUNT(*) AS cnt
            FROM Patient P JOIN Admission A ON P.Patient_AMKA = A.Patient_AMKA
            GROUP BY P.Insurance_Provider ORDER BY cnt DESC
        """)
    except:
        insurance_stats = []

    return render_template('index.html', tables=tables_info, total=total,
                           dept_stats=dept_stats, recent=recent,
                           insurance_stats=insurance_stats)

# ======================== TABLE BROWSE / CRUD ========================

@app.route('/table/<table_name>')
@login_required
def view_table(table_name):
    if table_name not in ALL_TABLES:
        flash('Μη έγκυρο όνομα πίνακα.', 'danger')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    search = request.args.get('search', '').strip()

    count_rows, _ = run_query(f"SELECT COUNT(*) AS cnt FROM `{table_name}`")
    total = count_rows[0]['cnt']

    col_info, _ = run_query(f"DESCRIBE `{table_name}`")

    if search:
        conditions = ' OR '.join([f"`{c['Field']}` LIKE %s" for c in col_info])
        search_params = [f"%{search}%"] * len(col_info)
        rows, columns = run_query(
            f"SELECT * FROM `{table_name}` WHERE {conditions} LIMIT %s OFFSET %s",
            tuple(search_params) + (per_page, offset)
        )
        count_search, _ = run_query(
            f"SELECT COUNT(*) AS cnt FROM `{table_name}` WHERE {conditions}",
            tuple(search_params)
        )
        total = count_search[0]['cnt']
    else:
        rows, columns = run_query(f"SELECT * FROM `{table_name}` LIMIT %s OFFSET %s", (per_page, offset))

    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template('table_view.html', table_name=table_name, rows=rows,
                           columns=columns, col_info=col_info,
                           page=page, total_pages=total_pages, total=total,
                           search=search)

@app.route('/table/<table_name>/insert', methods=['POST'])
@admin_required
def insert_row(table_name):
    col_info, _ = run_query(f"DESCRIBE `{table_name}`")
    cols = [c['Field'] for c in col_info]
    values = [None if request.form.get(c, '') == '' else request.form.get(c) for c in cols]
    placeholders = ', '.join(['%s'] * len(cols))
    col_names = ', '.join([f'`{c}`' for c in cols])
    try:
        run_modify(f"INSERT INTO `{table_name}` ({col_names}) VALUES ({placeholders})", tuple(values))
        flash('Η εγγραφή προστέθηκε επιτυχώς!', 'success')
    except Error as e:
        flash(f'Σφάλμα: {e.msg}', 'danger')
    return redirect(url_for('view_table', table_name=table_name))

@app.route('/table/<table_name>/delete', methods=['POST'])
@admin_required
def delete_row(table_name):
    col_info, _ = run_query(f"DESCRIBE `{table_name}`")
    pk_cols = [c['Field'] for c in col_info if c['Key'] == 'PRI']
    if not pk_cols:
        flash('Ο πίνακας δεν έχει primary key.', 'danger')
        return redirect(url_for('view_table', table_name=table_name))
    conditions = ' AND '.join([f"`{c}` = %s" for c in pk_cols])
    values = [request.form.get(c) for c in pk_cols]
    try:
        run_modify(f"DELETE FROM `{table_name}` WHERE {conditions}", tuple(values))
        flash('Η εγγραφή διαγράφηκε επιτυχώς!', 'success')
    except Error as e:
        flash(f'Σφάλμα: {e.msg}', 'danger')
    return redirect(url_for('view_table', table_name=table_name))

@app.route('/table/<table_name>/update', methods=['POST'])
@admin_required
def update_row(table_name):
    col_info, _ = run_query(f"DESCRIBE `{table_name}`")
    pk_cols = [c['Field'] for c in col_info if c['Key'] == 'PRI']
    all_cols = [c['Field'] for c in col_info]
    if not pk_cols:
        flash('Ο πίνακας δεν έχει primary key.', 'danger')
        return redirect(url_for('view_table', table_name=table_name))
    # Build SET clause (non-PK columns)
    set_cols = [c for c in all_cols if c not in pk_cols]
    set_clause = ', '.join([f"`{c}` = %s" for c in set_cols])
    set_values = [None if request.form.get(c, '') == '' else request.form.get(c) for c in set_cols]
    # Build WHERE clause (PK columns — use old_ prefix values)
    where_clause = ' AND '.join([f"`{c}` = %s" for c in pk_cols])
    where_values = [request.form.get(f'old_{c}') for c in pk_cols]
    try:
        run_modify(f"UPDATE `{table_name}` SET {set_clause} WHERE {where_clause}",
                   tuple(set_values) + tuple(where_values))
        flash('Η εγγραφή ενημερώθηκε επιτυχώς!', 'success')
    except Error as e:
        flash(f'Σφάλμα: {e.msg}', 'danger')
    return redirect(url_for('view_table', table_name=table_name))

# ======================== QUERIES ========================

@app.route('/queries')
@login_required
def queries():
    return render_template('queries.html')

# Q1: Revenue by department/year/KEN/insurance
@app.route('/query/1')
@login_required
def query1():
    sql = """SELECT Admission.Department_Name, YEAR(Admission.Release_Date) AS year,
       Admission.KEN_Code, Patient.Insurance_Provider,
       COUNT(Admission.AdmissionID) AS total_admissions,
       SUM(KEN.KEN_Cost) AS basic_cost,
       SUM(Admission.Total_Cost - KEN.KEN_Cost) AS extra_cost,
       SUM(Admission.Total_Cost) AS total_revenue
FROM Admission
JOIN KEN ON Admission.KEN_Code = KEN.KEN_Code
JOIN Patient ON Admission.Patient_AMKA = Patient.Patient_AMKA
WHERE Admission.Release_Date IS NOT NULL
GROUP BY Admission.Department_Name, YEAR(Admission.Release_Date),
         Admission.KEN_Code, Patient.Insurance_Provider
ORDER BY Admission.Department_Name, year, Admission.KEN_Code"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=1,
        title='Συνολικά Έσοδα ανά Τμήμα, Έτος, ΚΕΝ & Ασφαλιστικό Φορέα',
        desc='Ανάλυση εσόδων νοσοκομείου με βασικό κόστος ΚΕΝ και πρόσθετη χρέωση λόγω υπέρβασης ΜΔΝ, κατανομή ανά ασφαλιστικό φορέα.',
        rows=rows, columns=columns, sql=sql)

# Q2: Doctors by specialty with shifts and surgeries
@app.route('/query/2', methods=['GET', 'POST'])
@login_required
def query2():
    specialties, _ = run_query("SELECT DISTINCT Specialty FROM Doctor ORDER BY Specialty")
    selected = request.form.get('specialty', request.args.get('specialty', ''))
    rows, columns = [], []
    sql = ""
    if selected:
        sql = """SELECT Staff.Staff_AMKA, Staff.First_Name, Staff.Last_Name,
       IF(COUNT(DISTINCT Shift_Staff.Shift_Date) > 0, 'Ναι', 'Όχι') AS had_shift_this_year,
       COUNT(DISTINCT Surgery.Action_Code) AS total_surgeries
FROM Staff
JOIN Doctor ON Staff.Staff_AMKA = Doctor.Staff_AMKA
LEFT JOIN Shift_Staff ON Staff.Staff_AMKA = Shift_Staff.Staff_AMKA
                      AND YEAR(Shift_Staff.Shift_Date) = YEAR(CURDATE())
LEFT JOIN Surgery ON Staff.Staff_AMKA = Surgery.Main_Surgeon_AMKA
WHERE Doctor.Specialty = %s
GROUP BY Staff.Staff_AMKA, Staff.First_Name, Staff.Last_Name"""
        rows, columns = run_query(sql, (selected,))
        sql = sql.replace('%s', f"'{selected}'")
    return render_template('query2.html', specialties=specialties,
                           selected=selected, rows=rows, columns=columns, sql=sql)

# Q3: Patients with >3 admissions in same department
@app.route('/query/3')
@login_required
def query3():
    sql = """SELECT Patient.Patient_AMKA, Patient.Patient_First_Name, Patient.Patient_Last_Name,
       Admission.Department_Name,
       COUNT(Admission.AdmissionID) AS times_admitted,
       SUM(Admission.Total_Cost) AS total_cost
FROM Patient
JOIN Admission ON Patient.Patient_AMKA = Admission.Patient_AMKA
GROUP BY Patient.Patient_AMKA, Patient.Patient_First_Name, Patient.Patient_Last_Name,
         Admission.Department_Name
HAVING COUNT(Admission.AdmissionID) > 3
ORDER BY total_cost DESC"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=3,
        title='Ασθενείς με >3 Νοσηλείες στο Ίδιο Τμήμα',
        desc='Ασθενείς που νοσηλεύτηκαν περισσότερες από 3 φορές στο ίδιο τμήμα με συνολικό κόστος.',
        rows=rows, columns=columns, sql=sql)

# Q4: Doctor evaluation averages
@app.route('/query/4', methods=['GET', 'POST'])
@login_required
def query4():
    doctors, _ = run_query("""
        SELECT DISTINCT DE.Doctor_AMKA, S.First_Name, S.Last_Name
        FROM Doctor_Evaluation DE JOIN Staff S ON DE.Doctor_AMKA = S.Staff_AMKA
        ORDER BY S.Last_Name
    """)
    selected = request.form.get('doctor_amka', request.args.get('doctor_amka', ''))
    rows, columns = [], []
    sql = ""
    if selected:
        sql = """SELECT Doctor_Evaluation.Doctor_AMKA,
       AVG(Doctor_Evaluation.Doctor_Quality) AS avg_medical_care_quality,
       AVG(Evaluation.Overall_Experience) AS avg_overall_hospitalization_experience
FROM Doctor_Evaluation
JOIN Evaluation ON Doctor_Evaluation.AdmissionID = Evaluation.AdmissionID
WHERE Doctor_Evaluation.Doctor_AMKA = %s
GROUP BY Doctor_Evaluation.Doctor_AMKA"""
        rows, columns = run_query(sql, (selected,))
        sql = sql.replace('%s', f"'{selected}'")
    return render_template('query4.html', doctors=doctors,
                           selected=selected, rows=rows, columns=columns, sql=sql)

# Q5: Young doctors (<35) with most surgeries
@app.route('/query/5')
@login_required
def query5():
    sql = """SELECT Staff.Staff_AMKA, Staff.First_Name, Staff.Last_Name, Staff.Age,
       COUNT(Surgery.Action_Code) AS surgery_count
FROM Staff
JOIN Doctor ON Staff.Staff_AMKA = Doctor.Staff_AMKA
JOIN Surgery ON Doctor.Staff_AMKA = Surgery.Main_Surgeon_AMKA
WHERE Staff.Age < 35
GROUP BY Staff.Staff_AMKA, Staff.First_Name, Staff.Last_Name, Staff.Age
ORDER BY surgery_count DESC"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=5,
        title='Νέοι Ιατροί (<35) με τις Περισσότερες Επεμβάσεις',
        desc='Νέοι ιατροί (ηλικία < 35) που εκτέλεσαν τις περισσότερες χειρουργικές επεμβάσεις ως κύριοι χειρουργοί.',
        rows=rows, columns=columns, sql=sql)

# Q6: Patient admission history
@app.route('/query/6', methods=['GET', 'POST'])
@login_required
def query6():
    patients, _ = run_query("""
        SELECT DISTINCT P.Patient_AMKA, P.Patient_First_Name, P.Patient_Last_Name
        FROM Patient P JOIN Admission A ON P.Patient_AMKA = A.Patient_AMKA
        ORDER BY P.Patient_Last_Name
    """)
    selected = request.form.get('patient_amka', request.args.get('patient_amka', ''))
    rows, columns = [], []
    sql = ""
    if selected:
        sql = """SELECT A.Admission_Date, A.Release_Date, A.Total_Cost, A.Department_Name,
       A.Admission_Diagnosis_ICD_10_Code, A.Release_Diagnosis_ICD_10_Code,
       (E.Nursing_Quality+E.Cleanliness+E.Food+E.Overall_Experience)/4.0 AS Average_Evaluation
FROM Admission A
LEFT OUTER JOIN Evaluation E ON A.AdmissionID = E.AdmissionID
WHERE A.Patient_AMKA = %s
ORDER BY A.Admission_Date"""
        rows, columns = run_query(sql, (selected,))
        sql = sql.replace('%s', f"'{selected}'")
    return render_template('query6.html', patients=patients,
                           selected=selected, rows=rows, columns=columns, sql=sql)

# Q7: Active substances — allergies vs medicines
@app.route('/query/7')
@login_required
def query7():
    sql = """SELECT substance.Substance_Name,
       (SELECT COUNT(*) FROM Patient_Allergy PA
        WHERE PA.Substance_ID = substance.Substance_ID) AS Allergy_Count,
       (SELECT COUNT(*) FROM Medicine_Composition MC
        WHERE MC.Substance_ID = substance.Substance_ID) AS Medicine_Count
FROM Active_Substance substance
ORDER BY Allergy_Count DESC"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=7,
        title='Δραστικές Ουσίες — Αλλεργίες & Φάρμακα',
        desc='Αριθμός αλλεργιών και φαρμάκων ανά δραστική ουσία.',
        rows=rows, columns=columns, sql=sql)

# Q8: Staff NOT on shift for date/department
@app.route('/query/8', methods=['GET', 'POST'])
@login_required
def query8():
    departments, _ = run_query("SELECT Department_Name FROM Department ORDER BY Department_Name")
    selected_dept = request.form.get('department', request.args.get('department', ''))
    selected_date = request.form.get('target_date', request.args.get('target_date', '2026-03-01'))
    rows, columns = [], []
    sql = ""
    if selected_dept:
        sql = """SELECT staff.Staff_AMKA, staff.First_Name, staff.Last_Name, staff.Staff_Type
FROM STAFF staff
WHERE NOT EXISTS(
    SELECT 1
    FROM Shift shift
    INNER JOIN Shift_Staff shift_staff USING (Shift_Date, Shift_Type, Department_Name)
    WHERE shift.Department_Name = %s
    AND shift_staff.Staff_AMKA = staff.Staff_AMKA
    AND DATE(shift.Start_Time) <= %s
    AND DATE(shift.End_Time) >= %s
)"""
        rows, columns = run_query(sql, (selected_dept, selected_date, selected_date))
        sql = sql.replace('%s', f"'{selected_dept}'", 1).replace('%s', f"'{selected_date}'", 1).replace('%s', f"'{selected_date}'", 1)
    return render_template('query8.html', departments=departments,
                           selected_dept=selected_dept, selected_date=selected_date,
                           rows=rows, columns=columns, sql=sql)

# Q9: Patients >15 days stayed in last year (with duplicates)
@app.route('/query/9')
@login_required
def query9():
    sql = """WITH ppl AS (
    SELECT p.Patient_AMKA, p.Patient_First_Name, p.Patient_Last_Name,
           SUM(DATEDIFF(COALESCE(a.Release_Date, CURDATE()), a.Admission_Date)) AS Total_Days_Stayed
    FROM Patient p
    INNER JOIN Admission a USING (Patient_AMKA)
    WHERE a.Admission_Date > DATE_SUB(CURDATE(), INTERVAL 365 DAY)
    GROUP BY p.Patient_AMKA
    HAVING Total_Days_Stayed > 15
)
SELECT * FROM ppl X
WHERE EXISTS(
    SELECT 1 FROM ppl Y
    WHERE Y.Total_Days_Stayed = X.Total_Days_Stayed
    AND Y.Patient_AMKA <> X.Patient_AMKA
)
ORDER BY Total_Days_Stayed DESC"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=9,
        title='Ασθενείς >15 Ημέρες Νοσηλείας (τελευταίο έτος)',
        desc='Ασθενείς με συνολική παραμονή >15 ημερών το τελευταίο έτος, που μοιράζονται τον ίδιο αριθμό ημερών με κάποιον άλλο.',
        rows=rows, columns=columns, sql=sql)

# Q10: Top 3 co-prescribed substance pairs
@app.route('/query/10')
@login_required
def query10():
    sql = """WITH substance_given AS (
    SELECT p.AdmissionID, p.Start_Date, p.End_Date,
           AC.Substance_ID, AC.Substance_Name
    FROM Prescription p
    INNER JOIN Medicine M USING (EMA_Code)
    INNER JOIN Medicine_Composition MC USING (EMA_Code)
    INNER JOIN Active_Substance AC USING (Substance_ID)
)
SELECT substance_A.Substance_Name AS Substance_A,
       substance_B.Substance_Name AS Substance_B,
       COUNT(*) AS Pair_Count
FROM substance_given substance_A
INNER JOIN substance_given substance_B
    ON substance_A.AdmissionID = substance_B.AdmissionID
WHERE substance_A.Substance_ID < substance_B.Substance_ID
    AND substance_A.Start_Date <= substance_B.End_Date
    AND substance_B.Start_Date <= substance_A.End_Date
GROUP BY substance_A.Substance_ID, substance_B.Substance_ID
ORDER BY Pair_Count DESC
LIMIT 3"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=10,
        title='Top 3 Ζεύγη Συγχορηγούμενων Ουσιών',
        desc='Τα 3 πιο συχνά ζεύγη δραστικών ουσιών που χορηγούνται ταυτόχρονα στην ίδια νοσηλεία.',
        rows=rows, columns=columns, sql=sql)

# Q11: Doctors with ≤ max-5 surgeries this year
@app.route('/query/11')
@login_required
def query11():
    sql = """SELECT d.Staff_AMKA,
       COUNT(ma.Action_Code) AS num_surgeries
FROM Doctor d
LEFT JOIN Surgery ON Surgery.Main_Surgeon_AMKA = d.Staff_AMKA
LEFT JOIN Medical_Action ma ON Surgery.Action_Code = ma.Action_Code
    AND YEAR(ma.Action_Start) = YEAR(CURDATE())
GROUP BY d.Staff_AMKA
HAVING COUNT(ma.Action_Code) <= (
    SELECT MAX(num_surgeries)
    FROM (
        SELECT COUNT(*) AS num_surgeries
        FROM Surgery
        JOIN Medical_Action ON Surgery.Action_Code = Medical_Action.Action_Code
        WHERE YEAR(Medical_Action.Action_Start) = YEAR(CURDATE())
        GROUP BY Main_Surgeon_AMKA
    ) AS surgeon_counts
) - 5
ORDER BY num_surgeries DESC"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=11,
        title='Ιατροί με ≤ max-5 Επεμβάσεις Φέτος',
        desc='Ιατροί που έκαναν τουλάχιστον 5 λιγότερες επεμβάσεις από τον κορυφαίο χειρουργό φέτος.',
        rows=rows, columns=columns, sql=sql)

# Q12: Weekly shift schedule
@app.route('/query/12', methods=['GET', 'POST'])
@login_required
def query12():
    selected_date = request.form.get('week_start', request.args.get('week_start', '2026-03-01'))
    sql = """SELECT ss.Shift_Date, ss.Shift_Type, ss.Department_Name, s.Staff_Type,
       CASE
           WHEN s.Staff_Type = 'Ιατρός'       THEN d.Specialty
           WHEN s.Staff_Type = 'Νοσηλευτής'   THEN n.Nurse_Rank
           WHEN s.Staff_Type = 'Διοικητικός'  THEN m.Role
       END AS Subcategory,
       COUNT(*) AS Num_Staff
FROM Shift_Staff ss
JOIN STAFF s ON ss.Staff_AMKA = s.Staff_AMKA
LEFT JOIN Doctor d     ON ss.Staff_AMKA = d.Staff_AMKA
LEFT JOIN Nurse n      ON ss.Staff_AMKA = n.Staff_AMKA
LEFT JOIN Management m ON ss.Staff_AMKA = m.Staff_AMKA
WHERE ss.Shift_Date BETWEEN %s AND DATE_ADD(%s, INTERVAL 6 DAY)
GROUP BY ss.Shift_Date, ss.Shift_Type, ss.Department_Name, s.Staff_Type, Subcategory
ORDER BY ss.Shift_Date, ss.Shift_Type, ss.Department_Name, s.Staff_Type"""
    rows, columns = run_query(sql, (selected_date, selected_date))
    display_sql = sql.replace('%s', f"'{selected_date}'", 1).replace('%s', f"'{selected_date}'", 1)
    return render_template('query12.html', selected_date=selected_date,
                           rows=rows, columns=columns, sql=display_sql)

# Q13: Doctor hierarchy (recursive)
@app.route('/query/13')
@login_required
def query13():
    sql = """WITH RECURSIVE hierarchy AS (
    SELECT d.Staff_AMKA AS original_doctor, d.Staff_AMKA AS current_doctor,
           d.Supervisor_AMKA, 1 AS Level
    FROM Doctor d WHERE d.Supervisor_AMKA IS NOT NULL
    UNION ALL
    SELECT h.original_doctor, d_next.Staff_AMKA, d_next.Supervisor_AMKA, h.Level + 1
    FROM Doctor d_next
    JOIN hierarchy h ON d_next.Staff_AMKA = h.Supervisor_AMKA
    WHERE d_next.Supervisor_AMKA IS NOT NULL
)
SELECT DISTINCT hierarchy.original_doctor,
       s1.First_Name, s1.Last_Name,
       s2.First_Name AS Supervisor_First_Name,
       s2.Last_Name AS Supervisor_Last_Name,
       Level
FROM hierarchy
JOIN STAFF s1 ON hierarchy.current_doctor = s1.Staff_AMKA
JOIN STAFF s2 ON hierarchy.Supervisor_AMKA = s2.Staff_AMKA
ORDER BY original_doctor, Level"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=13,
        title='Ιεραρχία Ιατρών (Recursive)',
        desc='Αναδρομική ιεραρχία εποπτών — κάθε ιατρός και η αλυσίδα εποπτείας του.',
        rows=rows, columns=columns, sql=sql)

# Q14: ICD-10 categories with same admissions across years
@app.route('/query/14')
@login_required
def query14():
    sql = """SELECT counts_a.ICD10_Category AS ICD10_Category,
       counts_a.admission_year AS Year_1,
       counts_b.admission_year AS Year_2,
       counts_a.Num_Admissions
FROM (
    SELECT LEFT(Admission_Diagnosis_ICD_10_Code, 1) AS ICD10_Category,
           YEAR(Admission_Date) AS admission_year, COUNT(*) AS Num_Admissions
    FROM Admission GROUP BY LEFT(Admission_Diagnosis_ICD_10_Code, 1), YEAR(Admission_Date)
    HAVING COUNT(*) >= 5
) AS counts_a
JOIN (
    SELECT LEFT(Admission_Diagnosis_ICD_10_Code, 1) AS ICD10_Category,
           YEAR(Admission_Date) AS admission_year, COUNT(*) AS Num_Admissions
    FROM Admission GROUP BY LEFT(Admission_Diagnosis_ICD_10_Code, 1), YEAR(Admission_Date)
    HAVING COUNT(*) >= 5
) AS counts_b
ON counts_a.ICD10_Category = counts_b.ICD10_Category
AND counts_b.admission_year = counts_a.admission_year + 1
AND counts_a.Num_Admissions = counts_b.Num_Admissions"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=14,
        title='Κατηγορίες ICD-10 με Ίδιες Νοσηλείες σε Διαδοχικά Έτη',
        desc='Κατηγορίες ICD-10 (πρώτο γράμμα) με ≥5 νοσηλείες που εμφανίζουν ίδιο αριθμό σε δύο συνεχόμενα έτη.',
        rows=rows, columns=columns, sql=sql)

# Q15: Triage statistics by urgency level
@app.route('/query/15')
@login_required
def query15():
    sql = """SELECT stats.Urgency_Level, stats.Num_Triages, stats.Avg_Wait,
       stats.Pct_Admitted, refs.Department_Name, refs.Num_Referred
FROM (
    SELECT T.Urgency_Level, COUNT(*) AS Num_Triages,
           AVG(T.Waiting_Minutes) AS Avg_Wait,
           COUNT(A.AdmissionID) / COUNT(*) * 100 AS Pct_Admitted
    FROM Triage T
    LEFT JOIN Admission A ON T.Triage_ID = A.Triage_ID
    GROUP BY T.Urgency_Level
) AS stats
JOIN (
    SELECT T.Urgency_Level, A.Department_Name, COUNT(*) AS Num_Referred
    FROM Triage T
    JOIN Admission A ON T.Triage_ID = A.Triage_ID
    GROUP BY T.Urgency_Level, A.Department_Name
) AS refs ON stats.Urgency_Level = refs.Urgency_Level
ORDER BY stats.Urgency_Level, refs.Department_Name"""
    rows, columns = run_query(sql)
    return render_template('query_result.html', query_num=15,
        title='Στατιστικά Διαλογής ανά Επίπεδο Επείγοντος',
        desc='Αριθμός τριάζ, μέσος χρόνος αναμονής, ποσοστό εισαγωγής και κατανομή παραπομπών ανά τμήμα.',
        rows=rows, columns=columns, sql=sql)

# ======================== CUSTOM SQL ========================

@app.route('/custom', methods=['GET', 'POST'])
@login_required
def custom_query():
    rows, columns, sql, error = [], [], '', None
    if request.method == 'POST':
        sql = request.form.get('sql', '').strip()
        if sql:
            try:
                upper = sql.upper().lstrip()
                if any(upper.startswith(k) for k in ['SELECT', 'EXPLAIN', 'SHOW', 'DESCRIBE', 'DESC', 'WITH']):
                    rows, columns = run_query(sql)
                elif upper.startswith('SET'):
                    rows, columns = run_multi_query(sql)
                else:
                    if session.get('role') != 'admin':
                        error = 'Δεν έχετε δικαίωμα εκτέλεσης DML ερωτημάτων (viewer mode).'
                    else:
                        affected = run_modify(sql)
                        flash(f'{affected} εγγραφή(-ές) επηρεάστηκαν.', 'success')
            except Error as e:
                error = str(e)
    return render_template('custom.html', rows=rows, columns=columns, sql=sql, error=error)

# ======================== API for Charts ========================

@app.route('/api/dept_revenue')
def api_dept_revenue():
    rows, _ = run_query("""
        SELECT Department_Name, SUM(Total_Cost) AS revenue
        FROM Admission WHERE Release_Date IS NOT NULL
        GROUP BY Department_Name ORDER BY revenue DESC
    """)
    return jsonify([{'dept': r['Department_Name'], 'revenue': float(r['revenue']) if r['revenue'] else 0} for r in rows])

@app.route('/api/insurance_dist')
def api_insurance_dist():
    rows, _ = run_query("""
        SELECT Insurance_Provider, COUNT(*) AS cnt FROM Patient GROUP BY Insurance_Provider
    """)
    return jsonify([{'provider': r['Insurance_Provider'], 'count': r['cnt']} for r in rows])

@app.route('/api/monthly_admissions')
def api_monthly_admissions():
    rows, _ = run_query("""
        SELECT DATE_FORMAT(Admission_Date, '%Y-%m') AS month, COUNT(*) AS cnt
        FROM Admission GROUP BY month ORDER BY month
    """)
    return jsonify([{'month': r['month'], 'count': r['cnt']} for r in rows])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
