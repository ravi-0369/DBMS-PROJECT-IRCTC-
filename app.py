"""
IRCTC Railway Reservation System - Flask backend
Run:  python app.py
Open: http://127.0.0.1:5000
"""

import random
import uuid
from functools import wraps
import secrets
import requests
import mysql.connector
from flask import (Flask, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-string"

# ------------------------------------------------------------
# DATABASE CONFIG  -> change the password to your MySQL password
# ------------------------------------------------------------
import os

app.secret_key = os.environ["SECRET_KEY"]

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "database": os.environ.get("DB_NAME", "IRCTC"),
}
OTP_VALID_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_SECONDS = 60


def send_otp_email(to_email, otp):
    payload = {
        "sender": {
            "name": os.environ.get("MAIL_SENDER_NAME", "Railway Reservation System"),
            "email": os.environ["MAIL_SENDER_EMAIL"],
        },
        "to": [{"email": to_email}],
        "subject": "Your password reset OTP",
        "htmlContent": (
            f"<p>Your OTP to reset your password is "
            f"<b style='font-size:20px'>{otp}</b>.</p>"
            f"<p>It is valid for {OTP_VALID_MINUTES} minutes. "
            f"If you did not request this, ignore this email.</p>"
        ),
    }
    try:
        r = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers={
                "api-key": os.environ["BREVO_API_KEY"],
                "accept": "application/json",
            },
            timeout=10,
        )
        return r.status_code in (200, 201)
    except requests.RequestException as e:
        print("Email error:", e)
        return False


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip()
        db = get_db()
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("SELECT user_id FROM Users WHERE email=%s", (email,))
            user = cur.fetchone()
            if user:
                cur.execute(
                    "SELECT TIMESTAMPDIFF(SECOND, last_sent, NOW()) AS age "
                    "FROM PasswordResets WHERE email=%s",
                    (email,),
                )
                row = cur.fetchone()
                if row is None or row["age"] >= OTP_RESEND_SECONDS:
                    otp = f"{secrets.randbelow(10 ** 6):06d}"
                    cur.execute(
                        "INSERT INTO PasswordResets "
                        "(email, otp_hash, expires_at, attempts, last_sent) "
                        "VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL %s MINUTE), 0, NOW()) "
                        "ON DUPLICATE KEY UPDATE otp_hash=VALUES(otp_hash), "
                        "expires_at=VALUES(expires_at), attempts=0, "
                        "last_sent=VALUES(last_sent)",
                        (email, generate_password_hash(otp), OTP_VALID_MINUTES),
                    )
                    db.commit()
                    if not send_otp_email(email, otp):
                        cur.execute(
                            "DELETE FROM PasswordResets WHERE email=%s", (email,)
                        )
                        db.commit()
                        flash("Could not send the OTP right now. Please try again later.")
                        return redirect(url_for("forgot_password"))
        finally:
            db.close()
        session["reset_email"] = email
        session.pop("reset_ok", None)
        flash("If this email is registered, an OTP has been sent to it.")
        return redirect(url_for("verify_otp"))
    return render_template("forgot-password.html")


@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("forgot_password"))
    if request.method == "POST":
        otp = request.form["otp"].strip()
        db = get_db()
        cur = db.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT otp_hash, attempts, expires_at > NOW() AS valid "
                "FROM PasswordResets WHERE email=%s",
                (email,),
            )
            row = cur.fetchone()
            if not row or not row["valid"] or row["attempts"] >= OTP_MAX_ATTEMPTS:
                cur.execute("DELETE FROM PasswordResets WHERE email=%s", (email,))
                db.commit()
                flash("OTP expired or invalid. Please request a new one.")
                return redirect(url_for("forgot_password"))
            if check_password_hash(row["otp_hash"], otp):
                cur.execute("DELETE FROM PasswordResets WHERE email=%s", (email,))
                db.commit()
                session["reset_ok"] = True
                return redirect(url_for("reset_password"))
            cur.execute(
                "UPDATE PasswordResets SET attempts = attempts + 1 WHERE email=%s",
                (email,),
            )
            db.commit()
            flash("Incorrect OTP. Please try again.")
        finally:
            db.close()
    return render_template("verify-otp.html", email=email)


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = session.get("reset_email")
    if not email or not session.get("reset_ok"):
        return redirect(url_for("forgot_password"))
    if request.method == "POST":
        password = request.form["password"]
        confirm = request.form["confirm"]
        if len(password) < 6:
            flash("Password must be at least 6 characters.")
        elif password != confirm:
            flash("Passwords do not match.")
        else:
            db = get_db()
            cur = db.cursor()
            try:
                cur.execute(
                    "UPDATE Users SET password=%s WHERE email=%s",
                    (generate_password_hash(password), email),
                )
                db.commit()
            finally:
                db.close()
            session.pop("reset_email", None)
            session.pop("reset_ok", None)
            flash("Password updated. Please login.")
            return redirect(url_for("login"))
    return render_template("reset-password.html")


if __name__ == "__main__":
    app.run()


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def get_stations():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT station_id, station_name FROM Stations ORDER BY station_name")
    rows = cur.fetchall()
    db.close()
    return rows


def generate_pnr(cur):
    """Create a unique 10-digit PNR."""
    while True:
        pnr = "".join(random.choices("0123456789", k=10))
        cur.execute("SELECT 1 FROM Bookings WHERE pnr_number=%s", (pnr,))
        if not cur.fetchone():
            return pnr


# ============================================================
# PUBLIC PAGES
# ============================================================

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", stations=get_stations())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "INSERT INTO Users (user_id, username, password, email, phone) "
                "VALUES (%s, %s, %s, %s, %s)",
                ("U" + uuid.uuid4().hex[:8],
                 request.form["username"],
                 generate_password_hash(request.form["password"]),
                 request.form["email"],
                 request.form.get("phone", "")),
            )
            db.commit()
            flash("Registered successfully! Please login.")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("This email is already registered.")
        finally:
            db.close()
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM Users WHERE email=%s", (request.form["email"],))
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user["password"], request.form["password"]):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/pnr-status", methods=["GET", "POST"])
def pnr_status():
    ticket = None
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT b.pnr_number, t.train_number, t.train_name,
                   s1.station_name AS source_station,
                   s2.station_name AS destination_station,
                   t.departure_time, t.arrival_time, b.journey_date,
                   tc.class_name, tc.fare, b.seat_count, b.booking_status
            FROM Bookings b
            JOIN TrainClasses tc ON b.train_class_id = tc.train_class_id
            JOIN Trains t ON tc.train_id = t.train_id
            JOIN Stations s1 ON t.source_station_id = s1.station_id
            JOIN Stations s2 ON t.destination_station_id = s2.station_id
            WHERE b.pnr_number = %s
        """, (request.form["pnr"].strip(),))
        ticket = cur.fetchone()
        db.close()
        if not ticket:
            flash("PNR not found.")
    return render_template("pnr-status.html", ticket=ticket)


# ============================================================
# LOGGED-IN PAGES
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/book-ticket")
@login_required
def book_ticket():
    return render_template("book-ticket.html", stations=get_stations())


@app.route("/search-trains", methods=["GET", "POST"])
@login_required
def search_trains():
    if request.method == "GET":
        return redirect(url_for("book_ticket"))

    f = request.form
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT t.train_number, t.train_name,
               s1.station_name AS source_station,
               s2.station_name AS destination_station,
               t.departure_time, t.arrival_time,
               tc.train_class_id, tc.class_name, tc.fare, tc.available_seats
        FROM Trains t
        JOIN Stations s1 ON t.source_station_id = s1.station_id
        JOIN Stations s2 ON t.destination_station_id = s2.station_id
        JOIN TrainClasses tc ON t.train_id = tc.train_id
        WHERE s1.station_id = %s
          AND s2.station_id = %s
          AND tc.class_name = %s
          AND tc.available_seats >= %s
    """, (f["from"], f["to"], f["class"], int(f["passengers"])))
    trains = cur.fetchall()
    db.close()

    return render_template("search-results.html", trains=trains,
                           date=f["date"], passengers=f["passengers"])


@app.route("/book", methods=["POST"])
@login_required
def book():
    f = request.form
    seats = int(f["passengers"])

    db = get_db()
    cur = db.cursor()
    try:
        # 1. reduce seats only if enough are available
        cur.execute(
            "UPDATE TrainClasses SET available_seats = available_seats - %s "
            "WHERE train_class_id = %s AND available_seats >= %s",
            (seats, f["train_class_id"], seats),
        )
        if cur.rowcount != 1:
            db.rollback()
            flash("Not enough seats available.")
            return redirect(url_for("book_ticket"))

        # 2. create booking
        pnr = generate_pnr(cur)
        cur.execute("""
            INSERT INTO Bookings (booking_id, user_id, train_class_id,
                                  journey_date, seat_count, pnr_number,
                                  booking_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Confirmed')
        """, ("B" + uuid.uuid4().hex[:8], session["user_id"],
              f["train_class_id"], f["date"], seats, pnr))

        db.commit()
        flash(f"Booking confirmed! Your PNR is {pnr}")
        return redirect(url_for("my_bookings"))
    except Exception as e:
        db.rollback()
        print("Booking error:", e)
        flash("Booking failed. Please try again.")
        return redirect(url_for("book_ticket"))
    finally:
        db.close()


@app.route("/my-bookings")
@login_required
def my_bookings():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT b.booking_id, b.pnr_number, t.train_number, t.train_name,
               s1.station_name AS source_station,
               s2.station_name AS destination_station,
               t.departure_time, t.arrival_time, b.journey_date,
               tc.class_name, tc.fare, b.seat_count, b.booking_status
        FROM Bookings b
        JOIN TrainClasses tc ON b.train_class_id = tc.train_class_id
        JOIN Trains t ON tc.train_id = t.train_id
        JOIN Stations s1 ON t.source_station_id = s1.station_id
        JOIN Stations s2 ON t.destination_station_id = s2.station_id
        WHERE b.user_id = %s
        ORDER BY b.journey_date
    """, (session["user_id"],))
    bookings = cur.fetchall()
    db.close()
    return render_template("my-bookings.html", bookings=bookings)


@app.route("/cancellation", methods=["GET", "POST"])
@login_required
def cancellation():
    if request.method == "POST":
        pnr = request.form["pnr"].strip()
        reason = request.form.get("reason", "")
        uid = session["user_id"]

        db = get_db()
        cur = db.cursor()
        try:
            # give seats back
            cur.execute("""
                UPDATE TrainClasses tc
                JOIN Bookings b ON tc.train_class_id = b.train_class_id
                SET tc.available_seats = tc.available_seats + b.seat_count
                WHERE b.pnr_number = %s AND b.user_id = %s
                  AND b.booking_status = 'Confirmed'
            """, (pnr, uid))

            if cur.rowcount == 0:
                db.rollback()
                flash("No confirmed booking found for this PNR.")
            else:
                # mark booking cancelled
                cur.execute("""
                    UPDATE Bookings
                    SET booking_status = 'Cancelled', cancellation_reason = %s
                    WHERE pnr_number = %s AND user_id = %s
                      AND booking_status = 'Confirmed'
                """, (reason, pnr, uid))
                db.commit()
                flash("Ticket cancelled successfully.")
        except Exception as e:
            db.rollback()
            print("Cancellation error:", e)
            flash("Cancellation failed.")
        finally:
            db.close()
    return render_template("cancellation.html")


if __name__ == "__main__":
    app.run(debug=True)
