import sys
import time

from src.network.NetworkEngine import NetworkEngine
from src.network.NetworkObserver import NetworkObserver
from src.game.Player import Player
from src.game.TerminalView import TerminalView

class GameController(NetworkObserver):

    def __init__(self, network_engine, player_name):
        self._network = network_engine
        self._local_player = Player(player_name)
        self._is_game_running = False

    def setup_connection(self, role, host, port):
        self._is_game_running = True

        if role == "host":
            self._local_player.set_turn(True)
            self._network.start_as_host(host, port)
            TerminalView.display_message(f"[*] Aguardando conexão em {host}:{port}...")
        else:
            self._local_player.set_turn(False)
            TerminalView.display_message(f"[*] Conectando-se a {host}:{port}...")
            if not self._network.connect_as_guest(host, port):
                TerminalView.display_message("[-] Falha crítica ao conectar ao Host.")
                sys.exit(1)

    def start_chat_loop(self):
        TerminalView.display_message("[+] Conexão Estabelecida! Digite 'exit' para sair.\n")

        while self._is_game_running:
            if self._local_player._is_my_turn:
                text = TerminalView.prompt_input(f"({self._local_player.name}) Sua mensagem: ")

                if text.strip().lower() == "exit":
                    self.stop()
                    break

                if text.strip():
                    payload = {
                        "action": "CHAT_MESSAGE",
                        "sender": self._local_player.name,
                        "payload": {"text": text}
                    }
                    self._network.send(payload)
                    self._local_player.set_turn(False)
            else:
                time.sleep(0.1)

    def on_message_received(self, data):
        action = data.get("action")
        sender = data.get("sender", "Oponente")

        if action == "CHAT_MESSAGE":
            message_text = data.get("payload", {}).get("text", "")
            TerminalView.display_opponent_message(sender, message_text)
            self._local_player.set_turn(True)

    def on_connection_lost(self):
        TerminalView.display_message("\n[-] Conexão com o adversário foi perdida.")
        self.stop()
        sys.exit(0)

    def stop(self):
        self._is_game_running = False
        self._network.disconnect()
        TerminalView.display_message("[*] Aplicação encerrada com sucesso.")