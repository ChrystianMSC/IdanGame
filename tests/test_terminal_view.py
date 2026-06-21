import pytest
from unittest.mock import patch, MagicMock
import os
from src.game.TerminalView import TerminalView
from src.game.Player import Player

def test_clear_screen_calls_os_system():
    """Garante que o método de limpar a tela chama a função do sistema operacional correta."""
    with patch("os.system") as mock_system:
        TerminalView.clear_screen()
        # Verifica se o os.system foi chamado pelo menos uma vez
        mock_system.assert_called_once()
        # O argumento deve ser 'cls' no Windows ou 'clear' no Linux/Mac
        assert mock_system.call_args[0][0] in ['cls', 'clear']

def test_display_message_prints_to_stdout(capsys):
    """Garante que display_message envia o texto correto para a saída padrão (sys.stdout)."""
    TerminalView.display_message("Mensagem de Teste")
    captured = capsys.readouterr()
    assert captured.out == "Mensagem de Teste\n"

def test_display_opponent_message_formats_correctly(capsys):
    """Garante que a mensagem do oponente é exibida no formato estruturado esperado."""
    TerminalView.display_opponent_message("Adversario", "Minha jogada")
    captured = capsys.readouterr()
    assert captured.out == "\n[Adversario]: Minha jogada\n"

def test_prompt_input_returns_user_string():
    """Garante que o prompt_input captura e retorna exatamente o que o usuário digitou."""
    with patch("builtins.input", return_value="pass"):
        result = TerminalView.prompt_input("Digite algo: ")
        assert result == "pass"


def test_display_board_renders_all_components(capsys):
    """Garante que a renderização do tabuleiro imprime os dados cruciais (Vida, Mana, Mão)."""
    # Criamos um mock do jogador para não depender do sorteio real de cartas
    mock_player = MagicMock(spec=Player)
    mock_player.name = "Chrystian"
    mock_player.hp = 10
    mock_player.mana_pool = 3
    mock_player.mana_max = 3
    mock_player.mana_deck = 7
    mock_player.defense_active = 2
    mock_player.is_my_turn = True
    mock_player.deck = [1, 2, 3, 4, 5]  # Simula tamanho do deck
    mock_player.hand = [
        {"name": "Bola de Fogo", "type": "DANO", "cost": 2, "value": 4, "return_mana": False}
    ]

    # Forçamos o os.system a não fazer nada para não limpar o terminal de teste real
    with patch("os.system"):
        TerminalView.display_board(mock_player, 8, "1/1", 3, 0)

    captured = capsys.readouterr()

    # Validamos se as palavras-chave do estado do jogo aparecem na tela gerada
    assert "ADVERSÁRIO" in captured.out
    assert "SUA VEZ: True" in captured.out
    assert "Vida: 10/10" in captured.out
    assert "Mana: 3/3" in captured.out
    assert "Bola de Fogo" in captured.out