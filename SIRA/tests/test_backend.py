import os
import tempfile
import unittest
from pathlib import Path

import database
import backend

class SiraApiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_path = database.DB_PATH
        database.DB_PATH = Path(self.tempdir.name) / "test.db"
        database.init_db()
        self.client = backend.app.test_client()

    def tearDown(self):
        database.DB_PATH = self.original_path
        self.tempdir.cleanup()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_alerts_filters(self):
        response = self.client.get("/api/alerts?risk_type=Enchente")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(row["risk_type"] == "Enchente" for row in response.get_json()))

    def test_invalid_latitude_rejected(self):
        payload = {"title":"Teste", "risk_type":"Enchente", "severity":"Alerta", "location":"Local",
                   "lat":100, "lng":0, "issuer":"Teste", "description":"Descrição", "instructions":"Orientação",
                   "date_time":"2026-10-20 10:00"}
        response = self.client.post("/api/alerts", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_valid_alert_created(self):
        payload = {"title":"Alerta de teste", "risk_type":"Enchente", "severity":"Alerta", "location":"Local",
                   "lat":-22.9, "lng":-47.0, "issuer":"Teste", "description":"Descrição", "instructions":"Orientação",
                   "date_time":"2026-10-20 10:00"}
        response = self.client.post("/api/alerts", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.get_json())

if __name__ == "__main__":
    unittest.main()
