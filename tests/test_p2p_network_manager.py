import pytest
from unittest.mock import MagicMock, patch
import socket
from src.network.P2PNetworkManager import P2PNetworkManager


@pytest.fixture
def network_manager():
    return P2PNetworkManager()


def test_register_and_remove_observer(network_manager):
    """Garante que o gerenciador adiciona e remove observadores corretamente."""
    mock_observer = MagicMock()

    network_manager.register_observer(mock_observer)
    assert mock_observer in network_manager._observers

    network_manager.remove_observer(mock_observer)
    assert mock_observer not in network_manager._observers


def test_disconnect_closes_sockets_and_clears_state(network_manager):
    """Garante que o método disconnect fecha as conexões ativas com segurança."""
    mock_server_socket = MagicMock(spec=socket.socket)
    mock_client_socket = MagicMock(spec=socket.socket)

    network_manager._server_socket = mock_server_socket
    network_manager._client_socket = mock_client_socket
    network_manager._is_running = True

    network_manager.disconnect()

    mock_client_socket.close.assert_called_once()
    mock_server_socket.close.assert_called_once()
    assert network_manager._is_running is False
