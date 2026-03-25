import threading
import time
import requests

from ..NodoD import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_register_nodes():

    r1 = client.post("/register", json={"host": "127.0.0.1", "port": 5001})

    assert r1.status_code == 200

    r2 = client.post("/register", json={"host": "127.0.0.1", "port": 5002})

    peers = r2.json()["nodosPares"]

    assert len(peers) == 1


def test_health():

    r = client.get("/health")

    assert r.status_code == 200

    assert "status" in r.json()