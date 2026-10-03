from flask import Flask, render_template, request, redirect, session
import sqlite3
from collections import deque
import heapq


app = Flask(__name__)

app.secret_key = "hospital_management_secret_key"


# =====================================================
# NORMAL PATIENT QUEUE
# =====================================================

patient_queue = deque()


# =====================================================
# EMERGENCY PRIORITY QUEUE
# =====================================================

emergency_queue = []


# =====================================================
# RECENTLY TREATED PATIENTS STACK
# =====================================================

treated_stack = []


# =====================================================
# UNDO OPERATION STACK
# =====================================================

undo_stack = []


# =====================================================
# PATIENT BINARY SEARCH TREE
# =====================================================

class BSTNode:

    def __init__(self, patient):

        self.patient = patient

        self.left = None

        self.right = None


class PatientBST:

    def __init__(self):

        self.root = None


    def insert(self, patient):

        if self.root is None:

            self.root = BSTNode(patient)

        else:

            self._insert(
                self.root,
                patient
            )


    def _insert(self, node, patient):

        if patient[0] < node.patient[0]:

            if node.left is None:

                node.left = BSTNode(patient)

            else:

                self._insert(
                    node.left,
                    patient
                )


        elif patient[0] > node.patient[0]:

            if node.right is None:

                node.right = BSTNode(patient)

            else:

                self._insert(
                    node.right,
                    patient
                )


    def search(self, patient_id):

        return self._search(
            self.root,
            patient_id
        )


    def _search(self, node, patient_id):

        if node is None:

            return None


        if patient_id == node.patient[0]:

            return node.patient


        if patient_id < node.patient[0]:

            return self._search(
                node.left,
                patient_id
            )


        return self._search(
            node.right,
            patient_id
        )


    def inorder(self):

        result = []

        self._inorder(
            self.root,
            result
        )

        return result


    def _inorder(self, node, result):

        if node is not None:

            self._inorder(
                node.left,
                result
            )

            result.append(
                node.patient
            )

            self._inorder(
                node.right,
                result
            )


# =====================================================
# HOSPITAL GRAPH
# =====================================================

hospital_graph = {

    "Emergency": [
        "Reception",
        "ICU"
    ],

    "Reception": [
        "Emergency",
        "Pharmacy"
    ],

    "ICU": [
        "Emergency",
        "Operation Theatre"
    ],

    "Operation Theatre": [
        "ICU",
        "Pharmacy"
    ],

    "Pharmacy": [
        "Reception",
        "Operation Theatre"
    ]

}


# =====================================================
# GRAPH BFS ROUTE
# =====================================================

def find_route(start, destination):

    queue = deque()

    queue.append(
        [start]
    )

    visited = set()

    visited.add(start)


    while queue:

        path = queue.popleft()

        current = path[-1]


        if current == destination:

            return path


        for neighbour in hospital_graph.get(
            current,
            []
        ):

            if neighbour not in visited:

                visited.add(
                    neighbour
                )

                new_path = list(path)

                new_path.append(
                    neighbour
                )

                queue.append(
                    new_path
                )


    return None


# =====================================================
# DATABASE
# =====================================================

def init_db():

    conn = sqlite3.connect(
        "hospital.db"
    )

    cursor = conn.cursor()


    # Patient table

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (

            patient_id INTEGER PRIMARY KEY,

            name TEXT NOT NULL,

            age INTEGER NOT NULL,

            gender TEXT NOT NULL,

            disease TEXT NOT NULL,

            phone TEXT NOT NULL

        )
    """)


    # Medical history table

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_history (

            history_id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER NOT NULL,

            date TEXT NOT NULL,

            doctor TEXT NOT NULL,

            diagnosis TEXT NOT NULL,

            treatment TEXT NOT NULL

        )
    """)


    conn.commit()

    conn.close()


# =====================================================
# LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    error = ""


    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]


        # Simple project login

        if username == "admin" and password == "1234":

            session["logged_in"] = True

            return redirect("/")


        else:

            error = (
                "Invalid username or password."
            )


    return render_template(
        "login.html",
        error=error
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():

    if not session.get("logged_in"):

        return redirect("/login")


    return render_template(
        "index.html"
    )


# =====================================================
# REGISTER PATIENT
# =====================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if not session.get("logged_in"):

        return redirect("/login")


    error = ""


    if request.method == "POST":

        patient_id = request.form[
            "patient_id"
        ]

        name = request.form[
            "name"
        ]

        age = request.form[
            "age"
        ]

        gender = request.form[
            "gender"
        ]

        disease = request.form[
            "disease"
        ]

        phone = request.form[
            "phone"
        ]


        conn = sqlite3.connect(
            "hospital.db"
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT * FROM patients
            WHERE patient_id = ?
            """,

            (patient_id,)
        )


        existing_patient = (
            cursor.fetchone()
        )


        if existing_patient:

            conn.close()

            error = (
                "Patient ID already exists. "
                "Please use another ID."
            )

            return render_template(
                "register.html",
                error=error
            )


        cursor.execute(
            """
            INSERT INTO patients
            (
                patient_id,
                name,
                age,
                gender,
                disease,
                phone
            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,

            (
                patient_id,
                name,
                age,
                gender,
                disease,
                phone
            )
        )


        conn.commit()

        conn.close()


        return redirect("/")


    return render_template(
        "register.html",
        error=error
    )


# =====================================================
# DISPLAY ALL RECORDS
# =====================================================

@app.route("/records")
def records():

    if not session.get("logged_in"):

        return redirect("/login")


    conn = sqlite3.connect(
        "hospital.db"
    )

    cursor = conn.cursor()


    cursor.execute(
        "SELECT * FROM patients"
    )

    patients = cursor.fetchall()


    conn.close()


    return render_template(
        "records.html",
        patients=patients
    )


# =====================================================
# SEARCH PATIENT
# =====================================================

@app.route(
    "/search",
    methods=["GET", "POST"]
)
def search():

    if not session.get("logged_in"):

        return redirect("/login")


    patient = None

    error = ""


    if request.method == "POST":

        patient_id = request.form[
            "patient_id"
        ]


        conn = sqlite3.connect(
            "hospital.db"
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT * FROM patients
            WHERE patient_id = ?
            """,

            (patient_id,)
        )


        patient = cursor.fetchone()


        conn.close()


        if patient is None:

            error = (
                "Patient not found. "
                "Please check the Patient ID."
            )


    return render_template(
        "search.html",
        patient=patient,
        error=error
    )


# =====================================================
# SORT PATIENT RECORDS
# =====================================================

@app.route(
    "/sort",
    methods=["GET", "POST"]
)
def sort_patients():

    if not session.get("logged_in"):

        return redirect("/login")


    patients = []


    if request.method == "POST":

        sort_by = request.form[
            "sort_by"
        ]

        order = request.form[
            "order"
        ]


        column_map = {

            "patient_id":
                "patient_id",

            "name":
                "name",

            "age":
                "age"

        }


        column = column_map.get(
            sort_by,
            "patient_id"
        )


        if order == "descending":

            sort_order = "DESC"

        else:

            sort_order = "ASC"


        conn = sqlite3.connect(
            "hospital.db"
        )

        cursor = conn.cursor()


        query = f"""
            SELECT * FROM patients
            ORDER BY {column} {sort_order}
        """


        cursor.execute(query)

        patients = cursor.fetchall()


        conn.close()


    return render_template(
        "sort.html",
        patients=patients
    )


# =====================================================
# NORMAL PATIENT QUEUE
# =====================================================

@app.route(
    "/queue",
    methods=["GET", "POST"]
)
def queue():

    if not session.get("logged_in"):

        return redirect("/login")


    message = ""

    error = ""


    if request.method == "POST":

        patient_id = request.form[
            "patient_id"
        ]


        conn = sqlite3.connect(
            "hospital.db"
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT * FROM patients
            WHERE patient_id = ?
            """,

            (patient_id,)
        )


        patient = cursor.fetchone()


        conn.close()


        if patient is None:

            error = (
                "Patient not found. "
                "Please register the patient first."
            )


        else:

            already_in_queue = False


            for p in patient_queue:

                if p[0] == patient[0]:

                    already_in_queue = True

                    break


            if already_in_queue:

                error = (
                    "Patient is already "
                    "in the queue."
                )


            else:

                patient_queue.append(
                    patient
                )

                message = (
                    "Patient "
                    + patient[1]
                    + " added to the queue."
                )


    return render_template(
        "queue.html",
        queue=list(patient_queue),
        message=message,
        error=error
    )


# =====================================================
# CALL NEXT NORMAL PATIENT
# =====================================================

@app.route("/call-next")
def call_next():

    if not session.get("logged_in"):

        return redirect("/login")


    message = ""

    error = ""


    if len(patient_queue) > 0:

        patient = (
            patient_queue.popleft()
        )


        treated_stack.append(
            patient
        )


        undo_stack.append(
            (
                "normal",
                patient
            )
        )


        message = (

            "Now calling Patient "

            + patient[1]

            + " (ID: "

            + str(patient[0])

            + ")"

        )


    else:

        error = (
            "Queue is empty. "
            "No patient is waiting."
        )


    return render_template(
        "queue.html",
        queue=list(patient_queue),
        message=message,
        error=error
    )


# =====================================================
# EMERGENCY PATIENT
# =====================================================

@app.route(
    "/emergency",
    methods=["GET", "POST"]
)
def emergency():

    if not session.get("logged_in"):

        return redirect("/login")


    message = ""

    error = ""


    if request.method == "POST":

        patient_id = request.form[
            "patient_id"
        ]

        priority = int(
            request.form["priority"]
        )


        conn = sqlite3.connect(
            "hospital.db"
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT * FROM patients
            WHERE patient_id = ?
            """,

            (patient_id,)
        )


        patient = cursor.fetchone()


        conn.close()


        if patient is None:

            error = (
                "Patient not found. "
                "Please register the patient first."
            )


        else:

            already_exists = False


            for item in emergency_queue:

                if item[1][0] == patient[0]:

                    already_exists = True

                    break


            if already_exists:

                error = (
                    "Patient is already "
                    "in the emergency queue."
                )


            else:

                heapq.heappush(

                    emergency_queue,

                    (
                        priority,
                        patient
                    )

                )


                message = (

                    "Emergency patient "

                    + patient[1]

                    + " added successfully."

                )


    sorted_queue = sorted(
        emergency_queue,
        key=lambda x: x[0]
    )


    emergency_patients = []


    for item in sorted_queue:

        priority = item[0]

        patient = item[1]


        emergency_patients.append(
            patient + (priority,)
        )


    return render_template(
        "emergency.html",
        emergency_queue=emergency_patients,
        message=message,
        error=error
    )


# =====================================================
# CALL NEXT EMERGENCY PATIENT
# =====================================================

@app.route("/call-emergency")
def call_emergency():

    if not session.get("logged_in"):

        return redirect("/login")


    message = ""

    error = ""


    if len(emergency_queue) > 0:

        priority, patient = (
            heapq.heappop(
                emergency_queue
            )
        )


        treated_stack.append(
            patient
        )


        undo_stack.append(
            (
                "emergency",
                patient,
                priority
            )
        )


        message = (

            "Now calling emergency patient "

            + patient[1]

            + " (ID: "

            + str(patient[0])

            + ")"

            + " with Priority "

            + str(priority)

        )


    else:

        error = (
            "Emergency queue is empty."
        )


    sorted_queue = sorted(
        emergency_queue,
        key=lambda x: x[0]
    )


    emergency_patients = []


    for item in sorted_queue:

        priority = item[0]

        patient = item[1]


        emergency_patients.append(
            patient + (priority,)
        )


    return render_template(
        "emergency.html",
        emergency_queue=emergency_patients,
        message=message,
        error=error
    )


# =====================================================
# PATIENT BST
# =====================================================

@app.route(
    "/bst",
    methods=["GET", "POST"]
)
def bst():

    if not session.get("logged_in"):

        return redirect("/login")


    found_patient = None

    error = ""


    patient_bst = PatientBST()


    conn = sqlite3.connect(
        "hospital.db"
    )

    cursor = conn.cursor()


    cursor.execute(
        "SELECT * FROM patients"
    )

    all_patients = cursor.fetchall()


    conn.close()


    for patient in all_patients:

        patient_bst.insert(
            patient
        )


    if request.method == "POST":

        patient_id = int(
            request.form["patient_id"]
        )


        found_patient = (
            patient_bst.search(
                patient_id
            )
        )


        if found_patient is None:

            error = (
                "Patient not found in BST."
            )


    patients = patient_bst.inorder()


    return render_template(
        "bst.html",
        patients=patients,
        found_patient=found_patient,
        error=error
    )


# =====================================================
# AMBULANCE ROUTE
# =====================================================

@app.route(
    "/ambulance",
    methods=["GET", "POST"]
)
def ambulance():

    if not session.get("logged_in"):

        return redirect("/login")


    route = None

    error = ""

    start = ""

    destination = ""


    if request.method == "POST":

        start = request.form[
            "start"
        ]

        destination = request.form[
            "destination"
        ]


        if start == destination:

            route = [start]


        else:

            route = find_route(
                start,
                destination
            )


            if route is None:

                error = (
                    "No route found between "
                    "the selected locations."
                )


    return render_template(
        "ambulance.html",
        route=route,
        start=start,
        destination=destination,
        error=error
    )


# =====================================================
# HOSPITAL DEPARTMENT GRAPH
# =====================================================

@app.route("/department")
def department():

    if not session.get("logged_in"):

        return redirect("/login")


    return render_template(
        "department.html",
        graph=hospital_graph
    )


# =====================================================
# RECENTLY TREATED PATIENTS
# =====================================================

@app.route("/treated")
def treated():

    if not session.get("logged_in"):

        return redirect("/login")


    return render_template(
        "treated.html",
        patients=list(
            reversed(treated_stack)
        )
    )


# =====================================================
# UNDO LAST OPERATION
# =====================================================

@app.route("/undo")
def undo():

    if not session.get("logged_in"):

        return redirect("/login")


    message = ""

    error = ""


    if len(undo_stack) == 0:

        error = (
            "There is no operation to undo."
        )

    else:

        operation = undo_stack.pop()


        # ---------------------------------------------
        # UNDO NORMAL PATIENT CALL
        # ---------------------------------------------

        if operation[0] == "normal":

            patient = operation[1]


            patient_queue.appendleft(
                patient
            )


            if len(treated_stack) > 0:

                treated_stack.pop()


            message = (

                "Undo successful. "

                + patient[1]

                + " has been returned to "
                  "the normal patient queue."

            )


        # ---------------------------------------------
        # UNDO EMERGENCY PATIENT CALL
        # ---------------------------------------------

        elif operation[0] == "emergency":

            patient = operation[1]

            priority = operation[2]


            heapq.heappush(

                emergency_queue,

                (
                    priority,
                    patient
                )

            )


            if len(treated_stack) > 0:

                treated_stack.pop()


            message = (

                "Undo successful. "

                + patient[1]

                + " has been returned to "
                  "the emergency queue."

            )


    return render_template(
        "undo.html",
        message=message,
        error=error,
        undo_count=len(undo_stack)
    )


# =====================================================
# PATIENT MEDICAL HISTORY
# =====================================================

@app.route(
    "/medical-history",
    methods=["GET", "POST"]
)
def medical_history():

    if not session.get("logged_in"):

        return redirect("/login")


    patient = None

    history = []

    error = ""


    if request.method == "POST":

        patient_id = request.form[
            "patient_id"
        ]


        conn = sqlite3.connect(
            "hospital.db"
        )

        cursor = conn.cursor()


        # Find patient

        cursor.execute(
            """
            SELECT * FROM patients
            WHERE patient_id = ?
            """,
            (patient_id,)
        )


        patient = cursor.fetchone()


        if patient is None:

            error = (
                "Patient not found. "
                "Please check the Patient ID."
            )

        else:

            # Get medical history

            cursor.execute(
                """
                SELECT
                    history_id,
                    patient_id,
                    date,
                    doctor,
                    diagnosis,
                    treatment
                FROM medical_history
                WHERE patient_id = ?
                ORDER BY history_id DESC
                """,
                (patient_id,)
            )


            history = cursor.fetchall()


        conn.close()


    return render_template(
        "medical_history.html",
        patient=patient,
        history=history,
        error=error
    )


# =====================================================
# ADD MEDICAL HISTORY
# =====================================================

@app.route(
    "/add-medical-history",
    methods=["POST"]
)
def add_medical_history():

    if not session.get("logged_in"):

        return redirect("/login")


    patient_id = request.form[
        "patient_id"
    ]

    date = request.form[
        "date"
    ]

    doctor = request.form[
        "doctor"
    ]

    diagnosis = request.form[
        "diagnosis"
    ]

    treatment = request.form[
        "treatment"
    ]


    conn = sqlite3.connect(
        "hospital.db"
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO medical_history
        (
            patient_id,
            date,
            doctor,
            diagnosis,
            treatment
        )

        VALUES (?, ?, ?, ?, ?)
        """,

        (
            patient_id,
            date,
            doctor,
            diagnosis,
            treatment
        )
    )


    conn.commit()

    conn.close()


    return redirect(
        "/medical-history"
    )


# =====================================================
# EXIT
# =====================================================

@app.route("/exit")
def exit_app():

    session.clear()

    return render_template(
        "exit.html"
    )


# =====================================================
# START APPLICATION
# =====================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )