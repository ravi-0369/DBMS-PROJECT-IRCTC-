import uuid
from datetime import date, datetime, timedelta
from functools import wraps

import mysql.connector
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for)

CLASS_CHOICES = [
    ("sleeper", "Sleeper"),
    ("3ac", "AC 3 Tier"),
    ("2ac", "AC 2 Tier"),
    ("1ac", "AC First Class"),
    ("chair-car", "Chair Car"),
]

BOOKING_SELECT = """
    SELECT b.booking_id, b.pnr_number, u.username, u.email,
           t.train_number, t.train_name, tc.class_name, b.journey_date,
           b.seat_count, tc.fare * b.seat_count AS amount, b.booking_status
    FROM Bookings b
    JOIN Users u ON b.user_id = u.user_id
    JOIN TrainClasses tc ON b.train_class_id = tc.train_class_id
    JOIN Trains t ON tc.train_id = t.train_id
"""

TRAIN_SELECT = """
    SELECT t.train_id, t.train_number, t.train_name,
           t.departure_time, t.arrival_time,
           s1.station_name AS source_station,
           s2.station_name AS destination_station
    FROM Trains t
    JOIN Stations s1 ON t.source_station_id = s1.station_id
    JOIN Stations s2 ON t.destination_station_id = s2.station_id
"""


def to_int(value, low, high):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if low <= n <= high else None


def clean_time(value):
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).strftime("%H:%M:%S")
        except (TypeError, ValueError):
            continue
    return None


def create_admin_blueprint(get_db):
    bp = Blueprint("admin", __name__, url_prefix="/admin")

    @bp.app_template_filter("hhmm")
    def hhmm(value):
        if value is None:
            return ""
        if isinstance(value, timedelta):
            seconds = int(value.total_seconds())
            return f"{seconds // 3600 % 24:02d}:{seconds % 3600 // 60:02d}"
        return value.strftime("%H:%M")

    def query(sql, params=(), one=False):
        db = get_db()
        try:
            cur = db.cursor(dictionary=True)
            cur.execute(sql, params)
            return cur.fetchone() if one else cur.fetchall()
        finally:
            db.close()

    def run(sql, params=(), success=None):
        db = get_db()
        try:
            cur = db.cursor()
            cur.execute(sql, params)
            db.commit()
            if success:
                flash(success)
            return cur.rowcount
        except mysql.connector.IntegrityError:
            db.rollback()
            flash("That change conflicts with existing data: a duplicate "
                  "value, or a record that is still in use.")
        except mysql.connector.Error as e:
            db.rollback()
            print("Admin DB error:", e)
            flash("Database error. Check the values and try again.")
        finally:
            db.close()
        return None

    def admin_required(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please login first.")
                return redirect(url_for("login"))
            row = query("SELECT is_admin FROM Users WHERE user_id=%s",
                        (session["user_id"],), one=True)
            if not row or not row["is_admin"]:
                abort(403)
            return f(*args, **kwargs)
        return wrapper

    @bp.route("/")
    @admin_required
    def dashboard():
        stats = query("""
            SELECT
                (SELECT COUNT(*) FROM Users) AS users,
                (SELECT COUNT(*) FROM Trains) AS trains,
                (SELECT COUNT(*) FROM Stations) AS stations,
                (SELECT COUNT(*) FROM Bookings
                  WHERE booking_status = 'Confirmed') AS confirmed,
                (SELECT COUNT(*) FROM Bookings
                  WHERE booking_status = 'Cancelled') AS cancelled,
                (SELECT COALESCE(SUM(tc.fare * b.seat_count), 0)
                   FROM Bookings b
                   JOIN TrainClasses tc
                     ON b.train_class_id = tc.train_class_id
                  WHERE b.booking_status = 'Confirmed') AS revenue
        """, one=True)
        recent = query(BOOKING_SELECT +
                       " ORDER BY b.journey_date DESC LIMIT 8")
        return render_template("admin_overview.html", stats=stats,
                               recent=recent)

    @bp.route("/users")
    @admin_required
    def users():
        q = request.args.get("q", "").strip()
        like = f"%{q}%"
        rows = query("""
            SELECT u.user_id, u.username, u.email, u.phone, u.is_admin,
                   COUNT(b.booking_id) AS bookings
            FROM Users u
            LEFT JOIN Bookings b ON b.user_id = u.user_id
            WHERE u.username LIKE %s OR u.email LIKE %s
            GROUP BY u.user_id, u.username, u.email, u.phone, u.is_admin
            ORDER BY u.username
        """, (like, like))
        return render_template("admin_users.html", users=rows, q=q)

    @bp.route("/users/<user_id>/toggle-admin", methods=["POST"])
    @admin_required
    def toggle_admin(user_id):
        if user_id == session["user_id"]:
            flash("You cannot change your own admin access.")
        else:
            run("UPDATE Users SET is_admin = 1 - is_admin WHERE user_id=%s",
                (user_id,), "Admin access updated.")
        return redirect(url_for("admin.users"))

    @bp.route("/users/<user_id>/delete", methods=["POST"])
    @admin_required
    def delete_user(user_id):
        if user_id == session["user_id"]:
            flash("You cannot delete your own account.")
        else:
            run("DELETE FROM Users WHERE user_id=%s", (user_id,),
                "User deleted.")
        return redirect(url_for("admin.users"))

    @bp.route("/trains")
    @admin_required
    def trains():
        rows = query("""
            SELECT t.train_id, t.train_number, t.train_name,
                   s1.station_name AS source_station,
                   s2.station_name AS destination_station,
                   t.departure_time, t.arrival_time,
                   (SELECT COUNT(*) FROM TrainClasses c
                     WHERE c.train_id = t.train_id) AS classes,
                   (SELECT COALESCE(SUM(c.total_seats), 0) FROM TrainClasses c
                     WHERE c.train_id = t.train_id) AS seats,
                   (SELECT COUNT(*) FROM TrainStops s
                     WHERE s.train_id = t.train_id) AS stops
            FROM Trains t
            JOIN Stations s1 ON t.source_station_id = s1.station_id
            JOIN Stations s2 ON t.destination_station_id = s2.station_id
            ORDER BY t.train_number
        """)
        stations = query("SELECT station_id, station_name FROM Stations "
                         "ORDER BY station_name")
        return render_template("admin_trains.html", trains=rows,
                               stations=stations)

    @bp.route("/trains/add", methods=["POST"])
    @admin_required
    def add_train():
        f = request.form
        number = to_int(f.get("train_number"), 1, 999999)
        name = f.get("train_name", "").strip()
        dep = clean_time(f.get("departure_time"))
        arr = clean_time(f.get("arrival_time"))
        source = f.get("source")
        dest = f.get("destination")
        if number is None or not name or dep is None or arr is None \
                or not source or not dest:
            flash("Enter a valid train number, name, stations and times.")
            return redirect(url_for("admin.trains"))
        if source == dest:
            flash("Source and destination must be different.")
            return redirect(url_for("admin.trains"))

        train_id = "T" + uuid.uuid4().hex[:8]
        db = get_db()
        try:
            cur = db.cursor()
            cur.execute("""
                INSERT INTO Trains (train_id, train_number, train_name,
                                    source_station_id, destination_station_id,
                                    departure_time, arrival_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (train_id, number, name[:50], source, dest, dep, arr))
            cur.execute("""
                INSERT INTO TrainStops (train_id, station_id, stop_number,
                                        arrival_time, departure_time,
                                        halt_minutes)
                VALUES (%s, %s, 1, %s, %s, 0), (%s, %s, 2, %s, %s, 0)
            """, (train_id, source, dep, dep, train_id, dest, arr, arr))
            db.commit()
            flash("Train added. Now add its classes and seats.")
            return redirect(url_for("admin.train_detail", train_id=train_id))
        except mysql.connector.Error as e:
            db.rollback()
            print("Add train error:", e)
            flash("Could not add the train. The train number may already "
                  "exist.")
        finally:
            db.close()
        return redirect(url_for("admin.trains"))

    @bp.route("/trains/<train_id>")
    @admin_required
    def train_detail(train_id):
        train = query(TRAIN_SELECT + " WHERE t.train_id = %s", (train_id,),
                      one=True)
        if not train:
            abort(404)
        try:
            journey = date.fromisoformat(request.args.get("date", ""))
        except ValueError:
            journey = date.today()

        classes = query("""
            SELECT tc.train_class_id, tc.class_name, tc.fare, tc.total_seats,
                   COALESCE((
                       SELECT SUM(b.seat_count) FROM Bookings b
                       WHERE b.train_class_id = tc.train_class_id
                         AND b.journey_date = %s
                         AND b.booking_status = 'Confirmed'
                   ), 0) AS booked
            FROM TrainClasses tc
            WHERE tc.train_id = %s
            ORDER BY tc.fare
        """, (journey, train_id))
        stops = query("""
            SELECT ts.stop_id, ts.stop_number, s.station_name,
                   ts.arrival_time, ts.departure_time, ts.halt_minutes
            FROM TrainStops ts
            JOIN Stations s ON ts.station_id = s.station_id
            WHERE ts.train_id = %s
            ORDER BY ts.stop_number
        """, (train_id,))
        stations = query("SELECT station_id, station_name FROM Stations "
                         "ORDER BY station_name")
        return render_template("admin_train_detail.html", train=train,
                               classes=classes, stops=stops,
                               stations=stations, journey=journey.isoformat(),
                               class_choices=CLASS_CHOICES)

    @bp.route("/trains/<train_id>/edit", methods=["POST"])
    @admin_required
    def edit_train(train_id):
        f = request.form
        number = to_int(f.get("train_number"), 1, 999999)
        name = f.get("train_name", "").strip()
        dep = clean_time(f.get("departure_time"))
        arr = clean_time(f.get("arrival_time"))
        if number is None or not name or dep is None or arr is None:
            flash("Enter a valid train number, name and times.")
        else:
            run("""
                UPDATE Trains
                SET train_number=%s, train_name=%s,
                    departure_time=%s, arrival_time=%s
                WHERE train_id=%s
            """, (number, name[:50], dep, arr, train_id), "Train updated.")
        return redirect(url_for("admin.train_detail", train_id=train_id))

    @bp.route("/trains/<train_id>/delete", methods=["POST"])
    @admin_required
    def delete_train(train_id):
        db = get_db()
        try:
            cur = db.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM Bookings b
                JOIN TrainClasses tc ON b.train_class_id = tc.train_class_id
                WHERE tc.train_id = %s
            """, (train_id,))
            if cur.fetchone()[0]:
                flash("This train has booking records, so it cannot be "
                      "deleted.")
                return redirect(url_for("admin.train_detail",
                                        train_id=train_id))
            cur.execute("DELETE FROM TrainStops WHERE train_id=%s",
                        (train_id,))
            cur.execute("DELETE FROM TrainClasses WHERE train_id=%s",
                        (train_id,))
            cur.execute("DELETE FROM Trains WHERE train_id=%s", (train_id,))
            db.commit()
            flash("Train deleted.")
        except mysql.connector.Error as e:
            db.rollback()
            print("Delete train error:", e)
            flash("Could not delete the train.")
        finally:
            db.close()
        return redirect(url_for("admin.trains"))

    @bp.route("/trains/<train_id>/classes/save", methods=["POST"])
    @admin_required
    def save_class(train_id):
        f = request.form
        back = redirect(url_for("admin.train_detail", train_id=train_id))
        valid = {key for key, _ in CLASS_CHOICES}
        class_name = f.get("class_name")
        fare = to_int(f.get("fare"), 1, 1000000)
        seats = to_int(f.get("total_seats"), 1, 10000)
        if class_name not in valid or fare is None or seats is None:
            flash("Choose a class and enter a valid fare and seat count.")
            return back

        existing = query("""
            SELECT train_class_id FROM TrainClasses
            WHERE train_id=%s AND class_name=%s
        """, (train_id, class_name), one=True)

        if existing:
            peak = query("""
                SELECT COALESCE(MAX(booked), 0) AS peak FROM (
                    SELECT SUM(seat_count) AS booked FROM Bookings
                    WHERE train_class_id = %s
                      AND booking_status = 'Confirmed'
                      AND journey_date >= CURDATE()
                    GROUP BY journey_date
                ) x
            """, (existing["train_class_id"],), one=True)
            if seats < int(peak["peak"]):
                flash(f"Total seats cannot go below {int(peak['peak'])}: "
                      f"that many are already booked on an upcoming date.")
                return back
            run("""
                UPDATE TrainClasses SET fare=%s, total_seats=%s
                WHERE train_class_id=%s
            """, (fare, seats, existing["train_class_id"]), "Class updated.")
        else:
            run("""
                INSERT INTO TrainClasses
                    (train_class_id, train_id, class_name, fare, total_seats)
                VALUES (%s, %s, %s, %s, %s)
            """, ("TC" + uuid.uuid4().hex[:8], train_id, class_name, fare,
                  seats), "Class added.")
        return back

    @bp.route("/trains/<train_id>/classes/<train_class_id>/delete",
              methods=["POST"])
    @admin_required
    def delete_class(train_id, train_class_id):
        run("DELETE FROM TrainClasses WHERE train_class_id=%s AND train_id=%s",
            (train_class_id, train_id), "Class removed.")
        return redirect(url_for("admin.train_detail", train_id=train_id))

    @bp.route("/trains/<train_id>/stops/add", methods=["POST"])
    @admin_required
    def add_stop(train_id):
        f = request.form
        back = redirect(url_for("admin.train_detail", train_id=train_id))
        position = to_int(f.get("stop_number"), 1, 99)
        arrival = clean_time(f.get("arrival_time"))
        departure = clean_time(f.get("departure_time"))
        halt = to_int(f.get("halt_minutes"), 0, 120)
        station_id = f.get("station_id")
        if None in (position, arrival, departure, halt) or not station_id:
            flash("Enter a valid position, station, times and halt.")
            return back

        db = get_db()
        try:
            cur = db.cursor()
            cur.execute("""
                SELECT 1 FROM TrainStops WHERE train_id=%s AND station_id=%s
            """, (train_id, station_id))
            if cur.fetchone():
                flash("This station is already a stop on the train.")
                return back
            cur.execute("""
                UPDATE TrainStops SET stop_number = stop_number + 1
                WHERE train_id=%s AND stop_number >= %s
                ORDER BY stop_number DESC
            """, (train_id, position))
            cur.execute("""
                INSERT INTO TrainStops (train_id, station_id, stop_number,
                                        arrival_time, departure_time,
                                        halt_minutes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (train_id, station_id, position, arrival, departure, halt))
            db.commit()
            flash("Stop added.")
        except mysql.connector.Error as e:
            db.rollback()
            print("Add stop error:", e)
            flash("Could not add the stop.")
        finally:
            db.close()
        return back

    @bp.route("/trains/<train_id>/stops/<int:stop_id>/delete",
              methods=["POST"])
    @admin_required
    def delete_stop(train_id, stop_id):
        run("DELETE FROM TrainStops WHERE stop_id=%s AND train_id=%s",
            (stop_id, train_id), "Stop removed.")
        return redirect(url_for("admin.train_detail", train_id=train_id))

    @bp.route("/stations")
    @admin_required
    def stations():
        rows = query("""
            SELECT s.station_id, s.station_name, s.city, s.state,
                   (SELECT COUNT(*) FROM TrainStops ts
                     WHERE ts.station_id = s.station_id) AS stops
            FROM Stations s
            ORDER BY s.station_name
        """)
        return render_template("admin_stations.html", stations=rows)

    @bp.route("/stations/add", methods=["POST"])
    @admin_required
    def add_station():
        f = request.form
        name = f.get("station_name", "").strip()
        city = f.get("city", "").strip()
        state = f.get("state", "").strip()
        if not name:
            flash("Enter a station name.")
            return redirect(url_for("admin.stations"))
        last = query("""
            SELECT MAX(CAST(SUBSTRING(station_id, 2) AS UNSIGNED)) AS m
            FROM Stations WHERE station_id REGEXP '^S[0-9]+$'
        """, one=True)
        station_id = f"S{(last['m'] or 0) + 1:02d}"
        run("""
            INSERT INTO Stations (station_id, station_name, city, state)
            VALUES (%s, %s, %s, %s)
        """, (station_id, name[:50], city[:30], state[:30]), "Station added.")
        return redirect(url_for("admin.stations"))

    @bp.route("/stations/<station_id>/delete", methods=["POST"])
    @admin_required
    def delete_station(station_id):
        run("DELETE FROM Stations WHERE station_id=%s", (station_id,),
            "Station deleted.")
        return redirect(url_for("admin.stations"))

    @bp.route("/bookings")
    @admin_required
    def bookings():
        status = request.args.get("status", "")
        q = request.args.get("q", "").strip()
        where, params = [], []
        if status in ("Confirmed", "Cancelled"):
            where.append("b.booking_status = %s")
            params.append(status)
        if q:
            where.append("(b.pnr_number LIKE %s OR u.username LIKE %s "
                         "OR u.email LIKE %s)")
            params += [f"%{q}%"] * 3
        sql = BOOKING_SELECT
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY b.journey_date DESC LIMIT 200"
        rows = query(sql, tuple(params))
        return render_template("admin_bookings.html", bookings=rows,
                               status=status, q=q)

    @bp.route("/bookings/<booking_id>/cancel", methods=["POST"])
    @admin_required
    def cancel_booking(booking_id):
        changed = run("""
            UPDATE Bookings
            SET booking_status = 'Cancelled',
                cancellation_reason = 'Cancelled by admin'
            WHERE booking_id = %s AND booking_status = 'Confirmed'
        """, (booking_id,))
        if changed:
            flash("Booking cancelled. Its seats are available again.")
        elif changed == 0:
            flash("That booking is already cancelled.")
        return redirect(request.referrer or url_for("admin.bookings"))

    return bp
