import json, random, datetime, sys, os

random.seed(42)

# ─── helpers ─────────────────────────────────────────────────────────
def esc(s):
    """Escape single quotes and backslashes for SQL."""
    if s is None:
        return 'NULL'
    return str(s).replace("\\", "\\\\").replace("'", "''")

def sql_str(s, maxlen=None):
    if s is None:
        return 'NULL'
    s = str(s).strip().replace('\n', ' ').replace('\r', ' ')
    if maxlen:
        s = s[:maxlen]
    return f"'{esc(s)}'"

def sql_int(n):
    return str(int(n))

def sql_dec(n):
    return f"{float(n):.2f}"

def sql_date(d):
    return f"'{d.strftime('%Y-%m-%d')}'"

def sql_datetime(dt):
    return f"'{dt.strftime('%Y-%m-%d %H:%M:%S')}'"

def sql_null():
    return 'NULL'

def feminize_lastname(ln):
    if ln.endswith('ός'): return ln[:-2]+'ού'
    elif ln.endswith('ος'): return ln[:-2]+'ου'
    elif ln.endswith('ής'): return ln[:-2]+'ή'
    elif ln.endswith('ης'): return ln[:-2]+'η'
    elif ln.endswith('άς'): return ln[:-2]+'ά'
    elif ln.endswith('ας'): return ln[:-2]+'α'
    return ln

def rand_amka():
    """Generate 11-digit AMKA."""
    return ''.join([str(random.randint(0,9)) for _ in range(11)])

def rand_date(start, end):
    delta = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, max(0, delta)))

def rand_datetime(start_date, end_date):
    d = rand_date(start_date, end_date)
    h = random.randint(0, 23)
    m = random.randint(0, 59)
    return datetime.datetime(d.year, d.month, d.day, h, m, 0)

def batch_insert(f, table, columns, rows, batch_size=500):
    """Write batch INSERT statements."""
    col_str = ', '.join(columns)
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        f.write(f"INSERT INTO `{table}` ({col_str}) VALUES\n")
        for j, row in enumerate(batch):
            vals = ', '.join(row)
            sep = ',' if j < len(batch)-1 else ';'
            f.write(f"  ({vals}){sep}\n")
        f.write('\n')

# ─── Load reference data ────────────────────────────────────────────
print("Loading reference data...")
with open('ken_full.json') as f:
    ken_data = json.load(f)
with open('icd10_full.json') as f:
    icd10_data = json.load(f)
with open('ema_medicines.json') as f:
    ema_medicines = json.load(f)
with open('ema_substances.json') as f:
    ema_substances = json.load(f)
with open('ema_compositions.json') as f:
    ema_compositions = json.load(f)
with open('medical_actions_full.json') as f:
    medical_actions_ref = json.load(f)

print(f"  KEN: {len(ken_data)}")
print(f"  ICD-10: {len(icd10_data)}")
print(f"  Medicines: {len(ema_medicines)}")
print(f"  Substances: {len(ema_substances)}")
print(f"  Compositions: {len(ema_compositions)}")
print(f"  Medical actions ref: {len(medical_actions_ref)}")

# ─── Configuration ──────────────────────────────────────────────────
DEPARTMENTS = [
    ('Καρδιολογία',       'Τμήμα καρδιαγγειακών παθήσεων',     40, 1, 'Κτίριο Α'),
    ('Χειρουργική',       'Τμήμα γενικής χειρουργικής',         35, 2, 'Κτίριο Α'),
    ('ΜΕΘ',              'Μονάδα εντατικής θεραπείας',          20, 1, 'Κτίριο Β'),
    ('Επείγοντα',         'Τμήμα επειγόντων περιστατικών',      25, 0, 'Κτίριο Α'),
    ('Νευρολογία',        'Τμήμα νευρολογικών παθήσεων',        30, 3, 'Κτίριο Β'),
    ('Παθολογία',         'Τμήμα παθολογικών νοσημάτων',        45, 2, 'Κτίριο Α'),
    ('Ορθοπεδική',        'Τμήμα ορθοπεδικής χειρουργικής',     30, 3, 'Κτίριο Α'),
    ('Ουρολογία',         'Τμήμα ουρολογικών παθήσεων',         25, 4, 'Κτίριο Β'),
    ('Οφθαλμολογία',      'Τμήμα οφθαλμολογικών παθήσεων',      20, 4, 'Κτίριο Α'),
    ('ΩΡΛ',              'Ωτορινολαρυγγολογικό τμήμα',         20, 3, 'Κτίριο Β'),
    ('Πνευμονολογία',     'Τμήμα πνευμονολογίας',               30, 2, 'Κτίριο Β'),
    ('Γαστρεντερολογία',  'Τμήμα γαστρεντερολογίας',            25, 1, 'Κτίριο Β'),
    ('Νεφρολογία',        'Τμήμα νεφρολογίας',                  20, 4, 'Κτίριο Α'),
    ('Αιματολογία',       'Τμήμα αιματολογίας',                 20, 5, 'Κτίριο Β'),
    ('Ογκολογία',         'Τμήμα ογκολογίας',                   25, 5, 'Κτίριο Α'),
]

SPECIALTIES = {
    'Καρδιολογία': 'Καρδιολογία',
    'Χειρουργική': 'Γενική Χειρουργική',
    'ΜΕΘ': 'Εντατικολογία',
    'Επείγοντα': 'Επείγουσα Ιατρική',
    'Νευρολογία': 'Νευρολογία',
    'Παθολογία': 'Παθολογία',
    'Ορθοπεδική': 'Ορθοπεδική',
    'Ουρολογία': 'Ουρολογία',
    'Οφθαλμολογία': 'Οφθαλμολογία',
    'ΩΡΛ': 'Ωτορινολαρυγγολογία',
    'Πνευμονολογία': 'Πνευμονολογία',
    'Γαστρεντερολογία': 'Γαστρεντερολογία',
    'Νεφρολογία': 'Νεφρολογία',
    'Αιματολογία': 'Αιματολογία',
    'Ογκολογία': 'Ογκολογία',
}

MALE_FIRST = [
    'Γεώργιος','Ιωάννης','Κωνσταντίνος','Δημήτριος','Νικόλαος','Παναγιώτης',
    'Βασίλειος','Χρήστος','Αθανάσιος','Μιχαήλ','Ευάγγελος','Ανδρέας',
    'Θεόδωρος','Σπυρίδων','Αλέξανδρος','Εμμανουήλ','Στέφανος','Πέτρος',
    'Αντώνιος','Φώτιος','Ηλίας','Σωτήριος','Λεωνίδας','Γρηγόριος',
    'Κυριάκος','Στυλιανός','Αριστείδης','Θεμιστοκλής','Αποστόλος','Μάριος',
]
FEMALE_FIRST = [
    'Μαρία','Ελένη','Αικατερίνη','Βασιλική','Σοφία','Αναστασία',
    'Ευαγγελία','Γεωργία','Δήμητρα','Παρασκευή','Χριστίνα','Ειρήνη',
    'Θεοδώρα','Αθηνά','Κωνσταντίνα','Φωτεινή','Άννα','Ελευθερία',
    'Μαργαρίτα','Σταυρούλα','Πηνελόπη','Αγγελική','Ολυμπία','Ξανθίπη',
    'Καλλιόπη','Στέλλα','Νίκη','Δέσποινα','Βαρβάρα','Ευγενία',
]
LAST_NAMES = [
    'Παπαδόπουλος','Βλαχόπουλος','Αντωνίου','Γεωργίου','Νικολάου',
    'Δημητρίου','Κωνσταντινίδης','Μαυρίδης','Χατζηπέτρος','Ιωαννίδης',
    'Καραγιάννης','Μακρής','Παπαγεωργίου','Αλεξίου','Θεοδωρίδης',
    'Σταματίου','Βασιλείου','Χρυσανθόπουλος','Λαζαρίδης','Σπανός',
    'Κοντογιάννης','Τσιμπίδης','Ρήγας','Μπαλάσκας','Γαλανός',
    'Κουτσούμπας','Φραγκούλης','Ζαχαρίας','Λιάκος','Μπακογιάννης',
    'Πολυχρονίδης','Σακελλαρίου','Τζανετάκος','Οικονομίδης','Καρατζάς',
    'Δρακόπουλος','Λεβέντης','Μαρκόπουλος','Ξενάκης','Παπανδρέου',
]

PROFESSIONS = [
    'Μηχανικός','Εκπαιδευτικός','Λογιστής','Δικηγόρος','Γιατρός',
    'Φαρμακοποιός','Αρχιτέκτονας','Προγραμματιστής','Δημοσιογράφος',
    'Συνταξιούχος','Φοιτητής','Άνεργος','Αγρότης','Οδηγός','Υπάλληλος',
    'Ελεύθερος Επαγγελματίας','Στρατιωτικός','Αστυνομικός','Νοικοκυρά',
]

NATIONALITIES = ['Ελληνική','Ελληνική','Ελληνική','Ελληνική','Ελληνική',
                  'Αλβανική','Βουλγαρική','Ρουμανική','Γερμανική','Βρετανική']

CITIES = ['Αθήνα','Θεσσαλονίκη','Πάτρα','Ηράκλειο','Λάρισα','Βόλος',
          'Ιωάννινα','Χανιά','Καβάλα','Σέρρες','Χαλκίδα','Κατερίνη',
          'Τρίκαλα','Καλαμάτα','Ρόδος','Κέρκυρα','Αγρίνιο','Λαμία']

STREETS = ['Λεωφ. Αλεξάνδρας','Οδός Σταδίου','Λεωφ. Κηφισίας','Οδός Πατησίων',
           'Λεωφ. Βουλιαγμένης','Οδός Ερμού','Λεωφ. Μεσογείων','Οδός Πανεπιστημίου',
           'Οδός Ακαδημίας','Λεωφ. Συγγρού','Οδός Σόλωνος','Οδός Τσιμισκή']

EXAM_TYPES = [
    ('Αιματολογική', 'mg/dL'), ('Βιοχημική', 'U/L'), ('Ακτινογραφία', None),
    ('Υπερηχογράφημα', None), ('Αξονική Τομογραφία', None),
    ('Μαγνητική Τομογραφία', None), ('Ηλεκτροκαρδιογράφημα', None),
    ('Γενική Αίματος', 'x10³/μL'), ('Γενική Ούρων', None),
    ('Καλλιέργεια', None), ('Βιοψία', None), ('Σπιρομέτρηση', 'L'),
    ('Ενδοσκόπηση', None), ('Ηλεκτροεγκεφαλογράφημα', None),
]

EXAM_RESULTS = {
    'Αιματολογική': ['85','92','110','130','78','145','68','155'],
    'Βιοχημική': ['25','38','42','55','18','62','72','30'],
    'Ακτινογραφία': ['Φυσιολογική','Παθολογική','Αμφίβολη'],
    'Υπερηχογράφημα': ['Φυσιολογικό','Παθολογικό','Αμφίβολο'],
    'Αξονική Τομογραφία': ['Χωρίς ευρήματα','Ύποπτα ευρήματα','Παθολογική'],
    'Μαγνητική Τομογραφία': ['Φυσιολογική','Παθολογική','Αμφίβολη'],
    'Ηλεκτροκαρδιογράφημα': ['Φυσιολογικό','Αρρυθμία','Ισχαιμία'],
    'Γενική Αίματος': ['5.2','6.8','4.1','7.5','8.2','3.8'],
    'Γενική Ούρων': ['Φυσιολογική','Παθολογική','Ίχνη λευκωμάτων'],
    'Καλλιέργεια': ['Αρνητική','Θετική','Σε εξέλιξη'],
    'Βιοψία': ['Καλοήθης','Κακοήθης','Αμφίβολη'],
    'Σπιρομέτρηση': ['3.2','2.8','4.1','1.9','3.5'],
    'Ενδοσκόπηση': ['Φυσιολογική','Παθολογική','Ελκώδης'],
    'Ηλεκτροεγκεφαλογράφημα': ['Φυσιολογικό','Παθολογικό','Επιληπτική'],
}

SYMPTOMS = [
    'Πονοκέφαλος','Πυρετός','Βήχας','Δύσπνοια','Θωρακικό άλγος',
    'Κοιλιακό άλγος','Ναυτία','Εμετός','Ζάλη','Αδυναμία',
    'Πόνος στην πλάτη','Οίδημα κάτω άκρων','Αιμορραγία','Τραύμα',
    'Αλλεργική αντίδραση','Πόνος στο στήθος','Πυρετός 39°C',
    'Δερματικό εξάνθημα','Αρθραλγία','Μυαλγία',
]

ROOM_TYPES = ['Γενικό','Καρδιοχειρουργικό','Ορθοπεδικό','Νευροχειρουργικό',
              'Οφθαλμολογικό','ΩΡΛ','Ουρολογικό','Ογκολογικό',
              'Ενδοσκοπικό','Πολλαπλών Χρήσεων']

SURGERY_TYPES = ['Ανοικτή','Λαπαροσκοπική','Ρομποτική','Αρθροσκοπική',
                 'Ενδοσκοπική','Μικροχειρουργική']

# ─── Helper: clean name for consistent mapping ────────────────────
def clean_name(s, maxlen=None):
    """Clean name for consistent mapping (same logic as CSV export)."""
    if s is None: return ""
    s = str(s).strip().replace('\n', ' ').replace('\r', ' ')
    if maxlen: s = s[:maxlen]
    return s

# ─── Build EMA code / substance ID mappings ─────────────────────────
# IMPORTANT: use clean_name() for consistent mapping between load.sql and CSVs
print("Building EMA/Substance ID mappings...")
med_name_to_ema = {}
med_raw_to_clean = {}  # raw name → cleaned name (for composition lookup)
for i, med in enumerate(ema_medicines):
    code = f"EMA{i+1:06d}"
    cleaned = clean_name(med['name'], 200)
    med_name_to_ema[cleaned] = code
    med_raw_to_clean[med['name']] = cleaned

sub_name_to_id = {}
sub_raw_to_clean = {}
for i, sub_name in enumerate(ema_substances):
    sid = f"SUB{i+1:05d}"
    cleaned = clean_name(sub_name, 200)
    sub_name_to_id[cleaned] = sid
    sub_raw_to_clean[sub_name] = cleaned

# ─── Generate people ────────────────────────────────────────────────
print("Generating synthetic data...")

used_amkas = set()
def unique_amka():
    while True:
        a = rand_amka()
        if a not in used_amkas:
            used_amkas.add(a)
            return a

def gen_email(first, last, domain='hospital.gr'):
    tr = {'α':'a','β':'v','γ':'g','δ':'d','ε':'e','ζ':'z','η':'i','θ':'th',
          'ι':'i','κ':'k','λ':'l','μ':'m','ν':'n','ξ':'x','ο':'o','π':'p',
          'ρ':'r','σ':'s','ς':'s','τ':'t','υ':'y','φ':'f','χ':'ch','ψ':'ps','ω':'o',
          'ά':'a','έ':'e','ή':'i','ί':'i','ό':'o','ύ':'y','ώ':'o','ϊ':'i','ΰ':'y',
          'ΐ':'i'}
    def transliterate(s):
        return ''.join(tr.get(c.lower(), c) for c in s if c.isalpha())
    f = transliterate(first)
    l = transliterate(last)
    return f"{f}.{l}@{domain}"[:45]

def gen_phone():
    return f"69{random.randint(10000000,99999999)}"

# ─── Staff + Doctors (hierarchy per department) ─────────────────────
staff_records = []       # all staff (for lookups)
doctor_staff_records = []  # STAFF rows for doctors only (Phase 1)
other_staff_records = []   # STAFF rows for nurses + management (Phase 2)
doctor_records = []
dept_directors = {}
doctor_amkas_by_dept = {}
all_doctor_amkas = []

license_counter = 1000

for dept_name, desc, beds, floor, building in DEPARTMENTS:
    specialty = SPECIALTIES[dept_name]
    dept_doctors = []

    hierarchy = [
        ('Διευθυντής', 1),
        ('Επιμελητής Α', 2),
        ('Επιμελητής Β', 3),
        ('Ειδικευόμενος', 3),
    ]

    director_amka = None
    prev_rank_amkas = []

    for rank, count in hierarchy:
        for _ in range(count):
            amka = unique_amka()
            gender = random.choice(['M','F'])
            first = random.choice(MALE_FIRST if gender == 'M' else FEMALE_FIRST)
            last = random.choice(LAST_NAMES)
            if gender == 'F':
                last = feminize_lastname(last)

            if rank == 'Διευθυντής':
                age = random.randint(50, 65)
            elif rank == 'Επιμελητής Α':
                age = random.randint(40, 55)
            elif rank == 'Επιμελητής Β':
                age = random.randint(35, 48)
            else:
                age = random.randint(27, 35)

            email = gen_email(first, last)
            phone = gen_phone()
            years_working = age - 25 - random.randint(0, 5)
            hiring = datetime.date(2026,1,1) - datetime.timedelta(days=years_working*365)

            staff_records.append((amka, first, last, age, email, phone, hiring, 'Ιατρός'))
            doctor_staff_records.append((amka, first, last, age, email, phone, hiring, 'Ιατρός'))

            if rank == 'Διευθυντής':
                supervisor = None
                director_amka = amka
            elif rank == 'Επιμελητής Α':
                supervisor = director_amka
            elif rank == 'Επιμελητής Β':
                supervisor = random.choice(prev_rank_amkas) if prev_rank_amkas else director_amka
            else:
                supervisor = random.choice(prev_rank_amkas) if prev_rank_amkas else director_amka

            license_counter += 1
            doctor_records.append((str(license_counter), specialty, rank, amka, supervisor))
            dept_doctors.append(amka)
            all_doctor_amkas.append(amka)

            if rank == 'Διευθυντής':
                dept_directors[dept_name] = amka

        if rank in ('Επιμελητής Α', 'Επιμελητής Β'):
            prev_rank_amkas = [dr[3] for dr in doctor_records if dr[2] == rank and dr[3] in dept_doctors]

    doctor_amkas_by_dept[dept_name] = dept_doctors

print(f"  Doctors: {len(doctor_records)}")

# ─── Nurses ─────────────────────────────────────────────────────────
nurse_records = []
NURSE_RANKS = ['Βοηθός Νοσηλευτή', 'Νοσηλευτής', 'Προϊστάμενος']
all_nurse_amkas = []
nurse_amkas_by_dept = {}

# 18 nurses per department: 2 Προϊστάμενος, 8 Νοσηλευτής, 8 Βοηθός
NURSE_DIST = [('Προϊστάμενος', 2), ('Νοσηλευτής', 8), ('Βοηθός Νοσηλευτή', 8)]

for dept_name, *_ in DEPARTMENTS:
    dept_nurses = []
    for rank, count in NURSE_DIST:
        for _ in range(count):
            amka = unique_amka()
            gender = random.choice(['M','F'])
            first = random.choice(MALE_FIRST if gender == 'M' else FEMALE_FIRST)
            last = random.choice(LAST_NAMES)
            if gender == 'F':
                last = feminize_lastname(last)
            age = random.randint(25, 55)
            email = gen_email(first, last, 'hospital.gr')
            phone = gen_phone()
            hiring = datetime.date(2026,1,1) - datetime.timedelta(days=random.randint(365, 365*15))

            staff_records.append((amka, first, last, age, email, phone, hiring, 'Νοσηλευτής'))
            other_staff_records.append((amka, first, last, age, email, phone, hiring, 'Νοσηλευτής'))
            nurse_records.append((rank, amka, dept_name))
            all_nurse_amkas.append(amka)
            dept_nurses.append(amka)
    nurse_amkas_by_dept[dept_name] = dept_nurses

print(f"  Nurses: {len(nurse_records)}")

# ─── Management ─────────────────────────────────────────────────────
management_records = []
MGMT_ROLES = ['Γραμματέας', 'Λογιστής', 'Ανθρώπινο Δυναμικό']
all_mgmt_amkas = []
mgmt_amkas_by_dept = {}

for dept_name, *_ in DEPARTMENTS:
    dept_mgmt = []
    # 6 admins per department: 2 of each role
    roles_for_dept = MGMT_ROLES * 2  # 2 of each role
    for role in roles_for_dept:
        amka = unique_amka()
        gender = random.choice(['M','F'])
        first = random.choice(MALE_FIRST if gender == 'M' else FEMALE_FIRST)
        last = random.choice(LAST_NAMES)
        if gender == 'F':
            last = feminize_lastname(last)
        age = random.randint(25, 58)
        email = gen_email(first, last, 'hospital.gr')
        phone = gen_phone()
        hiring = datetime.date(2026,1,1) - datetime.timedelta(days=random.randint(365, 365*10))

        staff_records.append((amka, first, last, age, email, phone, hiring, 'Διοικητικός'))
        other_staff_records.append((amka, first, last, age, email, phone, hiring, 'Διοικητικός'))
        office = f"Γραφείο {random.randint(100,500)}"
        management_records.append((role, office, amka, dept_name))
        all_mgmt_amkas.append(amka)
        dept_mgmt.append(amka)
    mgmt_amkas_by_dept[dept_name] = dept_mgmt

print(f"  Management: {len(management_records)}")

# ─── Insurance ──────────────────────────────────────────────────────
insurance_records = [
    ('ΕΦΚΑ', '2101234567'),
    ('ΕΟΠΥΥ', '2109876543'),
    ('Ιδιωτική Ασφάλεια', '2105551234'),
    ('Ανασφάλιστος', None),
]

# ─── Patients ────────────────────────────────────────────────────────
patient_records = []
NUM_PATIENTS = 200

for i in range(NUM_PATIENTS):
    amka = unique_amka()
    gender = random.choice(['Άρρεν', 'Θήλυ'])
    first = random.choice(MALE_FIRST if gender == 'Άρρεν' else FEMALE_FIRST)
    last = random.choice(LAST_NAMES)
    if gender == 'Θήλυ':
        last = feminize_lastname(last)
    father = random.choice(MALE_FIRST)

    if random.random() < 0.05:
        age = 0
        age_month = random.randint(1, 11)
    else:
        age = random.randint(1, 90)
        age_month = 0

    weight = round(random.uniform(50, 120), 2) if age > 10 else round(random.uniform(3, 40), 2)
    height = round(random.uniform(1.50, 1.95), 2) if age > 10 else round(random.uniform(0.50, 1.40), 2)

    city = random.choice(CITIES)
    street = random.choice(STREETS)
    address = f"{street} {random.randint(1,200)}, {city}"[:45]
    phone = gen_phone()
    email = gen_email(first, last, 'email.gr')
    profession = random.choice(PROFESSIONS) if age > 18 else 'Μαθητής'
    nationality = random.choice(NATIONALITIES)
    emergency = gen_phone()
    insurance = random.choices(
        ['ΕΦΚΑ','ΕΟΠΥΥ','Ιδιωτική Ασφάλεια','Ανασφάλιστος'],
        weights=[50, 25, 15, 10]
    )[0]

    patient_records.append((amka, first, last, father, age, age_month, gender,
                            weight, height, address, phone, email, profession,
                            nationality, emergency, insurance))

print(f"  Patients: {len(patient_records)}")

# ─── Beds ────────────────────────────────────────────────────────────
bed_records = []
for dept_name, desc, num_beds, floor, building in DEPARTMENTS:
    for b in range(1, num_beds+1):
        if dept_name == 'ΜΕΘ':
            bed_type = 'ΜΕΘ'
        elif b <= 5:
            bed_type = 'Μονόκλινο'
        else:
            bed_type = 'Πολύκλινο'
        status = random.choices(['Διαθέσιμη','Κατειλημμένη','Υπό Συντήρηση'],
                                weights=[60,30,10])[0]
        bed_records.append((dept_name, b, bed_type, status))

print(f"  Beds: {len(bed_records)}")

# ─── Triage + Admissions ────────────────────────────────────────────
NUM_ADMISSIONS = 500
triage_records = []
admission_records = []

icd_codes = [d['code'] for d in icd10_data]
ken_codes = [k['code'] for k in ken_data]
ken_dict = {k['code']: k for k in ken_data}

dept_beds = {}
for dept_name, b, bt, st in bed_records:
    dept_beds.setdefault(dept_name, []).append(b)

start_period = datetime.date(2024, 1, 1)
end_period = datetime.date(2026, 4, 30)  # include 2026 for YEAR(CURDATE()) queries

# ── Query-targeted: 3 patients with 4+ admissions in same department ──
# Pick 3 patients and 3 departments for forced repeat admissions
repeat_patients = random.sample(patient_records, 3)
repeat_depts = ['Καρδιολογία', 'Παθολογία', 'Ορθοπεδική']
forced_pairs = [(repeat_patients[i][0], repeat_depts[i]) for i in range(3)]
# Each pair gets admissions 1-4 (first 12 adm_ids are forced)
forced_adm_count = 0

for adm_id in range(1, NUM_ADMISSIONS + 1):
    # First 12 admissions: forced repeats (4 each for 3 patients)
    if forced_adm_count < 12:
        pair_idx = forced_adm_count // 4
        pat_amka = forced_pairs[pair_idx][0]
        dept_name = forced_pairs[pair_idx][1]
        patient = [p for p in patient_records if p[0] == pat_amka][0]
        forced_adm_count += 1
    else:
        patient = random.choice(patient_records)
        pat_amka = patient[0]
        dept_idx = random.randint(0, 14)
        dept_name = DEPARTMENTS[dept_idx][0]

    bed_num = random.choice(dept_beds[dept_name])

    arrival = rand_datetime(start_period, end_period)
    urgency = random.choices([1,2,3,4,5], weights=[5,15,35,30,15])[0]
    symptom = random.choice(SYMPTOMS)
    waiting = random.randint(0, 120) if urgency >= 3 else random.randint(0, 15)
    nurse_amka = random.choice(all_nurse_amkas)

    triage_records.append((adm_id, symptom, urgency, arrival, waiting, pat_amka, nurse_amka))

    adm_date = arrival.date() + datetime.timedelta(days=random.randint(0, 1))
    ken_code = random.choice(ken_codes)
    ken_info = ken_dict[ken_code]
    adm_icd = random.choice(icd_codes)

    if random.random() < 0.80:
        stay_days = random.randint(1, max(1, ken_info['mdn'] * 2))
        release = adm_date + datetime.timedelta(days=stay_days)
        rel_icd = random.choice(icd_codes)

        days_stayed = stay_days
        if days_stayed <= ken_info['mdn']:
            total_cost = ken_info['cost']
        else:
            mdn = ken_info['mdn'] if ken_info['mdn'] > 0 else 1
            daily_extra = ken_info['cost'] / mdn
            total_cost = ken_info['cost'] + (days_stayed - ken_info['mdn']) * daily_extra
        total_cost = round(total_cost, 2)
    else:
        release = None
        rel_icd = None
        total_cost = None

    admission_records.append((adm_id, adm_date, release, total_cost, dept_name,
                              bed_num, pat_amka, adm_id, ken_code, adm_icd, rel_icd))

completed_admissions = [a for a in admission_records if a[2] is not None]

print(f"  Triages: {len(triage_records)}")
print(f"  Admissions: {len(admission_records)} ({len(completed_admissions)} completed)")

# ─── Operating Rooms ────────────────────────────────────────────────
NUM_OPERATING_ROOMS = 10
operating_rooms = [(i+1, ROOM_TYPES[i]) for i in range(NUM_OPERATING_ROOMS)]

# ─── Medical Actions & Surgeries ─────────────────────────────────────
NUM_MEDICAL_ACTIONS = 150
action_types = ['Χειρουργική', 'Διαγνωστική', 'Θεραπευτική']

medical_action_records = []
surgery_records = []
surgery_assistant_records = []

room_schedules = {r: [] for r in range(1, NUM_OPERATING_ROOMS+1)}
surgeon_schedules = {}

action_name_pool = [a['name'][:400] for a in medical_actions_ref]

for ac_code in range(1, NUM_MEDICAL_ACTIONS + 1):
    adm = random.choice(admission_records)
    adm_id = adm[0]
    adm_date = adm[1]

    action_type = random.choices(action_types, weights=[30, 40, 30])[0]
    action_name = random.choice(action_name_pool)
    duration = random.choice([15, 30, 45, 60, 90, 120, 180])
    cost = round(random.uniform(100, 5000), 2)

    room_code = random.randint(1, NUM_OPERATING_ROOMS)

    attempts = 0
    while attempts < 50:
        base_date = adm_date + datetime.timedelta(days=random.randint(0, 5))
        hour = random.randint(7, 18)
        minute = random.choice([0, 15, 30, 45])
        action_start = datetime.datetime(base_date.year, base_date.month, base_date.day, hour, minute)
        action_end = action_start + datetime.timedelta(minutes=duration)

        conflict = False
        for (s, e) in room_schedules[room_code]:
            if not (action_end <= s or action_start >= e):
                conflict = True
                break

        if not conflict:
            break
        attempts += 1
        room_code = random.randint(1, NUM_OPERATING_ROOMS)

    room_schedules[room_code].append((action_start, action_end))

    medical_action_records.append((ac_code, action_name, action_type, action_start,
                                    duration, cost, adm_id, room_code))

    if action_type == 'Χειρουργική':
        dept_name = adm[4]
        dept_doc_list = doctor_amkas_by_dept.get(dept_name, all_doctor_amkas[:5])
        surgeon_amka = random.choice(dept_doc_list)

        if surgeon_amka not in surgeon_schedules:
            surgeon_schedules[surgeon_amka] = []

        s_conflict = False
        for (s, e) in surgeon_schedules[surgeon_amka]:
            if not (action_end <= s or action_start >= e):
                s_conflict = True
                break

        if not s_conflict:
            surgeon_schedules[surgeon_amka].append((action_start, action_end))
            surgery_type = random.choice(SURGERY_TYPES)
            surgery_records.append((surgery_type, ac_code, surgeon_amka))

            num_assistants = random.randint(1, 2)
            possible_assistants = [a for a in dept_doc_list if a != surgeon_amka]
            if not possible_assistants:
                possible_assistants = [a for a in all_doctor_amkas if a != surgeon_amka]
            assistants = random.sample(possible_assistants, min(num_assistants, len(possible_assistants)))
            for asst in assistants:
                surgery_assistant_records.append((ac_code, asst))

print(f"  Medical Actions: {len(medical_action_records)}")
print(f"  Surgeries: {len(surgery_records)}")
print(f"  Surgery Assistants: {len(surgery_assistant_records)}")

# ─── Shifts (fully compliant with assignment requirements) ───────────
# Requirements per shift: 3 doctors, 6 nurses, 2 admins
# Constraints: 8h rest (= max 1 shift/person/day), monthly limits (15/20/25),
#   senior with junior, max 3 consecutive night shifts
NUM_SHIFT_DAYS = 7  # 7 days — all constraints satisfied
shift_records = []
shift_staff_records = []

shift_base = datetime.date(2026, 3, 1)  # March 2026 for YEAR(CURDATE()) queries
shift_types_def = [
    ('Πρωινή', 7, 15),
    ('Απογευματινή', 15, 23),
    ('Νυχτερινή', 23, 7),
]

# Build doctor rank lookup
doctor_rank_map = {dr[3]: dr[2] for dr in doctor_records}
SENIOR_RANKS = {'Διευθυντής', 'Επιμελητής Α'}

# Track monthly shift counts per person
monthly_shift_count = {}
MONTHLY_LIMITS = {}
for s in staff_records:
    amka, stype = s[0], s[7]
    if stype == 'Ιατρός':
        MONTHLY_LIMITS[amka] = 15
    elif stype == 'Νοσηλευτής':
        MONTHLY_LIMITS[amka] = 20
    elif stype == 'Διοικητικός':
        MONTHLY_LIMITS[amka] = 25
    monthly_shift_count[amka] = 0

# Track daily assignments (8h rest = max 1 shift per day)
daily_assigned = {}  # (amka, date_str) -> True

# Track night shift history for consecutive nights check
night_history = {}  # amka -> sorted list of dates they worked nights

def count_consecutive_nights_before(amka, d):
    """Count how many consecutive nights this person worked ending yesterday."""
    hist = night_history.get(amka, [])
    if not hist:
        return 0
    consec = 0
    check_date = d - datetime.timedelta(days=1)
    while check_date in hist:
        consec += 1
        check_date -= datetime.timedelta(days=1)
    return consec

def can_assign(amka, d, shift_type):
    day_key = (amka, str(d))
    if day_key in daily_assigned:
        return False  # already works today (8h rest)
    if monthly_shift_count.get(amka, 0) >= MONTHLY_LIMITS.get(amka, 15):
        return False  # monthly limit
    if shift_type == 'Νυχτερινή' and count_consecutive_nights_before(amka, d) >= 3:
        return False  # max 3 consecutive nights
    return True

def assign_staff(amka, d, shift_type, dept_name):
    monthly_shift_count[amka] = monthly_shift_count.get(amka, 0) + 1
    daily_assigned[(amka, str(d))] = True
    shift_staff_records.append((d, shift_type, dept_name, amka))
    if shift_type == 'Νυχτερινή':
        night_history.setdefault(amka, set()).add(d)

for day_offset in range(NUM_SHIFT_DAYS):
    d = shift_base + datetime.timedelta(days=day_offset)

    for dept_name, *_ in DEPARTMENTS:
        dept_docs = doctor_amkas_by_dept.get(dept_name, [])
        dept_nurses_list = nurse_amkas_by_dept.get(dept_name, [])
        dept_mgmt_list = mgmt_amkas_by_dept.get(dept_name, [])

        # Process night shift FIRST so the most constrained shift type
        # gets first pick of available staff (avoids unstaffed nights).
        # Records are collected per-department then sorted for output.
        processing_order = [
            ('Νυχτερινή', 23, 7),
            ('Πρωινή', 7, 15),
            ('Απογευματινή', 15, 23),
        ]

        for shift_type, start_h, end_h in processing_order:
            start_dt = datetime.datetime(d.year, d.month, d.day, start_h, 0, 0)
            if end_h < start_h:
                end_d = d + datetime.timedelta(days=1)
                end_dt = datetime.datetime(end_d.year, end_d.month, end_d.day, end_h, 0, 0)
            else:
                end_dt = datetime.datetime(d.year, d.month, d.day, end_h, 0, 0)

            shift_records.append((d, shift_type, start_dt, end_dt, dept_name))

            # Select 3 doctors — round-robin, ensure 1 senior, respect all constraints
            available_docs = [a for a in dept_docs if can_assign(a, d, shift_type)]
            available_docs.sort(key=lambda a: monthly_shift_count.get(a, 0))
            selected_docs = []

            seniors = [a for a in available_docs if doctor_rank_map.get(a) in SENIOR_RANKS]
            others = [a for a in available_docs if a not in seniors]

            if seniors:
                selected_docs.append(seniors[0])
            for a in (others + seniors[1:]):
                if len(selected_docs) >= 3:
                    break
                if a not in selected_docs:
                    selected_docs.append(a)

            for a in selected_docs:
                assign_staff(a, d, shift_type, dept_name)

            # Select 6 nurses — round-robin, respect constraints
            available_nurses = [a for a in dept_nurses_list if can_assign(a, d, shift_type)]
            available_nurses.sort(key=lambda a: monthly_shift_count.get(a, 0))
            for a in available_nurses[:6]:
                assign_staff(a, d, shift_type, dept_name)

            # Select 2 admins — round-robin, respect constraints
            available_mgmt = [a for a in dept_mgmt_list if can_assign(a, d, shift_type)]
            available_mgmt.sort(key=lambda a: monthly_shift_count.get(a, 0))
            for a in available_mgmt[:2]:
                assign_staff(a, d, shift_type, dept_name)

print(f"  Shifts: {len(shift_records)}")
print(f"  Shift Staff (raw): {len(shift_staff_records)}")

doc_per_shift = len(shift_staff_records) / len(shift_records) if shift_records else 0
print(f"  Avg staff/shift: {doc_per_shift:.1f}")
over_limit = sum(1 for a, c in monthly_shift_count.items() if c > MONTHLY_LIMITS.get(a, 99))
print(f"  Over monthly limit: {over_limit}")

# ─── Exams ───────────────────────────────────────────────────────────
NUM_EXAMS = 200
exam_records = []

for ex_code in range(1, NUM_EXAMS + 1):
    adm = random.choice(admission_records)
    adm_id = adm[0]
    adm_date = adm[1]

    exam_type, unit = random.choice(EXAM_TYPES)
    exam_date = adm_date + datetime.timedelta(days=random.randint(0, 5))
    result = random.choice(EXAM_RESULTS[exam_type])
    cost = round(random.uniform(20, 500), 2)
    doctor_amka = random.choice(all_doctor_amkas)

    exam_records.append((ex_code, exam_type, exam_date, result, unit, cost, adm_id, doctor_amka))

print(f"  Exams: {len(exam_records)}")

# ─── Patient Allergies ──────────────────────────────────────────────
patient_allergy_records = []
patient_allergies = {}

substance_ids = list(sub_name_to_id.values())

for pat in patient_records:
    if random.random() < 0.30:
        num_allergies = random.randint(1, 3)
        allergy_subs = random.sample(substance_ids, min(num_allergies, len(substance_ids)))
        patient_allergies[pat[0]] = set(allergy_subs)
        for sid in allergy_subs:
            patient_allergy_records.append((pat[0], sid))

print(f"  Patient Allergies: {len(patient_allergy_records)}")

# ─── Prescriptions ──────────────────────────────────────────────────
NUM_PRESCRIPTIONS = 300
prescription_records = []
prescription_combos = set()

med_ema_to_subs = {}
for comp in ema_compositions:
    ema = med_name_to_ema.get(clean_name(comp['medicine_name'], 200))
    sub = sub_name_to_id.get(clean_name(comp['substance_name'], 200))
    if ema and sub:
        med_ema_to_subs.setdefault(ema, set()).add(sub)

all_ema_codes = list(med_name_to_ema.values())

doctor_patient_pairs = {}

prx_id = 0
attempts = 0
while prx_id < NUM_PRESCRIPTIONS and attempts < NUM_PRESCRIPTIONS * 10:
    attempts += 1

    pat = random.choice(patient_records)
    pat_amka = pat[0]
    doc_amka = random.choice(all_doctor_amkas)
    ema_code = random.choice(all_ema_codes)

    start = rand_date(datetime.date(2024,1,1), datetime.date(2026,4,1))
    end = start + datetime.timedelta(days=random.randint(5, 90))

    combo = (doc_amka, pat_amka, ema_code, str(start))
    if combo in prescription_combos:
        continue

    pat_allergy_set = patient_allergies.get(pat_amka, set())
    med_subs = med_ema_to_subs.get(ema_code, set())
    if pat_allergy_set & med_subs:
        continue

    prx_id += 1
    prescription_combos.add(combo)

    dosage = random.choice([1, 2, 3, 5, 10, 20, 50, 100, 250, 500])
    frequency = random.choice([1, 2, 3, 4, 6, 8, 12])

    prescription_records.append((prx_id, start, end, dosage, frequency, pat_amka, doc_amka, ema_code))

    doctor_patient_pairs.setdefault(pat_amka, set()).add(doc_amka)

print(f"  Prescriptions: {len(prescription_records)}")

# ─── Evaluations + Doctor Evaluations ───────────────────────────────
evaluation_records = []
doctor_eval_records = []

eval_candidates = list(completed_admissions)
random.shuffle(eval_candidates)
eval_candidates = eval_candidates[:min(200, len(eval_candidates))]

for adm in eval_candidates:
    adm_id = adm[0]
    pat_amka = adm[6]

    nq = random.randint(1, 5)
    cl = random.randint(1, 5)
    fd = random.randint(1, 5)
    oe = random.randint(1, 5)

    evaluation_records.append((nq, cl, fd, oe, adm_id))

    prescribing_docs = doctor_patient_pairs.get(pat_amka, set())
    if prescribing_docs:
        docs_to_eval = random.sample(list(prescribing_docs), min(random.randint(1,2), len(prescribing_docs)))
        for doc_amka in docs_to_eval:
            dq = random.randint(1, 5)
            doctor_eval_records.append((adm_id, doc_amka, dq))

print(f"  Evaluations: {len(evaluation_records)}")
print(f"  Doctor Evaluations: {len(doctor_eval_records)}")

# ═══════════════════════════════════════════════════════════════════
# ═══ WRITE load.sql ════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════
print("\nWriting load.sql...")

outpath = 'load.sql'
with open(outpath, 'w', encoding='utf-8') as f:
    f.write("-- load.sql — Νοσοκομείο Υγειόπολης\n")
    f.write("-- Auto-generated: full reference data + synthetic data for 15 departments\n")
    f.write("-- Compatible with sql/install.sql\n")
    f.write("-- Insertion order: phased by FK dependencies\n\n")
    f.write("USE `mydb`;\n\n")
    f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
    f.write("SET NAMES utf8mb4;\n\n")

    # ╔═══════════════════════════════════════════════════════════════╗
    # ║  ΦΑΣΗ 0: Ανεξάρτητοι πίνακες (κανένα FK)                    ║
    # ╚═══════════════════════════════════════════════════════════════╝
    f.write("-- ╔═══════════════════════════════════════════════════════════╗\n")
    f.write("-- ║  ΦΑΣΗ 0: Ανεξάρτητοι πίνακες (κανένα FK)                ║\n")
    f.write("-- ╚═══════════════════════════════════════════════════════════╝\n\n")

    # 0.1 Insurance
    f.write("-- Insurance — 4 εγγραφές\n\n")
    for prov, phone in insurance_records:
        ph = sql_str(phone) if phone else 'NULL'
        f.write(f"INSERT INTO `Insurance` (Provider, Provider_Phone) VALUES ({sql_str(prov)}, {ph});\n")
    f.write('\n')

    # 0.2 Operating_Room
    f.write(f"-- Operating_Room — {len(operating_rooms)} εγγραφές\n\n")
    for code, rtype in operating_rooms:
        f.write(f"INSERT INTO `Operating_Room` (Room_Code, Room_Type) VALUES ({sql_int(code)}, {sql_str(rtype)});\n")
    f.write('\n')

    # 0.3 KEN
    f.write(f"-- KEN (Κλειστά Ενοποιημένα Νοσήλια) — {len(ken_data)} εγγραφές\n\n")
    rows = []
    for k in ken_data:
        rows.append((sql_str(k['code'], 10), sql_dec(k['cost']), sql_int(k['mdn'])))
    batch_insert(f, 'KEN', ['KEN_Code','KEN_Cost','MDN'], rows)

    # 0.4 Diagnosis (ICD-10)
    f.write(f"-- Diagnosis (ICD-10) — {len(icd10_data)} εγγραφές\n\n")
    rows = []
    for d in icd10_data:
        rows.append((sql_str(d['code'], 10), sql_str(d['description'], 200)))
    batch_insert(f, 'Diagnosis', ['ICD_10_Code','Description'], rows)

    # 0.5 Medicine (EMA Article 57)
    f.write(f"-- Medicine (EMA Article 57) — {len(ema_medicines)} εγγραφές\n\n")
    rows = []
    for med in ema_medicines:
        cleaned = med_raw_to_clean[med['name']]
        ema_code = med_name_to_ema[cleaned]
        rows.append((sql_str(ema_code, 45), sql_str(cleaned, 200)))
    batch_insert(f, 'Medicine', ['EMA_Code','Medicine_Name'], rows, batch_size=1000)

    # 0.6 Active_Substance
    f.write(f"-- Active_Substance — {len(ema_substances)} εγγραφές\n\n")
    rows = []
    for sub_name in ema_substances:
        cleaned = sub_raw_to_clean[sub_name]
        sid = sub_name_to_id[cleaned]
        rows.append((sql_str(sid, 45), sql_str(cleaned, 200)))
    batch_insert(f, 'Active_Substance', ['Substance_ID','Substance_Name'], rows)

    # 0.7 Medicine_Composition
    f.write(f"-- Medicine_Composition — συνθέσεις φαρμάκων\n\n")
    rows = []
    seen_comps = set()
    for comp in ema_compositions:
        ema = med_name_to_ema.get(clean_name(comp['medicine_name'], 200))
        sub = sub_name_to_id.get(clean_name(comp['substance_name'], 200))
        if ema and sub:
            key = (ema, sub)
            if key not in seen_comps:
                seen_comps.add(key)
                rows.append((sql_str(ema, 45), sql_str(sub, 45)))
    batch_insert(f, 'Medicine_Composition', ['EMA_Code','Substance_ID'], rows, batch_size=1000)

    # ╔═══════════════════════════════════════════════════════════════╗
    # ║  ΦΑΣΗ 1: Προσωπικό (Μέρος Α') — Ιατροί & Τμήματα           ║
    # ╚═══════════════════════════════════════════════════════════════╝
    f.write("-- ╔═══════════════════════════════════════════════════════════╗\n")
    f.write("-- ║  ΦΑΣΗ 1: Προσωπικό (Μέρος Α') — Ιατροί & Τμήματα       ║\n")
    f.write("-- ╚═══════════════════════════════════════════════════════════╝\n\n")

    # 1.1 STAFF — μόνο ιατροί
    f.write(f"-- STAFF (Ιατροί) — {len(doctor_staff_records)} εγγραφές\n\n")
    rows = []
    for s in doctor_staff_records:
        rows.append((sql_str(s[0]), sql_str(s[1]), sql_str(s[2]), sql_int(s[3]),
                      sql_str(s[4],45), sql_str(s[5]), sql_date(s[6]), sql_str(s[7])))
    batch_insert(f, 'STAFF',
                 ['Staff_AMKA','First_Name','Last_Name','Age','Email','Phone_Number','Hiring_Date','Staff_Type'],
                 rows)

    # 1.2 Doctor (individual inserts — trigger order matters)
    f.write(f"-- Doctor — {len(doctor_records)} εγγραφές (sorted by rank for circular_supervision trigger)\n\n")
    rank_order = {'Διευθυντής': 0, 'Επιμελητής Α': 1, 'Επιμελητής Β': 2, 'Ειδικευόμενος': 3}
    sorted_doctors = sorted(doctor_records, key=lambda d: rank_order.get(d[2], 99))
    for dr in sorted_doctors:
        lic, spec, rank, amka, sup = dr
        sup_val = sql_str(sup) if sup else 'NULL'
        f.write(f"INSERT INTO `Doctor` (License_Number, Specialty, `Rank`, Staff_AMKA, Supervisor_AMKA) "
                f"VALUES ({sql_str(lic)}, {sql_str(spec)}, {sql_str(rank)}, {sql_str(amka)}, {sup_val});\n")
    f.write('\n')

    # 1.3 Department (needs DirectedBy → Doctor)
    f.write(f"-- Department — {len(DEPARTMENTS)} εγγραφές\n\n")
    for dept_name, desc, beds, floor, building in DEPARTMENTS:
        director = dept_directors[dept_name]
        f.write(f"INSERT INTO `Department` (Department_Name, Description, Num_of_Beds, Floor, Building, DirectedBy) "
                f"VALUES ({sql_str(dept_name)}, {sql_str(desc,45)}, {sql_int(beds)}, {sql_int(floor)}, "
                f"{sql_str(building)}, {sql_str(director)});\n")
    f.write('\n')

    # ╔═══════════════════════════════════════════════════════════════╗
    # ║  ΦΑΣΗ 2: Προσωπικό (Μέρος Β') & Υποδομές                    ║
    # ╚═══════════════════════════════════════════════════════════════╝
    f.write("-- ╔═══════════════════════════════════════════════════════════╗\n")
    f.write("-- ║  ΦΑΣΗ 2: Προσωπικό (Μέρος Β') & Υποδομές                ║\n")
    f.write("-- ╚═══════════════════════════════════════════════════════════╝\n\n")

    # 2.1 Bed (needs Department)
    f.write(f"-- Bed — {len(bed_records)} εγγραφές\n\n")
    rows = []
    for dept, bnum, btype, status in bed_records:
        rows.append((sql_str(dept), sql_int(bnum), sql_str(btype), sql_str(status)))
    batch_insert(f, 'Bed', ['Department_Name','Bed_Number','Bed_Type','Status'], rows)

    # 2.2 STAFF — νοσηλευτές & διοικητικοί
    f.write(f"-- STAFF (Νοσηλευτές & Διοικητικοί) — {len(other_staff_records)} εγγραφές\n\n")
    rows = []
    for s in other_staff_records:
        rows.append((sql_str(s[0]), sql_str(s[1]), sql_str(s[2]), sql_int(s[3]),
                      sql_str(s[4],45), sql_str(s[5]), sql_date(s[6]), sql_str(s[7])))
    batch_insert(f, 'STAFF',
                 ['Staff_AMKA','First_Name','Last_Name','Age','Email','Phone_Number','Hiring_Date','Staff_Type'],
                 rows)

    # 2.3 Nurse (needs STAFF + Department)
    f.write(f"-- Nurse — {len(nurse_records)} εγγραφές\n\n")
    rows = []
    for rank, amka, dept in nurse_records:
        rows.append((sql_str(rank), sql_str(amka), sql_str(dept)))
    batch_insert(f, 'Nurse', ['Nurse_Rank','Staff_AMKA','NurseBelongsDepartment'], rows)

    # 2.4 Management (needs STAFF + Department)
    f.write(f"-- Management — {len(management_records)} εγγραφές\n\n")
    rows = []
    for role, office, amka, dept in management_records:
        rows.append((sql_str(role), sql_str(office), sql_str(amka), sql_str(dept)))
    batch_insert(f, 'Management', ['`Role`','Office','Staff_AMKA','ManagerBelongsDepartment'], rows)

    # 2.5 Belongs_Doctor (needs Doctor + Department)
    f.write(f"-- Belongs_Doctor — {sum(len(v) for v in doctor_amkas_by_dept.values())} εγγραφές\n\n")
    rows = []
    for dept_name in doctor_amkas_by_dept:
        for doc_amka in doctor_amkas_by_dept[dept_name]:
            rows.append((sql_str(doc_amka), sql_str(dept_name)))
    batch_insert(f, 'Belongs_Doctor', ['Doctor_AMKA','Department_Name'], rows)

    # ╔═══════════════════════════════════════════════════════════════╗
    # ║  ΦΑΣΗ 3: Ασθενείς & Άφιξη                                   ║
    # ╚═══════════════════════════════════════════════════════════════╝
    f.write("-- ╔═══════════════════════════════════════════════════════════╗\n")
    f.write("-- ║  ΦΑΣΗ 3: Ασθενείς & Άφιξη                               ║\n")
    f.write("-- ╚═══════════════════════════════════════════════════════════╝\n\n")

    # 3.1 Patient (needs Insurance)
    f.write(f"-- Patient — {len(patient_records)} εγγραφές\n\n")
    rows = []
    for p in patient_records:
        rows.append((
            sql_str(p[0]), sql_str(p[1]), sql_str(p[2]), sql_str(p[3]),
            sql_int(p[4]), sql_int(p[5]), sql_str(p[6]),
            sql_dec(p[7]), sql_dec(p[8]),
            sql_str(p[9],45), sql_str(p[10]), sql_str(p[11],45),
            sql_str(p[12]), sql_str(p[13]), sql_str(p[14]), sql_str(p[15])
        ))
    batch_insert(f, 'Patient',
                 ['Patient_AMKA','Patient_First_Name','Patient_Last_Name','Patient_Father_Name',
                  'Patient_Age','Age_Month','Patient_Gender','Patient_Weight','Patient_Height',
                  'Patient_Address','Patient_Phone_Number','Patient_Email','Patient_Profession',
                  'Patient_Nationality','Emergency_Contact','Insurance_Provider'], rows)

    # 3.2 Patient_Allergy (needs Patient + Active_Substance)
    f.write(f"-- Patient_Allergy — {len(patient_allergy_records)} εγγραφές\n\n")
    rows = []
    for pat, sid in patient_allergy_records:
        rows.append((sql_str(pat), sql_str(sid)))
    batch_insert(f, 'Patient_Allergy', ['Patient_AMKA','Substance_ID'], rows)

    # 3.3 Triage (needs Patient + Nurse)
    f.write(f"-- Triage — {len(triage_records)} εγγραφές\n\n")
    rows = []
    for t in triage_records:
        rows.append((sql_int(t[0]), sql_str(t[1],45), sql_int(t[2]),
                      sql_datetime(t[3]), sql_int(t[4]), sql_str(t[5]), sql_str(t[6])))
    batch_insert(f, 'Triage',
                 ['Triage_ID','Symptoms','Urgency_Level','Arrival_DateTime','Waiting_Minutes',
                  'Patient_AMKA','Nurse_AMKA'], rows)

    # ╔═══════════════════════════════════════════════════════════════╗
    # ║  ΦΑΣΗ 4: Κύρια Λειτουργία Νοσοκομείου                       ║
    # ╚═══════════════════════════════════════════════════════════════╝
    f.write("-- ╔═══════════════════════════════════════════════════════════╗\n")
    f.write("-- ║  ΦΑΣΗ 4: Κύρια Λειτουργία Νοσοκομείου                   ║\n")
    f.write("-- ╚═══════════════════════════════════════════════════════════╝\n\n")

    # 4.1 Admission (needs Bed, Patient, Triage, KEN, Diagnosis)
    f.write(f"-- Admission — {len(admission_records)} εγγραφές (individual INSERTs, pre-calculated Total_Cost)\n\n")
    for a in admission_records:
        adm_id, adm_date, release, cost, dept, bed, pat, tri, ken, adm_icd, rel_icd = a
        rel_str = sql_date(release) if release else 'NULL'
        cost_str = sql_dec(cost) if cost is not None else 'NULL'
        rel_icd_str = sql_str(rel_icd) if rel_icd else 'NULL'
        f.write(f"INSERT INTO `Admission` (AdmissionID, Admission_Date, Release_Date, Total_Cost, "
                f"Department_Name, Bed_Number, Patient_AMKA, Triage_ID, KEN_Code, "
                f"Admission_Diagnosis_ICD_10_Code, Release_Diagnosis_ICD_10_Code) VALUES "
                f"({sql_int(adm_id)}, {sql_date(adm_date)}, {rel_str}, {cost_str}, "
                f"{sql_str(dept)}, {sql_int(bed)}, {sql_str(pat)}, {sql_int(tri)}, "
                f"{sql_str(ken)}, {sql_str(adm_icd)}, {rel_icd_str});\n")
    f.write('\n')

    # 4.2 Shift (needs Department)
    # Sort by date, department, then canonical shift order (Πρωινή, Απογευματινή, Νυχτερινή)
    shift_order = {'Πρωινή': 0, 'Απογευματινή': 1, 'Νυχτερινή': 2}
    shift_records.sort(key=lambda r: (r[0], r[4], shift_order.get(r[1], 9)))
    f.write(f"-- Shift — {len(shift_records)} εγγραφές\n\n")
    rows = []
    for d, stype, start, end, dept in shift_records:
        rows.append((sql_date(d), sql_str(stype), sql_datetime(start), sql_datetime(end), sql_str(dept)))
    batch_insert(f, 'Shift', ['Shift_Date','Shift_Type','Start_Time','End_Time','Department_Name'], rows)

    # 4.3 Shift_Staff (needs Shift + STAFF)
    f.write(f"-- Shift_Staff — τοποθετήσεις βάρδιας\n\n")
    ss_set = set()
    ss_unique = []
    for d, stype, dept, amka in shift_staff_records:
        key = (str(d), stype, dept, amka)
        if key not in ss_set:
            ss_set.add(key)
            ss_unique.append((d, stype, dept, amka))
    rows = []
    for d, stype, dept, amka in ss_unique:
        rows.append((sql_date(d), sql_str(stype), sql_str(dept), sql_str(amka)))
    batch_insert(f, 'Shift_Staff', ['Shift_Date','Shift_Type','Department_Name','Staff_AMKA'], rows, batch_size=1000)

    # 4.4 Medical_Action (needs Admission + Operating_Room)
    f.write(f"-- Medical_Action — {len(medical_action_records)} εγγραφές (individual INSERTs)\n\n")
    for ma in medical_action_records:
        ac_code, name, atype, start, dur, cost, adm_id, room = ma
        f.write(f"INSERT INTO `Medical_Action` (Action_Code, Action_Name, Action_Type, Action_Start, "
                f"Action_Duration, Action_Cost, AdmissionID, Operating_Room_Code) VALUES "
                f"({sql_int(ac_code)}, {sql_str(name, 400)}, {sql_str(atype)}, {sql_datetime(start)}, "
                f"{sql_int(dur)}, {sql_dec(cost)}, {sql_int(adm_id)}, {sql_int(room)});\n")
    f.write('\n')

    # 4.5 Surgery (needs Medical_Action + Doctor — trigger: surgery_constraints)
    f.write(f"-- Surgery — {len(surgery_records)} εγγραφές (individual INSERTs for surgery_constraints trigger)\n\n")
    for stype, ac_code, surgeon in surgery_records:
        f.write(f"INSERT INTO `Surgery` (Surgery_Type, Action_Code, Main_Surgeon_AMKA) VALUES "
                f"({sql_str(stype)}, {sql_int(ac_code)}, {sql_str(surgeon)});\n")
    f.write('\n')

    # 4.6 Surgery_Assistant (needs Surgery + Doctor)
    f.write(f"-- Surgery_Assistant — {len(surgery_assistant_records)} εγγραφές\n\n")
    rows = []
    for ac_code, asst in surgery_assistant_records:
        rows.append((sql_int(ac_code), sql_str(asst)))
    batch_insert(f, 'Surgery_Assistant', ['Surgery_Action_Code','Assistant_AMKA'], rows)

    # 4.7 Exam (needs Admission + Doctor)
    f.write(f"-- Exam — {len(exam_records)} εγγραφές\n\n")
    rows = []
    for ex in exam_records:
        code, etype, edate, result, unit, cost, adm_id, doc = ex
        unit_str = sql_str(unit) if unit else 'NULL'
        rows.append((sql_int(code), sql_str(etype), sql_date(edate), sql_str(result,45),
                      unit_str, sql_dec(cost), sql_int(adm_id), sql_str(doc)))
    batch_insert(f, 'Exam',
                 ['Exam_Code','Exam_Type','Exam_Date','Exam_Result','Measurement_Unit',
                  'Exam_Cost','AdmissionID','Doctor_AMKA'], rows)

    # 4.8 Prescription (needs Patient + Doctor + Medicine — trigger: prescription_allergy_check)
    f.write(f"-- Prescription — {len(prescription_records)} εγγραφές\n\n")
    rows = []
    for prx in prescription_records:
        pid, start, end, dosage, freq, pat, doc, ema = prx
        rows.append((sql_int(pid), sql_date(start), sql_date(end), sql_int(dosage),
                      sql_int(freq), sql_str(pat), sql_str(doc), sql_str(ema)))
    batch_insert(f, 'Prescription',
                 ['Prescription_ID','Start_Date','End_Date','Dosage','Frequency',
                  'Patient_AMKA','Doctor_AMKA','EMA_Code'], rows)

    # ── RE-ENABLE FK CHECKS ─────────────────────────────────────────
    f.write("SET FOREIGN_KEY_CHECKS = 1;\n\n")

    # ╔═══════════════════════════════════════════════════════════════╗
    # ║  ΦΑΣΗ 5: Αξιολογήσεις (απαιτεί FK_CHECKS = 1 για triggers)  ║
    # ╚═══════════════════════════════════════════════════════════════╝
    f.write("-- ╔═══════════════════════════════════════════════════════════╗\n")
    f.write("-- ║  ΦΑΣΗ 5: Αξιολογήσεις (FK_CHECKS = 1, triggers active)  ║\n")
    f.write("-- ╚═══════════════════════════════════════════════════════════╝\n\n")

    # 5.1 Evaluation (needs completed Admission — trigger: evaluation_completed_admission)
    f.write(f"-- Evaluation — {len(evaluation_records)} εγγραφές (μόνο ολοκληρωμένες νοσηλείες)\n\n")
    for ev in evaluation_records:
        f.write(f"INSERT INTO `Evaluation` (Nursing_Quality, Cleanliness, Food, Overall_Experience, AdmissionID) "
                f"VALUES ({sql_int(ev[0])}, {sql_int(ev[1])}, {sql_int(ev[2])}, {sql_int(ev[3])}, {sql_int(ev[4])});\n")
    f.write('\n')

    # 5.2 Doctor_Evaluation (trigger: chk_doctor_eval_prescribed)
    f.write(f"-- Doctor_Evaluation — {len(doctor_eval_records)} εγγραφές\n\n")
    for de in doctor_eval_records:
        f.write(f"INSERT INTO `Doctor_Evaluation` (AdmissionID, Doctor_AMKA, Doctor_Quality) "
                f"VALUES ({sql_int(de[0])}, {sql_str(de[1])}, {sql_int(de[2])});\n")
    f.write('\n')

    # ╔═══════════════════════════════════════════════════════════════╗
    # ║  Entity_Image — ενδεικτικές εικόνες ανά οντότητα              ║
    # ╚═══════════════════════════════════════════════════════════════╝
    f.write("-- ╔═══════════════════════════════════════════════════════════╗\n")
    f.write("-- ║  Entity_Image — ενδεικτικές εικόνες ανά οντότητα         ║\n")
    f.write("-- ╚═══════════════════════════════════════════════════════════╝\n\n")

    # Generate Entity_Image records
    entity_image_rows = []
    # Department images
    dept_images = {
        'Καρδιολογία': 'Εξωτερική άποψη του καρδιολογικού τμήματος',
        'Χειρουργική': 'Χειρουργική αίθουσα γενικής χειρουργικής',
        'ΜΕΘ': 'Μονάδα εντατικής θεραπείας με εξοπλισμό παρακολούθησης',
        'Επείγοντα': 'Τμήμα επειγόντων περιστατικών - είσοδος',
        'Νευρολογία': 'Νευρολογικό εργαστήριο με εξοπλισμό ΗΕΓ',
        'Παθολογία': 'Παθολογική κλινική - κοινόχρηστος χώρος',
        'Ορθοπεδική': 'Ορθοπεδικό τμήμα με εξοπλισμό αποκατάστασης',
        'Ουρολογία': 'Ουρολογική κλινική - χώρος εξέτασης',
        'Οφθαλμολογία': 'Οφθαλμολογικό εργαστήριο με εξοπλισμό laser',
        'ΩΡΛ': 'Ωτορινολαρυγγολογικό ιατρείο',
        'Πνευμονολογία': 'Πνευμονολογική κλινική με σπιρόμετρο',
        'Γαστρεντερολογία': 'Ενδοσκοπικό εργαστήριο γαστρεντερολογίας',
        'Νεφρολογία': 'Μονάδα τεχνητού νεφρού',
        'Αιματολογία': 'Αιματολογικό εργαστήριο',
        'Ογκολογία': 'Ογκολογική κλινική - χώρος χημειοθεραπείας',
    }
    for dept_name, desc_img in dept_images.items():
        entity_image_rows.append(('Department', dept_name,
            f'images/departments/{dept_name.lower().replace(" ","_")}.jpg', desc_img))

    # Doctor images (first 15 - one per department director)
    for dept_name in dept_directors:
        doc_amka = dept_directors[dept_name]
        doc_info = [dr for dr in doctor_records if dr[3] == doc_amka][0]
        staff_info = [s for s in doctor_staff_records if s[0] == doc_amka][0]
        entity_image_rows.append(('Doctor', doc_amka,
            f'images/doctors/doctor_{doc_amka}.jpg',
            f'Φωτογραφία Διευθυντή {staff_info[1]} {staff_info[2]}'))

    # Operating Room images
    for code, rtype in operating_rooms:
        entity_image_rows.append(('Operating_Room', str(code),
            f'images/operating_rooms/or_{code}.jpg',
            f'Χειρουργική αίθουσα {code} - {rtype}'))

    # Patient images (sample of 10)
    for pat in patient_records[:10]:
        entity_image_rows.append(('Patient', pat[0],
            f'images/patients/patient_{pat[0]}.jpg',
            f'Φωτογραφία ασθενούς {pat[1]} {pat[2]}'))

    # Medicine images (sample of 5)
    sample_meds = list(med_name_to_ema.items())[:5]
    for mname, ema_code in sample_meds:
        clean_name = mname[:60].replace("'","")
        entity_image_rows.append(('Medicine', ema_code,
            f'images/medicines/med_{ema_code}.jpg',
            f'Συσκευασία φαρμάκου {clean_name}'))

    for etype, ekey, url, desc_img in entity_image_rows:
        f.write(f"INSERT INTO `Entity_Image` (Entity_Type, Entity_Key, Image_URL, Description) "
                f"VALUES ({sql_str(etype)}, {sql_str(ekey, 100)}, {sql_str(url)}, {sql_str(desc_img)});\n")
    f.write('\n')

    f.write(f"\n-- End of load.sql — {len(entity_image_rows)} Entity_Image records\n")

file_size = os.path.getsize(outpath)
print(f"\nDone! load.sql: {file_size/1024/1024:.1f} MB")
print(f"Entity_Image records: {len(entity_image_rows)}")
