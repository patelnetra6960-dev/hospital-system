from flask import Flask, render_template, request, redirect, session
import pymysql
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "hospital_secret_key"

# ---------------- UPLOAD CONFIG ----------------
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------- MYSQL CONNECTION ----------------
def get_connection():
    try:
        return pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='hospital_db',
            cursorclass=pymysql.cursors.DictCursor
        )
    except:
        return None


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('login.html')



# =================================================
#                PATIENT PANEL
# =================================================

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email,password)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            return redirect('/dashboard')
        else:
            return "Invalid Login"

    return render_template('login.html')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users(name,email,password,phone) VALUES(%s,%s,%s,%s)",
            (name,email,password,phone)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template('dashboard.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- VIEW DOCTORS ----------------
@app.route('/doctors')
def doctors():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('doctors.html', doctors=doctors)

# ---------------- BOOK APPOINTMENT ----------------
@app.route('/book/<int:doctor_id>', methods=['GET','POST'])
def book(doctor_id):
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        user_id = session['user_id']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO appointments(user_id,doctor_id,appointment_date,appointment_time,status)
            VALUES(%s,%s,%s,%s,'Booked')
        """,(user_id,doctor_id,date,time))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect('/my_appointments')

    return render_template('book.html')

# ---------------- MY APPOINTMENTS ----------------
@app.route('/my_appointments')
def my_appointments():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.name,a.appointment_date,a.appointment_time,a.status
        FROM appointments a
        JOIN doctors d ON a.doctor_id=d.doctor_id
        WHERE a.user_id=%s
    """,(session['user_id'],))

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('my_appointments.html', data=data)

# ---------------- UPLOAD REPORT ----------------
@app.route('/upload_report', methods=['GET','POST'])
def upload_report():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        file = request.files['report']
        filename = secure_filename(file.filename)

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO reports(user_id,file_name) VALUES(%s,%s)",
            (session['user_id'],filename)
        )
        conn.commit()

        cursor.close()
        conn.close()

    return render_template('upload_report.html')

# ---------------- MY REPORTS ----------------
@app.route('/my_reports')
def my_reports():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT file_name FROM reports WHERE user_id=%s",
        (session['user_id'],)
    )

    reports = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('my_reports.html', reports=reports)

# =================================================
#                ADMIN PANEL
# =================================================

# ---------------- ADMIN LOGIN ----------------
@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE username=%s AND password=%s",
            (username,password)
        )
        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin:
            session['admin'] = admin['admin_id']
            return redirect('/admin_dashboard')
        else:
            return "Invalid Admin Login"

    return render_template('admin_login.html')

# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_dashboard.html', doctors=doctors)

# ---------------- ADD DOCTOR ----------------
@app.route('/add_doctor', methods=['POST'])
def add_doctor():
    if 'admin' not in session:
        return redirect('/admin')

    name = request.form['name']
    specialization = request.form['specialization']
    time = request.form['available_time']

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO doctors(name,specialization,available_time) VALUES(%s,%s,%s)",
        (name,specialization,time)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/admin_dashboard')

# ---------------- DELETE DOCTOR ----------------
@app.route('/delete_doctor/<int:id>')
def delete_doctor(id):
    if 'admin' not in session:
        return redirect('/admin')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM doctors WHERE doctor_id=%s",(id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/admin_dashboard')

# ---------------- ADMIN APPOINTMENTS VIEW ----------------
@app.route('/admin_appointments')
def admin_appointments():
    if 'admin' not in session:
        return redirect('/admin')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.appointment_id,u.name AS patient,d.name AS doctor,
        a.appointment_date,a.appointment_time,a.admin_status
        FROM appointments a
        JOIN users u ON a.user_id=u.user_id
        JOIN doctors d ON a.doctor_id=d.doctor_id
    """)

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_appointments.html', data=data)


# ---------------- APPROVE APPOINTMENT ----------------
@app.route('/approve/<int:id>')
def approve(id):
    if 'admin' not in session:
        return redirect('/admin')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE appointments SET admin_status='Approved' WHERE appointment_id=%s",(id,)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/admin_appointments')


# ---------------- REJECT APPOINTMENT ----------------
@app.route('/reject/<int:id>')
def reject(id):
    if 'admin' not in session:
        return redirect('/admin')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE appointments SET admin_status='Rejected' WHERE appointment_id=%s",(id,)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/admin_appointments')

# ---------------- GOD LEVEL ADMIN DASHBOARD ----------------
@app.route('/god_dashboard')
def god_dashboard():
    if 'admin' not in session:
        return redirect('/admin')

    conn = get_connection()
    cursor = conn.cursor()

    # Total counts
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    patients = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM doctors")
    doctors = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM appointments")
    appointments = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template(
        'god_dashboard.html',
        patients=patients,
        doctors=doctors,
        appointments=appointments
    )



# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)












