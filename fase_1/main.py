"""
Jogo de autorama para dois jogadores feito em Pygame.

O jogo simula uma pista vista de cima, com dois carros controlados pelo teclado
e colisão precisa com a borda da pista usando máscaras.
"""

import os
import pygame
import math
from utils import scale_image, blit_rotate_center

pygame.init()

FILE_PATH = os.path.dirname(__file__)
IMG_PATH = os.path.join(FILE_PATH, "img")

GRASS = scale_image(pygame.image.load(os.path.join(IMG_PATH, "grass.jpg")), 2.5)
TRACK = scale_image(pygame.image.load(os.path.join(IMG_PATH, "track.png")), 1)

# Imagem da borda da pista, usada para detectar colisões.
# Ela deve ter o mesmo fator de escala da pista.
TRACK_BORDER = scale_image(pygame.image.load(os.path.join(IMG_PATH, "track-border.png")), 1)

RED_CAR = scale_image(pygame.image.load(os.path.join(IMG_PATH, "red-car.png")), 0.55)
GREEN_CAR = scale_image(pygame.image.load(os.path.join(IMG_PATH, "green-car.png")), 0.55)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autorama 2 Jogadores")

FPS = 60

class AbstractCar:
    """
 self.vele baseself.img.get_heightm carro no autorama.

    Centraliza a lógica de movimento, rotação, aceleração e colisão,
    permitindo que diferentes carros compartilhem o mesmo comportamento.
    """
    def _init_(self, max_vel, rotation_vel):
        """Inicializa os atributos principais do carro."""
        self.img = self.IMG
        self.max_vel = max_vel
        self.vel = 0
        self.rotation_vel = rotation_vel
        self.angle = 0
        self.x, self.y = self.START_POS
        self.acceleration = 0.1
        self.width = self.img.get_width()
        self.height = self.img.get_height()

    def rotate(self, left=False, right=False):
        """
        Rotaciona o carro para a esquerda ou para a direita.

        No contexto do autorama, isso representa a mudança de direção
        enquanto o carrinho percorre a pista.
        """
        if left:
            self.angle += self.rotation_vel
        elif right:
            self.angle -= self.rotation_vel

    def draw(self, win):
        """Desenha o carro na tela já considerando sua rotação atual."""
        blit_rotate_center(win, self.img, (self.x, self.y), self.angle)

    def get_rotated_mask(self):
        """
        Retorna a máscara do carro na rotação atual e a imagem rotacionada.

        Isso é importante para detectar colisão com a borda da pista de forma precisa.
        """
        rotated_image = pygame.transform.rotate(self.img, self.angle)
        return pygame.mask.from_surface(rotated_image), rotated_image

    def collide(self, mask, x=0, y=0):
        """
        Verifica se o carro colidiu com uma máscara fornecida.

        No jogo, essa máscara representa a borda da pista, simulando
        o limite físico do autorama.
        """
        car_mask, rotated_image = self.get_rotated_mask()

        # Pega o retângulo do carro rotacionado para descobrir sua posição exata.
        rotated_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)

        # Calcula o deslocamento entre a posição da máscara da pista e a posição do carro.
        offset = (int(rotated_rect.left - x), int(rotated_rect.top - y))

        # Se houver sobreposição, retorna um ponto de colisão; caso contrário, retorna None.
        poi = mask.overlap(car_mask, offset)
        return poi

    def move_forward(self):
        """
        Move o carro para frente.

        Se o carro tocar na borda da pista, o movimento é desfeito
        e a velocidade é zerada.
        """
        old_x, old_y = self.x, self.y
        self.vel = min(self.vel + self.acceleration, self.max_vel)
        self.move()

        if self.collide(TRACK_BORDER_MASK) is not None:
            self.x, self.y = old_x, old_y
            self.vel = 0  # Para o carro imediatamente ao bater

    def move_backward(self):
        """
        Move o carro para trás.

        Se o carro tocar na borda da pista, o movimento é desfeito
        e a velocidade é zerada.
        """
        old_x, old_y = self.x, self.y
        self.vel = max(self.vel - self.acceleration, -self.max_vel / 2)
        self.move()

        if self.collide(TRACK_BORDER_MASK) is not None:
            self.x, self.y = old_x, old_y
            self.vel = 0

    def move(self):
        """
        Atualiza a posição do carro de acordo com seu ângulo e velocidade.

        A matemática usa seno e cosseno para fazer o movimento seguir
        a direção apontada pelo carro, como em um autorama real.
        """
        radians = math.radians(self.angle)
        vertical = math.cos(radians) * self.vel
        horizontal = math.sin(radians) * self.vel

        self.y -= vertical
        self.x -= horizontal

    def reduce_speed(self):
        """
        Reduz gradualmente a velocidade do carro quando não há aceleração.

        Isso simula a desaceleração natural do carrinho no autorama.
        Se houver colisão durante esse deslocamento, o carro volta à posição anterior.
        """
        old_x, old_y = self.x, self.y

        if self.vel > 0:
            self.vel = max(self.vel - self.acceleration / 2, 0)
        elif self.vel < 0:
            self.vel = min(self.vel + self.acceleration / 2, 0)

        self.move()

        if self.collide(TRACK_BORDER_MASK) is not None:
            self.x, self.y = old_x, old_y
            self.vel = 0




class PlayerCar(AbstractCar):
    """
    Carro do jogador 1.

    Usa a imagem vermelha e começa em uma posição específica da pista.
    """
    IMG = RED_CAR
    START_POS = (430, 75)   # carro 1


class GreenCar(AbstractCar):
    """
    Carro do jogador 2.

    Usa a imagem verde e começa em uma posição específica da pista.
    """
    IMG = GREEN_CAR
    START_POS = (520, 75)   # carro 2

def draw(win, car1, car2):
    """
    Desenha a cena completa do jogo.

    Primeiro a pista é colocada no fundo, depois os carros,
    e por fim a tela é atualizada.
    """
    win.blit(TRACK, (0, 0))
    # Se quiser desenhar a borda da pista por cima da imagem da pista, use esta linha:
    # win.blit(TRACK_BORDER, (0, 0))
    car1.draw(win)
    car2.draw(win)
    pygame.display.update()
