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


def test_execute_card_action_dano(game_controller, mock_network):
    """Garante que jogar uma carta de DANO dispara um ATTACK_REQUEST na rede."""
    card = {"name": "Explosão", "type": "DANO", "value": 5, "cost": 2}
    game_controller._execute_card_action(card)

    assert game_controller._is_waiting_defense is True
    mock_network.send.assert_called_once_with({
        "action": "ATTACK_REQUEST",
        "value": 5,
        "card_name": "Explosão"
    })

def test_execute_card_action_cura(game_controller):
    """Garante que jogar uma carta de CURA recupera vida respeitando o teto de 10 HP."""
    game_controller._local_player.hp = 7
    card = {"name": "Luz", "type": "CURA", "value": 5, "cost": 1}

    with patch("time.sleep"):
        game_controller._execute_card_action(card)

    assert game_controller._local_player.hp == 10  # 7 + 5 = 12, mas teto é 10

def test_execute_card_action_defesa(game_controller):
    """Garante que jogar uma carta de DEFESA incrementa os pontos de armadura passiva."""
    game_controller._local_player.defense_active = 1
    card = {"name": "Escudo", "type": "DEFESA", "value": 3, "cost": 1}

    with patch("time.sleep"):
        game_controller._execute_card_action(card)

    assert game_controller._local_player.defense_active == 4

def test_turn_loop_card_penalty_return_mana(game_controller):
    """Garante que uma carta com a propriedade 'return_mana' ativa penaliza o deck de mana do jogador."""
    game_controller._local_player.set_turn(True)
    game_controller._local_player.mana_max = 4
    game_controller._local_player.mana_pool = 4
    game_controller._local_player.mana_deck = 5

    penalized_card = {"name": "Pacto Sobrenatural", "type": "CURA", "value": 2, "cost": 2, "return_mana": True}
    game_controller._local_player.hand = [penalized_card]

    game_controller._view.prompt_input.side_effect = ["0", "pass"]

    with patch("time.sleep"):
        game_controller._turn_loop()

    assert game_controller._local_player.mana_pool == 2
    assert game_controller._local_player.mana_max == 3
    assert game_controller._local_player.mana_deck == 6


def test_setup_connection_guest_critical_failure(game_controller, mock_network):
    """Garante que se o Guest falhar ao conectar, o sistema encerra com sys.exit(1)."""
    mock_network.connect_as_guest.return_value = False

    with pytest.raises(SystemExit) as exc_info:
        game_controller.setup_connection("guest", "127.0.0.1", 9999)

    assert exc_info.value.code == 1


def test_turn_loop_exit_command(game_controller):
    """Garante que digitar 'exit' no turn_loop encerra o loop de turnos e para o jogo."""
    game_controller._local_player.set_turn(True)
    game_controller._view.prompt_input.return_value = "exit"

    with patch("time.sleep"), patch.object(game_controller, "stop") as mock_stop:
        game_controller._turn_loop()
        mock_stop.assert_called_once()


def test_turn_loop_insufficient_mana(game_controller):
    """Garante que o jogador não pode jogar uma carta se não tiver mana suficiente."""
    game_controller._local_player.set_turn(True)
    game_controller._local_player.mana_pool = 1
    card = {"name": "Super Dano", "type": "DANO", "value": 5, "cost": 3}
    game_controller._local_player.hand = [card]

    game_controller._view.prompt_input.side_effect = ["0", "pass"]

    with patch("time.sleep"), patch.object(game_controller, "_execute_card_action") as mock_execute:
        game_controller._turn_loop()
        mock_execute.assert_not_called()
        assert len(game_controller._local_player.hand) == 1


def test_turn_loop_invalid_index(game_controller):
    """Garante que digitar um índice de carta inexistente exibe erro e não quebra o loop."""
    game_controller._local_player.set_turn(True)
    game_controller._local_player.hand = [{"name": "A", "type": "CURA", "value": 1, "cost": 0}]

    game_controller._view.prompt_input.side_effect = ["9", "pass"]

    with patch("time.sleep"):
        game_controller._turn_loop()
        assert len(game_controller._local_player.hand) == 1


def test_handle_incoming_attack_with_successful_defense(game_controller, mock_network):
    """Garante que o jogador pode escolher uma carta de defesa válida para reagir ao ataque."""
    game_controller._local_player.hp = 10
    game_controller._local_player.mana_pool = 2
    game_controller._local_player.defense_active = 0

    defense_card = {"name": "Escudo de Madeira", "type": "DEFESA", "value": 3, "cost": 2}
    game_controller._local_player.hand = [defense_card]

    game_controller._view.prompt_input.return_value = "0"

    with patch("time.sleep"):
        game_controller._handle_incoming_attack(4, "Golpe")

        assert game_controller._local_player.hp == 9
        assert game_controller._local_player.mana_pool == 0
        assert len(game_controller._local_player.hand) == 0

        mock_network.send.assert_any_call({
            "action": "ATTACK_RESOLVED",
            "final_damage": 1
        })


def test_handle_incoming_attack_with_defense_penalty_mana(game_controller):
    """Garante que defender usando uma carta com a penalidade 'return_mana' afeta os cristais."""
    game_controller._local_player.mana_pool = 2
    game_controller._local_player.mana_max = 3
    game_controller._local_player.mana_deck = 5

    cursed_defense = {"name": "Barreira Maldita", "type": "DEFESA", "value": 5, "cost": 1, "return_mana": True}
    game_controller._local_player.hand = [cursed_defense]
    game_controller._view.prompt_input.return_value = "0"

    with patch("time.sleep"):
        game_controller._handle_incoming_attack(2, "Golpe")

        assert game_controller._local_player.mana_max == 2
        assert game_controller._local_player.mana_deck == 6


def test_handle_incoming_attack_resulting_in_death(game_controller, mock_network):
    """Garante que se o dano zerar a vida do jogador local, o jogo envia a resolução e fecha."""
    game_controller._local_player.hp = 3
    game_controller._local_player.mana_pool = 0
    game_controller._local_player.defense_active = 0

    with patch("time.sleep"), patch.object(game_controller, "stop") as mock_stop:
        game_controller._handle_incoming_attack(5, "Ataque Fatal")

        assert game_controller._local_player.hp <= 0
        mock_network.send.assert_any_call({
            "action": "ATTACK_RESOLVED",
            "final_damage": 5
        })
        mock_stop.assert_called_once()


def test_on_connection_lost_triggers_stop(game_controller):
    """Garante que o evento de perda de conexão invoca o encerramento do jogo."""
    with patch.object(game_controller, "stop") as mock_stop:
        game_controller.on_connection_lost()
        mock_stop.assert_called_once()


def test_stop_method_cleanup(game_controller, mock_network):
    """Garante que o método stop limpa os flags, desconecta a rede e sai do sistema."""
    game_controller._is_game_running = True

    with patch("time.sleep"), pytest.raises(SystemExit) as exc_info:
        game_controller.stop()

    assert game_controller._is_game_running is False
    mock_network.disconnect.assert_called_once()
    assert exc_info.value.code == 0


def test_start_chat_loop_and_turn_sequence(game_controller):
    """Garante o fluxo completo do loop principal passando de esperando conexão para o turno."""
    game_controller._is_game_running = True
    game_controller._is_connected = False
    game_controller._local_player.set_turn(True)
    game_controller._local_player.is_first_turn = True
    game_controller._opp_mana = "1/1"

    game_controller._local_player.hand = []

    def mock_turn_loop_side_effect():
        game_controller._is_game_running = False

    with patch("time.sleep"), \
            patch.object(game_controller, "_turn_loop", side_effect=mock_turn_loop_side_effect) as mock_turn, \
            patch.object(game_controller, "_sync_state") as mock_sync:
        game_controller._is_connected = True

        game_controller.start_chat_loop()

        mock_turn.assert_called_once()
        mock_sync.assert_called_once()


def test_start_chat_loop_opponent_turn(game_controller):
    """Garante que o loop se comporta corretamente e renderiza o board esperando o oponente."""
    game_controller._is_game_running = True
    game_controller._is_connected = True
    game_controller._local_player.set_turn(False)  # Turno do oponente

    call_count = 0

    def mock_display_board(*args):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            game_controller._is_game_running = False

    game_controller._view.display_board.side_effect = mock_display_board

    with patch("time.sleep"):
        game_controller.start_chat_loop()

        game_controller._view.display_board.assert_called()