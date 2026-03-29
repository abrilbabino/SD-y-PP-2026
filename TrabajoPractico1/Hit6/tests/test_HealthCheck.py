import threading
import time
import requests

from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_register_nodes():

    r1 = client.post("/Hit6/register", json={"host": "127.0.0.1", "port": 5001})

    assert r1.status_code == 200

    r2 = client.post("/Hit6/register", json={"host": "127.0.0.1", "port": 5002})

    peers = r2.json()["nodosPares"]

    assert len(peers) == 1


def test_health():

    r = client.get("/Hit6/health")

    assert r.status_code == 200

    assert "status" in r.json()