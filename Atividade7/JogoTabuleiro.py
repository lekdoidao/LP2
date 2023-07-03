import pygame
import random
import os

# Inicialização do Pygame
pygame.init()

# Configurações da janela
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jogo de Tabuleiro")

# Cores
WHITE = (255, 255, 255)

# Sons
CORRECT_SOUND = pygame.mixer.Sound("sounds/correct.wav")
WRONG_SOUND = pygame.mixer.Sound("sounds/wrong.wav")
WIN_SOUND = pygame.mixer.Sound("sounds/win.wav")

# Configurações do jogo
GRID_SIZE = (4, 5)
CARD_WIDTH, CARD_HEIGHT = 150, 150
GAP = 10
TIMEOUT = 1.5

# Classe para representar as cartas
class Card:
    def __init__(self, image, x, y):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.is_flipped = False
        self.show_image = False
        self.timeout = 0

    def draw(self):
        if self.show_image:
            WIN.blit(self.image, self.rect)
        else:
            pygame.draw.rect(WIN, WHITE, self.rect)

    def flip(self):
        self.show_image = not self.show_image
        self.timeout = pygame.time.get_ticks() + TIMEOUT

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)

    def is_ready_to_flip(self):
        return self.show_image and pygame.time.get_ticks() > self.timeout


def generate_board(grid_size):
    cards = []
    images_path = "images"
    images = os.listdir(images_path)

    random.shuffle(images)

    for y in range(grid_size[1]):
        for x in range(grid_size[0]):
            image_path = os.path.join(images_path, images.pop())
            image = pygame.image.load(image_path)
            image = pygame.transform.scale(image, (CARD_WIDTH, CARD_HEIGHT))
            card = Card(image, x * (CARD_WIDTH + GAP), y * (CARD_HEIGHT + GAP))
            cards.append(card)

    return cards


def main():
    pygame.mixer.music.load("sounds/background_music.mp3")
    pygame.mixer.music.play(-1)

    clock = pygame.time.Clock()
    running = True
    cards = generate_board(GRID_SIZE)
    selected_cards = []

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if len(selected_cards) < 2:
                    for card in cards:
                        if card.is_hovered(pygame.mouse.get_pos()) and not card.is_flipped:
                            card.flip()
                            selected_cards.append(card)

        if len(selected_cards) == 2:
            card1, card2 = selected_cards
            if card1.image == card2.image:
                card1.is_flipped = True
                card2.is_flipped = True
                pygame.mixer.Sound.play(CORRECT_SOUND)
            else:
                card1.flip()
                card2.flip()
                pygame.mixer.Sound.play(WRONG_SOUND)

            selected_cards = []

        WIN.fill(WHITE)

        for card in cards:
            card.draw()

        pygame.display.update()

        if all(card.is_flipped for card in cards):
            pygame.mixer.music.stop()
            pygame.mixer.Sound.play(WIN_SOUND)
            running = False

    pygame.time.delay(2000)  # Espera 2 segundos para finalizar
    pygame.quit()


if __name__ == "__main__":
    main()
