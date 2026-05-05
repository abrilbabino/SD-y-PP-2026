import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ex2.src import producer
from ex2.src import worker

@patch('ex2.src.producer.threading.Thread')
@patch('ex2.src.producer.time.sleep', side_effect=KeyboardInterrupt)
@patch('ex2.src.producer.pika.BlockingConnection')
def test_producer_declares_fanout_exchange(mock_blocking_connection, mock_sleep, mock_thread):
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel
    mock_blocking_connection.return_value = mock_connection

    try:
        producer.main()
    except KeyboardInterrupt:
        pass

    mock_channel.exchange_declare.assert_called_with(
        exchange='block_events', 
        exchange_type='fanout'
    )

@patch('ex2.src.worker.threading.Thread')
@patch('ex2.src.worker.pika.BlockingConnection')
def test_worker_declares_exclusive_queue(mock_blocking_connection, mock_thread):
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    
    mock_queue_declare_result = MagicMock()
    mock_queue_declare_result.method.queue = 'amq.gen-mocked-queue'
    mock_channel.queue_declare.return_value = mock_queue_declare_result
    
    mock_channel.start_consuming.side_effect = KeyboardInterrupt
    
    mock_connection.channel.return_value = mock_channel
    mock_blocking_connection.return_value = mock_connection

    try:
        worker.main()
    except KeyboardInterrupt:
        pass

    mock_channel.queue_declare.assert_called_with(
        queue='', 
        exclusive=True
    )

@patch('ex2.src.worker.threading.Thread')
@patch('ex2.src.worker.pika.BlockingConnection')
def test_worker_binds_queue_to_exchange(mock_blocking_connection, mock_thread):
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    
    mock_queue_declare_result = MagicMock()
    mock_queue_declare_result.method.queue = 'amq.gen-mocked-queue'
    mock_channel.queue_declare.return_value = mock_queue_declare_result
    
    mock_channel.start_consuming.side_effect = KeyboardInterrupt
    
    mock_connection.channel.return_value = mock_channel
    mock_blocking_connection.return_value = mock_connection

    try:
        worker.main()
    except KeyboardInterrupt:
        pass

    mock_channel.queue_bind.assert_called_with(
        exchange='block_events', 
        queue='amq.gen-mocked-queue'
    )
