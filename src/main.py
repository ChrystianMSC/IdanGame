import sys
from src.network.P2PNetworkManager import P2PNetworkManager
from src.game.GameController import GameController

def main():
    if len(sys.argv) < 3:
        print("Uso correto: python main.py [host|guest] [SeuNome]")
        sys.exit(1)

    role = sys.argv[1].lower()
    player_name = sys.argv[2]

    IP = "127.0.0.1"
    PORT = 9999

    network_manager = P2PNetworkManager()
    game_controller = GameController(network_manager, player_name)

    network_manager.register_observer(game_controller)

    game_controller.setup_connection(role, IP, PORT)
    game_controller.start_chat_loop()

if __name__ == "__main__":
    main()