import pytest
import os
import json
from src.game.Player import Player

# Fixture para garantir que o arquivo de cartas exista de forma previsível antes dos testes
@pytest.fixture(autouse=True)
def setup_cards_json():
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", "cards.json")

    # Se o arquivo não existir por algum motivo no ambiente de CI, criamos um mock rápido
    if not os.path.exists(path):
        mock_cards = [
            {"id": i, "name": f"Carta {i}", "type": "DANO", "value": 2, "cost": 1, "return_mana": False}
            for i in range(1, 41)
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(mock_cards, f)

def test_player_initialization_defaults():
    """Garante que o jogador inicia com os status de vida e mana corretos."""
    player = Player("Chrystian")
    assert player.name == "Chrystian"
    assert player.hp == 10
    assert player.mana_pool == 0
    assert player.mana_max == 0
    assert player.mana_deck == 10
    assert player.defense_active == 0
    assert player.is_first_turn is True
    assert player.is_my_turn is False

def test_player_initialization_hand_and_deck():
    """Garante que o jogador começa com exatamente 3 cartas na mão e 17 no deck (total 20)."""
    player = Player("Chrystian")
    assert len(player.hand) == 3
    assert len(player.deck) == 17