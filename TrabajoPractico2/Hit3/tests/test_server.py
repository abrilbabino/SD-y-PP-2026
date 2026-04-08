'''from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from TrabajoPractico2.Hit3 import server

app = FastAPI()
app.include_router(server.router4)


def test_server_asignar_tarea_leader_assigns_to_available_worker():
    """Verifica que el líder enruta la tarea a un worker disponible."""
    with patch.object(server, 'worker_id', 1), \
         patch.object(server, 'leader_id', 1), \
         patch.object(server, 'encontrar_worker_disponible', return_value={'id': 2, 'url': 'http://worker2:8000'}) as mock_available, \
         patch.object(server, 'asignar_Tarea_Worker', return_value={'result': 8}) as mock_assign:

        client = TestClient(app)
        response = client.post(
            '/asignar_tarea',
            json={'image': 'local/task-service:latest', 'task': 'noop', 'params': {}}
        )

        assert response.status_code == 200
        assert response.json() == {
            'msg': 'Tarea asignada al worker 2',
            'result': {'result': 8}
        }
        mock_available.assert_called_once()
        mock_assign.assert_called_once()


def test_server_asignar_tarea_non_leader_forwards_to_leader():
    """Verifica que un worker no líder reenvía la tarea al líder conocido."""
    with patch.object(server, 'worker_id', 1), \
         patch.object(server, 'leader_id', 2), \
         patch.object(server, 'get_leader', return_value={'id': 2, 'url': 'http://worker2:8000'}), \
         patch('TrabajoPractico2.Hit3.server.requests.post') as mock_post:

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'msg': 'Tarea reenviada al líder',
            'result': {'result': 8}
        }
        mock_post.return_value = mock_response

        client = TestClient(app)
        response = client.post(
            '/asignar_tarea',
            json={'image': 'local/task-service:latest', 'task': 'noop', 'params': {}}
        )

        assert response.status_code == 200
        assert response.json() == {
            'msg': 'Tarea reenviada al líder',
            'result': {'result': 8}
        }
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == 'http://worker2:8000/asignar_tarea'


def test_server_elegir_lider_prefers_highest_alive_node():
    """Verifica la elección de líder tipo Bully seleccionando al mayor nodo vivo."""
    with patch.object(server, 'worker_id', 1), \
         patch.object(server, 'leader_id', None), \
         patch('TrabajoPractico2.Hit3.server.requests.get') as mock_get, \
         patch('TrabajoPractico2.Hit3.server.requests.post') as mock_post:

        mock_get.return_value = MagicMock(status_code=200)

        selected = server.elegir_lider()

        assert selected == 3
        assert server.leader_id == 3
        assert mock_post.call_count == len(server.WORKERS)


def test_server_coordinador_updates_leader():
    """Verifica que el endpoint /coordinador actualiza el líder local."""
    with patch.object(server, 'leader_id', None):
        client = TestClient(app)
        response = client.post('/coordinador', json={'leader': 2})

        assert response.status_code == 200
        assert response.json() == {'status': 'ok', 'leader_id': 2}
        assert server.leader_id == 2


def test_server_invalid_request_for_asignar_tarea():
    """Verifica que el endpoint /asignar_tarea rechaza un request inválido."""
    client = TestClient(app)
    response = client.post('/asignar_tarea', json={'invalid': 'request'})

    assert response.status_code == 422
'''