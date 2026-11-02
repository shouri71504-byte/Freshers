import streamlit as st
import pandas as pd
import time
import base64
import uuid
import io
import qrcode
from PIL import Image, ImageDraw, ImageFont
import database
import admin_server


# Start the background QR scanner server.
admin_server.start_server_background(port=8000)

st.set_page_config(
    page_title="GPCET Midnight Cyber Freshers 🎉",
    page_icon="🌌",
    layout="centered",
)

st.markdown(
    """
    <style>
    .stApp, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at center, #14082b 0%, #060212 80%) !important;
        background-color: #060212 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0b041a !important;
        border-right: 1px solid rgba(255, 0, 127, 0.3) !important;
    }
    div.block-container {
        max-width: 900px !important;
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        background: transparent !important;
    }
    h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] {
        color: #ffffff;
    }
    h1 {
        text-align: center;
        font-family: 'Arial Black', sans-serif;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }
    .subtitle {
        text-align: center;
        font-size: 13px;
        color: #00ffff !important;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        margin-bottom: 25px;
    }
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #090414 !important;
        border-radius: 10px !important;
    }
    input, select, textarea {
        color: #ffffff !important;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #ff007f 0%, #7928ca 100%) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 12px !important;
        min-height: 44px;
    }
    [data-testid="stMetricValue"] {
        color: #00ffff !important;
        font-family: 'Courier New', monospace !important;
        font-weight: 900 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_excel_data():
    """Load the paid-student roster from the expected Excel sheet."""
    try:
        df = pd.read_excel("Students_list.xlsx", sheet_name="CSE-TOTAL")
        df.columns = df.columns.str.strip()
        df["Roll Number"] = df["Roll Number"].astype(str).str.upper().str.strip()
        df["Payment Status"] = df["Payment Status"].astype(str).str.lower().str.strip()
        return df
    except Exception as exc:
        st.sidebar.error(f"System Trace Log: {exc}")
        return None


def get_image_base64(image_bytes):
    if image_bytes is None:
        return ""
    return base64.b64encode(image_bytes).decode("utf-8")


def init_session_state():
    defaults = {
        "step": "login",
        "s_name": "",
        "s_roll": "",
        "s_dept": "",
        "s_id": "",
        "s_token": "",
        "s_photo": None,
        "s_meal": "",
        "s_downloaded": False,
        "s_registered": False,
        "admin_logged_in": False,
        "admin_user": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_qr_checkin():
    query_params = st.query_params
    raw_query_val = query_params.get("verify") or query_params.get("token")
    scanned_token = str(raw_query_val).strip()

    st.markdown("<h1>🔒 GPCET GATE EXPRESS CHECK-IN</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subtitle'>Atomic verification portal for auditorium gate crew</p>",
        unsafe_allow_html=True,
    )

    checkin_res = database.verify_and_checkin(
        scanned_token, admin_id="Gate-Express", scan_type="QR"
    )

    with st.container():
        if checkin_res.get("status") == "APPROVED":
            st.success("✅ ENTRY APPROVED! Pass Verified Successfully.")
            col_details, col_photo = st.columns(2)
            with col_details:
                st.markdown(f"### **{checkin_res.get('student_name', '').upper()}**")
                st.write(f"🎟️ **Roll Number:** `{checkin_res.get('roll_no', '')}`")
                st.write(f"🏢 **Department:** {checkin_res.get('department', '')} (2nd Year)")
                st.write(f"🍱 **Meal Ticket:** {checkin_res.get('meal', '')}")
                st.write(f"🆔 **Pass Serial:** `{checkin_res.get('pass_id', '')}`")
                st.write("🟢 **Entry Status:** CHECK-IN SUCCESSFUL")
                st.write(f"⏰ **Checked In At:** `{checkin_res.get('checkin_time', '')}`")
            with col_photo:
                photo_b64 = checkin_res.get("photo_b64")
                if photo_b64:
                    st.image(
                        base64.b64decode(photo_b64),
                        caption="Verified Profile Image",
                        width=180,
                    )
        elif checkin_res.get("status") == "ALREADY_USED":
            st.error("🚫 ENTRY ALREADY USED! Double Entry Denied.")
            st.warning(
                "This invitation has already been used. First checked in at: "
                f"{checkin_res.get('first_checkin', 'Unknown')}"
            )
            st.markdown(f"### **{checkin_res.get('student_name', '').upper()}**")
            st.write(f"🎟️ **Roll Number:** `{checkin_res.get('roll_no', '')}`")
            st.write(f"🆔 **Pass Serial:** `{checkin_res.get('pass_id', '')}`")
        else:
            st.error("❌ ACCESS DENIED! Invalid or Unregistered Ticket Pass Token.")
            st.warning(
                checkin_res.get("message", "QR code not recognized in database records.")
            )

    if st.button("⬅️ Return to Main Screen Portal", use_container_width=True):
        st.query_params.clear()
        st.rerun()
    st.stop()


def render_admin_dashboard():
    if not st.session_state.admin_logged_in:
        st.markdown("<h1>🔐 ADMIN ACCESS PORTAL</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p class='subtitle'>Restricted Gate Control Authorization Required</p>",
            unsafe_allow_html=True,
        )
        with st.container():
            st.write("### 🔑 Admin Credentials")
            adm_user = st.text_input("Admin Username", placeholder="e.g. admin")
            adm_pass = st.text_input(
                "Admin Password", type="password", placeholder="••••••••"
            )
            if st.button("Unlock Freshers Entry Control 🚀", use_container_width=True):
                if database.verify_admin_login(adm_user, adm_pass):
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_user = adm_user.strip()
                    st.success("Access Authorized! Opening Control Center...")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("❌ Invalid admin credentials. Access Denied.")
        return

    st.markdown("<h1>🎫 FRESHERS ENTRY CONTROL</h1>", unsafe_allow_html=True)
    st.markdown(
        f"Live Gate Security & Attendance Station | Authenticated: "
        f"{st.session_state.admin_user}"
    )

    scanner_url = f"http://{admin_server.HOST_IP}:8000/admin"
    st.markdown("### 📷 LAUNCH HIGH-SPEED CAMERA QR SCANNER")
    st.markdown(
        "Continuous scanning with rear/front camera support and instant sound effects."
    )
    st.link_button("OPEN LIVE CAMERA SCANNER 🚀", scanner_url, use_container_width=True)

    stats = database.get_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Total Registered", stats.get("total_registered", 0))
    c2.metric("✅ Checked In", stats.get("total_checked_in", 0))
    c3.metric("⏳ Remaining", stats.get("remaining", 0))
    c4, c5, c6 = st.columns(3)
    c4.metric("🚫 Duplicate Scans", stats.get("duplicate_attempts", 0))
    c5.metric("🟢 Veg Checked In", stats.get("veg_checked_in", 0))
    c6.metric("🔴 Non-Veg Checked In", stats.get("nonveg_checked_in", 0))

    st.divider()
    st.write("### 🔍 Manual Gate Verification Fallback")
    st.caption("Use this fallback if a student's QR code cannot be scanned physically.")
    col_manual, col_button = st.columns([3, 1])
    with col_manual:
        manual_val = st.text_input(
            "Enter Pass ID / Roll Number",
            placeholder="e.g. 25ATA0501 or GPCET-25-88A1",
        ).strip()
    with col_button:
        verify_btn = st.button("VERIFY PASS 🔍", use_container_width=True)

    if verify_btn:
        if not manual_val:
            st.warning("Enter a Pass ID or Roll Number first.")
        else:
            m_res = database.verify_and_checkin(
                manual_val,
                admin_id=st.session_state.admin_user,
                scan_type="MANUAL",
            )
            if m_res.get("status") == "APPROVED":
                st.success(
                    f"✅ ENTRY APPROVED for {m_res.get('student_name')} "
                    f"({m_res.get('roll_no')}) | Meal: {m_res.get('meal')} | "
                    f"Time: {m_res.get('checkin_time')}"
                )
            elif m_res.get("status") == "ALREADY_USED":
                st.error(
                    f"🚫 ENTRY ALREADY USED: {m_res.get('student_name')} "
                    f"({m_res.get('roll_no')}) was already checked in at "
                    f"{m_res.get('first_checkin')}."
                )
            else:
                st.error(
                    f"❌ INVALID INVITATION: "
                    f"{m_res.get('message', 'Pass could not be verified.')}"
                )

    st.divider()
    st.write("### 👥 Attendee Status Directory Search")
    search_query = st.text_input(
        "Search by Roll Number, Name, or Pass ID:",
        placeholder="Type search keywords...",
    ).strip()
    if search_query:
        results = database.search_students(search_query)
        if not results:
            st.info("ℹ️ No registered student matches found.")
        else:
            for student in results:
                is_in = student.get("checked_in", 0) == 1
                checkin_time = student.get("checkin_time") or ""
                status_badge = (
                    f"🔴 CHECKED IN ({checkin_time})"
                    if is_in
                    else "🟢 NOT CHECKED IN"
                )
                with st.container():
                    col_info, col_pic = st.columns([3, 1])
                    with col_info:
                        st.markdown(
                            f"#### {student.get('name', '').upper()} — {status_badge}"
                        )
                        st.write(
                            f"🎟️ Roll: {student.get('roll_no', '')} | "
                            f"🏢 Branch: {student.get('department', '')} | "
                            f"🍱 Meal: {student.get('meal', '')}"
                        )
                        registered_at = student.get("registered_at") or ""
                        st.write(
                            f"🆔 Pass Serial: {student.get('pass_id', '')} | "
                            f"📅 Registered: {registered_at[:10]}"
                        )
                    with col_pic:
                        photo_b64 = student.get("photo_b64")
                        if photo_b64:
                            try:
                                st.image(base64.b64decode(photo_b64), width=90)
                            except Exception:
                                st.caption("Photo unavailable")
                st.write("---")

    with st.expander("⚠️ Protected Action: Reverse Check-In Override"):
        st.warning(
            "Reversing a check-in re-activates the student pass. "
            "This action requires your admin password and a mandatory audit reason."
        )
        rev_target = st.text_input(
            "Student Roll No / Pass ID to Reverse", key="rev_t"
        ).strip()
        rev_reason = st.text_input(
            "Mandatory Reason for Reversal", key="rev_r"
        ).strip()
        rev_pass = st.text_input(
            "Admin Password Confirmation", type="password", key="rev_p"
        )
        if st.button("Confirm Check-In Reversal 🔄"):
            if not rev_target or not rev_reason or not rev_pass:
                st.error("Please complete all fields before reversing check-in.")
            else:
                rev_res = database.reverse_checkin(
                    rev_target,
                    st.session_state.admin_user,
                    rev_pass,
                    rev_reason,
                )
                if rev_res.get("success"):
                    st.success(rev_res.get("message", "Check-in reversal completed."))
                    time.sleep(1.2)
                    st.rerun()
                else:
                    st.error(rev_res.get("error", "Check-in reversal failed."))

    with st.expander("🗑️ Pre-Event Setup: Delete Student/Test Records"):
        st.info("Use this module to purge mock data and student tests.")
        del_target = st.text_input(
            "Enter Student Roll No / Pass ID to Purge", key="del_t"
        ).strip()
        del_pass = st.text_input(
            "Enter Organizer Password Confirmation", type="password", key="del_p"
        )
        if st.button("DELETE RECORD COMPLETELY ❌", use_container_width=True):
            if not del_target or not del_pass:
                st.error("Please insert target registration keys and credentials.")
            else:
                del_res = database.delete_student_entry(
                    del_target, st.session_state.admin_user, del_pass
                )
                if del_res.get("success"):
                    st.success(del_res.get("message", "Student record deleted."))
                    time.sleep(1.2)
                    st.rerun()
                else:
                    st.error(del_res.get("error", "Student deletion failed."))

    st.divider()
    st.write("### 📋 Recent Gate Activity Log")
    recent_logs = database.get_recent_logs(limit=25)
    if recent_logs:
        df_logs = pd.DataFrame(recent_logs)
        expected_cols = [
            "scan_timestamp", "student_name", "roll_no", "department",
            "meal", "scan_type", "result", "notes"
        ]
        available_cols = [col for col in expected_cols if col in df_logs.columns]
        df_logs = df_logs[available_cols]
        df_logs.columns = [
            {
                "scan_timestamp": "Time",
                "student_name": "Student",
                "roll_no": "Roll No",
                "department": "Dept",
                "meal": "Meal",
                "scan_type": "Type",
                "result": "Status",
                "notes": "Notes",
            }[col]
            for col in available_cols
        ]
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("No check-in transactions recorded yet.")

    if st.button("Logout Admin Session 🚪", type="secondary"):
        st.session_state.admin_logged_in = False
        st.session_state.admin_user = ""
        st.rerun()


def render_student_login():
    st.markdown("<h1>✨ THE GRAND GPCET FRESHERS ✨</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subtitle'>2nd Year & Lateral Entry Exclusive Automated Invitation Portal</p>",
        unsafe_allow_html=True,
    )
    st.write("### 🔑 Step 1: Scan Roll Credentials")
    roll_query = st.text_input(
        "Roll Number", placeholder="e.g., 25ATA0501 or 26ATA05L01"
    ).upper().strip()
    dept_query = st.selectbox(
        "Select Your Department Branch 👇",
        ["Select Department", "CSE", "CAI", "ECE", "EEE", "ME", "CE"],
    )

    if st.button("Verify Contribution & Unlock Pass 🚀", use_container_width=True):
        if not roll_query or dept_query == "Select Department":
            st.error(
                "⚠️ Input required! Please enter your roll number and select your "
                "correct branch department."
            )
            return

        if not (roll_query.startswith("25ATA") or roll_query.startswith("26ATA")):
            st.error(
                "🚫 Access Restricted! This application portal is built exclusively "
                "for 2nd-year and Lateral Entry students."
            )
            return

        dept_series_map = {
            "ME": "ATA03",
            "CE": "ATA01",
            "EEE": "ATA02",
            "ECE": "ATA04",
            "CSE": "ATA05",
            "CAI": "ATA31",
        }
        target_suffix = dept_series_map[dept_query]
        is_valid_regular = roll_query.startswith(f"25{target_suffix}")
        is_valid_lateral = (
            roll_query.startswith(f"26{target_suffix}") and "L" in roll_query
        )
        if not (is_valid_regular or is_valid_lateral):
            st.error(
                f"❌ Cross-Match Verification Failed! The roll number format does "
                f"not match the official series pattern for the {dept_query} branch."
            )
            return

        student_df = load_excel_data()
        if student_df is None:
            st.error(
                "🚨 Missing database resource file! Make sure 'students_list.xlsx' "
                "is in the project directory and has a 'CSE-TOTAL' sheet."
            )
            return

        existing_record = database.get_student_by_roll(roll_query)
        if existing_record:
            st.toast("Welcome back! Loading your security pass card configuration...")
            time.sleep(1)
            st.session_state.s_name = existing_record["name"]
            st.session_state.s_roll = existing_record["roll_no"]
            st.session_state.s_dept = existing_record["department"]
            st.session_state.s_id = existing_record["pass_id"]
            st.session_state.s_token = existing_record["qr_token"]
            st.session_state.s_meal = existing_record["meal"]
            photo_b64 = existing_record.get("photo_b64")
            st.session_state.s_photo = (
                base64.b64decode(photo_b64) if photo_b64 else None
            )
            st.session_state.s_downloaded = True
            st.session_state.s_registered = True
            st.session_state.step = "ticket"
            st.rerun()
            return

        matched_row = student_df[student_df["Roll Number"] == roll_query]
        if matched_row.empty:
            st.error(
                "❌ Identity Record Not Found in Excel! Check your roll number or "
                "contact your department coordinator."
            )
            return

        status = str(matched_row["Payment Status"].values[0]).lower().strip()
        if status != "paid":
            st.error(
                "🚫 Access Denied! Our records show your Freshers contribution "
                "payment status is unpaid. Please complete payment with your coordinator."
            )
            return

        st.session_state.s_name = str(
            matched_row["Name of the Student"].values[0]
        ).strip()
        st.session_state.s_roll = roll_query
        st.session_state.s_dept = dept_query
        entry_type = "LE" if "L" in roll_query else "25"
        st.session_state.s_id = (
            f"GPCET-{entry_type}-{str(uuid.uuid4()).upper()[-4:]}"
        )
        st.session_state.s_token = database.generate_secure_token()
        st.session_state.s_photo = None
        st.session_state.s_meal = ""
        st.session_state.s_downloaded = False
        st.session_state.s_registered = False
        st.balloons()
        st.snow()
        st.success(
            f"🎉 Payment Verified! Welcome {st.session_state.s_name}. "
            "Opening selfie gate..."
        )
        time.sleep(1.2)
        st.session_state.step = "security"
        st.rerun()


def render_security_step():
    st.markdown("<h1>📸 IDENTITY HUB & MEAL TOKEN 🍽️</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subtitle'>Secure your verified entry photo pass and select your catering coupon preference</p>",
        unsafe_allow_html=True,
    )
    st.write(
        f"🎨 Attendee Name: {st.session_state.s_name} | "
        f"Branch: {st.session_state.s_dept}"
    )
    st.divider()

    col_left, col_right = st.columns(2)
    with col_left:
        st.write("### 📸 Security Profile Snapshot")
        st.warning(
            "🔒 MANDATORY SECURITY PHOTOGRAPH: Capture a live selfie or upload "
            "a portrait face photograph."
        )
        capture_style = st.radio(
            "Select Capture Feed Source:",
            ["Activate Live Web-Cam 📷", "Upload File Attachment 📁"],
        )
        if capture_style == "Activate Live Web-Cam 📷":
            photo_bytes = st.camera_input("Snap official gate matching profile snapshot:")
        else:
            photo_bytes = st.file_uploader(
                "Select Profile Image Asset (JPG/PNG)", type=["jpg", "jpeg", "png"]
            )

    with col_right:
        st.write("### 🍱 Freshers Catering Token Selection")
        st.info(
            "💡 Select your food coupon class. Only one option can be chosen per pass."
        )
        meal_choice = st.radio(
            "Choose your Dinner Box Preference 👇",
            [
                "Select Meal Type 🍽️",
                "🟢 Pure Vegetarian Box (Veg)",
                "🔴 Traditional Non-Vegetarian Box (Non-Veg)",
            ],
            index=0,
        )

    st.divider()
    if st.button("Generate My Dynamic Cyber Ticket Pass 🎫", use_container_width=True):
        if photo_bytes is None:
            st.error("❌ Profile photo is required to generate your pass.")
        elif meal_choice == "Select Meal Type 🍽️":
            st.error("❌ Dinner option selection is mandatory. Please choose a meal.")
        else:
            st.session_state.s_meal = (
                "VEGETARIAN 🟢"
                if "Vegetarian" in meal_choice
                else "NON-VEGETARIAN 🔴"
            )
            st.session_state.s_photo = photo_bytes.getvalue()
            st.session_state.step = "ticket"
            st.rerun()


def render_ticket_step():
    if not st.session_state.s_name or not st.session_state.s_token:
        st.warning("Your session is incomplete. Please start registration again.")
        if st.button("Return to Registration"):
            st.session_state.step = "login"
            st.rerun()
        return

    st.markdown("<h1>🌌 YOUR DOCKING INVITATION PASS</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subtitle'>Your secure horizontal cyber neon ticket pass is ready</p>",
        unsafe_allow_html=True,
    )

    website_base_url = f"http://{admin_server.HOST_IP}:8000"
    qr_link_url = f"{website_base_url}/admin/checkin?token={st.session_state.s_token}"
    qr_engine = qrcode.QRCode(version=1, box_size=3, border=1)
    qr_engine.add_data(qr_link_url)
    qr_engine.make(fit=True)
    qr_img = qr_engine.make_image(
        fill_color="black", back_color="white"
    ).convert("RGB").resize((175, 175))

    img_b64 = get_image_base64(st.session_state.s_photo)

    img_card = Image.new("RGB", (1050, 480), color="#060212")
    draw = ImageDraw.Draw(img_card)
    for radius in range(750, 0, -5):
        color_val = int(20 * (1 - radius / 750))
        draw.ellipse(
            [(525 - radius, 240 - radius), (525 + radius, 240 + radius)],
            fill=(15 + color_val, 8 + color_val // 2, 35 + color_val),
        )
    draw.rectangle([(20, 20), (1030, 460)], outline="#00ffff", width=4)
    draw.rectangle([(23, 23), (1027, 457)], outline="#122240", width=2)
    draw.rectangle([(20, 95), (1030, 100)], fill="#ff007f")

    try:
        font_header = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 20)
        font_name = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 28)
        font_body_bd = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 18)
        font_body = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 18)
        font_footer = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 15)
    except OSError:
        font_header = font_name = font_body_bd = font_body = font_footer = (
            ImageFont.load_default()
        )

    draw.text((40, 42), "G. PULLAIAH COLLEGE OF ENGG & TECH", fill="#ffffff", font=font_header)
    draw.text((850, 42), "PAID ENTRY", fill="#ff007f", font=font_header)
    draw.text((50, 145), "ATTENDEE :", fill="#00ffff", font=font_body_bd)
    draw.text((170, 140), st.session_state.s_name.upper(), fill="#00ffff", font=font_name)
    draw.text((50, 205), "ROLL NO  :", fill="#ffffff", font=font_body_bd)
    draw.text((170, 205), st.session_state.s_roll, fill="#ffffff", font=font_body)
    draw.text((50, 265), "BRANCH   :", fill="#ffffff", font=font_body_bd)
    draw.text(
        (170, 265), f"{st.session_state.s_dept} (2nd Year)",
        fill="#ffffff", font=font_body
    )
    draw.text((50, 325), "MEAL COU :", fill="#ffffff", font=font_body_bd)
    if "VEGETARIAN" in st.session_state.s_meal:
        draw.text((170, 325), "VEGETARIAN", fill="#fffb00", font=font_body_bd)
        draw.ellipse([(295, 328), (312, 345)], fill="#00ff00", outline="#ffffff", width=2)
    else:
        draw.text((170, 325), "NON-VEGETARIAN", fill="#fffb00", font=font_body_bd)
        draw.ellipse([(340, 328), (357, 345)], fill="#ff0000", outline="#ffffff", width=2)

    draw.text(
        (40, 422), "Date: 15th Oct 2026 | Venue: G. Pullaiah College (Auditorium)",
        fill="#ffffff", font=font_footer
    )
    draw.text(
        (790, 422), f"PASS ID: {st.session_state.s_id}",
        fill="#ff007f", font=font_footer
    )

    if st.session_state.s_photo:
        try:
            profile = Image.open(io.BytesIO(st.session_state.s_photo)).convert("RGB")
            profile = profile.resize((175, 215))
            img_card.paste(profile, (630, 140))
            draw.rectangle([(628, 138), (807, 357)], outline="#ff007f", width=4)
        except Exception:
            st.warning("Could not place the uploaded profile photo on the ticket.")

    img_card.paste(qr_img.resize((175, 215)), (825, 140))
    draw.rectangle([(823, 138), (1002, 357)], outline="#00ffff", width=4)

    byte_arr = io.BytesIO()
    img_card.save(byte_arr, format="PNG")
    png_bytes = byte_arr.getvalue()

    st.image(png_bytes, caption="Your Freshers Entry Pass", use_container_width=True)
    st.write("### 📥 Step 3: Secure Your Entry Image File")
    st.warning(
        "Download your PNG ticket pass and show it at the auditorium gates."
    )
    st.download_button(
        label="📥 DOWNLOAD CYBER PASS TICKET IMAGE (PNG) 📸",
        data=png_bytes,
        file_name=f"{st.session_state.s_roll}_Freshers_Pass.png",
        mime="image/png",
        use_container_width=True,
    )

    # Persist the pass once per registration session, not on every Streamlit rerun.
    if not st.session_state.s_registered:
        reg_res = database.register_student(
            name=st.session_state.s_name,
            roll_no=st.session_state.s_roll,
            department=st.session_state.s_dept,
            pass_id=st.session_state.s_id,
            qr_token=st.session_state.s_token,
            meal=st.session_state.s_meal,
            photo_b64=img_b64 if img_b64 else None,
        )
        if reg_res.get("success"):
            st.session_state.s_registered = True
            st.toast("Pass claimed and secured to official database! 🎫")
        else:
            st.error(reg_res.get("error", "Could not save the pass to the database."))
            return

    st.success(
        f"🎉 REGISTRATION SECURED! Welcome to the roster, "
        f"{st.session_state.s_name.upper()}! Show your downloaded pass at the gates."
    )
    st.write("")
    if st.button("Logout & Register Another Student 🚪", type="secondary", use_container_width=True):
        for key, value in {
            "step": "login",
            "s_downloaded": False,
            "s_registered": False,
            "s_name": "",
            "s_roll": "",
            "s_dept": "",
            "s_id": "",
            "s_token": "",
            "s_photo": None,
            "s_meal": "",
        }.items():
            st.session_state[key] = value
        st.rerun()


def main():
    init_session_state()

    query_params = st.query_params
    if "verify" in query_params or "token" in query_params:
        render_qr_checkin()

    is_admin_query = (
        ("page" in query_params and query_params.get("page") == "admin")
        or ("admin" in query_params)
    )
    default_nav_idx = 1 if is_admin_query else 0

    st.sidebar.markdown("### 🌌 GPCET NAVIGATION")
    portal_mode = st.sidebar.radio(
        "Choose Active Portal:",
        ["🎓 Student Invitation Pass", "🔐 Admin Gate Control"],
        index=default_nav_idx,
    )

    if portal_mode == "🔐 Admin Gate Control":
        render_admin_dashboard()
    elif st.session_state.step == "login":
        render_student_login()
    elif st.session_state.step == "security":
        render_security_step()
    elif st.session_state.step == "ticket":
        render_ticket_step()
    else:
        st.session_state.step = "login"
        st.rerun()


if __name__ == "__main__":
    main()
