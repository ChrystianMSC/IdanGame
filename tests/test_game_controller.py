import pytest
from unittest.mock import MagicMock, patch
import time
from src.game.GameController import GameController
from src.network.NetworkEngine import NetworkEngine

@pytest.fixture
def mock_network():
    """Cria um mock para o motor de rede P2P."""
    return MagicMock(spec=NetworkEngine)
