import sqlite3
import os
import secrets
import hashlib
import threading
from datetime import datetime
from urllib.parse import urlparse, parse_qs

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "freshers_events.db")
db_lock = threading.Lock()

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn

def hash_password(password: str) -> str:
    salt = "gpcet_cyber_freshers_2026_salt"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def generate_secure_token() -> str:
    # 32-character cryptographically secure token
    return f"FSH26_{secrets.token_urlsafe(24)}"

def init_db():
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    pass_id TEXT UNIQUE NOT NULL,
                    qr_token TEXT UNIQUE NOT NULL,
                    meal TEXT NOT NULL,
                    photo_b64 TEXT,
                    registered INTEGER DEFAULT 1,
                    registered_at TEXT NOT NULL,
                    checked_in INTEGER DEFAULT 0,
                    checkin_time TEXT,
                    checkin_by TEXT
                )
            """)
            
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_students_token ON students(qr_token)")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_students_pass ON students(pass_id)")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_students_roll ON students(roll_no)")
            
            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    qr_token TEXT,
                    student_id TEXT,
                    student_name TEXT,
                    roll_no TEXT,
                    department TEXT,
                    meal TEXT,
                    scan_timestamp TEXT NOT NULL,
                    admin_id TEXT DEFAULT 'Admin',
                    scan_type TEXT DEFAULT 'QR',
                    result TEXT NOT NULL,
                    notes TEXT
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(scan_timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_result ON audit_log(result)")

            # Admin credentials table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'admin',
                    created_at TEXT NOT NULL
                )
            """)
            
            # Seed default admin user (admin / admin2026)
            default_admin = "admin"
            default_pass_hash = hash_password("admin2026")
            now_iso = datetime.now().isoformat()
            
            cursor.execute(
                "INSERT OR IGNORE INTO admin_users (username, password_hash, role, created_at) VALUES (?, ?, 'admin', ?)",
                (default_admin, default_pass_hash, now_iso)
            )
            conn.commit()

def verify_admin_login(username: str, password: str) -> bool:
    if not username or not password:
        return False
    p_hash = hash_password(password)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM admin_users WHERE username = ? AND password_hash = ?", (username.strip(), p_hash))
        return cursor.fetchone() is not None

def register_student(name: str, roll_no: str, department: str, pass_id: str, qr_token: str, meal: str, photo_b64: str = None) -> dict:
    roll_clean = roll_no.strip().upper()
    name_clean = name.strip()
    dept_clean = department.strip()
    pass_clean = pass_id.strip()
    now_iso = datetime.now().isoformat()
    
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Check existing roll
            cursor.execute("SELECT * FROM students WHERE roll_no = ?", (roll_clean,))
            existing = cursor.fetchone()
            if existing:
                return {"success": False, "error": f"Roll number {roll_clean} has already registered!", "student": dict(existing)}
            
            cursor.execute("""
                INSERT INTO students (roll_no, name, department, pass_id, qr_token, meal, photo_b64, registered, registered_at, checked_in)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 0)
            """, (roll_clean, name_clean, dept_clean, pass_clean, qr_token, meal, photo_b64, now_iso))
            conn.commit()
            
            cursor.execute("SELECT * FROM students WHERE roll_no = ?", (roll_clean,))
            row = cursor.fetchone()
            return {"success": True, "student": dict(row)}

def get_student_by_roll(roll_no: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no.strip().upper(),))
        row = cursor.fetchone()
        return dict(row) if row else None

def extract_token(raw_input: str) -> str:
    """Extracts raw token if user scanned a full URL or typed an identifier."""
    cleaned = raw_input.strip()
    if not cleaned:
        return ""
    if "token=" in cleaned:
        try:
            parsed = urlparse(cleaned)
            query = parse_qs(parsed.query)
            if "token" in query and query["token"]:
                return query["token"][0].strip()
        except Exception:
            pass
    return cleaned

def verify_and_checkin(raw_token: str, admin_id: str = "Admin", scan_type: str = "QR") -> dict:
    token = extract_token(raw_token)
    if not token:
        return {"status": "INVALID", "message": "Empty or unrecognized pass token."}
    
    now = datetime.now()
    now_str = now.strftime("%I:%M:%S %p")
    now_iso = now.isoformat()
    
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Find the student record matching qr_token, pass_id, or roll_no
            cursor.execute("""
                SELECT id, name, roll_no, department, pass_id, qr_token, meal, photo_b64, checked_in, checkin_time, checkin_by
                FROM students 
                WHERE qr_token = ? OR pass_id = ? OR roll_no = ?
            """, (token, token.upper(), token.upper()))
            student_row = cursor.fetchone()
            
            if not student_row:
                # Log invalid attempt
                cursor.execute("""
                    INSERT INTO audit_log (qr_token, scan_timestamp, admin_id, scan_type, result, notes)
                    VALUES (?, ?, ?, ?, 'INVALID', 'Token or ID not found in database')
                """, (token[:50], now_str, admin_id, scan_type))
                conn.commit()
                return {
                    "status": "INVALID",
                    "message": "QR code not recognized.",
                    "timestamp": now_str
                }
            
            student = dict(student_row)
            
            # Check if student is ALREADY checked in
            if student["checked_in"] == 1:
                first_checkin_display = student["checkin_time"] or "Unknown"
                cursor.execute("""
                    INSERT INTO audit_log (qr_token, student_id, student_name, roll_no, department, meal, scan_timestamp, admin_id, scan_type, result, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ALREADY_USED', ?)
                """, (student["qr_token"], student["pass_id"], student["name"], student["roll_no"], student["department"], student["meal"], now_str, admin_id, scan_type, f"Duplicate attempt. First checked in: {first_checkin_display}"))
                conn.commit()
                return {
                    "status": "ALREADY_USED",
                    "message": "This invitation has already been used.",
                    "student_name": student["name"],
                    "roll_no": student["roll_no"],
                    "pass_id": student["pass_id"],
                    "department": student["department"],
                    "meal": student["meal"],
                    "first_checkin": first_checkin_display,
                    "timestamp": now_str
                }
            
            # ATOMIC Check-in UPDATE
            cursor.execute("""
                UPDATE students 
                SET checked_in = 1, checkin_time = ?, checkin_by = ? 
                WHERE id = ? AND checked_in = 0
            """, (now_str, admin_id, student["id"]))
            
            if cursor.rowcount == 1:
                # Successfully updated exactly one row
                cursor.execute("""
                    INSERT INTO audit_log (qr_token, student_id, student_name, roll_no, department, meal, scan_timestamp, admin_id, scan_type, result, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'APPROVED', 'Entry check-in successful')
                """, (student["qr_token"], student["pass_id"], student["name"], student["roll_no"], student["department"], student["meal"], now_str, admin_id, scan_type))
                conn.commit()
                
                student["checked_in"] = 1
                student["checkin_time"] = now_str
                return {
                    "status": "APPROVED",
                    "message": "Entry Approved! Check-in successful.",
                    "student_name": student["name"],
                    "roll_no": student["roll_no"],
                    "pass_id": student["pass_id"],
                    "department": student["department"],
                    "meal": student["meal"],
                    "photo_b64": student["photo_b64"],
                    "checkin_time": now_str,
                    "timestamp": now_str
                }
            else:
                # Concurrent race condition caught! Another request just checked in
                cursor.execute("SELECT checkin_time FROM students WHERE id = ?", (student["id"],))
                updated = cursor.fetchone()
                first_checkin_display = updated["checkin_time"] if updated else now_str
                
                cursor.execute("""
                    INSERT INTO audit_log (qr_token, student_id, student_name, roll_no, department, meal, scan_timestamp, admin_id, scan_type, result, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ALREADY_USED', 'Simultaneous race condition resolved. Blocked duplicate entry.')
                """, (student["qr_token"], student["pass_id"], student["name"], student["roll_no"], student["department"], student["meal"], now_str, admin_id, scan_type))
                conn.commit()
                
                return {
                    "status": "ALREADY_USED",
                    "message": "This invitation has already been used.",
                    "student_name": student["name"],
                    "roll_no": student["roll_no"],
                    "pass_id": student["pass_id"],
                    "department": student["department"],
                    "meal": student["meal"],
                    "first_checkin": first_checkin_display,
                    "timestamp": now_str
                }

def reverse_checkin(roll_no_or_pass_id: str, admin_username: str, admin_password: str, reason: str) -> dict:
    if not verify_admin_login(admin_username, admin_password):
        return {"success": False, "error": "Invalid admin password. Action unauthorized."}
    
    if not reason or len(reason.strip()) < 3:
        return {"success": False, "error": "A valid reason for reversal is mandatory."}
    
    target = roll_no_or_pass_id.strip().upper()
    now_str = datetime.now().strftime("%I:%M:%S %p")
    
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM students WHERE roll_no = ? OR pass_id = ?
            """, (target, target))
            student = cursor.fetchone()
            
            if not student:
                return {"success": False, "error": "Student not found with provided Roll No or Pass ID."}
            
            if student["checked_in"] == 0:
                return {"success": False, "error": f"Student {student['name']} is not currently checked in."}
            
            # Perform reversal
            cursor.execute("""
                UPDATE students 
                SET checked_in = 0, checkin_time = NULL, checkin_by = NULL
                WHERE id = ?
            """, (student["id"],))
            
            cursor.execute("""
                INSERT INTO audit_log (qr_token, student_id, student_name, roll_no, department, meal, scan_timestamp, admin_id, scan_type, result, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MANUAL', 'REVERSED', ?)
            """, (student["qr_token"], student["pass_id"], student["name"], student["roll_no"], student["department"], student["meal"], now_str, admin_username, f"Check-in reversed by {admin_username}. Reason: {reason.strip()}"))
            conn.commit()
            
            return {
                "success": True, 
                "message": f"Successfully reversed check-in for {student['name']} ({student['roll_no']}). Pass is now active again.",
                "student": dict(student)
            }

def get_stats() -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM students")
        total_registered = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) AS checked FROM students WHERE checked_in = 1")
        total_checked_in = cursor.fetchone()["checked"]
        
        remaining = max(0, total_registered - total_checked_in)
        
        cursor.execute("SELECT COUNT(*) AS dupes FROM audit_log WHERE result = 'ALREADY_USED'")
        duplicate_attempts = cursor.fetchone()["dupes"]
        
        cursor.execute("SELECT COUNT(*) AS veg FROM students WHERE checked_in = 1 AND meal LIKE '%VEG%' AND meal NOT LIKE '%NON%'")
        veg_checked = cursor.fetchone()["veg"]
        
        cursor.execute("SELECT COUNT(*) AS nonveg FROM students WHERE checked_in = 1 AND meal LIKE '%NON%'")
        nonveg_checked = cursor.fetchone()["nonveg"]
        
        return {
            "total_registered": total_registered,
            "total_checked_in": total_checked_in,
            "remaining": remaining,
            "duplicate_attempts": duplicate_attempts,
            "veg_checked_in": veg_checked,
            "nonveg_checked_in": nonveg_checked
        }

def get_recent_logs(limit: int = 50) -> list:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, scan_timestamp, student_name, roll_no, department, meal, scan_type, result, notes
            FROM audit_log
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def search_students(query_str: str) -> list:
    q = query_str.strip()
    if not q:
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        like_pattern = f"%{q}%"
        cursor.execute("""
            SELECT roll_no, name, department, pass_id, meal, photo_b64, checked_in, checkin_time, registered_at
            FROM students
            WHERE roll_no LIKE ? OR name LIKE ? OR pass_id LIKE ?
            LIMIT 20
        """, (like_pattern, like_pattern, like_pattern))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

# Initialize tables when module is imported
init_db()
# =================================---------
# STEP 1: ADD THIS TO YOUR database.py FILE
# =================================---------

def delete_student_entry(roll_no_or_pass_id: str, admin_username: str, admin_password: str) -> dict:
    """
    Deletes a student registration completely from the database.
    Useful for removing test entries before the live event launch.
    """
    if not verify_admin_login(admin_username, admin_password):
        return {"success": False, "error": "Invalid admin password. Action unauthorized."}
    
    target = roll_no_or_pass_id.strip().upper()
    
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Find the student first to fetch their token
            cursor.execute("SELECT * FROM students WHERE roll_no = ? OR pass_id = ?", (target, target))
            student = cursor.fetchone()
            
            if not student:
                return {"success": False, "error": "Student record not found."}
            
            # Delete from audit logs first to prevent loose records
            cursor.execute("DELETE FROM audit_log WHERE qr_token = ? OR roll_no = ?", (student["qr_token"], student["roll_no"]))
            
            # Delete the student record
            cursor.execute("DELETE FROM students WHERE id = ?", (student["id"],))
            conn.commit()
            
            return {
                "success": True, 
                "message": f"Successfully deleted all records for {student['name']} ({student['roll_no']})."
            }

