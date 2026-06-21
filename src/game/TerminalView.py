import os

class TerminalView:
    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def display_message(message):
        print(message)

    @staticmethod
    def display_opponent_message(sender, message):
        print(f"\n[{sender}]: {message}")

    @staticmethod
    def prompt_input(prompt=""):
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            return "exit"

    @staticmethod
    def display_board(local_player, opponent_hp, opponent_mana, opponent_hand_count, opponent_defense):
        TerminalView.clear_screen()
        print("=" * 65)
        print(f" ADVERSÁRIO: Vida: {opponent_hp}/10 | Mana: {opponent_mana} | Cartas: {opponent_hand_count} | Defesa: {opponent_defense}")
        print("=" * 65)
        print(f"\n SUA VEZ: {local_player.is_my_turn}")
        print(f" STATUS: Vida: {local_player.hp}/10 | Mana: {local_player.mana_pool}/{local_player.mana_max} | Deck: {len(local_player.deck)} | Deck de Mana: {local_player.mana_deck} | Defesa: {local_player.defense_active}\n")
        print(" SUA MÃO:")
        for idx, card in enumerate(local_player.hand):
            # Tag especial caso a carta tenha penalidade de retorno de mana
            special_tag = " [⚠️ RETORNA 1 MANA PRO DECK]" if card.get("return_mana", False) else ""
            # Exibe o Nome primeiro, seguido pelo Tipo e os atributos
            print(f"  {idx} - {card['name']} ({card['type']}) - Custo: {card['cost']} | Val: {card['value']}{special_tag}")
        print("=" * 65)