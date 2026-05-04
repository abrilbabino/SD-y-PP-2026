import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ajustar PYTHONPATH para importar producer y worker
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import producer
import worker

class TestPubSubFanout(unittest.TestCase):

    @patch('producer.threading.Thread')
    @patch('producer.time.sleep', side_effect=KeyboardInterrupt) # Rompe el loop infinito
    @patch('producer.pika.BlockingConnection')
    def test_producer_declares_fanout_exchange(self, mock_blocking_connection, mock_sleep, mock_thread):
        # Setup mocks
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_blocking_connection.return_value = mock_connection

        # Ejecutamos el main del producer. Levantará KeyboardInterrupt al intentar el primer sleep().
        producer.main()

        # Verificamos que el producer declara un exchange de tipo fanout
        mock_channel.exchange_declare.assert_called_with(
            exchange='block_events', 
            exchange_type='fanout'
        )

    @patch('worker.threading.Thread')
    @patch('worker.pika.BlockingConnection')
    def test_worker_declares_exclusive_queue(self, mock_blocking_connection, mock_thread):
        # Setup mocks
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        
        # Simular resultado de queue_declare para obtener un nombre de cola
        mock_queue_declare_result = MagicMock()
        mock_queue_declare_result.method.queue = 'amq.gen-mocked-queue'
        mock_channel.queue_declare.return_value = mock_queue_declare_result
        
        # Romper la ejecución bloqueante de start_consuming()
        mock_channel.start_consuming.side_effect = KeyboardInterrupt
        
        mock_connection.channel.return_value = mock_channel
        mock_blocking_connection.return_value = mock_connection

        # Ejecutamos el worker
        worker.main()

        # Verificamos que el worker declara una cola temporal y exclusiva (fundamental para el fanout)
        mock_channel.queue_declare.assert_called_with(
            queue='', 
            exclusive=True
        )

    @patch('worker.threading.Thread')
    @patch('worker.pika.BlockingConnection')
    def test_worker_binds_queue_to_exchange(self, mock_blocking_connection, mock_thread):
        # Setup mocks
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        
        mock_queue_declare_result = MagicMock()
        mock_queue_declare_result.method.queue = 'amq.gen-mocked-queue'
        mock_channel.queue_declare.return_value = mock_queue_declare_result
        
        mock_channel.start_consuming.side_effect = KeyboardInterrupt
        
        mock_connection.channel.return_value = mock_channel
        mock_blocking_connection.return_value = mock_connection

        # Ejecutamos el worker
        worker.main()

        # Verificamos que el worker enlaza su cola temporal exclusiva al exchange correcto
        mock_channel.queue_bind.assert_called_with(
            exchange='block_events', 
            queue='amq.gen-mocked-queue'
        )

if __name__ == '__main__':
    unittest.main()
