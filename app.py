"""
HealthBook - Patient Appointment Booking System
A lightweight RESTful web service for managing patient appointments in a healthcare setting.
"""
from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "healthbook.db")

def get_db():
    db_dir = os.path.dirname(os.path.abspath(DB_PATH))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                patient   TEXT    NOT NULL,
                doctor    TEXT    NOT NULL,
                date      TEXT    NOT NULL,
                reason    TEXT,
                status    TEXT    DEFAULT 'scheduled',
                created   TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "HealthBook", "timestamp": datetime.utcnow().isoformat()}), 200

@app.route("/appointments", methods=["GET"])
def list_appointments():
    doctor = request.args.get("doctor")
    status = request.args.get("status")
    query = "SELECT * FROM appointments WHERE 1=1"
    params = []
    if doctor:
        query += " AND doctor = ?"
        params.append(doctor)
    if status:
        query += " AND status = ?"
        params.append(status)
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows]), 200

@app.route("/appointments", methods=["POST"])
def create_appointment():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Malformed or empty JSON payload"}), 400
    required = ("patient", "doctor", "date")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO appointments (patient, doctor, date, reason) VALUES (?, ?, ?, ?)",
            (data["patient"], data["doctor"], data["date"], data.get("reason", "")),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM appointments WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route("/appointments/<int:appt_id>", methods=["GET"])
def get_appointment(appt_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM appointments WHERE id = ?", (appt_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row)), 200

@app.route("/appointments/<int:appt_id>", methods=["PATCH"])
def update_status(appt_id):
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Malformed or empty JSON payload"}), 400
    new_status = data.get("status")
    valid = ("scheduled", "completed", "cancelled")
    if new_status not in valid:
        return jsonify({"error": f"status must be one of {valid}"}), 400
    with get_db() as conn:
        conn.execute("UPDATE appointments SET status = ? WHERE id = ?", (new_status, appt_id))
        conn.commit()
        row = conn.execute("SELECT * FROM appointments WHERE id = ?", (appt_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row)), 200

@app.route("/appointments/<int:appt_id>", methods=["DELETE"])
def delete_appointment(appt_id):
    with get_db() as conn:
        conn.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))
        conn.commit()
    return jsonify({"deleted": appt_id}), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
