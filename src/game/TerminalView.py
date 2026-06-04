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