from contextlib import contextmanager
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import mimetypes
import os
import re
import sqlite3
import traceback
from urllib.parse import parse_qs, unquote, urlparse


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("CINEMAHUB_DB_PATH", DATA_DIR / "cinemahub.sqlite3"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS Genres (
    GenreID INTEGER PRIMARY KEY AUTOINCREMENT,
    GenreName TEXT NOT NULL UNIQUE,
    Description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS Halls (
    HallID INTEGER PRIMARY KEY AUTOINCREMENT,
    HallName TEXT NOT NULL UNIQUE,
    Capacity INTEGER NOT NULL CHECK (Capacity > 0),
    IsVIP INTEGER NOT NULL DEFAULT 0 CHECK (IsVIP IN (0, 1))
);
CREATE TABLE IF NOT EXISTS Movies (
    MovieID INTEGER PRIMARY KEY AUTOINCREMENT,
    Title TEXT NOT NULL,
    GenreID INTEGER NOT NULL REFERENCES Genres(GenreID) ON DELETE RESTRICT,
    DurationMinutes INTEGER NOT NULL CHECK (DurationMinutes > 0),
    AgeRating TEXT NOT NULL DEFAULT '12+',
    BasePrice REAL NOT NULL CHECK (BasePrice >= 0),
    Synopsis TEXT NOT NULL DEFAULT '',
    Accent TEXT NOT NULL DEFAULT '#9a583b'
);
CREATE TABLE IF NOT EXISTS Sessions (
    SessionID INTEGER PRIMARY KEY AUTOINCREMENT,
    MovieID INTEGER NOT NULL REFERENCES Movies(MovieID) ON DELETE CASCADE,
    HallID INTEGER NOT NULL REFERENCES Halls(HallID) ON DELETE RESTRICT,
    StartTime TEXT NOT NULL,
    TicketPrice REAL NOT NULL CHECK (TicketPrice >= 0),
    UNIQUE (HallID, StartTime)
);
CREATE TABLE IF NOT EXISTS Tickets (
    TicketID INTEGER PRIMARY KEY AUTOINCREMENT,
    SessionID INTEGER NOT NULL REFERENCES Sessions(SessionID) ON DELETE CASCADE,
    CustomerName TEXT NOT NULL,
    CustomerPhone TEXT NOT NULL DEFAULT '',
    SeatNumber INTEGER NOT NULL CHECK (SeatNumber > 0),
    PurchaseDate TEXT NOT NULL,
    IsPaid INTEGER NOT NULL DEFAULT 1 CHECK (IsPaid IN (0, 1)),
    UNIQUE (SessionID, SeatNumber)
);
CREATE INDEX IF NOT EXISTS IX_Sessions_StartTime ON Sessions(StartTime);
CREATE INDEX IF NOT EXISTS IX_Tickets_Session_Paid ON Tickets(SessionID, IsPaid);
"""

GENRES = [
    ("Наукова фантастика", "Космос, майбутнє й технології."),
    ("Екшн та пригоди", "Динамічні історії та великі пригоди."),
    ("Драма", "Сильні історії про людей і вибір."),
    ("Анімація", "Яскраві стрічки для всієї родини."),
]

HALLS = [
    ("Зал «Синій»", 150, 0),
    ("Зал «Червоний»", 100, 0),
    ("VIP Lounge", 30, 1),
    ("Мала зала", 48, 0),
]

MOVIES = [
    ("Дюна: Частина друга", "Наукова фантастика", 166, "16+", 200, "Пол Атрейдес обирає між коханням і долею цілого всесвіту.", "#bd774e"),
    ("Інтерстеллар", "Наукова фантастика", 169, "12+", 180, "Екіпаж вирушає крізь простір і час, щоб знайти людству новий дім.", "#607789"),
    ("Оппенгеймер", "Драма", 180, "18+", 220, "Портрет ученого, чиє відкриття змінило перебіг історії.", "#ab5945"),
    ("Дедпул і Росомаха", "Екшн та пригоди", 127, "18+", 210, "Двоє несхожих героїв вирушають у пригоду поза межами звичного світу.", "#a84b4b"),
    ("Думками навиворіт 2", "Анімація", 96, "0+", 160, "Райлі дорослішає, а в її голові з'являються нові емоції.", "#9584ba"),
    ("Кунг-фу Панда 4", "Анімація", 94, "0+", 150, "По старанності й апетиту По завжди є куди рости.", "#7e9b6d"),
    ("Марсіанин", "Наукова фантастика", 144, "12+", 170, "Сам на Червоній планеті астронавт планує повернення додому.", "#bf7656"),
]

SESSION_SEEDS = [
    (0, 0, 0, 11, 40, 220), (1, 1, 0, 12, 10, 190), (4, 3, 0, 13, 20, 170),
    (2, 2, 0, 14, 0, 360), (3, 1, 0, 16, 40, 240), (0, 2, 0, 18, 30, 340),
    (5, 1, 0, 19, 0, 170), (1, 0, 0, 20, 45, 200), (6, 3, 1, 10, 30, 180),
    (2, 1, 1, 18, 15, 240), (4, 0, 1, 12, 0, 170), (3, 2, 1, 21, 0, 350),
    (0, 1, 2, 16, 40, 220), (6, 0, 2, 19, 20, 200),
]

CUSTOMERS = [
    ("Олександр Іваненко", "+380 97 111 22 33"),
    ("Марія Бондаренко", "+380 50 222 33 44"),
    ("Дмитро Шевченко", "+380 63 333 44 55"),
    ("Віктор Мороз", "+380 98 444 55 66"),
    ("Олена Кравець", "+380 50 555 66 77"),
    ("Андрій Ткачук", "+380 67 666 77 88"),
    ("Ігор Мельник", "+380 93 777 88 99"),
    ("Наталія Савченко", "+380 50 888 99 00"),
    ("Сергій Поліщук", "+380 97 999 00 11"),
    ("Юлія Лисенко", "+380 63 000 11 22"),
    ("Аліна Коваль", "+380 95 400 20 10"),
    ("Тарас Мельник", "+380 68 208 77 04"),
    ("Софія Петренко", "+380 93 870 12 45"),
    ("Максим Романюк", "+380 67 310 65 21"),
    ("Ірина Бойко", "+380 50 450 32 19"),
    ("Богдан Олійник", "+380 96 810 42 03"),
    ("Катерина Гнатюк", "+380 73 204 66 18"),
    ("Павло Клим", "+380 99 503 90 12"),
    ("Дарина Кравчук", "+380 63 701 28 54"),
    ("Михайло Дорошенко", "+380 98 326 40 77"),
]


@contextmanager
def connect_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with connect_db() as db:
        db.executescript(SCHEMA)
        if db.execute("SELECT COUNT(*) FROM Genres").fetchone()[0]:
            return
        db.executemany("INSERT INTO Genres (GenreName, Description) VALUES (?, ?)", GENRES)
        genre_ids = {row["GenreName"]: row["GenreID"] for row in db.execute("SELECT GenreID, GenreName FROM Genres")}
        db.executemany("INSERT INTO Halls (HallName, Capacity, IsVIP) VALUES (?, ?, ?)", HALLS)
        db.executemany(
            "INSERT INTO Movies (Title, GenreID, DurationMinutes, AgeRating, BasePrice, Synopsis, Accent) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(title, genre_ids[genre], duration, rating, price, synopsis, accent) for title, genre, duration, rating, price, synopsis, accent in MOVIES],
        )
        today = date.today()
        for movie_index, hall_index, day_offset, hour, minute, price in SESSION_SEEDS:
            start = datetime.combine(today + timedelta(days=day_offset), datetime.min.time()).replace(hour=hour, minute=minute)
            db.execute(
                "INSERT INTO Sessions (MovieID, HallID, StartTime, TicketPrice) VALUES (?, ?, ?, ?)",
                (movie_index + 1, hall_index + 1, start.isoformat(timespec="minutes"), price),
            )
        session_ids = [row["SessionID"] for row in db.execute("SELECT SessionID FROM Sessions ORDER BY SessionID")]
        ticket_seeds = [
            (0, 12, 0), (0, 13, 1), (0, 14, 2), (0, 25, 10),
            (1, 45, 3), (1, 46, 4), (2, 20, 5), (3, 5, 6),
            (3, 6, 7), (4, 88, 8), (5, 15, 9), (5, 18, 10),
            (6, 5, 11), (7, 30, 12), (9, 17, 13), (9, 24, 14),
            (10, 9, 15), (11, 4, 16), (12, 40, 17), (13, 11, 18),
            (13, 20, 19),
        ]
        for session_index, seat_number, customer_index in ticket_seeds:
            if session_index >= len(session_ids):
                continue
            session_id = session_ids[session_index]
            customer_name, phone = CUSTOMERS[customer_index]
            is_paid = 0 if customer_index in (9, 18) else 1
            purchased = (datetime.now() - timedelta(days=(customer_index % 4))).isoformat(timespec="minutes")
            db.execute(
                "INSERT INTO Tickets (SessionID, CustomerName, CustomerPhone, SeatNumber, PurchaseDate, IsPaid) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, customer_name, phone, seat_number, purchased, is_paid),
            )


def rows_as_dicts(cursor):
    return [dict(row) for row in cursor.fetchall()]


def parse_date(value, default):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return default


def overview(db):
    today = date.today().isoformat()
    metrics = db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM Movies) AS movie_count,
            (SELECT COUNT(*) FROM Sessions WHERE date(StartTime) = ?) AS today_sessions,
            (SELECT COUNT(*) FROM Tickets WHERE IsPaid = 1) AS paid_tickets,
            (SELECT COALESCE(SUM(s.TicketPrice), 0) FROM Tickets t JOIN Sessions s ON s.SessionID = t.SessionID WHERE t.IsPaid = 1) AS revenue
        """,
        (today,),
    ).fetchone()
    sessions = rows_as_dicts(db.execute(
        """
        SELECT s.SessionID, s.StartTime, s.TicketPrice, m.Title, m.AgeRating, m.DurationMinutes,
               h.HallName, h.Capacity, h.IsVIP, COUNT(t.TicketID) AS Sold,
               ROUND(COUNT(t.TicketID) * 100.0 / h.Capacity, 1) AS Occupancy
        FROM Sessions s
        JOIN Movies m ON m.MovieID = s.MovieID
        JOIN Halls h ON h.HallID = s.HallID
        LEFT JOIN Tickets t ON t.SessionID = s.SessionID AND t.IsPaid = 1
        WHERE date(s.StartTime) = ?
        GROUP BY s.SessionID ORDER BY s.StartTime LIMIT 7
        """,
        (today,),
    ))
    best_sellers = rows_as_dicts(db.execute(
        """
        SELECT m.Title, m.Accent, COUNT(t.TicketID) AS Sold
        FROM Movies m
        JOIN Sessions s ON s.MovieID = m.MovieID
        JOIN Tickets t ON t.SessionID = s.SessionID AND t.IsPaid = 1
        GROUP BY m.MovieID ORDER BY Sold DESC, m.Title LIMIT 4
        """
    ))
    return {
        "metrics": dict(metrics),
        "sessions": sessions,
        "bestSellers": best_sellers,
        "halls": rows_as_dicts(db.execute("SELECT COUNT(*) AS count FROM Halls")),
    }


def list_sessions(db, day=None):
    filters = []
    params = []
    if day:
        filters.append("date(s.StartTime) = ?")
        params.append(day)
    where = "WHERE " + " AND ".join(filters) if filters else ""
    return rows_as_dicts(db.execute(
        f"""
        SELECT s.SessionID, s.MovieID, s.HallID, s.StartTime, s.TicketPrice,
               m.Title, m.AgeRating, m.DurationMinutes, m.Accent, m.GenreName,
               h.HallName, h.Capacity, h.IsVIP,
               COUNT(t.TicketID) AS Sold,
               h.Capacity - COUNT(t.TicketID) AS AvailableSeats,
               ROUND(COUNT(t.TicketID) * 100.0 / h.Capacity, 1) AS Occupancy
        FROM Sessions s
        JOIN (SELECT m.*, g.GenreName FROM Movies m JOIN Genres g ON g.GenreID = m.GenreID) m ON m.MovieID = s.MovieID
        JOIN Halls h ON h.HallID = s.HallID
        LEFT JOIN Tickets t ON t.SessionID = s.SessionID AND t.IsPaid = 1
        {where}
        GROUP BY s.SessionID ORDER BY s.StartTime
        """,
        params,
    ))


QUERY_FIELDS = {
    "m.Title": "m.Title AS Title",
    "m.AgeRating": "m.AgeRating AS AgeRating",
    "g.GenreName": "g.GenreName AS Genre",
    "h.HallName": "h.HallName AS Hall",
    "h.Capacity": "h.Capacity AS Capacity",
    "h.IsVIP": "h.IsVIP AS IsVIP",
    "s.StartTime": "s.StartTime AS StartTime",
    "s.TicketPrice": "s.TicketPrice AS TicketPrice",
    "s.SessionID": "s.SessionID AS SessionID",
    "t.TicketID": "t.TicketID AS TicketID",
    "t.CustomerName": "t.CustomerName AS CustomerName",
    "t.PurchaseDate": "t.PurchaseDate AS PurchaseDate",
    "t.IsPaid": "t.IsPaid AS IsPaid",
    "COUNT(t.TicketID)": "COUNT(t.TicketID) AS TicketCount",
    "SUM(s.TicketPrice)": "SUM(s.TicketPrice) AS Revenue",
    "ROUND(COUNT(t.TicketID)*100.0/h.Capacity,1)": "ROUND(COUNT(t.TicketID)*100.0/h.Capacity, 1) AS Occupancy",
}

QUERY_BASE = """
FROM Genres g
JOIN Movies m ON m.GenreID = g.GenreID
JOIN Sessions s ON s.MovieID = m.MovieID
JOIN Halls h ON h.HallID = s.HallID
LEFT JOIN Tickets t ON t.SessionID = s.SessionID
"""

QUERY_FILTERS = {
    "m.Title": "m.Title",
    "m.AgeRating": "m.AgeRating",
    "g.GenreName": "g.GenreName",
    "h.HallName": "h.HallName",
    "h.IsVIP": "h.IsVIP",
    "s.StartTime": "s.StartTime",
    "s.TicketPrice": "s.TicketPrice",
    "t.CustomerName": "t.CustomerName",
    "t.PurchaseDate": "t.PurchaseDate",
    "t.IsPaid": "t.IsPaid",
}


def run_query(db, payload):
    kind = payload.get("kind", "custom")
    if kind == "schedule":
        query = """
            SELECT m.Title, m.AgeRating, g.GenreName AS Genre, h.HallName AS Hall,
                   h.Capacity, s.StartTime, s.TicketPrice
            FROM Genres g JOIN Movies m ON m.GenreID = g.GenreID
            JOIN Sessions s ON s.MovieID = m.MovieID
            JOIN Halls h ON h.HallID = s.HallID
            WHERE h.IsVIP = 0
            ORDER BY s.StartTime ASC LIMIT 200
        """
        return query, [], rows_as_dicts(db.execute(query))
    if kind == "revenue":
        query = """
            SELECT m.Title, COUNT(CASE WHEN t.IsPaid = 1 THEN t.TicketID END) AS TicketsSold,
                   COALESCE(SUM(CASE WHEN t.IsPaid = 1 THEN s.TicketPrice ELSE 0 END), 0) AS Revenue
            FROM Movies m JOIN Sessions s ON s.MovieID = m.MovieID
            JOIN Tickets t ON t.SessionID = s.SessionID
            GROUP BY m.MovieID HAVING SUM(CASE WHEN t.IsPaid = 1 THEN s.TicketPrice ELSE 0 END) > 300
            ORDER BY Revenue DESC LIMIT 200
        """
        return query, [], rows_as_dicts(db.execute(query))
    if kind == "occupancy":
        query = """
            SELECT s.SessionID, m.Title, s.StartTime, h.HallName, h.Capacity,
                   COUNT(CASE WHEN t.IsPaid = 1 THEN t.TicketID END) AS TicketsSold,
                   ROUND(COUNT(CASE WHEN t.IsPaid = 1 THEN t.TicketID END) * 100.0 / h.Capacity, 1) AS Occupancy
            FROM Sessions s JOIN Movies m ON m.MovieID = s.MovieID
            JOIN Halls h ON h.HallID = s.HallID
            LEFT JOIN Tickets t ON t.SessionID = s.SessionID
            GROUP BY s.SessionID ORDER BY Occupancy DESC LIMIT 200
        """
        return query, [], rows_as_dicts(db.execute(query))
    if kind == "customers":
        query = """
            SELECT t.CustomerName, COUNT(t.TicketID) AS TicketsBought
            FROM Tickets t WHERE t.IsPaid = 1
            GROUP BY t.CustomerName HAVING COUNT(t.TicketID) > 2
            ORDER BY TicketsBought DESC LIMIT 200
        """
        return query, [], rows_as_dicts(db.execute(query))
    if kind == "client":
        client = str(payload.get("client", "")).strip()
        start = str(payload.get("start", ""))
        end = str(payload.get("end", ""))
        if not client:
            raise ValueError("Укажіть ім’я клієнта для пошуку.")
        if not valid_iso_date(start) or not valid_iso_date(end):
            raise ValueError("Виберіть коректний діапазон дат.")
        query = """
            SELECT t.TicketID, t.CustomerName, t.CustomerPhone, t.SeatNumber,
                   t.PurchaseDate, t.IsPaid, s.StartTime, s.TicketPrice,
                   m.Title, h.HallName
            FROM Tickets t JOIN Sessions s ON s.SessionID = t.SessionID
            JOIN Movies m ON m.MovieID = s.MovieID JOIN Halls h ON h.HallID = s.HallID
            WHERE t.CustomerName LIKE ? AND date(t.PurchaseDate) BETWEEN ? AND ?
            ORDER BY t.PurchaseDate DESC LIMIT 200
        """
        values = [f"%{client}%", start, end]
        return query, values, rows_as_dicts(db.execute(query, values))
    fields = payload.get("fields") or ["m.Title", "g.GenreName", "s.StartTime", "s.TicketPrice"]
    if not isinstance(fields, list) or not 1 <= len(fields) <= 12 or any(field not in QUERY_FIELDS for field in fields):
        raise ValueError("Оберіть від 1 до 12 доступних полів.")
    filters = payload.get("filters") or []
    if not isinstance(filters, list) or len(filters) > 8:
        raise ValueError("Дозволено не більше восьми умов.")
    filter_clauses = []
    parameters = []
    operators = {"=", "!=", ">", ">=", "<", "<=", "contains"}
    for item in filters:
        field = item.get("field")
        operator = item.get("operator")
        value = item.get("value")
        if field not in QUERY_FILTERS or operator not in operators or value is None:
            raise ValueError("Перевірте поле, оператор і значення фільтра.")
        if field == "h.IsVIP":
            if str(value) not in {"0", "1"}:
                raise ValueError("Для VIP-фільтра виберіть 0 або 1.")
            value = int(value)
        if operator == "contains":
            filter_clauses.append(f"{QUERY_FILTERS[field]} LIKE ?")
            parameters.append(f"%{value}%")
        else:
            filter_clauses.append(f"{QUERY_FILTERS[field]} {operator} ?")
            parameters.append(value)
    selected = ", ".join(QUERY_FIELDS[field] for field in fields)
    query = f"SELECT {selected} {QUERY_BASE}"
    if filter_clauses:
        query += " WHERE " + " AND ".join(filter_clauses)
    sort_field = payload.get("sort") if payload.get("sort") in QUERY_FIELDS else fields[0]
    direction = "DESC" if payload.get("direction") == "DESC" else "ASC"
    query += f" ORDER BY {sort_field} {direction} LIMIT 200"
    return query, parameters, rows_as_dicts(db.execute(query, parameters))


def valid_iso_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def report_data(db, start, end):
    if not valid_iso_date(start) or not valid_iso_date(end) or start > end:
        raise ValueError("Вкажіть коректний період звіту.")
    params = (start, end)
    revenue = rows_as_dicts(db.execute(
        """
        SELECT m.Title, COUNT(CASE WHEN t.IsPaid = 1 THEN t.TicketID END) AS TicketsSold,
               COALESCE(SUM(CASE WHEN t.IsPaid = 1 THEN s.TicketPrice ELSE 0 END), 0) AS Revenue
        FROM Movies m JOIN Sessions s ON s.MovieID = m.MovieID
        LEFT JOIN Tickets t ON t.SessionID = s.SessionID AND date(t.PurchaseDate) BETWEEN ? AND ?
        GROUP BY m.MovieID ORDER BY Revenue DESC, m.Title
        """,
        params,
    ))
    halls = rows_as_dicts(db.execute(
        """
        SELECT h.HallName, h.Capacity, COUNT(CASE WHEN t.IsPaid = 1 THEN t.TicketID END) AS TicketsSold,
               ROUND(COUNT(CASE WHEN t.IsPaid = 1 THEN t.TicketID END) * 100.0 / h.Capacity, 1) AS Occupancy,
               COALESCE(SUM(CASE WHEN t.IsPaid = 1 THEN s.TicketPrice ELSE 0 END), 0) AS Revenue
        FROM Halls h LEFT JOIN Sessions s ON s.HallID = h.HallID
        LEFT JOIN Tickets t ON t.SessionID = s.SessionID AND date(t.PurchaseDate) BETWEEN ? AND ?
        GROUP BY h.HallID ORDER BY Revenue DESC
        """,
        params,
    ))
    time_slots = rows_as_dicts(db.execute(
        """
        SELECT CASE CAST(strftime('%w', s.StartTime) AS INTEGER)
                   WHEN 0 THEN 'Неділя' WHEN 1 THEN 'Понеділок' WHEN 2 THEN 'Вівторок'
                   WHEN 3 THEN 'Середа' WHEN 4 THEN 'Четвер' WHEN 5 THEN 'П’ятниця'
                   ELSE 'Субота' END AS Day,
               CASE WHEN CAST(strftime('%H', s.StartTime) AS INTEGER) < 13 THEN '10:00–13:00'
                    WHEN CAST(strftime('%H', s.StartTime) AS INTEGER) < 17 THEN '13:00–17:00'
                    WHEN CAST(strftime('%H', s.StartTime) AS INTEGER) < 21 THEN '17:00–21:00'
                    ELSE '21:00+' END AS TimeSlot,
               COUNT(t.TicketID) AS TicketsSold,
               COALESCE(SUM(s.TicketPrice), 0) AS Revenue
        FROM Tickets t JOIN Sessions s ON s.SessionID = t.SessionID
        WHERE t.IsPaid = 1 AND date(t.PurchaseDate) BETWEEN ? AND ?
        GROUP BY Day, TimeSlot ORDER BY MIN(s.StartTime)
        """,
        params,
    ))
    totals = db.execute(
        """
        SELECT COUNT(*) AS tickets,
               COALESCE(SUM(s.TicketPrice), 0) AS revenue,
               COALESCE(AVG(s.TicketPrice), 0) AS average_price
        FROM Tickets t JOIN Sessions s ON s.SessionID = t.SessionID
        WHERE t.IsPaid = 1 AND date(t.PurchaseDate) BETWEEN ? AND ?
        """,
        params,
    ).fetchone()
    return {"totals": dict(totals), "revenue": revenue, "halls": halls, "timeSlots": time_slots}


def clean_string(payload, key, label, max_length, required=True):
    value = payload.get(key, "")
    if not isinstance(value, str):
        raise ValueError(f"Поле «{label}» має бути текстом.")
    value = value.strip()
    if required and not value:
        raise ValueError(f"Заповніть поле «{label}».")
    if len(value) > max_length:
        raise ValueError(f"Поле «{label}» не може перевищувати {max_length} символів.")
    return value


def positive_int(payload, key, label, allow_zero=False):
    try:
        value = int(payload.get(key))
    except (TypeError, ValueError):
        raise ValueError(f"Поле «{label}» має бути цілим числом.")
    if value < (0 if allow_zero else 1):
        raise ValueError(f"Поле «{label}» має бути не менше {0 if allow_zero else 1}.")
    return value


def nonnegative_number(payload, key, label):
    try:
        value = float(payload.get(key))
    except (TypeError, ValueError):
        raise ValueError(f"Поле «{label}» має бути числом.")
    if value < 0:
        raise ValueError(f"Поле «{label}» не може бути від’ємним.")
    return value


def fetch_movie(db, movie_id):
    return db.execute(
        """
        SELECT m.MovieID, m.Title, m.GenreID, g.GenreName, m.DurationMinutes,
               m.AgeRating, m.BasePrice, m.Synopsis, m.Accent,
               COUNT(DISTINCT s.SessionID) AS Sessions, COUNT(t.TicketID) AS Tickets
        FROM Movies m JOIN Genres g ON g.GenreID = m.GenreID
        LEFT JOIN Sessions s ON s.MovieID = m.MovieID
        LEFT JOIN Tickets t ON t.SessionID = s.SessionID
        WHERE m.MovieID = ? GROUP BY m.MovieID
        """,
        (movie_id,),
    ).fetchone()


def fetch_ticket(db, ticket_id):
    return db.execute(
        """
        SELECT t.TicketID, t.SessionID, t.CustomerName, t.CustomerPhone,
               t.SeatNumber, t.PurchaseDate, t.IsPaid, s.StartTime, s.TicketPrice,
               m.Title, m.AgeRating, m.DurationMinutes, h.HallName, g.GenreName
        FROM Tickets t JOIN Sessions s ON s.SessionID = t.SessionID
        JOIN Movies m ON m.MovieID = s.MovieID JOIN Halls h ON h.HallID = s.HallID
        JOIN Genres g ON g.GenreID = m.GenreID
        WHERE t.TicketID = ?
        """,
        (ticket_id,),
    ).fetchone()


class CinemaHubHandler(BaseHTTPRequestHandler):
    server_version = "CinemaHub/1.0"

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")

    def send_json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 1_000_000:
            raise ValueError("Запит завеликий.")
        try:
            result = json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("Не вдалося розібрати тіло запиту.")
        if not isinstance(result, dict):
            raise ValueError("Очікується JSON-об’єкт.")
        return result

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)
        try:
            with connect_db() as db:
                if path == "/api/overview":
                    return self.send_json(overview(db))
                if path == "/api/movies":
                    movies = rows_as_dicts(db.execute(
                        """
                        SELECT m.MovieID, m.Title, m.GenreID, g.GenreName, m.DurationMinutes,
                               m.AgeRating, m.BasePrice, m.Synopsis, m.Accent,
                               COUNT(DISTINCT s.SessionID) AS Sessions,
                               COUNT(DISTINCT CASE WHEN t.IsPaid = 1 THEN t.TicketID END) AS Tickets
                        FROM Movies m JOIN Genres g ON g.GenreID = m.GenreID
                        LEFT JOIN Sessions s ON s.MovieID = m.MovieID
                        LEFT JOIN Tickets t ON t.SessionID = s.SessionID
                        GROUP BY m.MovieID ORDER BY m.Title
                        """
                    ))
                    return self.send_json(movies)
                if path == "/api/genres":
                    return self.send_json(rows_as_dicts(db.execute("SELECT * FROM Genres ORDER BY GenreName")))
                if path == "/api/halls":
                    return self.send_json(rows_as_dicts(db.execute(
                        """
                        SELECT h.HallID, h.HallName, h.Capacity, h.IsVIP,
                               COUNT(DISTINCT s.SessionID) AS Sessions,
                               COUNT(CASE WHEN t.IsPaid = 1 THEN t.TicketID END) AS TicketsSold,
                               ROUND(COUNT(CASE WHEN t.IsPaid = 1 THEN t.TicketID END) * 100.0 / h.Capacity, 1) AS Occupancy
                        FROM Halls h LEFT JOIN Sessions s ON s.HallID = h.HallID
                        LEFT JOIN Tickets t ON t.SessionID = s.SessionID
                        GROUP BY h.HallID ORDER BY h.HallID
                        """
                    )))
                if path == "/api/sessions":
                    day = query.get("date", [""])[0]
                    if day and not valid_iso_date(day):
                        raise ValueError("Вкажіть дату у форматі РРРР-ММ-ДД.")
                    return self.send_json(list_sessions(db, day))
                if path == "/api/tickets":
                    status = query.get("status", ["all"])[0]
                    filters = []
                    values = []
                    if status in ("paid", "pending"):
                        filters.append("t.IsPaid = ?")
                        values.append(1 if status == "paid" else 0)
                    search = query.get("search", [""])[0].strip()
                    if search:
                        filters.append("(t.CustomerName LIKE ? OR m.Title LIKE ? OR CAST(t.TicketID AS TEXT) = ?)")
                        values.extend((f"%{search}%", f"%{search}%", search.lstrip("#")))
                    where = "WHERE " + " AND ".join(filters) if filters else ""
                    return self.send_json(rows_as_dicts(db.execute(
                        f"""
                        SELECT t.TicketID, t.SessionID, t.CustomerName, t.CustomerPhone, t.SeatNumber,
                               t.PurchaseDate, t.IsPaid, s.StartTime, s.TicketPrice, m.Title, h.HallName
                        FROM Tickets t JOIN Sessions s ON s.SessionID = t.SessionID
                        JOIN Movies m ON m.MovieID = s.MovieID JOIN Halls h ON h.HallID = s.HallID
                        {where} ORDER BY t.PurchaseDate DESC, t.TicketID DESC LIMIT 500
                        """,
                        values,
                    )))
                if path == "/api/reports":
                    start = query.get("start", [date.today().replace(day=1).isoformat()])[0]
                    end = query.get("end", [date.today().isoformat()])[0]
                    return self.send_json(report_data(db, start, end))
                if path == "/api/ticket":
                    try:
                        ticket_id = int(query.get("id", [""])[0])
                    except ValueError:
                        raise ValueError("Укажіть коректний номер квитка.")
                    if ticket_id < 1:
                        raise ValueError("Укажіть коректний номер квитка.")
                    ticket = fetch_ticket(db, ticket_id)
                    if ticket is None:
                        return self.send_json({"error": "Квиток не знайдено."}, 404)
                    return self.send_json(dict(ticket))
            if path == "/schema.sql":
                return self.send_file(BASE_DIR / "sql" / "cinemahub.sql")
            return self.send_static(path)
        except ValueError as error:
            self.send_json({"error": str(error)}, 400)
        except sqlite3.IntegrityError as error:
            message = str(error)
            if "UNIQUE constraint failed: Tickets.SessionID, Tickets.SeatNumber" in message:
                self.send_json({"error": "Це місце вже зайняте на обраному сеансі."}, 409)
            elif "UNIQUE constraint failed: Sessions.HallID, Sessions.StartTime" in message:
                self.send_json({"error": "У цій залі на цей час уже заплановано сеанс."}, 409)
            elif "UNIQUE constraint failed: Genres.GenreName" in message or "UNIQUE constraint failed: Halls.HallName" in message:
                self.send_json({"error": "Запис із такою назвою вже існує."}, 409)
            else:
                self.send_json({"error": "Зміни порушують зв’язки або обмеження бази даних."}, 409)
        except Exception:
            traceback.print_exc()
            self.send_json({"error": "Не вдалося обробити запит. Перегляньте журнал сервера."}, 500)

    def send_file(self, path):
        if not path.is_file():
            return self.send_json({"error": "Файл не знайдено."}, 404)
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, requested_path):
        if requested_path == "/":
            requested_path = "/index.html"
        target = (STATIC_DIR / requested_path.lstrip("/")).resolve()
        if STATIC_DIR.resolve() not in target.parents and target != STATIC_DIR.resolve():
            return self.send_json({"error": "Некоректний шлях."}, 400)
        if not target.is_file():
            return self.send_json({"error": "Сторінку не знайдено."}, 404)
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            with connect_db() as db:
                if parsed.path == "/api/movies":
                    return self.create_movie(db, payload)
                if parsed.path == "/api/genres":
                    name = clean_string(payload, "genreName", "назву жанру", 50)
                    description = clean_string(payload, "description", "опис", 255, False)
                    cursor = db.execute("INSERT INTO Genres (GenreName, Description) VALUES (?, ?)", (name, description))
                    genre = db.execute("SELECT * FROM Genres WHERE GenreID = ?", (cursor.lastrowid,)).fetchone()
                    return self.send_json(dict(genre), 201)
                if parsed.path == "/api/halls":
                    name = clean_string(payload, "hallName", "назву залу", 50)
                    capacity = positive_int(payload, "capacity", "місткість")
                    is_vip = payload.get("isVip", False)
                    if is_vip not in (0, 1, False, True):
                        raise ValueError("Ознака VIP має бути 0 або 1.")
                    cursor = db.execute(
                        "INSERT INTO Halls (HallName, Capacity, IsVIP) VALUES (?, ?, ?)",
                        (name, capacity, int(is_vip)),
                    )
                    hall = db.execute("SELECT * FROM Halls WHERE HallID = ?", (cursor.lastrowid,)).fetchone()
                    return self.send_json(dict(hall), 201)
                if parsed.path == "/api/sessions":
                    return self.create_session(db, payload)
                if parsed.path == "/api/tickets":
                    return self.create_ticket(db, payload)
                if parsed.path == "/api/query":
                    sql, parameters, result = run_query(db, payload)
                    return self.send_json({"sql": sql.strip(), "parameters": parameters, "columns": list(result[0].keys()) if result else [], "rows": result})
            return self.send_json({"error": "Ресурс не знайдено."}, 404)
        except ValueError as error:
            self.send_json({"error": str(error)}, 400)
        except sqlite3.IntegrityError as error:
            message = str(error)
            if "UNIQUE constraint failed: Tickets.SessionID, Tickets.SeatNumber" in message:
                self.send_json({"error": "Це місце вже зайняте на обраному сеансі."}, 409)
            elif "UNIQUE constraint failed: Sessions.HallID, Sessions.StartTime" in message:
                self.send_json({"error": "У цій залі на цей час уже заплановано сеанс."}, 409)
            elif "UNIQUE constraint failed: Genres.GenreName" in message:
                self.send_json({"error": "Жанр із такою назвою вже існує."}, 409)
            else:
                self.send_json({"error": "Запис порушує обмеження бази даних."}, 409)
        except Exception:
            traceback.print_exc()
            self.send_json({"error": "Не вдалося обробити запит. Перегляньте журнал сервера."}, 500)

    def create_movie(self, db, payload):
        values = self.movie_values(payload)
        cursor = db.execute(
            """
            INSERT INTO Movies (Title, GenreID, DurationMinutes, AgeRating, BasePrice, Synopsis, Accent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        movie = fetch_movie(db, cursor.lastrowid)
        if movie is None:
            raise RuntimeError("Створений фільм не вдалося повторно завантажити.")
        self.send_json(dict(movie), 201)

    def movie_values(self, payload):
        title = clean_string(payload, "title", "назву фільму", 150)
        genre_id = positive_int(payload, "genreId", "жанр")
        duration = positive_int(payload, "durationMinutes", "тривалість")
        base_price = nonnegative_number(payload, "basePrice", "базова ціна")
        age_rating = clean_string(payload, "ageRating", "віковий рейтинг", 10)
        synopsis = clean_string(payload, "synopsis", "опис", 500, False)
        accent = clean_string(payload, "accent", "колір постера", 7, False) or "#9a583b"
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
            raise ValueError("Колір постера має бути у форматі #RRGGBB.")
        return title, genre_id, duration, age_rating, base_price, synopsis, accent

    def create_session(self, db, payload):
        movie_id = positive_int(payload, "movieId", "фільм")
        hall_id = positive_int(payload, "hallId", "кінозал")
        start_time = clean_string(payload, "startTime", "дату і час сеансу", 16)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", start_time):
            raise ValueError("Вкажіть дату й час сеансу.")
        try:
            parsed_time = datetime.fromisoformat(start_time)
        except ValueError:
            raise ValueError("Вкажіть дату й час сеансу.")
        ticket_price = nonnegative_number(payload, "ticketPrice", "ціну квитка")
        movie = db.execute("SELECT DurationMinutes FROM Movies WHERE MovieID = ?", (movie_id,)).fetchone()
        hall = db.execute("SELECT HallID FROM Halls WHERE HallID = ?", (hall_id,)).fetchone()
        if movie is None:
            raise ValueError("Обраний фільм не знайдено.")
        if hall is None:
            raise ValueError("Обрану залу не знайдено.")
        finish = parsed_time + timedelta(minutes=movie["DurationMinutes"])
        conflicts = db.execute(
            """
            SELECT m.Title FROM Sessions s JOIN Movies m ON m.MovieID = s.MovieID
            WHERE s.HallID = ?
              AND datetime(s.StartTime) < datetime(?)
              AND datetime(s.StartTime, '+' || m.DurationMinutes || ' minutes') > datetime(?)
            """,
            (hall_id, finish.isoformat(timespec="minutes"), parsed_time.isoformat(timespec="minutes")),
        ).fetchone()
        if conflicts:
            raise ValueError(f"Час перетинається із сеансом «{conflicts['Title']}» у цій залі.")
        cursor = db.execute(
            "INSERT INTO Sessions (MovieID, HallID, StartTime, TicketPrice) VALUES (?, ?, ?, ?)",
            (movie_id, hall_id, parsed_time.isoformat(timespec="minutes"), ticket_price),
        )
        session = next((item for item in list_sessions(db) if item["SessionID"] == cursor.lastrowid), None)
        if session is None:
            raise RuntimeError("Створений сеанс не вдалося повторно завантажити.")
        self.send_json(session, 201)

    def create_ticket(self, db, payload):
        session_id = positive_int(payload, "sessionId", "сеанс")
        customer_name = clean_string(payload, "customerName", "ім’я покупця", 100)
        customer_phone = clean_string(payload, "customerPhone", "телефон", 20, False)
        seat_number = positive_int(payload, "seatNumber", "місце")
        session = db.execute(
            """
            SELECT s.StartTime, h.Capacity FROM Sessions s JOIN Halls h ON h.HallID = s.HallID
            WHERE s.SessionID = ?
            """,
            (session_id,),
        ).fetchone()
        if session is None:
            raise ValueError("Обраний сеанс не знайдено.")
        if seat_number > session["Capacity"]:
            raise ValueError(f"У цій залі лише {session['Capacity']} місць.")
        if db.execute("SELECT 1 FROM Tickets WHERE SessionID = ? AND SeatNumber = ?", (session_id, seat_number)).fetchone():
            raise ValueError("Це місце вже зайняте на обраному сеансі.")
        cursor = db.execute(
            """
            INSERT INTO Tickets (SessionID, CustomerName, CustomerPhone, SeatNumber, PurchaseDate, IsPaid)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (session_id, customer_name, customer_phone, seat_number, datetime.now().isoformat(timespec="minutes")),
        )
        ticket = fetch_ticket(db, cursor.lastrowid)
        if ticket is None:
            raise RuntimeError("Створений квиток не вдалося повторно завантажити.")
        self.send_json(dict(ticket), 201)

    def do_PUT(self):
        match = re.fullmatch(r"/api/movies/(\d+)", urlparse(self.path).path)
        if not match:
            return self.send_json({"error": "Ресурс не знайдено."}, 404)
        try:
            payload = self.read_json()
            with connect_db() as db:
                values = self.movie_values(payload)
                movie_id = int(match.group(1))
                cursor = db.execute(
                    """
                    UPDATE Movies SET Title = ?, GenreID = ?, DurationMinutes = ?, AgeRating = ?,
                                      BasePrice = ?, Synopsis = ?, Accent = ?
                    WHERE MovieID = ?
                    """,
                    (*values, movie_id),
                )
                if cursor.rowcount == 0:
                    return self.send_json({"error": "Фільм не знайдено."}, 404)
                movie = fetch_movie(db, movie_id)
                self.send_json(dict(movie))
        except ValueError as error:
            self.send_json({"error": str(error)}, 400)
        except sqlite3.IntegrityError:
            self.send_json({"error": "Перевірте обраний жанр і значення полів."}, 409)
        except Exception:
            traceback.print_exc()
            self.send_json({"error": "Не вдалося оновити фільм."}, 500)

    def do_PATCH(self):
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            with connect_db() as db:
                match = re.fullmatch(r"/api/tickets/(\d+)", parsed.path)
                if match:
                    ticket_id = int(match.group(1))
                    paid = payload.get("isPaid")
                    if paid not in (0, 1, False, True):
                        raise ValueError("Статус оплати має бути 0 або 1.")
                    cursor = db.execute("UPDATE Tickets SET IsPaid = ? WHERE TicketID = ?", (int(paid), ticket_id))
                    if cursor.rowcount == 0:
                        return self.send_json({"error": "Квиток не знайдено."}, 404)
                    return self.send_json(dict(fetch_ticket(db, ticket_id)))
            self.send_json({"error": "Ресурс не знайдено."}, 404)
        except ValueError as error:
            self.send_json({"error": str(error)}, 400)
        except Exception:
            traceback.print_exc()
            self.send_json({"error": "Не вдалося оновити квиток."}, 500)

    def do_DELETE(self):
        match = re.fullmatch(r"/api/(movies|sessions|tickets|halls|genres)/(\d+)", urlparse(self.path).path)
        if not match:
            return self.send_json({"error": "Ресурс не знайдено."}, 404)
        table, record_id = match.group(1), int(match.group(2))
        table_data = {
            "movies": ("Movies", "MovieID"),
            "sessions": ("Sessions", "SessionID"),
            "tickets": ("Tickets", "TicketID"),
            "halls": ("Halls", "HallID"),
            "genres": ("Genres", "GenreID"),
        }
        table_name, primary_key = table_data[table]
        try:
            with connect_db() as db:
                cursor = db.execute(f"DELETE FROM {table_name} WHERE {primary_key} = ?", (record_id,))
                if not cursor.rowcount:
                    return self.send_json({"error": "Запис не знайдено."}, 404)
            self.send_json({"deleted": record_id})
        except sqlite3.IntegrityError:
            self.send_json({"error": "Не можна видалити зал або жанр, поки його використовують сеанси чи фільми."}, 409)
        except Exception:
            traceback.print_exc()
            self.send_json({"error": "Не вдалося видалити запис."}, 500)


def main():
    initialize_database()
    host = os.environ.get("CINEMAHUB_HOST", "127.0.0.1")
    port = int(os.environ.get("CINEMAHUB_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), CinemaHubHandler)
    print(f"CinemaHub запущено: http://{host}:{port}")
    print(f"База даних: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер CinemaHub зупинено.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
