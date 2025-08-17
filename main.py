import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user, login_required, current_user
)
from functools import wraps
import bcrypt

# ---------- CONFIG ----------

import os
from dotenv import load_dotenv
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "freedb.tech")
DB_USER = os.getenv("DB_USER", "freedb_Priyanshu")
DB_PASS = os.getenv("DB_PASS")   # ← will raise if missing
if not DB_PASS:
    raise RuntimeError("DB_PASS not found in .env")

conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=os.getenv("DB_NAME", "freedb_gym"),
    port=int(os.getenv("DB_PORT", 3306)),
    ssl_disabled=True
)
cursor = conn.cursor()

app = Flask(__name__)
app.secret_key = 'change_me_in_production'

# ---------- LOGIN ----------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role


@login_manager.user_loader
def load_user(user_id):
    cursor.execute("SELECT user_id, username, role FROM Users WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()
    return User(*row) if row else None


# ---------- ROLE DECORATOR ----------
def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        @login_required
        def decorated(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return decorated
    return wrapper


# ---------- AUTH ROUTES ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        plain = request.form['password'].encode('utf-8')
        cursor.execute(
            "SELECT user_id, password_hash, role FROM Users WHERE username=%s",
            (username,)
        )
        row = cursor.fetchone()
        if row and bcrypt.checkpw(plain, row[1].encode('utf-8')):
            login_user(User(*row))
            return redirect(url_for('index'))
        return "Invalid credentials"
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ---------- PUBLIC / PROTECTED ----------
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Get analytics data
    analytics = get_analytics_data()
    
    # Route to appropriate dashboard based on role
    if current_user.role == 'admin':
        recent_payments = get_recent_payments(5)
        recent_members = get_recent_members(5)
        return render_template('admin-dashboard.html', 
                              analytics=analytics,
                              recent_payments=recent_payments,
                              recent_members=recent_members)
    else:  # receptionist
        todays_classes = get_todays_classes()
        recent_attendance = get_recent_attendance(5)
        recent_payments = get_recent_payments(3)
        return render_template('receptionist_dashboard.html',
                              analytics=analytics,
                              todays_classes=todays_classes,
                              recent_attendance=recent_attendance,
                              recent_payments=recent_payments)


# ---------- ANALYTICS FUNCTIONS ----------
def get_analytics_data():
    analytics = {}
    
    # Total revenue
    cursor.execute("SELECT SUM(amount) FROM Payments")
    result = cursor.fetchone()
    analytics['total_revenue'] = float(result[0]) if result[0] else 0
    
    # Total members
    cursor.execute("SELECT COUNT(*) FROM Members")
    analytics['total_members'] = cursor.fetchone()[0]
    
    # New members this month
    cursor.execute("""
        SELECT COUNT(*) FROM Members 
        WHERE MONTH(start_date) = MONTH(CURDATE()) 
        AND YEAR(start_date) = YEAR(CURDATE())
    """)
    analytics['new_members_this_month'] = cursor.fetchone()[0]
    
    # Total classes
    cursor.execute("SELECT COUNT(*) FROM Classes")
    analytics['total_classes'] = cursor.fetchone()[0]
    
    # Total trainers
    cursor.execute("SELECT COUNT(*) FROM Trainers")
    analytics['total_trainers'] = cursor.fetchone()[0]
    
    # Today's attendance
    cursor.execute("""
        SELECT COUNT(*) FROM Attendance 
        WHERE date = CURDATE()
    """)
    analytics['today_attendance'] = cursor.fetchone()[0]
    
    # Today's payments
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM Payments 
        WHERE payment_date = CURDATE()
    """)
    result = cursor.fetchone()
    analytics['today_payments'] = float(result[0]) if result[0] else 0
    
    # Attendance rate (simplified calculation)
    if analytics['total_members'] > 0:
        analytics['attendance_rate'] = round((analytics['today_attendance'] / analytics['total_members']) * 100)
    else:
        analytics['attendance_rate'] = 0
    
    return analytics

def get_recent_payments(limit=5):
    cursor.execute("""
        SELECT * FROM Payments 
        ORDER BY payment_date DESC, payment_id DESC 
        LIMIT %s
    """, (limit,))
    return cursor.fetchall()

def get_recent_members(limit=5):
    cursor.execute("""
        SELECT * FROM Members 
        ORDER BY start_date DESC, member_id DESC 
        LIMIT %s
    """, (limit,))
    return cursor.fetchall()

def get_recent_attendance(limit=5):
    cursor.execute("""
        SELECT * FROM Attendance 
        ORDER BY date DESC, attendance_id DESC 
        LIMIT %s
    """, (limit,))
    return cursor.fetchall()

def get_todays_classes():
    cursor.execute("SELECT * FROM Classes ORDER BY time")
    return cursor.fetchall()


# ---------- REPORTS ----------
@app.route('/reports')
@role_required('admin')
def reports():
    reports_data = get_reports_data()
    return render_template('reports.html', 
                         reports=reports_data,
                         monthly_payments=get_monthly_payments(),
                         membership_stats=get_membership_stats(),
                         class_popularity=get_class_popularity(),
                         trainer_performance=get_trainer_performance())

def get_reports_data():
    reports = {}
    
    # Monthly revenue
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM Payments 
        WHERE MONTH(payment_date) = MONTH(CURDATE()) 
        AND YEAR(payment_date) = YEAR(CURDATE())
    """)
    result = cursor.fetchone()
    reports['monthly_revenue'] = float(result[0]) if result[0] else 0
    
    # Member growth
    cursor.execute("""
        SELECT COUNT(*) FROM Members 
        WHERE MONTH(start_date) = MONTH(CURDATE()) 
        AND YEAR(start_date) = YEAR(CURDATE())
    """)
    reports['member_growth'] = cursor.fetchone()[0]
    
    # Average attendance (simplified)
    cursor.execute("SELECT COUNT(*) FROM Members")
    total_members = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM Attendance 
        WHERE MONTH(date) = MONTH(CURDATE()) 
        AND YEAR(date) = YEAR(CURDATE())
    """)
    monthly_attendance = cursor.fetchone()[0]
    
    if total_members > 0:
        reports['avg_attendance'] = round((monthly_attendance / total_members) * 100)
    else:
        reports['avg_attendance'] = 0
    
    # Class utilization (simplified)
    reports['class_utilization'] = 75  # Placeholder
    reports['revenue_growth'] = 12  # Placeholder
    
    return reports

def get_monthly_payments():
    cursor.execute("""
        SELECT 
            DATE_FORMAT(payment_date, '%Y-%m') as month,
            SUM(amount) as total,
            COUNT(*) as count
        FROM Payments 
        WHERE payment_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
        ORDER BY month DESC
    """)
    results = cursor.fetchall()
    return [{'month': row[0], 'total': float(row[1]), 'count': row[2]} for row in results]

def get_membership_stats():
    cursor.execute("""
        SELECT 
            membership_type as type,
            COUNT(*) as count,
            ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Members)), 1) as percentage
        FROM Members 
        GROUP BY membership_type
        ORDER BY count DESC
    """)
    results = cursor.fetchall()
    return [{'type': row[0], 'count': row[1], 'percentage': float(row[2])} for row in results]

def get_class_popularity():
    cursor.execute("""
        SELECT 
            c.class_name as name,
            c.time,
            COUNT(a.attendance_id) as attendance
        FROM Classes c
        LEFT JOIN Attendance a ON c.class_id = a.class_id
        GROUP BY c.class_id, c.class_name, c.time
        ORDER BY attendance DESC
        LIMIT 10
    """)
    results = cursor.fetchall()
    return [{'name': row[0], 'time': str(row[1]), 'attendance': row[2]} for row in results]

def get_trainer_performance():
    cursor.execute("""
        SELECT 
            t.name,
            t.speciality as specialty,
            COUNT(DISTINCT c.class_id) as classes,
            COALESCE(AVG(class_attendance.avg_attendance), 0) as avg_attendance
        FROM Trainers t
        LEFT JOIN Classes c ON t.trainer_id = c.trainer_id
        LEFT JOIN (
            SELECT 
                class_id,
                COUNT(*) as avg_attendance
            FROM Attendance
            GROUP BY class_id
        ) class_attendance ON c.class_id = class_attendance.class_id
        GROUP BY t.trainer_id, t.name, t.speciality
        ORDER BY classes DESC, avg_attendance DESC
    """)
    results = cursor.fetchall()
    return [{'name': row[0], 'specialty': row[1], 'classes': row[2], 'avg_attendance': round(float(row[3]))} for row in results]


# ---------- MEMBERS ----------
@app.route('/members')
@login_required
def members():
    cursor.execute("SELECT * FROM Members")
    data = cursor.fetchall()
    return render_template('members.html', members_data=data)


@app.route('/insert_member', methods=['POST'])
@role_required('admin', 'receptionist')
def insert_member():
    name = request.form['name']
    contact = request.form['phone']
    email = request.form['email']
    mtype = request.form['membership_type']
    start = request.form['join_date']
    sql = """INSERT INTO Members
             (name, contact_number, email, membership_type, start_date)
             VALUES (%s,%s,%s,%s,%s)"""
    cursor.execute(sql, (name, contact, email, mtype, start))
    db.commit()
    return redirect(url_for('members'))


# ---------- TRAINERS ----------
@app.route('/trainers')
@login_required
def trainers():
    cursor.execute("SELECT * FROM Trainers")
    return render_template('trainers.html', trainers_data=cursor.fetchall())


@app.route('/insert_trainer', methods=['POST'])
@role_required('admin', 'receptionist')
def insert_trainer():
    name = request.form['name']
    speciality = request.form['speciality']
    phone = request.form['Phone']
    sql = "INSERT INTO Trainers (name, speciality, Contact_number) VALUES (%s,%s,%s)"
    cursor.execute(sql, (name, speciality, phone))
    db.commit()
    return redirect(url_for('trainers'))


# ---------- CLASSES ----------
@app.route('/classes')
@login_required
def classes():
    cursor.execute("SELECT * FROM Classes")
    return render_template('classes.html', classes_data=cursor.fetchall())


@app.route('/insert_class', methods=['POST'])
@role_required('admin', 'receptionist')
def insert_class():
    class_name = request.form['class_name']
    trainer_id = request.form['trainer_id']
    time = request.form['time']
    sql = "INSERT INTO Classes (class_name, trainer_id, time) VALUES (%s,%s,%s)"
    cursor.execute(sql, (class_name, trainer_id, time))
    db.commit()
    return redirect(url_for('classes'))


# ---------- PAYMENTS ----------
@app.route('/payments')
@login_required
def payments():
    cursor.execute("SELECT * FROM Payments")
    return render_template('payments.html', payments_data=cursor.fetchall())


@app.route('/insert_payment', methods=['POST'])
@role_required('admin', 'receptionist')
def insert_payment():
    member_id = request.form['member_id']
    amount = request.form['amount']
    payment_date = request.form['payment_date']
    sql = "INSERT INTO Payments (member_id, amount, payment_date) VALUES (%s,%s,%s)"
    cursor.execute(sql, (member_id, amount, payment_date))
    db.commit()
    return redirect(url_for('payments'))


# ---------- ATTENDANCE ----------
@app.route('/attendance')
@login_required
def attendance():
    cursor.execute("SELECT * FROM attendance")
    return render_template('attendance.html', attendance_data=cursor.fetchall())


@app.route('/insert_attendance', methods=['POST'])
@role_required('admin', 'receptionist')
def insert_attendance():
    member_id = request.form['member_id']
    class_id = request.form['class_id']
    date = request.form['payment_date']
    sql = "INSERT INTO attendance (member_id, class_id, date) VALUES (%s,%s,%s)"
    cursor.execute(sql, (member_id, class_id, date))
    db.commit()
    return redirect(url_for('attendance'))


# ---------- MAIN ----------
if __name__ == '__main__':
    app.run(debug=True)

# ---------- CLEANUP ----------
db.close()