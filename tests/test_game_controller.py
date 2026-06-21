import pytest
from unittest.mock import MagicMock, patch
import time
from src.game.GameController import GameController
from src.network.NetworkEngine import NetworkEngine

@pytest.fixture
def mock_network():
    """Cria um mock para o motor de rede P2P."""
    return MagicMock(spec=NetworkEngine)

@pytest.fixture
def game_controller(mock_network):
    """Instancia o GameController usando o mock de rede e um nome padrão."""
    # Desativamos o time.sleep para os testes rodarem instantaneamente
    with patch("time.sleep"):
        controller = GameController(mock_network, "Chrystian")
        return controller


def test_setup_connection_as_host(game_controller, mock_network):
    """Garante que o Host inicia o servidor de rede e começa com a prioridade do turno."""
    with patch("src.game.GameController.TerminalView.display_message") as mock_display:
        game_controller.setup_connection("host", "127.0.0.1", 9999)

        assert game_controller._local_player.is_my_turn is True
        assert game_controller._is_game_running is True
        mock_network.start_as_host.assert_called_once_with("127.0.0.1", 9999)


def test_setup_connection_as_guest(game_controller, mock_network):
    """Garante que o Guest se conecta ao host e inicia aguardando o turno."""
    mock_network.connect_as_guest.return_value = True

    with patch("src.game.GameController.TerminalView.display_message"), \
            patch("src.game.GameController.TerminalView.display_board"):
        game_controller.setup_connection("guest", "127.0.0.1", 9999)

        assert game_controller._local_player.is_my_turn is False
        assert game_controller._is_connected is True
        mock_network.connect_as_guest.assert_called_once_with("127.0.0.1", 9999)