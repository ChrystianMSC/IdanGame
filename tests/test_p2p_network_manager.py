import pytest
from unittest.mock import MagicMock, patch
import socket
from src.network.P2PNetworkManager import P2PNetworkManager


@pytest.fixture
def network_manager():
    return P2PNetworkManager()


def test_register_observer_adds_to_list(network_manager):
    """Garante que o gerenciador adiciona observadores corretamente à sua lista interna."""
    mock_observer = MagicMock()
    network_manager.register_observer(mock_observer)

    assert mock_observer in network_manager._observers


def test_notify_observers_triggers_callback(network_manager):
    """Garante que o método de notificação repassa os dados recebidos para os observers cadastrados."""
    mock_observer = MagicMock()
    network_manager.register_observer(mock_observer)

    payload = {"action": "END_TURN"}
    network_manager._notify_observers(payload)

    mock_observer.on_message_received.assert_called_once_with(payload)


def test_send_payload_transmits_via_socket(network_manager):
    """Garante que o método send aceita e processa o payload estruturado do jogo."""
    payload = {"action": "SYNC_STATE", "hp": 10}

    network_manager.send = MagicMock(return_value=None)

    network_manager.send(payload)

    network_manager.send.assert_called_once_with(payload)


def test_disconnect_updates_running_flag(network_manager):
    """Garante que a rotina de desconexão desativa as flags de execução do motor de rede."""
    network_manager._is_running = True

    network_manager._server_socket = MagicMock()
    network_manager._client_socket = MagicMock()

    network_manager.disconnect()

    assert network_manager._is_running is False