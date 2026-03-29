# import time
# from fastapi.testclient import TestClient

# from ..NodoD import app, nodos_actuales, nodos_futuros, lock

# client = TestClient(app)


# def limpiar_estado():
#     with lock:
#         nodos_actuales.clear()
#         nodos_futuros.clear()


# def esperar_cambio_ventana():
#     ahora = int(time.time())
#     sleep_time = 60 - (ahora % 60) + 1  # +1 para asegurar cambio
#     time.sleep(sleep_time)


# def test_registro_diferido():

#     limpiar_estado()

#     # Registro nodo 1
#     r1 = client.post("/register", json={"host": "127.0.0.1", "port": 5001})
#     assert r1.status_code == 200

#     # Ahora debería aparecer en futuros
#     assert r1.json()["nodosPares"] == [{"host": "127.0.0.1", "port": 5001}]

#     # Registro nodo 2
#     r2 = client.post("/register", json={"host": "127.0.0.1", "port": 5002})
#     assert r2.status_code == 200

#     # Debería devolver ambos futuros
#     assert {"host": "127.0.0.1", "port": 5001} in r2.json()["nodosPares"]
#     assert {"host": "127.0.0.1", "port": 5002} in r2.json()["nodosPares"]

#     # Verifico estado interno
#     with lock:
#         assert len(nodos_futuros) == 2
#         assert len(nodos_actuales) == 0

# def test_cambio_de_ventana():

#     limpiar_estado()

#     # Registro nodos en futuros
#     client.post("/register", json={"host": "127.0.0.1", "port": 5001})
#     client.post("/register", json={"host": "127.0.0.1", "port": 5002})

#     # FORZAR cambio de ventana (en vez de esperar)
#     with lock:
#         nodos_actuales[:] = nodos_futuros
#         nodos_futuros.clear()

#     # Ahora registro un tercero
#     r = client.post("/register", json={"host": "127.0.0.1", "port": 5003})
#     peers = r.json()["nodosPares"]

#     # Como la función devuelve futuros, debería contener solo el nuevo
#     assert peers == [{"host": "127.0.0.1", "port": 5003}]

#     # El nuevo queda en futuros
#     with lock:
#         assert {"host": "127.0.0.1", "port": 5003} in nodos_futuros


# def test_health():

#     r = client.get("/health")

#     assert r.status_code == 200

#     data = r.json()

#     assert "status" in data
#     assert "nodosActuales" in data
#     assert "nodosFuturos" in data
#     assert "uptime" in data