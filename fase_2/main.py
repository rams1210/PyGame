import math
import os
import sys
import pygame

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from utils import scale_image, blit_rotate_center

pygame.init()
pygame.font.init()

IMG_PATH = os.path.join(ROOT_DIR, "img")

FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK = (18, 18, 18)
GRAY = (90, 90, 90)
GREEN = (60, 180, 75)
YELLOW = (255, 215, 0)

WIN = pygame.display.set_mode((900, 600))
pygame.display.set_caption("Autorama - Fase 2")

FONT_BIG = pygame.font.SysFont("arial", 54, bold=True)
FONT_MED = pygame.font.SysFont("arial", 34, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 24)


def load_image(filename: str, scale: float = 1.0, fallback: str | None = None) -> pygame.Surface:
    path = os.path.join(IMG_PATH, filename)
    if not os.path.exists(path):
        if fallback is None:
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        path = os.path.join(IMG_PATH, fallback)
    image = pygame.image.load(path)
    return scale_image(image, scale)


def load_assets():
    grass = load_image("grass2.jpg", 2.5, fallback="gramado.png")
    track = load_image("track2.png", 1.0, fallback="pista.png")
    border = load_image("track2-border.png", 1.0, fallback="contorno.png")
    red_car = load_image("mazda.png", 0.070, fallback="red-car.png")
    green_car = load_image("lfa.png", 0.070, fallback="green-car.png")
    return grass, track, border, red_car, green_car


def pct(w: int, h: int, x: float, y: float) -> tuple[int, int]:
    return int(w * x), int(h * y)


def build_path(points: list[tuple[int, int]], density: int = 18) -> list[tuple[float, float]]:
    path: list[tuple[float, float]] = []
    for i in range(len(points)):
        a = points[i]
        b = points[(i + 1) % len(points)]
        for step in range(density):
            t = step / density
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            path.append((x, y))
    return path


def normalize(x: float, y: float) -> tuple[float, float]:
    dist = math.hypot(x, y)
    if dist == 0:
        return 0.0, 0.0
    return x / dist, y / dist


def offset_closed_polyline(points: list[tuple[int, int]], offset: float) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    n = len(points)

    for i in range(n):
        x, y = points[i]
        px, py = points[i - 1]
        nx, ny = points[(i + 1) % n]

        v1x, v1y = normalize(x - px, y - py)
        v2x, v2y = normalize(nx - x, ny - y)

        n1x, n1y = -v1y, v1x
        n2x, n2y = -v2y, v2x

        ox, oy = normalize(n1x + n2x, n1y + n2y)
        if ox == 0 and oy == 0:
            ox, oy = n1x, n1y
            if ox == 0 and oy == 0:
                ox, oy = n2x, n2y

        result.append((int(x + ox * offset), int(y + oy * offset)))

    return result


def centerline_points(track: pygame.Surface) -> list[tuple[int, int]]:
    w, h = track.get_width(), track.get_height()

    raw = [
        (0.12, 0.06),
        (0.42, 0.06),
        (0.54, 0.16),
        (0.54, 0.34),
        (0.80, 0.34),
        (0.88, 0.50),
        (0.81, 0.66),
        (0.60, 0.66),
        (0.60, 0.83),
        (0.43, 0.91),
        (0.18, 0.84),
        (0.09, 0.66),
        (0.09, 0.38),
        (0.18, 0.20),
    ]

    return [pct(w, h, x, y) for x, y in raw]


def build_lane_paths(track: pygame.Surface, lane_offset: int = 16):
    center = centerline_points(track)
    left_lane = build_path(offset_closed_polyline(center, -lane_offset), density=18)
    right_lane = build_path(offset_closed_polyline(center, lane_offset), density=18)
    return left_lane, right_lane


class SlotCar:
    def __init__(self, image: pygame.Surface, path: list[tuple[float, float]], max_vel: float = 4.2):
        self.img = image
        self.path = path
        self.max_vel = max_vel
        self.vel = 0.0
        self.acceleration = 0.08
        self.angle = 0.0
        self.path_index = 0
        self.laps = 0
        self.locked = False
        self.x, self.y = self.path[0]
        self.sync_angle()

    def sync_angle(self):
        if len(self.path) > 1:
            nx, ny = self.path[1]
            self.angle = -math.degrees(math.atan2(ny - self.y, nx - self.x)) + 90

    def draw(self, win: pygame.Surface):
        blit_rotate_center(win, self.img, (self.x, self.y), self.angle)

    def advance(self, distance: float):
        remaining = distance

        while remaining > 0 and not self.locked:
            next_index = (self.path_index + 1) % len(self.path)
            next_x, next_y = self.path[next_index]

            dx = next_x - self.x
            dy = next_y - self.y
            dist = math.hypot(dx, dy)

            if dist < 0.001:
                self.x, self.y = next_x, next_y
                self.path_index = next_index
                if self.path_index == 0:
                    self.laps += 1
                    if self.laps >= 5:
                        self.locked = True
                        self.vel = 0.0
                        return
                continue

            step = min(remaining, dist)
            self.angle = -math.degrees(math.atan2(dy, dx)) + 90
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            remaining -= step

            if step >= dist - 0.001:
                self.path_index = next_index
                if self.path_index == 0:
                    self.laps += 1
                    if self.laps >= 5:
                        self.locked = True
                        self.vel = 0.0
                        return
            else:
                break

    def accelerate(self):
        if self.locked:
            return
        self.vel = min(self.vel + self.acceleration, self.max_vel)
        self.advance(self.vel)

    def brake(self):
        if self.locked:
            return
        self.vel = max(self.vel - self.acceleration * 2, 0.0)
        if self.vel > 0:
            self.advance(self.vel)

    def coast(self):
        if self.locked:
            return
        self.vel = max(self.vel - self.acceleration * 0.35, 0.0)
        if self.vel > 0:
            self.advance(self.vel)


def center_text(surface, text, font, color, y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(surface.get_width() // 2, y))
    surface.blit(rendered, rect)


def show_message(title, lines, footer="Pressione ENTER para continuar"):
    clock = pygame.time.Clock()
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return

        WIN.fill(DARK)
        center_text(WIN, title, FONT_BIG, WHITE, 120)

        y = 240
        for line in lines:
            center_text(WIN, line, FONT_MED, WHITE, y)
            y += 50

        center_text(WIN, footer, FONT_SMALL, YELLOW, 520)
        pygame.display.update()


def run_phase_2(player1_name="Corredor 1", player2_name="Corredor 2"):
    global WIN

    grass, track, border, red_car_img, green_car_img = load_assets()
    WIN = pygame.display.set_mode(track.get_size())

    lane_left, lane_right = build_lane_paths(track)

    car1 = SlotCar(red_car_img, lane_left)
    car2 = SlotCar(green_car_img, lane_right)

    clock = pygame.time.Clock()
    winner = None

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            car1.accelerate()
        elif keys[pygame.K_s]:
            car1.brake()
        else:
            car1.coast()

        if keys[pygame.K_UP]:
            car2.accelerate()
        elif keys[pygame.K_DOWN]:
            car2.brake()
        else:
            car2.coast()

        if car1.laps >= 5 and winner is None:
            winner = 1
        if car2.laps >= 5 and winner is None:
            winner = 2

        WIN.blit(grass, (0, 0))
        WIN.blit(track, (0, 0))
        WIN.blit(border, (0, 0))

        car1.draw(WIN)
        car2.draw(WIN)

        laps_1 = FONT_SMALL.render(f"{player1_name}: {car1.laps}/5", True, WHITE)
        laps_2 = FONT_SMALL.render(f"{player2_name}: {car2.laps}/5", True, WHITE)
        WIN.blit(laps_1, (20, 18))
        WIN.blit(laps_2, (20, 46))

        pygame.display.update()

        if winner is not None:
            return winner, car1.laps, car2.laps


def main():
    show_message(
        "FASE 2",
        [
            "Nesta fase o carro também segue uma faixa fixa.",
            "O primeiro a completar 5 voltas vence.",
        ],
    )

    winner, laps1, laps2 = run_phase_2()

    show_message(
        "Resultado da Fase 2",
        [
            f"Vencedor: {'Carro vermelho' if winner == 1 else 'Carro verde'}",
            f"Voltas do carro vermelho: {laps1}",
            f"Voltas do carro verde: {laps2}",
        ],
        footer="Pressione ENTER para sair",
    )

    pygame.quit()


if __name__ == "__main__":
    main()