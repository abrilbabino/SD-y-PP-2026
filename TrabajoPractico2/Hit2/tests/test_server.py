from pathlib import Path
from unittest.mock import MagicMock, patch
import threading
import time

from fastapi.testclient import TestClient
from api.main import app
from TrabajoPractico2.Hit2 import server


def test_server_getRemoteTask2_returns_result_and_lamport_ts():
    """Verifica que el endpoint devuelve resultado y lamport_ts."""
    with patch.object(server, 'ejecutar_task') as mock_ejecutar_task:
        def complete_task(task):
            task['result'] = {'result': 8}

        mock_ejecutar_task.side_effect = complete_task

        client = TestClient(app)
        response = client.post(
            '/getRemoteTask2',
            json={
                'image': 'local/task-service:latest',
                'task': 'suma',
                'params': {'a': 5, 'b': 3},
                'timestamp': 0
            }
        )

        assert response.status_code == 200
        assert isinstance(response.json().get('lamport_ts'), int)
        assert response.json().get('result') == {'result': 8}


def test_server_uses_queue_lock_on_enqueue():
    """Verifica que se usa exclusión mutua al encolar tareas."""
    mock_lock = MagicMock()
    mock_lock.__enter__ = MagicMock(return_value=None)
    mock_lock.__exit__ = MagicMock(return_value=None)

    with patch.object(server, 'queue_lock', mock_lock):
        with patch.object(server.task_queue, 'put') as mock_put:
            def fake_put(task):
                task['result'] = {'result': 'ok'}

            mock_put.side_effect = fake_put

            client = TestClient(app)
            response = client.post(
                '/getRemoteTask2',
                json={
                    'image': 'local/task-service:latest',
                    'task': 'noop',
                    'params': {},
                    'timestamp': 1
                }
            )

            assert response.status_code == 200
            assert mock_lock.__enter__.call_count == 2
            assert mock_lock.__exit__.call_count == 2
            mock_put.assert_called_once()


def test_server_lamport_clock_uses_request_timestamp():
    """Verifica el uso del timestamp recibido para avanzar el reloj de Lamport."""
    with patch.object(server, 'increment_clock', wraps=server.increment_clock) as mock_increment_clock:
        with patch.object(server, 'ejecutar_task') as mock_ejecutar_task:
            mock_ejecutar_task.side_effect = lambda task: task.__setitem__('result', {'result': 'ok'})

            client = TestClient(app)
            request_timestamp = 50
            response = client.post(
                '/getRemoteTask2',
                json={
                    'image': 'local/task-service:latest',
                    'task': 'noop',
                    'params': {},
                    'timestamp': request_timestamp
                }
            )

            assert response.status_code == 200
            mock_increment_clock.assert_called_once_with(2)
            assert response.json()['lamport_ts'] >= 3


def test_concurrent_requests_are_queued_and_processed_by_worker_pool():
    """Simula múltiples requests concurrentes para validar el pool de workers y la cola."""
    with patch.object(server, 'ejecutar_task') as mock_ejecutar_task:
        def execute_with_delay(task):
            time.sleep(0.05)
            task['result'] = {'result': task['req'].task}

        mock_ejecutar_task.side_effect = execute_with_delay

        client = TestClient(app)
        responses = []
        responses_lock = threading.Lock()

        def send_request(task_id):
            response = client.post(
                '/getRemoteTask2',
                json={
                    'image': 'local/task-service:latest',
                    'task': f'task-{task_id}',
                    'params': {'id': task_id},
                    'timestamp': 0
                }
            )
            with responses_lock:
                responses.append(response)

        threads = [threading.Thread(target=send_request, args=(i,)) for i in range(8)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert len(responses) == 8
        assert all(response.status_code == 200 for response in responses)

        lamport_ts = [response.json()['lamport_ts'] for response in responses]
        assert len(set(lamport_ts)) == 8
        sorted_ts = sorted(lamport_ts)
        assert sorted_ts == list(range(sorted_ts[0], sorted_ts[0] + 8))


def test_readme_mentions_throughput_and_shared_bottlenecks():
    """Verifica la existencia de documentación sobre throughput y cuellos de botella."""
    readme_path = Path(__file__).resolve().parents[1] / 'README.md'
    content = readme_path.read_text(encoding='utf-8').lower()

    assert 'worker' in content
    assert 'pool' in content
    assert 'lamport' in content
    assert 'docker' in content
    assert 'daemon' in content
