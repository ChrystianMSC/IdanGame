import sys
import time
from src.network.NetworkObserver import NetworkObserver
from src.game.Player import Player


class GameController(NetworkObserver):

    def __init__(self, network_engine, player_name, view):
        self._network = network_engine
        self._local_player = Player(player_name)
        self._view = view
        self._is_game_running = False
        self._is_connected = False

        self._opp_hp = 10
        self._opp_mana = "0/0"
        self._opp_hand_count = 3
        self._opp_defense = 0
        self._is_waiting_defense = False

    def setup_connection(self, role, host, port):
        self._is_game_running = True
        if role == "host":
            self._local_player.set_turn(True)
            self._network.start_as_host(host, port)
            self._view.display_message(f"[*] Aguardando conexão em {host}:{port}...")
        else:
            self._local_player.set_turn(False)
            self._view.display_message(f"[*] Conectando-se a {host}:{port}...")
            if not self._network.connect_as_guest(host, port):
                self._view.display_message("[-] Falha crítica ao conectar ao Host.")
                sys.exit(1)

            self._is_connected = True
            time.sleep(0.5)
            self._sync_state()

    def _sync_state(self):
        payload = {
            "action": "SYNC_STATE",
            "hp": self._local_player.hp,
            "mana": f"{self._local_player.mana_pool}/{self._local_player.mana_max}",
            "hand_count": len(self._local_player.hand),
            "defense": self._local_player.defense_active
        }
        self._network.send(payload)

    def start_chat_loop(self):
        while self._is_game_running and not self._is_connected:
            time.sleep(0.2)

        self._view.display_message("[+] Conexão Estabelecida! O jogo começou.\n")
        time.sleep(0.5)

        while self._is_game_running:
            if self._local_player.is_my_turn:
                self._local_player.draw_card()

                if not self._local_player.is_first_turn:
                    self._local_player.draw_mana()
                else:
                    self._local_player.draw_mana()
                    if self._opp_mana != "0/0":
                        self._local_player.draw_mana()
                    self._local_player.is_first_turn = False

                self._sync_state()
                self._turn_loop()
            else:
                self._view.display_board(self._local_player, self._opp_hp, self._opp_mana, self._opp_hand_count,
                                           self._opp_defense)
                print("Aguardando o turno do oponente...")

                while not self._local_player.is_my_turn and self._is_game_running:
                    time.sleep(0.3)

    def _turn_loop(self):
        while self._local_player.is_my_turn:
            self._view.display_board(self._local_player, self._opp_hp, self._opp_mana, self._opp_hand_count,
                                       self._opp_defense)
            print("Comandos: [id_da_carta] para jogar | 'pass' para passar o turno | 'exit' para sair")
            choice = self._view.prompt_input("Sua escolha: ").strip().lower()

            if choice == "exit":
                self.stop()
                return
            elif choice == "pass":
                self._local_player.set_turn(False)
                self._network.send({"action": "END_TURN"})
                break

            if choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(self._local_player.hand):
                    card = self._local_player.hand[idx]

                    if self._local_player.mana_pool < card["cost"]:
                        print("Mana insuficiente!")
                        time.sleep(1)
                        continue

                    self._local_player.hand.pop(idx)
                    self._local_player.mana_pool -= card["cost"]

                    if card.get("return_mana", False):
                        self._local_player.mana_deck += 1
                        self._local_player.mana_max = max(0, self._local_player.mana_max - 1)
                        print(f"\n* ativou a penalidade: 1 Cristal de Mana foi devolvido ao deck!")

                    self._execute_card_action(card)
                    self._sync_state()

                    while self._is_waiting_defense and self._is_game_running:
                        time.sleep(0.1)
                else:
                    print("Índice de carta inválido.")
                    time.sleep(1)

    def _execute_card_action(self, card):
        if card["type"] == "DANO":
            self._is_waiting_defense = True
            self._network.send({
                "action": "ATTACK_REQUEST",
                "value": card["value"],
                "card_name": card["name"]
            })
            print(f"Jogando {card['name']}! Aguardando resposta do oponente...")

        elif card["type"] == "CURA":
            self._local_player.hp = min(10, self._local_player.hp + card["value"])
            print(f"Você jogou {card['name']} e se curou em {card['value']} pontos.")
            time.sleep(1.5)

        elif card["type"] == "DEFESA":
            self._local_player.defense_active += card["value"]
            print(f"Você jogou {card['name']}. Defesa passiva aumentada em +{card['value']}.")
            time.sleep(1.5)

    def on_message_received(self, data):
        if not self._is_connected:
            self._is_connected = True

        action = data.get("action")

        if action == "SYNC_STATE":
            self._opp_hp = data.get("hp")
            self._opp_mana = data.get("mana")
            self._opp_hand_count = data.get("hand_count")
            self._opp_defense = data.get("defense")

        elif action == "END_TURN":
            self._local_player.set_turn(True)

        elif action == "ATTACK_REQUEST":
            damage = data.get("value")
            card_name = data.get("card_name")
            self._handle_incoming_attack(damage, card_name)

        elif action == "ATTACK_RESOLVED":
            final_damage = data.get("final_damage")
            self._opp_hp -= final_damage
            self._is_waiting_defense = False
            self._sync_state()

    def _handle_incoming_attack(self, damage, card_name):
        self._view.clear_screen()
        print(f"⚠️ Oponente usou a carta [{card_name}] causando {damage} de Dano!")

        playable_defenses = [
            (idx, c) for idx, c in enumerate(self._local_player.hand)
            if c["type"] == "DEFESA" and self._local_player.mana_pool >= c["cost"]
        ]

        if playable_defenses:
            print("\nVocê possui cartas de defesa válidas na mão:")
            for idx, c in playable_defenses:
                special_info = " (⚠️ Devolve 1 Mana ao Deck)" if c.get("return_mana", False) else ""
                print(f"  [{idx}] {c['name']} (Defesa: {c['value']}, Custo: {c['cost']}){special_info}")
            print("  [pass] Não defender (sofrer dano ou mitigar com defesa passiva)")

            choice = self._view.prompt_input(f"Escolha sua reação contra [{card_name}]: ").strip().lower()
            if choice.isdigit():
                chosen_idx = int(choice)
                if any(idx == chosen_idx for idx, _ in playable_defenses):
                    chosen_card = self._local_player.hand.pop(chosen_idx)
                    self._local_player.mana_pool -= chosen_card["cost"]
                    self._local_player.defense_active += chosen_card["value"]
                    print(f"\n[+] Você jogou a carta de defesa de reação: {chosen_card['name']}!")

                    if chosen_card.get("return_mana", False):
                        self._local_player.mana_deck += 1
                        self._local_player.mana_max = max(0, self._local_player.mana_max - 1)
                        print("[*] Defesa Penalizada! 1 Cristal de Mana foi devolvido ao deck.")
        else:
            print("\nVocê não possui mana ou cartas de defesa para reagir a este ataque.")
            time.sleep(1.5)

        total_defense = self._local_player.defense_active
        if total_defense >= damage:
            self._local_player.defense_active -= damage
            final_damage = 0
        else:
            final_damage = damage - total_defense
            self._local_player.defense_active = 0
            self._local_player.hp -= final_damage

        print(f"Resultado do Impacto de [{card_name}]: Dano real sofrido: {final_damage}")

        if self._local_player.hp <= 0:
            print("\n💀 Você foi derrotado! Fim de jogo.")
            self._network.send({"action": "ATTACK_RESOLVED", "final_damage": final_damage})
            self._sync_state()
            time.sleep(1)
            self.stop()
            return

        self._network.send({
            "action": "ATTACK_RESOLVED",
            "final_damage": final_damage
        })
        self._sync_state()
        time.sleep(2.5)

    def on_connection_lost(self):
        self._view.display_message("\n[-] Conexão com o adversário foi perdida.")
        self.stop()

    def stop(self):
        self._is_game_running = False
        self._network.disconnect()
        self._view.display_message("[*] Aplicação encerrada com sucesso.")
        time.sleep(0.5)
        sys.exit(0)