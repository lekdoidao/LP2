import pygame
import random
import sys

# Inicialização do Pygame
pygame.init()

# Configurações da janela
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 300
WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Software Interativo")

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Fonte
FONT = pygame.font.Font(None, 36)

# Texto
prompt_text = "Clique no botão para obter uma resposta!"
button_text = "Clique aqui!"

# Função para obter uma resposta aleatória
def get_random_response():
    responses = [
        "Sim",
        "Não",
        "Talvez",
        "Definitivamente",
        "Claro!",
        "Sem dúvida",
        "Não acredito",
    ]
    return random.choice(responses)

def main():
    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Verificar se o clique ocorreu no botão
                if button_rect.collidepoint(pygame.mouse.get_pos()):
                    response = get_random_response()
                    print("Resposta:", response)

        WIN.fill(WHITE)

        # Desenhar o botão
        button_rect = pygame.Rect(150, 150, 100, 50)
        pygame.draw.rect(WIN, BLACK, button_rect)
        button_surface = FONT.render(button_text, True, WHITE)
        WIN.blit(button_surface, (160, 160))

        # Exibir o texto de instrução
        prompt_surface = FONT.render(prompt_text, True, BLACK)
        WIN.blit(prompt_surface, (40, 100))

        pygame.display.update()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
