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
IMG_PATH = os.path.join(FILE_PATH, "imgs")

GRASS = scale_image(pygame.image.load(os.path.join(IMG_PATH, "grass.jpg")), 2.5)
TRACK = scale_image(pygame.image.load(os.path.join(IMG_PATH, "track.png")), 1)

