import os
import json
import socket
import threading
from starlette.applications import Starlette
from starlette.responses import JSONResponse, HTMLResponse, Response
from starlette.routing import Route
import uvicorn
import database

# Determine local IP for Wi-Fi display
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    HOST_IP = s.getsockname()[0]
    s.close()
except Exception:
    HOST_IP = "localhost"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>GPCET Midnight Cyber - Freshers Entry Control 🎫</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="/html5-qrcode.min.js"></script>
    <style>
        :root {
            --bg-dark: #060212;
            --bg-card: rgba(18, 9, 36, 0.85);
            --neon-pink: #ff007f;
            --neon-cyan: #00ffff;
            --neon-purple: #7928ca;
            --neon-green: #00ff88;
            --neon-red: #ff0055;
            --text-main: #ffffff;
            --text-muted: rgba(255, 255, 255, 0.7);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            background-color: var(--bg-dark);
            background: radial-gradient(circle at 50% 10%, #1a0a38 0%, #060212 90%);
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
            padding-bottom: 60px;
        }

        /* Glassmorphism containers */
        .glass-panel {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 0, 127, 0.3);
            border-radius: 18px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 0 15px rgba(0, 255, 255, 0.05);
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px 16px;
        }

        /* Header section */
        header {
            text-align: center;
            margin-bottom: 25px;
            position: relative;
        }

        .title-badge {
            display: inline-block;
            background: linear-gradient(90deg, var(--neon-pink), var(--neon-purple));
            color: #fff;
            padding: 4px 14px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
            text-transform: uppercase;
            box-shadow: 0 0 15px rgba(255, 0, 127, 0.5);
            margin-bottom: 8px;
        }

        h1 {
            font-size: clamp(22px, 5vw, 32px);
            font-weight: 900;
            letter-spacing: 1px;
            text-transform: uppercase;
            background: linear-gradient(135deg, #ffffff 0%, var(--neon-cyan) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
            margin-bottom: 6px;
        }

        .subtitle {
            font-family: 'JetBrains Mono', monospace;
            color: var(--neon-cyan);
            font-size: 13px;
            text-shadow: 0 0 8px rgba(0, 255, 255, 0.4);
        }

        .logout-btn {
            position: absolute;
            right: 0;
            top: 0;
            background: rgba(255, 0, 85, 0.2);
            border: 1px solid var(--neon-red);
            color: #fff;
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 12px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }

        .logout-btn:hover {
            background: var(--neon-red);
            box-shadow: 0 0 15px var(--neon-red);
        }

        /* Metrics grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 25px;
        }

        .metric-card {
            padding: 16px 12px;
            text-align: center;
            border-radius: 14px;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s;
        }

        .metric-card:hover {
            transform: translateY(-2px);
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
        }

        .card-reg::before { background: var(--neon-cyan); }
        .card-in::before { background: var(--neon-green); }
        .card-rem::before { background: #ffaa00; }
        .card-dup::before { background: var(--neon-red); }
        .card-veg::before { background: #00ff88; }
        .card-nveg::before { background: #ff5555; }

        .metric-val {
            font-size: clamp(24px, 4vw, 32px);
            font-weight: 900;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 4px;
        }

        .metric-lbl {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 700;
            color: var(--text-muted);
        }

        /* Scanner Frame */
        .scanner-card {
            padding: 22px;
            border: 2px solid var(--neon-pink);
            box-shadow: 0 0 30px rgba(255, 0, 127, 0.25);
            margin-bottom: 25px;
        }

        .scanner-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 16px;
        }

        .scanner-title {
            font-size: 18px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #ffffff;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(0, 255, 136, 0.15);
            border: 1px solid var(--neon-green);
            color: var(--neon-green);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            animation: pulse-border 2s infinite;
        }

        @keyframes pulse-border {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.4); }
            70% { box-shadow: 0 0 0 8px rgba(0, 255, 136, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0); }
        }

        #reader-container {
            position: relative;
            width: 100%;
            max-width: 500px;
            margin: 0 auto;
            border-radius: 16px;
            overflow: hidden;
            background: #000;
            border: 2px solid rgba(0, 255, 255, 0.5);
            box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 255, 255, 0.2);
            aspect-ratio: 4/3;
        }

        #reader {
            width: 100% !important;
            height: 100% !important;
        }

        #reader video {
            object-fit: cover !important;
            width: 100% !important;
            height: 100% !important;
            border-radius: 14px;
        }

        /* Cyber viewfinder brackets */
        .reticle {
            position: absolute;
            inset: 20px;
            pointer-events: none;
            border: 2px dashed rgba(0, 255, 255, 0.4);
            border-radius: 12px;
            z-index: 10;
        }

        .reticle-corner {
            position: absolute;
            width: 20px;
            height: 20px;
            border: 3px solid var(--neon-pink);
        }
        .rc-tl { top: -2px; left: -2px; border-right: none; border-bottom: none; }
        .rc-tr { top: -2px; right: -2px; border-left: none; border-bottom: none; }
        .rc-bl { bottom: -2px; left: -2px; border-right: none; border-top: none; }
        .rc-br { bottom: -2px; right: -2px; border-left: none; border-top: none; }

        .scan-laser {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--neon-pink), var(--neon-cyan), transparent);
            box-shadow: 0 0 10px var(--neon-pink);
            animation: scan-beam 2.2s ease-in-out infinite;
            z-index: 12;
            pointer-events: none;
        }

        @keyframes scan-beam {
            0% { top: 10%; opacity: 0; }
            30% { opacity: 1; }
            70% { opacity: 1; }
            100% { top: 90%; opacity: 0; }
        }

        .scanner-controls {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 15px;
            flex-wrap: wrap;
        }

        select, input[type="text"], input[type="password"] {
            background: #090414;
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #ffffff;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: all 0.2s;
        }

        select:focus, input:focus {
            border-color: var(--neon-cyan);
            box-shadow: 0 0 12px rgba(0, 255, 255, 0.4);
        }

        .btn {
            background: linear-gradient(90deg, var(--neon-pink) 0%, var(--neon-purple) 100%);
            color: #fff;
            border: none;
            border-radius: 10px;
            padding: 10px 18px;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.5px;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 15px rgba(255, 0, 127, 0.4);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--neon-cyan);
            color: var(--neon-cyan);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            box-shadow: none;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
        }

        /* Manual Fallback */
        .manual-box {
            margin-top: 20px;
            padding-top: 18px;
            border-top: 1px dashed rgba(255, 255, 255, 0.15);
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
        }

        .manual-box input {
            flex: 1;
            min-width: 220px;
            max-width: 380px;
            text-transform: uppercase;
        }

        /* Result Modal Overlay */
        .result-overlay {
            position: fixed;
            inset: 0;
            background: rgba(6, 2, 18, 0.92);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 20px;
            animation: fadeIn 0.2s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.96); }
            to { opacity: 1; transform: scale(1); }
        }

        .result-card {
            width: 100%;
            max-width: 480px;
            border-radius: 20px;
            padding: 30px 24px;
            text-align: center;
            position: relative;
            box-shadow: 0 0 50px rgba(0, 0, 0, 0.9);
        }

        .res-approved {
            border: 3px solid var(--neon-green);
            background: radial-gradient(circle at center, #0a2618 0%, #08120e 100%);
            box-shadow: 0 0 45px rgba(0, 255, 136, 0.4);
        }

        .res-duplicate {
            border: 3px solid var(--neon-red);
            background: radial-gradient(circle at center, #2e0814 0%, #14050a 100%);
            box-shadow: 0 0 45px rgba(255, 0, 85, 0.4);
        }

        .res-invalid {
            border: 3px solid #ffaa00;
            background: radial-gradient(circle at center, #2b1d06 0%, #140d04 100%);
            box-shadow: 0 0 45px rgba(255, 170, 0, 0.4);
        }

        .res-badge {
            display: inline-block;
            font-size: clamp(20px, 4.5vw, 28px);
            font-weight: 900;
            letter-spacing: 1.5px;
            margin-bottom: 15px;
            text-transform: uppercase;
        }

        .res-approved .res-badge { color: var(--neon-green); text-shadow: 0 0 15px var(--neon-green); }
        .res-duplicate .res-badge { color: var(--neon-red); text-shadow: 0 0 15px var(--neon-red); }
        .res-invalid .res-badge { color: #ffaa00; text-shadow: 0 0 15px #ffaa00; }

        .student-photo {
            width: 120px;
            height: 140px;
            object-fit: cover;
            border-radius: 12px;
            margin: 0 auto 15px;
            display: block;
            border: 2px solid var(--neon-pink);
            box-shadow: 0 0 15px rgba(255, 0, 127, 0.4);
        }

        .student-name {
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .info-pill-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin: 15px 0;
            text-align: left;
        }

        .info-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 13px;
        }

        .info-label {
            font-size: 10px;
            color: var(--neon-cyan);
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 1px;
            margin-bottom: 2px;
        }

        .info-val {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            color: #ffffff;
        }

        .auto-dismiss-bar {
            height: 4px;
            width: 100%;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 15px;
        }

        .auto-dismiss-fill {
            height: 100%;
            width: 100%;
            background: currentColor;
            transform-origin: left;
            animation: shrink linear forwards;
        }

        @keyframes shrink {
            from { transform: scaleX(1); }
            to { transform: scaleX(0); }
        }

        /* Tabs / Sections */
        .section-panel {
            padding: 20px;
            margin-bottom: 25px;
        }

        .section-title {
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: var(--neon-cyan);
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Logs table */
        .table-responsive {
            width: 100%;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        th {
            background: rgba(255, 255, 255, 0.05);
            color: var(--neon-cyan);
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        tr:hover {
            background: rgba(255, 255, 255, 0.02);
        }

        .badge-approved {
            color: var(--neon-green);
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid var(--neon-green);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 700;
            display: inline-block;
        }

        .badge-duplicate {
            color: var(--neon-red);
            background: rgba(255, 0, 85, 0.1);
            border: 1px solid var(--neon-red);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 700;
            display: inline-block;
        }

        .badge-invalid {
            color: #ffaa00;
            background: rgba(255, 170, 0, 0.1);
            border: 1px solid #ffaa00;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 700;
            display: inline-block;
        }

        /* Login Modal / Gate */
        #login-modal {
            position: fixed;
            inset: 0;
            background: #060212;
            z-index: 2000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .login-box {
            width: 100%;
            max-width: 400px;
            padding: 35px 28px;
            text-align: center;
            border: 2px solid var(--neon-pink);
            box-shadow: 0 0 40px rgba(255, 0, 127, 0.35);
        }

        .login-box h2 {
            font-size: 24px;
            font-weight: 900;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .login-field {
            margin-bottom: 16px;
            text-align: left;
        }

        .login-field label {
            display: block;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: var(--neon-cyan);
            margin-bottom: 6px;
        }

        .login-field input {
            width: 100%;
        }

        .login-err {
            color: var(--neon-red);
            font-size: 13px;
            margin-top: 10px;
            display: none;
        }
    </style>
</head>
<body>

    <!-- ADMIN LOGIN MODAL -->
    <div id="login-modal">
        <div class="glass-panel login-box">
            <span class="title-badge">RESTRICTED PORTAL</span>
            <h2>ADMIN AUTHENTICATION</h2>
            <p class="subtitle" style="margin-bottom: 25px;">Enter credentials to unlock Entry Control</p>
            
            <form id="login-form" onsubmit="handleLogin(event)">
                <div class="login-field">
                    <label>ADMIN USERNAME</label>
                    <input type="text" id="admin-user" placeholder="admin" required autocomplete="username">
                </div>
                <div class="login-field">
                    <label>ADMIN PASSWORD</label>
                    <input type="password" id="admin-pass" placeholder="••••••••" required autocomplete="current-password">
                </div>
                <button type="submit" class="btn" style="width: 100%; margin-top: 10px;">UNLOCK ENTRY SCANNER 🚀</button>
                <div id="login-error" class="login-err">❌ Invalid credentials. Please try again.</div>
            </form>
        </div>
    </div>

    <!-- MAIN DASHBOARD CONTENT -->
    <div class="container" id="main-content" style="display: none;">
        <header>
            <span class="title-badge">GPCET FRESHERS 2026</span>
            <h1>🎫 FRESHERS ENTRY CONTROL</h1>
            <p class="subtitle">Live High-Speed Gate Scanning & Audit Dashboard</p>
            <button class="logout-btn" onclick="handleLogout()">Logout 🚪</button>
        </header>

        <!-- LIVE METRICS -->
        <div class="metrics-grid">
            <div class="glass-panel metric-card card-reg">
                <div class="metric-val" id="stat-registered">0</div>
                <div class="metric-lbl">👥 Registered</div>
            </div>
            <div class="glass-panel metric-card card-in">
                <div class="metric-val" style="color: var(--neon-green);" id="stat-checked">0</div>
                <div class="metric-lbl">✅ Checked In</div>
            </div>
            <div class="glass-panel metric-card card-rem">
                <div class="metric-val" style="color: #ffaa00;" id="stat-remaining">0</div>
                <div class="metric-lbl">⏳ Remaining</div>
            </div>
            <div class="glass-panel metric-card card-dup">
                <div class="metric-val" style="color: var(--neon-red);" id="stat-dupes">0</div>
                <div class="metric-lbl">🚫 Duplicate Scans</div>
            </div>
            <div class="glass-panel metric-card card-veg">
                <div class="metric-val" style="color: #00ff88;" id="stat-veg">0</div>
                <div class="metric-lbl">🟢 Veg Boxes</div>
            </div>
            <div class="glass-panel metric-card card-nveg">
                <div class="metric-val" style="color: #ff5555;" id="stat-nonveg">0</div>
                <div class="metric-lbl">🔴 Non-Veg Boxes</div>
            </div>
        </div>

        <!-- QR SCANNER INTERFACE -->
        <div class="glass-panel scanner-card">
            <div class="scanner-header">
                <div class="scanner-title">
                    <span>📷</span> SCANNER CAMERA FEED
                </div>
                <div class="status-pill" id="scanner-status">
                    <span>●</span> SCANNER READY
                </div>
            </div>

            <!-- CAMERA BOX -->
            <div id="reader-container">
                <div class="reticle">
                    <div class="reticle-corner rc-tl"></div>
                    <div class="reticle-corner rc-tr"></div>
                    <div class="reticle-corner rc-bl"></div>
                    <div class="reticle-corner rc-br"></div>
                </div>
                <div class="scan-laser" id="laser-beam"></div>
                <div id="reader"></div>
            </div>

            <div class="scanner-controls">
                <select id="camera-select" onchange="onCameraChange()">
                    <option value="">Detecting Cameras...</option>
                </select>
                <button class="btn btn-secondary" id="btn-toggle-camera" onclick="toggleCamera()">Stop Camera ⏸️</button>
            </div>

            <!-- MANUAL ENTRY FALLBACK -->
            <div class="manual-box">
                <input type="text" id="manual-input" placeholder="ENTER PASS ID OR ROLL NO (e.g. 25ATA0501)" onkeypress="if(event.key==='Enter') submitManualVerify()">
                <button class="btn" onclick="submitManualVerify()">VERIFY PASS 🔍</button>
            </div>
        </div>

        <!-- SEARCH STUDENT TOOL -->
        <div class="glass-panel section-panel">
            <div class="section-title">🔍 QUICK STUDENT SEARCH & VERIFICATION LOOKUP</div>
            <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                <input type="text" id="search-input" placeholder="Search by Roll No, Student Name, or Pass Serial..." style="flex: 1;" oninput="handleSearch()">
            </div>
            <div id="search-results" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px;"></div>
        </div>

        <!-- REVERSE CHECK-IN OVERRIDE (PROTECTED) -->
        <div class="glass-panel section-panel">
            <div class="section-title" style="color: #ffaa00;">⚠️ PROTECTED ACTION: REVERSE CHECK-IN</div>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">
                Organizers only. Reverse an accidental check-in and re-activate the student's entry pass. Requires admin password and documented reason.
            </p>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <input type="text" id="rev-target" placeholder="Student Roll No / Pass ID" style="min-width: 180px; flex: 1;">
                <input type="text" id="rev-reason" placeholder="Reason for reversal (mandatory)" style="min-width: 200px; flex: 1.5;">
                <input type="password" id="rev-pass" placeholder="Admin Password" style="min-width: 140px; flex: 1;">
                <button class="btn" style="background: linear-gradient(90deg, #ffaa00, #ff5500);" onclick="submitReversal()">CONFIRM REVERSAL 🔄</button>
            </div>
            <div id="rev-msg" style="margin-top: 8px; font-size: 13px;"></div>
        </div>

        <!-- RECENT AUDIT LOG TABLE -->
        <div class="glass-panel section-panel">
            <div class="section-title">📋 RECENT CHECK-IN & SCAN LOG (LIVE AUDIT)</div>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Student</th>
                            <th>Roll Number</th>
                            <th>Dept</th>
                            <th>Meal</th>
                            <th>Type</th>
                            <th>Status</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody id="audit-table-body">
                        <tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No scan logs recorded yet.</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- RESULT MODAL POPUP -->
    <div class="result-overlay" id="result-overlay">
        <div class="result-card" id="result-card">
            <div class="res-badge" id="res-badge">✅ ENTRY APPROVED</div>
            <img src="" id="res-photo" class="student-photo" style="display: none;" alt="Attendee Photo">
            <div class="student-name" id="res-name">RAHUL SHARMA</div>
            
            <div class="info-pill-grid" id="res-details">
                <div class="info-item">
                    <div class="info-label">Roll Number</div>
                    <div class="info-val" id="res-roll">25ATA0501</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Department</div>
                    <div class="info-val" id="res-dept">CSE</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Meal Ticket</div>
                    <div class="info-val" id="res-meal">VEGETARIAN 🟢</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Pass Serial</div>
                    <div class="info-val" id="res-id">GPCET-25-88A1</div>
                </div>
            </div>

            <div id="res-message" style="font-size: 14px; margin-top: 10px; font-weight: 600;"></div>
            <div id="res-time-meta" style="font-size: 12px; color: var(--text-muted); margin-top: 4px; font-family: 'JetBrains Mono', monospace;"></div>

            <div class="auto-dismiss-bar">
                <div class="auto-dismiss-fill" id="dismiss-bar"></div>
            </div>
        </div>
    </div>

    <script>
        // State variables
        let html5QrCode = null;
        let isScannerRunning = false;
        let isProcessing = false;
        let currentCameraId = null;
        let pollTimer = null;
        let authenticatedAdmin = null;

        // --- AUDIO SYNTHESIS ENGINE (Cyber Synth FX) ---
        function playSound(type) {
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (!AudioContext) return;
                const ctx = new AudioContext();

                if (type === 'APPROVED') {
                    // Uplifting dual chime (D5 -> A5)
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(587.33, ctx.currentTime);
                    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12);
                    gain.gain.setValueAtTime(0.3, ctx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
                    osc.start();
                    osc.stop(ctx.currentTime + 0.4);
                    if (navigator.vibrate) navigator.vibrate([100, 50, 100]);
                } else if (type === 'ALREADY_USED') {
                    // Heavy alert buzzer (200Hz -> 130Hz)
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(220, ctx.currentTime);
                    osc.frequency.setValueAtTime(140, ctx.currentTime + 0.15);
                    gain.gain.setValueAtTime(0.4, ctx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.45);
                    osc.start();
                    osc.stop(ctx.currentTime + 0.45);
                    if (navigator.vibrate) navigator.vibrate([350]);
                } else {
                    // Invalid generic buzzer
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.type = 'square';
                    osc.frequency.setValueAtTime(180, ctx.currentTime);
                    gain.gain.setValueAtTime(0.3, ctx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
                    osc.start();
                    osc.stop(ctx.currentTime + 0.3);
                    if (navigator.vibrate) navigator.vibrate([200]);
                }
            } catch(e) {
                console.error("Audio error:", e);
            }
        }

        // --- AUTHENTICATION ---
        async function handleLogin(e) {
            e.preventDefault();
            const u = document.getElementById("admin-user").value.trim();
            const p = document.getElementById("admin-pass").value.trim();
            const errEl = document.getElementById("login-error");
            
            try {
                const res = await fetch("/api/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username: u, password: p })
                });
                const data = await res.json();
                if (data.success) {
                    authenticatedAdmin = u;
                    sessionStorage.setItem("fsh_admin", u);
                    document.getElementById("login-modal").style.display = "none";
                    document.getElementById("main-content").style.display = "block";
                    errEl.style.display = "none";
                    initScanner();
                    fetchStats();
                    fetchLogs();
                    pollTimer = setInterval(() => { fetchStats(); fetchLogs(); }, 5000);
                } else {
                    errEl.style.display = "block";
                }
            } catch(err) {
                errEl.innerText = "Connection error. Ensure backend is running.";
                errEl.style.display = "block";
            }
        }

        function handleLogout() {
            sessionStorage.removeItem("fsh_admin");
            if (isScannerRunning && html5QrCode) {
                html5QrCode.stop().catch(()=>{});
            }
            if (pollTimer) clearInterval(pollTimer);
            window.location.reload();
        }

        // Check active session
        window.addEventListener("DOMContentLoaded", () => {
            const saved = sessionStorage.getItem("fsh_admin");
            if (saved) {
                authenticatedAdmin = saved;
                document.getElementById("login-modal").style.display = "none";
                document.getElementById("main-content").style.display = "block";
                initScanner();
                fetchStats();
                fetchLogs();
                pollTimer = setInterval(() => { fetchStats(); fetchLogs(); }, 5000);
            }
        });

        // --- QR SCANNER MANAGEMENT ---
        async function initScanner() {
            html5QrCode = new Html5Qrcode("reader");
            const selectEl = document.getElementById("camera-select");

            try {
                const devices = await Html5Qrcode.getCameras();
                selectEl.innerHTML = "";
                if (devices && devices.length) {
                    // Try to pick environment / back camera first
                    let preferred = devices[0].id;
                    devices.forEach((dev, idx) => {
                        const opt = document.createElement("option");
                        opt.value = dev.id;
                        opt.text = dev.label || `Camera ${idx + 1}`;
                        if (dev.label.toLowerCase().includes("back") || dev.label.toLowerCase().includes("environment")) {
                            preferred = dev.id;
                            opt.selected = true;
                        }
                        selectEl.appendChild(opt);
                    });
                    currentCameraId = preferred;
                    startCamera(currentCameraId);
                } else {
                    selectEl.innerHTML = "<option>No camera detected</option>";
                }
            } catch (err) {
                console.warn("Camera enum error:", err);
                // Fallback direct facingMode
                startCamera({ facingMode: "environment" });
            }
        }

        function startCamera(camConfig) {
            if (!html5QrCode) return;
            const config = {
                fps: 15,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.333333
            };

            html5QrCode.start(
                camConfig,
                config,
                onQrScanSuccess,
                (errorMessage) => { /* ignore per-frame decode misses */ }
            ).then(() => {
                isScannerRunning = true;
                document.getElementById("scanner-status").innerHTML = "<span>●</span> SCANNER READY";
                document.getElementById("scanner-status").style.color = "var(--neon-green)";
                document.getElementById("scanner-status").style.borderColor = "var(--neon-green)";
                document.getElementById("btn-toggle-camera").innerText = "Stop Camera ⏸️";
                document.getElementById("laser-beam").style.display = "block";
            }).catch(err => {
                console.error("Failed to start camera", err);
                document.getElementById("scanner-status").innerHTML = "<span>⚠️</span> CAMERA ERROR";
                document.getElementById("scanner-status").style.color = "var(--neon-red)";
            });
        }

        function toggleCamera() {
            if (!html5QrCode) return;
            if (isScannerRunning) {
                html5QrCode.stop().then(() => {
                    isScannerRunning = false;
                    document.getElementById("btn-toggle-camera").innerText = "Start Camera ▶️";
                    document.getElementById("scanner-status").innerHTML = "<span>○</span> PAUSED";
                    document.getElementById("scanner-status").style.color = "#ffaa00";
                    document.getElementById("laser-beam").style.display = "none";
                }).catch(e => console.error(e));
            } else {
                startCamera(currentCameraId || { facingMode: "environment" });
            }
        }

        function onCameraChange() {
            const selectEl = document.getElementById("camera-select");
            currentCameraId = selectEl.value;
            if (isScannerRunning && html5QrCode) {
                html5QrCode.stop().then(() => {
                    startCamera(currentCameraId);
                }).catch(()=>{});
            }
        }

        // --- SCAN PROCESSING (ATOMIC REST API CALL) ---
        async function onQrScanSuccess(decodedText) {
            if (isProcessing) return; // Prevent duplicate frame hammering
            isProcessing = true;

            document.getElementById("scanner-status").innerHTML = "<span>⚡</span> VERIFYING PASS...";
            document.getElementById("scanner-status").style.color = "var(--neon-cyan)";

            try {
                const res = await fetch("/api/checkin", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        token: decodedText,
                        admin_id: authenticatedAdmin || "Admin",
                        scan_type: "QR"
                    })
                });
                const result = await res.json();
                displayScanResult(result);
            } catch (err) {
                displayScanResult({
                    status: "INVALID",
                    message: "Network error connecting to verification backend."
                });
            }
        }

        async function submitManualVerify() {
            const input = document.getElementById("manual-input");
            const val = input.value.trim();
            if (!val) return;
            if (isProcessing) return;
            isProcessing = true;

            try {
                const res = await fetch("/api/checkin", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        token: val,
                        admin_id: authenticatedAdmin || "Admin",
                        scan_type: "MANUAL"
                    })
                });
                const result = await res.json();
                input.value = "";
                displayScanResult(result);
            } catch (err) {
                displayScanResult({
                    status: "INVALID",
                    message: "Network error during verification."
                });
            }
        }

        // --- RESULT PRESENTATION OVERLAY ---
        function displayScanResult(res) {
            playSound(res.status);
            
            const overlay = document.getElementById("result-overlay");
            const card = document.getElementById("result-card");
            const badge = document.getElementById("res-badge");
            const nameEl = document.getElementById("res-name");
            const rollEl = document.getElementById("res-roll");
            const deptEl = document.getElementById("res-dept");
            const mealEl = document.getElementById("res-meal");
            const idEl = document.getElementById("res-id");
            const photoEl = document.getElementById("res-photo");
            const msgEl = document.getElementById("res-message");
            const timeMetaEl = document.getElementById("res-time-meta");
            const dismissBar = document.getElementById("dismiss-bar");

            card.className = "result-card";

            let displayDuration = 2800; // 2.8 seconds as requested

            if (res.status === "APPROVED") {
                card.classList.add("res-approved");
                badge.innerText = "✅ ENTRY APPROVED";
                nameEl.innerText = (res.student_name || "").toUpperCase();
                rollEl.innerText = res.roll_no || "-";
                deptEl.innerText = res.department || "-";
                mealEl.innerText = res.meal || "-";
                idEl.innerText = res.pass_id || "-";
                msgEl.innerText = "🟢 CHECK-IN SUCCESSFUL";
                msgEl.style.color = "var(--neon-green)";
                timeMetaEl.innerText = `Checked in at: ${res.checkin_time || res.timestamp}`;

                if (res.photo_b64) {
                    photoEl.src = "data:image/jpeg;base64," + res.photo_b64;
                    photoEl.style.display = "block";
                } else {
                    photoEl.style.display = "none";
                }
                document.getElementById("res-details").style.display = "grid";

            } else if (res.status === "ALREADY_USED") {
                card.classList.add("res-duplicate");
                badge.innerText = "🚫 ENTRY ALREADY USED";
                nameEl.innerText = (res.student_name || "").toUpperCase();
                rollEl.innerText = res.roll_no || "-";
                deptEl.innerText = res.department || "-";
                mealEl.innerText = res.meal || "-";
                idEl.innerText = res.pass_id || "-";
                msgEl.innerText = "⚠️ This invitation has already been used.";
                msgEl.style.color = "var(--neon-red)";
                timeMetaEl.innerText = `First checked in: ${res.first_checkin || 'Earlier'}`;
                photoEl.style.display = "none";
                document.getElementById("res-details").style.display = "grid";

            } else {
                // INVALID
                card.classList.add("res-invalid");
                badge.innerText = "❌ INVALID INVITATION";
                nameEl.innerText = "ACCESS REJECTED";
                msgEl.innerText = "QR code not recognized.";
                msgEl.style.color = "#ffaa00";
                timeMetaEl.innerText = `Attempt logged at: ${res.timestamp || ''}`;
                photoEl.style.display = "none";
                document.getElementById("res-details").style.display = "none";
                displayDuration = 2500;
            }

            // Animate progress bar
            dismissBar.style.animation = `shrink ${displayDuration}ms linear forwards`;
            overlay.style.display = "flex";

            // Trigger immediate dashboard sync
            fetchStats();
            fetchLogs();

            // Automatically return to scanner
            setTimeout(() => {
                overlay.style.display = "none";
                document.getElementById("scanner-status").innerHTML = "<span>●</span> SCANNER READY";
                document.getElementById("scanner-status").style.color = "var(--neon-green)";
                isProcessing = false;
            }, displayDuration);
        }

        // --- DASHBOARD DATA SYNC ---
        async function fetchStats() {
            try {
                const res = await fetch("/api/stats");
                const d = await res.json();
                document.getElementById("stat-registered").innerText = d.total_registered || 0;
                document.getElementById("stat-checked").innerText = d.total_checked_in || 0;
                document.getElementById("stat-remaining").innerText = d.remaining || 0;
                document.getElementById("stat-dupes").innerText = d.duplicate_attempts || 0;
                document.getElementById("stat-veg").innerText = d.veg_checked_in || 0;
                document.getElementById("stat-nonveg").innerText = d.nonveg_checked_in || 0;
            } catch(e) {}
        }

        async function fetchLogs() {
            try {
                const res = await fetch("/api/logs");
                const logs = await res.json();
                const tbody = document.getElementById("audit-table-body");
                if (!logs || !logs.length) {
                    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No scan logs recorded yet.</td></tr>`;
                    return;
                }
                tbody.innerHTML = logs.map(l => {
                    let badgeClass = "badge-approved";
                    if (l.result === "ALREADY_USED") badgeClass = "badge-duplicate";
                    else if (l.result === "INVALID") badgeClass = "badge-invalid";

                    return `
                        <tr>
                            <td style="font-family:'JetBrains Mono';">${l.scan_timestamp || '-'}</td>
                            <td style="font-weight:700;">${l.student_name || 'Anonymous / Unknown'}</td>
                            <td style="font-family:'JetBrains Mono';">${l.roll_no || '-'}</td>
                            <td>${l.department || '-'}</td>
                            <td>${l.meal || '-'}</td>
                            <td style="font-size:11px; font-weight:700;">${l.scan_type || 'QR'}</td>
                            <td><span class="${badgeClass}">${l.result}</span></td>
                            <td style="font-size:11px; color:var(--text-muted);">${l.notes || '-'}</td>
                        </tr>
                    `;
                }).join("");
            } catch(e) {}
        }

        // --- SEARCH ENGINE ---
        let searchTimeout = null;
        function handleSearch() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(async () => {
                const query = document.getElementById("search-input").value.trim();
                const container = document.getElementById("search-results");
                if (!query) {
                    container.innerHTML = "";
                    return;
                }
                try {
                    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                    const list = await res.json();
                    if (!list.length) {
                        container.innerHTML = `<div style="color:var(--text-muted); padding:10px;">No students matching "${query}"</div>`;
                        return;
                    }
                    container.innerHTML = list.map(s => {
                        const isChecked = s.checked_in === 1;
                        const statusPill = isChecked 
                            ? `<span style="color:var(--neon-red); font-weight:800;">🔴 CHECKED IN (${s.checkin_time})</span>`
                            : `<span style="color:var(--neon-green); font-weight:800;">🟢 NOT CHECKED IN</span>`;
                        return `
                            <div class="glass-panel" style="padding: 12px; border: 1px solid rgba(255,255,255,0.15); border-radius: 10px;">
                                <div style="font-size:16px; font-weight:800;">${s.name.toUpperCase()}</div>
                                <div style="font-family:'JetBrains Mono'; font-size:13px; color:var(--neon-cyan);">🎟️ ${s.roll_no} | ${s.department}</div>
                                <div style="font-size:12px; margin: 4px 0;">🍱 ${s.meal}</div>
                                <div style="font-size:11px; margin-top:6px;">Status: ${statusPill}</div>
                            </div>
                        `;
                    }).join("");
                } catch(e) {}
            }, 300);
        }

        // --- PROTECTED REVERSAL SUBMIT ---
        async function submitReversal() {
            const target = document.getElementById("rev-target").value.trim();
            const reason = document.getElementById("rev-reason").value.trim();
            const pass = document.getElementById("rev-pass").value.trim();
            const msgEl = document.getElementById("rev-msg");

            if (!target || !reason || !pass) {
                msgEl.style.color = "var(--neon-red)";
                msgEl.innerText = "❌ Please complete all three reversal fields.";
                return;
            }

            try {
                const res = await fetch("/api/reverse-checkin", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        identifier: target,
                        reason: reason,
                        admin_username: authenticatedAdmin || "admin",
                        admin_password: pass
                    })
                });
                const d = await res.json();
                if (d.success) {
                    msgEl.style.color = "var(--neon-green)";
                    msgEl.innerText = "✅ " + d.message;
                    document.getElementById("rev-target").value = "";
                    document.getElementById("rev-reason").value = "";
                    document.getElementById("rev-pass").value = "";
                    fetchStats();
                    fetchLogs();
                } else {
                    msgEl.style.color = "var(--neon-red)";
                    msgEl.innerText = "❌ " + d.error;
                }
            } catch(e) {
                msgEl.style.color = "var(--neon-red)";
                msgEl.innerText = "❌ Network connection error.";
            }
        }
    </script>
</body>
</html>
"""

async def admin_page(request):
    return HTMLResponse(HTML_TEMPLATE)

async def checkin_landing_page(request):
    # When scanned via camera phone browser: /admin/checkin?token=XYZ
    token = request.query_params.get("token", "")
    if token:
        # Checkin directly or present verification status
        result = database.verify_and_checkin(token, admin_id="Direct-QR-Scan", scan_type="QR")
        status_color = "#00ff88" if result["status"] == "APPROVED" else ("#ff0055" if result["status"] == "ALREADY_USED" else "#ffaa00")
        msg = result["message"]
        student_info = ""
        if "student_name" in result:
            student_info = f"""
                <div style="margin-top:20px; font-size:18px; color:#fff; font-weight:bold;">{result['student_name']}</div>
                <div style="color:#00ffff; font-family:monospace; margin-top:5px;">Roll No: {result.get('roll_no', '')} | Dept: {result.get('department', '')}</div>
                <div style="color:#fffb00; margin-top:5px;">Meal Ticket: {result.get('meal', '')}</div>
            """
        html = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Freshers Gate Verification</title>
            <style>
                body {{ background: #060212; color: #fff; font-family: sans-serif; display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; padding:20px; box-sizing:border-box; text-align:center; }}
                .card {{ background: rgba(18,9,36,0.9); border: 2px solid {status_color}; border-radius: 20px; padding: 35px 25px; max-width: 450px; width:100%; box-shadow: 0 0 35px {status_color}; }}
                h1 {{ color: {status_color}; font-size: 26px; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>{result['status'].replace('_', ' ')}</h1>
                <p style="font-size:16px;">{msg}</p>
                {student_info}
                <div style="margin-top:25px; font-size:12px; color:rgba(255,255,255,0.6);">Official GPCET Midnight Cyber Entry System</div>
            </div>
        </body>
        </html>"""
        return HTMLResponse(html)
    return HTMLResponse(HTML_TEMPLATE)

async def serve_qr_script(request):
    js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html5-qrcode.min.js")
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            return Response(f.read(), media_type="application/javascript")
    return Response("// html5-qrcode fallback", media_type="application/javascript")

# --- API HANDLERS ---
async def api_login(request):
    try:
        body = await request.json()
        u = body.get("username", "")
        p = body.get("password", "")
        if database.verify_admin_login(u, p):
            return JSONResponse({"success": True, "username": u})
        return JSONResponse({"success": False, "error": "Invalid username or password"}, status_code=401)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

async def api_checkin(request):
    try:
        body = await request.json()
        token = body.get("token", "")
        admin_id = body.get("admin_id", "Admin")
        scan_type = body.get("scan_type", "QR")
        res = database.verify_and_checkin(token, admin_id=admin_id, scan_type=scan_type)
        return JSONResponse(res)
    except Exception as e:
        return JSONResponse({"status": "INVALID", "message": f"Server error: {str(e)}"}, status_code=500)

async def api_stats(request):
    stats = database.get_stats()
    return JSONResponse(stats)

async def api_logs(request):
    logs = database.get_recent_logs(limit=40)
    return JSONResponse(logs)

async def api_search(request):
    q = request.query_params.get("q", "")
    results = database.search_students(q)
    return JSONResponse(results)

async def api_reverse_checkin(request):
    try:
        body = await request.json()
        ident = body.get("identifier", "")
        reason = body.get("reason", "")
        admin_u = body.get("admin_username", "admin")
        admin_p = body.get("admin_password", "")
        res = database.reverse_checkin(ident, admin_u, admin_p, reason)
        return JSONResponse(res)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

routes = [
    Route("/admin", admin_page, methods=["GET"]),
    Route("/admin/checkin", checkin_landing_page, methods=["GET"]),
    Route("/html5-qrcode.min.js", serve_qr_script, methods=["GET"]),
    Route("/api/login", api_login, methods=["POST"]),
    Route("/api/checkin", api_checkin, methods=["POST"]),
    Route("/api/stats", api_stats, methods=["GET"]),
    Route("/api/logs", api_logs, methods=["GET"]),
    Route("/api/search", api_search, methods=["GET"]),
    Route("/api/reverse-checkin", api_reverse_checkin, methods=["POST"]),
    Route("/", admin_page, methods=["GET"]), # Also serve admin on root if accessed directly
]

app = Starlette(routes=routes)

_server_thread = None

def start_server_background(port: int = 8000):
    global _server_thread
    if _server_thread is not None and _server_thread.is_alive():
        return
    
    def run_uvicorn():
        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
        server = uvicorn.Server(config)
        server.run()

    _server_thread = threading.Thread(target=run_uvicorn, daemon=True)
    _server_thread.start()
    print(f"[*] Admin High-Speed Scanner Server started in background on http://0.0.0.0:{port}/admin")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
