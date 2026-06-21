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

def test_set_turn_modifies_state():
    """Garante que a mudança de turno altera corretamente a propriedade is_my_turn."""
    player = Player("Chrystian")
    player.set_turn(True)
    assert player.is_my_turn is True
    player.set_turn(False)
    assert player.is_my_turn is False


def test_draw_card_decrements_deck_and_increments_hand():
    """Garante que comprar uma carta tira do deck e põe na mão."""
    player = Player("Chrystian")
    initial_hand_count = len(player.hand)
    initial_deck_count = len(player.deck)

    success = player.draw_card()

    assert success is True
    assert len(player.hand) == initial_hand_count + 1
    assert len(player.deck) == initial_deck_count - 1


def test_draw_card_returns_false_when_deck_is_empty():
    """Garante que comprar carta retorna Falso se o deck acabar."""
    player = Player("Chrystian")
    player.deck = []  # Esvazia o deck forçadamente para o cenário de teste

    success = player.draw_card()

    assert success is False
    assert len(player.hand) == 3  # Mantém apenas as iniciais