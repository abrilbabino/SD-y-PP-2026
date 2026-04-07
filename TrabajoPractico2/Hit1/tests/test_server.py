from unittest.mock import MagicMock, patch
import uvicorn
from api.main import app
from fastapi.testclient import TestClient
from TrabajoPractico2.Hit1 import server

def run_server():
    """Levanta el servidor FastAPI en un hilo"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")


def test_server_getRemoteTask():
    """Test que el servidor responde correctamente a /getRemoteTask"""
    
    # Mock Docker para que no necesite Docker corriendo
    with patch.object(server, 'client') as mock_client:
        mock_container = MagicMock()
        mock_container.attrs = {
            'NetworkSettings': {
                'Ports': {'5000/tcp': [{'HostPort': '32768'}]}
            }
        }
        mock_client.images.pull.return_value = MagicMock()
        mock_client.containers.run.return_value = mock_container
        
        # Mock requests.post para simular respuesta del servicio tarea
        with patch('TrabajoPractico2.Hit3.server.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": 8}
            mock_post.return_value = mock_response
            
            # Usar TestClient en lugar de servidor real
            client = TestClient(app)
            
            # Hacer petición al endpoint
            response = client.post(
                "/getRemoteTask",
                json={
                    "image": "local/task-service:latest",
                    "task": "suma",
                    "params": {"a": 5, "b": 3}
                }
            )
            
            # Verificar respuesta
            assert response.status_code == 200
            assert response.json() == {"result": 8}
            
            # Verificar que se llamó a Docker
            mock_client.images.pull.assert_called_once_with("local/task-service:latest")
            mock_client.containers.run.assert_called_once()
            
            # Verificar que se llamó al servicio tarea
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/EjecutarTarea" in call_args[0][0]
            assert call_args[1]['json']['task'] == "suma"
            assert call_args[1]['json']['params'] == {"a": 5, "b": 3}


def test_server_invalid_request():
    """Test que el servidor rechaza requests inválidos"""
    
    client = TestClient(app)
    
    # Enviar request inválido (faltan campos)
    response = client.post(
        "/getRemoteTask",
        json={"invalid": "request"}
    )
    
    # Debe retornar 422 (Unprocessable Entity)
    assert response.status_code == 422


def test_server_endpoint_exists():
    """Test que el endpoint existe"""
    
    client = TestClient(app)
    
    # Solo verificar que el endpoint responde (aunque sea con error)
    response = client.post(
        "/getRemoteTask",
        json={"image": "test", "task": "test", "params": {}}
    )
    
    # No debe ser 404 (Not Found)
    assert response.status_code != 404
