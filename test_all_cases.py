import os
import sys
import sqlite3
import concurrent.futures
import time
import database

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_tests():
    print("=" * 60)
    print("RUNNING FRESHERS ENTRY CONTROL VERIFICATION SUITE")
    print("=" * 60)

    # Clean database tables for pristine test run
    database.init_db()
    with database.get_connection() as conn:
        conn.execute("DELETE FROM audit_log")
        conn.execute("DELETE FROM students")
        conn.commit()

    # Seed Student A and Student B
    token_a = database.generate_secure_token()
    token_b = database.generate_secure_token()

    reg_a = database.register_student(
        name="Rahul Sharma",
        roll_no="25ATA0501",
        department="CSE",
        pass_id="GPCET-25-A101",
        qr_token=token_a,
        meal="VEGETARIAN 🟢",
        photo_b64=None
    )
    assert reg_a["success"], f"Failed to register Student A: {reg_a}"

    reg_b = database.register_student(
        name="Priya Patel",
        roll_no="25ATA0502",
        department="ECE",
        pass_id="GPCET-25-B202",
        qr_token=token_b,
        meal="NON-VEGETARIAN 🔴",
        photo_b64=None
    )
    assert reg_b["success"], f"Failed to register Student B: {reg_b}"
    print("✅ Initial Student Registration Completed.")

    # ----------------------------------------------------
    # TEST 1: Student A scans QR for the first time
    # Expected: ENTRY APPROVED
    # ----------------------------------------------------
    print("\n--- TEST 1: Student A First Scan ---")
    qr_url_a = f"http://localhost:8000/admin/checkin?token={token_a}"
    res1 = database.verify_and_checkin(qr_url_a, admin_id="Device-1", scan_type="QR")
    print(f"Result: {res1['status']} | Message: {res1['message']}")
    assert res1["status"] == "APPROVED", f"Expected APPROVED but got {res1['status']}"
    assert res1["student_name"] == "Rahul Sharma"
    assert res1["roll_no"] == "25ATA0501"
    print("PASSED TEST 1: Student A first scan was APPROVED.")

    # ----------------------------------------------------
    # TEST 2: Student A scans the same QR again
    # Expected: ENTRY ALREADY USED
    # ----------------------------------------------------
    print("\n--- TEST 2: Student A Double Scan (Same QR) ---")
    res2 = database.verify_and_checkin(token_a, admin_id="Device-1", scan_type="QR")
    print(f"Result: {res2['status']} | Message: {res2['message']} | First Checkin: {res2.get('first_checkin')}")
    assert res2["status"] == "ALREADY_USED", f"Expected ALREADY_USED but got {res2['status']}"
    assert res2["student_name"] == "Rahul Sharma"
    print("PASSED TEST 2: Double scan correctly REJECTED with ALREADY_USED.")

    # ----------------------------------------------------
    # TEST 3: Student B scans their QR
    # Expected: ENTRY APPROVED
    # ----------------------------------------------------
    print("\n--- TEST 3: Student B Scans Separate QR ---")
    res3 = database.verify_and_checkin(token_b, admin_id="Device-2", scan_type="QR")
    print(f"Result: {res3['status']} | Message: {res3['message']}")
    assert res3["status"] == "APPROVED", f"Expected APPROVED but got {res3['status']}"
    assert res3["student_name"] == "Priya Patel"
    print("PASSED TEST 3: Student B scan was APPROVED.")

    # ----------------------------------------------------
    # TEST 4: Fake / Random QR
    # Expected: INVALID INVITATION
    # ----------------------------------------------------
    print("\n--- TEST 4: Fake / Random / Tampered QR ---")
    fake_token = "FSH26_FAKE_TOKEN_XYZ999999999"
    res4 = database.verify_and_checkin(fake_token, admin_id="Device-1", scan_type="QR")
    print(f"Result: {res4['status']} | Message: {res4['message']}")
    assert res4["status"] == "INVALID", f"Expected INVALID but got {res4['status']}"
    print("PASSED TEST 4: Fake QR correctly flagged as INVALID.")

    # ----------------------------------------------------
    # TEST 5: Concurrent Race Condition Test
    # Two admin devices scan Student C's QR almost simultaneously
    # Expected: Exactly ONE APPROVED, Exactly ONE ALREADY_USED
    # ----------------------------------------------------
    print("\n--- TEST 5: Atomic Concurrency Race Test ---")
    token_c = database.generate_secure_token()
    reg_c = database.register_student(
        name="Vikram Kumar",
        roll_no="25ATA0503",
        department="ME",
        pass_id="GPCET-25-C303",
        qr_token=token_c,
        meal="VEGETARIAN 🟢"
    )
    assert reg_c["success"]

    results = []
    def scan_device(device_id):
        # Scan with token
        return database.verify_and_checkin(token_c, admin_id=device_id, scan_type="QR")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(scan_device, f"Device-{i}") for i in range(1, 5)
        ]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    approved_count = sum(1 for r in results if r["status"] == "APPROVED")
    already_used_count = sum(1 for r in results if r["status"] == "ALREADY_USED")
    print(f"Concurrent scan outcomes: Approved={approved_count}, Already Used={already_used_count}")
    assert approved_count == 1, f"Expected exactly 1 APPROVED, got {approved_count}"
    assert already_used_count == len(results) - 1, f"Expected {len(results)-1} ALREADY_USED, got {already_used_count}"
    print("PASSED TEST 5: Atomic race condition handled safely. Exactly 1 request succeeded!")

    # ----------------------------------------------------
    # TEST 6: Application Restart Persistence Test
    # Check-in status survives restart
    # ----------------------------------------------------
    print("\n--- TEST 6: Persistence Across System / Process Restarts ---")
    # Verify directly from a fresh raw sqlite connection bypassing any Python cache
    with sqlite3.connect(database.DB_FILE) as raw_conn:
        raw_conn.row_factory = sqlite3.Row
        cur = raw_conn.cursor()
        cur.execute("SELECT roll_no, name, checked_in, checkin_time FROM students WHERE roll_no = '25ATA0501'")
        row = cur.fetchone()
        assert row["checked_in"] == 1, "Persistence failed: Student A was not checked in"
        assert row["checkin_time"] is not None
        print(f"Student A in fresh DB connection: checked_in={row['checked_in']}, time={row['checkin_time']}")
    print("PASSED TEST 6: Check-in status persisted into SQLite database.")

    # ----------------------------------------------------
    # TEST 7: Dashboard Statistics Refresh Test
    # ----------------------------------------------------
    print("\n--- TEST 7: Admin Dashboard Live Statistics Consistency ---")
    stats = database.get_stats()
    print(f"Live Dashboard Stats: {stats}")
    assert stats["total_registered"] == 3
    assert stats["total_checked_in"] == 3  # Student A, B, and C
    assert stats["remaining"] == 0
    assert stats["duplicate_attempts"] >= 4 # Student A scan 2 + concurrent scans for C
    assert stats["veg_checked_in"] == 2     # Rahul & Vikram
    assert stats["nonveg_checked_in"] == 1  # Priya
    print("PASSED TEST 7: Admin statistics calculations are completely accurate.")

    # ----------------------------------------------------
    # TEST 8: Reversal Test (Bonus validation)
    # ----------------------------------------------------
    print("\n--- TEST 8: Protected Reversal Action ---")
    rev_res = database.reverse_checkin("25ATA0501", "admin", "admin2026", "False scan test reversal")
    assert rev_res["success"], f"Reversal failed: {rev_res}"
    rev_stats = database.get_stats()
    assert rev_stats["total_checked_in"] == 2
    assert rev_stats["remaining"] == 1
    # Now scan again should succeed
    res_recheck = database.verify_and_checkin(token_a, admin_id="Device-1", scan_type="QR")
    assert res_recheck["status"] == "APPROVED"
    print("PASSED TEST 8: Protected Reversal safely restored pass and updated audit log.")

    print("\n" + "=" * 60)
    print("🎉 ALL 8 TESTS PASSED SUCCESSFULLY! 100% COMPLIANT.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
