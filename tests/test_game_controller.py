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
def mock_view():
    """Cria um mock para a interface de visualização (CLI ou GUI)."""
    return MagicMock()

@pytest.fixture
def game_controller(mock_network, mock_view):
    """Instancia o GameController usando os mocks de rede e visualização."""
    with patch("time.sleep"):
        controller = GameController(mock_network, "Chrystian", mock_view)
        return controller


def test_setup_connection_as_host(game_controller, mock_network):
    """Garante que o Host inicia o servidor de rede e começa com a prioridade do turno."""
    # Não precisa de patches! O mock_view injetado cuida de tudo de forma transparente.
    game_controller.setup_connection("host", "127.0.0.1", 9999)

    assert game_controller._local_player.is_my_turn is True
    assert game_controller._is_game_running is True
    mock_network.start_as_host.assert_called_once_with("127.0.0.1", 9999)


def test_setup_connection_as_guest(game_controller, mock_network):
    """Garante que o Guest se conecta ao host e inicia aguardando o turno."""
    mock_network.connect_as_guest.return_value = True

    game_controller.setup_connection("guest", "127.0.0.1", 9999)

    assert game_controller._local_player.is_my_turn is False
    assert game_controller._is_connected is True
    mock_network.connect_as_guest.assert_called_once_with("127.0.0.1", 9999)


def test_on_message_received_sync_state(game_controller):
    """[Integração] Garante que pacotes de SYNC_STATE atualizam as propriedades espelhadas do oponente."""
    payload = {
        "action": "SYNC_STATE",
        "hp": 7,
        "mana": "4/4",
        "hand_count": 2,
        "defense": 3
    }

    game_controller.on_message_received(payload)

    assert game_controller._opp_hp == 7
    assert game_controller._opp_mana == "4/4"
    assert game_controller._opp_hand_count == 2
    assert game_controller._opp_defense == 3
    assert game_controller._is_connected is True


def test_on_message_received_end_turn(game_controller):
    """[Integração] Garante que a mensagem END_TURN passa a prioridade de volta para o jogador local."""
    game_controller._local_player.set_turn(False)

    game_controller.on_message_received({"action": "END_TURN"})

    assert game_controller._local_player.is_my_turn is True


def test_on_message_received_attack_resolved(game_controller):
    """[Integração] Garante que a confirmação de ataque destrava o atacante e reduz a vida do alvo mockado."""
    game_controller._opp_hp = 10
    game_controller._is_waiting_defense = True

    payload = {
        "action": "ATTACK_RESOLVED",
        "final_damage": 4
    }
    game_controller.on_message_received(payload)

    assert game_controller._opp_hp == 6
    assert game_controller._is_waiting_defense is False


def test_handle_incoming_attack_no_defenses(game_controller, mock_network):
    """[Integração] Testa a resolução de um ataque recebido quando o jogador local não tem manas/cartas para defender."""
    game_controller._local_player.hp = 10
    game_controller._local_player.mana_pool = 0
    game_controller._local_player.defense_active = 2

    with patch("time.sleep"):
        game_controller._handle_incoming_attack(5, "Bola de Fogo")

        assert game_controller._local_player.hp == 7
        assert game_controller._local_player.defense_active == 0

        mock_network.send.assert_any_call({
            "action": "ATTACK_RESOLVED",
            "final_damage": 3
        })