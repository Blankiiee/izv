import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import server as cinema


class CinemaHubTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "cinemahub.sqlite3"
        self.database_patch = patch.object(cinema, "DB_PATH", self.database_path)
        self.database_patch.start()
        cinema.initialize_database()
        self.http_server = ThreadingHTTPServer(("127.0.0.1", 0), cinema.CinemaHubHandler)
        self.thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.http_server.server_address[1]}"

    def tearDown(self):
        self.http_server.shutdown()
        self.http_server.server_close()
        self.thread.join(timeout=2)
        self.database_patch.stop()
        self.temporary_directory.cleanup()

    def call_json(self, path, method="GET", payload=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urlopen(request) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as response:
            return response.code, json.loads(response.read().decode("utf-8"))

    def test_dashboard_uses_seeded_cinema_records(self):
        status, result = self.call_json("/api/overview")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(result["metrics"]["movie_count"], 6)
        self.assertGreater(result["metrics"]["today_sessions"], 0)
        self.assertGreater(result["metrics"]["revenue"], 0)

    def test_visual_builder_executes_join_and_left_join_examples(self):
        schedule_status, schedule = self.call_json("/api/query", "POST", {"kind": "schedule"})
        occupancy_status, occupancy = self.call_json("/api/query", "POST", {"kind": "occupancy"})
        self.assertEqual((schedule_status, occupancy_status), (200, 200))
        self.assertTrue(schedule["rows"])
        self.assertTrue(all(row["Hall"] != "VIP Lounge" for row in schedule["rows"]))
        self.assertTrue(any(row["TicketsSold"] == 0 for row in occupancy["rows"]))
        self.assertIn("LEFT JOIN", occupancy["sql"])

    def test_client_search_uses_parameters(self):
        status, result = self.call_json(
            "/api/query",
            "POST",
            {"kind": "client", "client": "Олександр", "start": "2000-01-01", "end": "2099-12-31"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(result["rows"])
        self.assertEqual(result["parameters"][0], "%Олександр%")
        invalid_status, error = self.call_json(
            "/api/query",
            "POST",
            {"kind": "client", "client": "x' OR 1=1 --", "start": "2000-01-01", "end": "2099-12-31"},
        )
        self.assertEqual(invalid_status, 200)
        self.assertFalse(error["rows"])

    def test_duplicate_seat_cannot_be_sold_twice(self):
        _, tickets = self.call_json("/api/tickets")
        occupied_ticket = tickets[0]
        status, result = self.call_json(
            "/api/tickets",
            "POST",
            {
                "sessionId": occupied_ticket["SessionID"],
                "customerName": "Тестовий покупець",
                "seatNumber": occupied_ticket["SeatNumber"],
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("зайняте", result["error"])

    def test_schedule_rejects_overlapping_show(self):
        _, sessions = self.call_json("/api/sessions")
        session = sessions[0]
        status, result = self.call_json(
            "/api/sessions",
            "POST",
            {
                "movieId": session["MovieID"],
                "hallId": session["HallID"],
                "startTime": session["StartTime"][:16],
                "ticketPrice": 200,
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("перетинається", result["error"])

    def test_movie_can_be_created_updated_and_removed(self):
        _, genres = self.call_json("/api/genres")
        status, movie = self.call_json(
            "/api/movies",
            "POST",
            {
                "title": "Тестова прем’єра",
                "genreId": genres[0]["GenreID"],
                "durationMinutes": 100,
                "ageRating": "12+",
                "basePrice": 140,
                "synopsis": "Перевірка повного циклу.",
                "accent": "#926844",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(movie["Title"], "Тестова прем’єра")
        status, updated = self.call_json(
            f"/api/movies/{movie['MovieID']}",
            "PUT",
            {
                "title": "Оновлена прем’єра",
                "genreId": genres[0]["GenreID"],
                "durationMinutes": 105,
                "ageRating": "12+",
                "basePrice": 150,
                "synopsis": "",
                "accent": "#926844",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["Title"], "Оновлена прем’єра")
        status, _ = self.call_json(f"/api/movies/{movie['MovieID']}", "DELETE")
        self.assertEqual(status, 200)

    def test_hall_and_genre_can_be_created_and_removed(self):
        hall_status, hall = self.call_json(
            "/api/halls",
            "POST",
            {"hallName": "Зал для перевірки", "capacity": 36, "isVip": True},
        )
        genre_status, genre = self.call_json(
            "/api/genres",
            "POST",
            {"genreName": "Історія для перевірки", "description": "Тестовий жанр."},
        )
        self.assertEqual((hall_status, genre_status), (201, 201))
        self.assertEqual(hall["Capacity"], 36)
        self.assertEqual(genre["GenreName"], "Історія для перевірки")
        self.assertEqual(self.call_json(f"/api/halls/{hall['HallID']}", "DELETE")[0], 200)
        self.assertEqual(self.call_json(f"/api/genres/{genre['GenreID']}", "DELETE")[0], 200)

    def test_ticket_sale_and_payment_update(self):
        _, sessions = self.call_json("/api/sessions")
        session = sessions[0]
        seat = session["Capacity"]
        status, ticket = self.call_json(
            "/api/tickets",
            "POST",
            {
                "sessionId": session["SessionID"],
                "customerName": "Тестовий покупець",
                "seatNumber": seat,
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(ticket["IsPaid"], 1)
        self.assertEqual(ticket["SeatNumber"], seat)
        update_status, updated = self.call_json(
            f"/api/tickets/{ticket['TicketID']}",
            "PATCH",
            {"isPaid": 0},
        )
        self.assertEqual(update_status, 200)
        self.assertEqual(updated["IsPaid"], 0)

    def test_reports_return_revenue_and_hall_statistics(self):
        status, result = self.call_json("/api/reports")
        self.assertEqual(status, 200)
        self.assertGreater(result["totals"]["tickets"], 0)
        self.assertGreater(result["totals"]["revenue"], 0)
        self.assertTrue(result["revenue"])
        self.assertTrue(result["halls"])
        self.assertTrue(result["timeSlots"])

    def test_web_interface_and_sql_server_script_are_served(self):
        with urlopen(self.base_url + "/") as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"CinemaHub", response.read())
        with urlopen(self.base_url + "/schema.sql") as response:
            self.assertEqual(response.status, 200)
            self.assertIn("CREATE TABLE dbo.Movies", response.read().decode("utf-8"))
        with urlopen(self.base_url + "/app.js") as response:
            self.assertEqual(response.status, 200)
            self.assertIn("Фільмотека", response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
