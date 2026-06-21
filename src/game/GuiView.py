import pygame
import sys


class GuiView:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("Idan - Card Game P2P")
        self.font = pygame.font.SysFont("Arial", 20)

    def display_board(self, local_player, opp_hp, opp_mana, opp_hand_count, opp_defense):
        self.screen.fill((30, 30, 30))

        texto_vida = self.font.render(f"Sua Vida: {local_player.hp}/10", True, (255, 255, 255))
        self.screen.blit(texto_vida, (50, 600))

        for idx, card in enumerate(local_player.hand):
            pygame.draw.rect(self.screen, (50, 50, 150), (50 + idx * 160, 650, 140, 90))

        pygame.display.flip()

    def prompt_input(self, prompt=""):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass