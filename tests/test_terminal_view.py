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