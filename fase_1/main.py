import importlib.util
import math
import os
import sys
import pygame

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
PHASE2_DIR = os.path.join(ROOT_DIR, "fase_2")

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from utils import scale_image, blit_rotate_center

pygame.init()

FILE_PATH = os.path.dirname(__file__)
IMG_PATH = os.path.abspath(os.path.join(FILE_PATH, "..", "img"))

GRASS = scale_image(pygame.image.load(os.path.join(IMG_PATH, "gramado.png")), 2.5)
TRACK = scale_image(pygame.image.load(os.path.join(IMG_PATH, "pista.png")), 1)

# Imagem da borda da pista, usada para detectar colisões.
# Ela deve ter o mesmo fator de escala da pista.
TRACK_BORDER = scale_image(pygame.image.load(os.path.join(IMG_PATH, "contorno.png")), 1)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

RED_CAR = scale_image(pygame.image.load(os.path.join(IMG_PATH, "mazda.png")), 0.070)
GREEN_CAR = scale_image(pygame.image.load(os.path.join(IMG_PATH, "lfa.png")), 0.070)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autorama 2 Jogadores")

FONT_BIG = pygame.font.SysFont("arial", 54, bold=True)
FONT_MED = pygame.font.SysFont("arial", 34, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 24)

FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 221, 0)
GREEN = (0, 200, 0)
GRAY = (100, 100, 100)
CYAN = (0, 200, 200)
DARK = (20, 20, 20)


def load_image(filename: str, scale: float = 1.0, fallback: str | None = None) -> pygame.Surface:
    path = os.path.join(IMG_PATH, filename)
    if not os.path.exists(path):
        if fallback is None:
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        path = os.path.join(IMG_PATH, fallback)
    image = pygame.image.load(path)
    return scale_image(image, scale)


def load_assets(level: int):
    if level == 2:
        grass = load_image("grass2.jpg", 2.5, fallback="gramado.png")
        track = load_image("track2.png", 1.0, fallback="pista.png")
        border = load_image("track2-border.png", 1.0, fallback="contorno.png")
    else:
        grass = load_image("gramado.png", 2.5, fallback="grass.jpg")
        track = load_image("pista.png", 1.0, fallback="track.png")
        border = load_image("contorno.png", 1.0, fallback="track-border.png")

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
    """Calcula as faixas laterais garantindo que a distância se mantenha nas curvas."""
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

        dot = ox * n1x + oy * n1y
        
        # CÁLCULO SEGURO: Limita a aberração em curvas muito fechadas
        if dot > 0.1:
            length = offset / dot
            # A TRAVA: Impede que o offset seja maior que 1.5x o espaço original
            length = min(length, offset * 1.5) 
        else:
            length = offset

        result.append((int(x + ox * length), int(y + oy * length)))

    return result


def centerline_points(level: int, track: pygame.Surface) -> list[tuple[int, int]]:
    w, h = track.get_width(), track.get_height()

    if level == 2:
        raw = [
            (0.12, 0.06), (0.42, 0.06), (0.54, 0.16), (0.54, 0.34),
            (0.80, 0.34), (0.88, 0.50), (0.81, 0.66), (0.60, 0.66),
            (0.60, 0.83), (0.43, 0.91), (0.18, 0.84), (0.09, 0.66),
            (0.09, 0.38), (0.18, 0.20),
        ]
    else:
        raw = [
    (0.50, 0.10),
    (0.56, 0.10),
    (0.59, 0.10),
    (0.64, 0.10),
    (0.69, 0.10),
    (0.72, 0.10),
    (0.75, 0.10),
    (0.79, 0.10),
    (0.82, 0.10),
    (0.84, 0.10),
    (0.86, 0.11),
    (0.88, 0.12),
    (0.90, 0.14),
    (0.90, 0.16),
    (0.90, 0.21),
    (0.90, 0.27),
    (0.90, 0.29),
    (0.89, 0.31),
    (0.87, 0.32),
    (0.86, 0.33),
    (0.80, 0.33),
    (0.74, 0.33),
    (0.60, 0.33),
    (0.57, 0.34),
    (0.56, 0.35),
    (0.54, 0.37),
    (0.54, 0.40),
    (0.54, 0.42),
    (0.54, 0.44),
    (0.56, 0.46),
    (0.57, 0.47),
    (0.59, 0.47),
    (0.61, 0.48),
    (0.84, 0.48),
    (0.86, 0.48),
    (0.88, 0.49),
    (0.88, 0.50),
    (0.89, 0.51),
    (0.90, 0.52),
    (0.90, 0.54),
    (0.90, 0.84),
    (0.90, 0.87),
    (0.88, 0.90),
    (0.86, 0.91),
    (0.84, 0.91),
    (0.82, 0.91),
    (0.80, 0.91),
    (0.77, 0.91),
    (0.75, 0.90),
    (0.73, 0.89),
    (0.72, 0.86),
    (0.71, 0.83),
    (0.71, 0.72),
    (0.70, 0.68),
    (0.68, 0.67),
    (0.66, 0.65),
    (0.64, 0.65),
    (0.60, 0.64),
    (0.58, 0.65),
    (0.57, 0.66),
    (0.55, 0.67),
    (0.54, 0.68),
    (0.53, 0.70),
    (0.52, 0.72),
    (0.52, 0.74),
    (0.52, 0.83),
    (0.51, 0.86),
    (0.49, 0.89),
    (0.47, 0.90),
    (0.45, 0.91),
    (0.41, 0.91),
    (0.38, 0.90),
    (0.36, 0.89),
    (0.35, 0.88),
    (0.10, 0.63),
    (0.09, 0.59),
    (0.09, 0.57),
    (0.10, 0.17),
    (0.11, 0.13),
    (0.13, 0.11),
    (0.15, 0.10),
    (0.17, 0.10),
    (0.19, 0.10),
    (0.20, 0.11),
    (0.22, 0.12),
    (0.23, 0.14),
    (0.23, 0.16),
    (0.24, 0.46),
    (0.25, 0.48),
    (0.27, 0.50),
    (0.29, 0.51),
    (0.32, 0.51),
    (0.33, 0.51),
    (0.36, 0.49),
    (0.37, 0.46),
    (0.38, 0.45),
    (0.38, 0.15),
    (0.40, 0.12),
    (0.42, 0.10),
    (0.45, 0.10),
    (0.46, 0.10),
    (0.48, 0.10),
    (0.50, 0.10),
]

    return [pct(w, h, x, y) for x, y in raw]


def build_lane_paths(track: pygame.Surface, level: int, lane_offset: int = 24):
    """
    Aumentamos o lane_offset de 16 para 24 para garantir
    que os carros fiquem mais afastados da linha do meio.
    """
    center = centerline_points(level, track)
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


def draw_button(surface, rect, text, active=False):
    color = YELLOW if active else GRAY
    pygame.draw.rect(surface, color, rect, border_radius=14)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=14)
    label = FONT_SMALL.render(text, True, BLACK)
    surface.blit(label, label.get_rect(center=rect.center))


def start_screen():
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
        center_text(WIN, "AUTORAMA 2 JOGADORES", FONT_BIG, WHITE, 110)
        center_text(WIN, "Cada carro tem sua faixa exclusiva", FONT_MED, YELLOW, 220)
        center_text(WIN, "P1: W acelera / S freia", FONT_MED, WHITE, 280)
        center_text(WIN, "P2: UP acelera / DOWN freia", FONT_MED, WHITE, 330)
        center_text(WIN, "Cada fase termina com 5 voltas", FONT_SMALL, WHITE, 390)
        center_text(WIN, "Pressione ENTER para começar", FONT_MED, GREEN, 470)
        pygame.display.update()


def ask_player_names():
    clock = pygame.time.Clock()
    name1 = ""
    name2 = ""
    active = 1

    box1 = pygame.Rect(120, 220, 560, 60)
    box2 = pygame.Rect(120, 330, 560, 60)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    active = 2 if active == 1 else 1
                elif event.key == pygame.K_RETURN:
                    return name1.strip() or "Corredor 1", name2.strip() or "Corredor 2"
                elif event.key == pygame.K_BACKSPACE:
                    if active == 1:
                        name1 = name1[:-1]
                    else:
                        name2 = name2[:-1]
                else:
                    if event.unicode.isprintable() and len(event.unicode) == 1:
                        if active == 1 and len(name1) < 16:
                            name1 += event.unicode
                        elif active == 2 and len(name2) < 16:
                            name2 += event.unicode

        WIN.fill(DARK)
        center_text(WIN, "Digite o nome dos corredores", FONT_BIG, WHITE, 110)
        center_text(WIN, "TAB troca de campo | ENTER confirma", FONT_SMALL, YELLOW, 170)

        label1 = FONT_SMALL.render("Carro vermelho:", True, WHITE)
        label2 = FONT_SMALL.render("Carro verde:", True, WHITE)
        WIN.blit(label1, (120, 190))
        WIN.blit(label2, (120, 300))

        pygame.draw.rect(WIN, WHITE, box1, 2, border_radius=12)
        pygame.draw.rect(WIN, WHITE, box2, 2, border_radius=12)

        if active == 1:
            pygame.draw.rect(WIN, GREEN, box1, 4, border_radius=12)
        else:
            pygame.draw.rect(WIN, GREEN, box2, 4, border_radius=12)

        text1 = FONT_MED.render(name1 or "...", True, WHITE)
        text2 = FONT_MED.render(name2 or "...", True, WHITE)
        WIN.blit(text1, (140, 230))
        WIN.blit(text2, (140, 340))

        draw_button(WIN, pygame.Rect(120, 430, 220, 52), "ENTER para confirmar", True)
        pygame.display.update()


def show_message_screen(title, lines, footer="Pressione ENTER para continuar"):
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
        center_text(WIN, title, FONT_BIG, WHITE, 110)

        y = 240
        for line in lines:
            center_text(WIN, line, FONT_MED, WHITE, y)
            y += 50

        center_text(WIN, footer, FONT_SMALL, YELLOW, WIN.get_height() - 70)
        pygame.display.update()


def run_phase(level: int, player1_name: str, player2_name: str):
    global WIN

    DEBUG_PATHS = True # <--- Deixe True para ver as linhas invisíveis

    grass, track, border, red_car_img, green_car_img = load_assets(level)
    WIN = pygame.display.set_mode(track.get_size())

    # Aumentado para 35 pixels de distância do centro para evitar colisões
    lane_offset = 22 
    
    # Gerando os caminhos
    center_raw_points = centerline_points(level, track)
    lane_left, lane_right = build_lane_paths(track, level, lane_offset)
    center_path = build_path(center_raw_points, density=18)

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

        # --- MODO DEBUG: DESENHANDO AS LINHAS ---
        if DEBUG_PATHS:
            if len(center_path) > 1:
                pygame.draw.lines(WIN, YELLOW, True, center_path, 2) # Linha do Meio (amarela)
            if len(lane_left) > 1:
                pygame.draw.lines(WIN, RED, True, lane_left, 2)      # Pista do Carro 1 (vermelha)
            if len(lane_right) > 1:
                pygame.draw.lines(WIN, GREEN, True, lane_right, 2)   # Pista do Carro 2 (verde)
        # ----------------------------------------

        car1.draw(WIN)
        car2.draw(WIN)

        laps_1 = FONT_SMALL.render(f"{player1_name}: {car1.laps}/5", True, WHITE)
        laps_2 = FONT_SMALL.render(f"{player2_name}: {car2.laps}/5", True, WHITE)
        phase_label = FONT_SMALL.render(f"Fase {level}", True, CYAN)

        WIN.blit(laps_1, (20, 18))
        WIN.blit(laps_2, (20, 46))
        WIN.blit(phase_label, (WIN.get_width() - 110, 18))

        pygame.display.update()

        if winner is not None:
            return winner, car1.laps, car2.laps

def load_phase2_module():
    phase2_path = os.path.join(PHASE2_DIR, "main.py")
    spec = importlib.util.spec_from_file_location("fase2_main_module", phase2_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Não foi possível carregar fase_2/main.py")

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, PHASE2_DIR)
    spec.loader.exec_module(module)
    return module


def show_phase_result(phase, winner_id, player1_name, player2_name, laps_1, laps_2):
    winner_name = player1_name if winner_id == 1 else player2_name
    show_message_screen(
        f"Fase {phase} concluída",
        [
            f"Vencedor: {winner_name}",
            f"{player1_name}: {laps_1} voltas",
            f"{player2_name}: {laps_2} voltas",
        ],
    )


def show_final_screen(phase1_winner, phase2_winner, player1_name, player2_name):
    score1 = (1 if phase1_winner == 1 else 0) + (1 if phase2_winner == 1 else 0)
    score2 = (1 if phase1_winner == 2 else 0) + (1 if phase2_winner == 2 else 0)

    if score1 > score2:
        champ = f"Campeão geral: {player1_name}"
    elif score2 > score1:
        champ = f"Campeão geral: {player2_name}"
    else:
        champ = "Empate geral!"

    show_message_screen(
        "Resultado final",
        [
            champ,
            f"Fase 1: {'carro vermelho' if phase1_winner == 1 else 'carro verde'}",
            f"Fase 2: {'carro vermelho' if phase2_winner == 1 else 'carro verde'}",
        ],
        footer="Pressione ENTER para sair",
    )


def main():
    start_screen()
    player1_name, player2_name = ask_player_names()

    phase1_winner, laps1_p1, laps1_p2 = run_phase(1, player1_name, player2_name)
    show_phase_result(1, phase1_winner, player1_name, player2_name, laps1_p1, laps1_p2)

    show_message_screen(
        "FASE 2",
        [
            "Agora a segunda pista vai começar.",
            "Os carrinhos continuam na própria faixa.",
            "Quem fizer 5 voltas primeiro vence.",
        ],
    )

    try:
        phase2_module = load_phase2_module()
        phase2_winner, laps2_p1, laps2_p2 = phase2_module.run_phase_2(player1_name, player2_name)
        show_phase_result(2, phase2_winner, player1_name, player2_name, laps2_p1, laps2_p2)
    except Exception as e:
        print(f"Não foi possível carregar a fase 2. Erro: {e}")

    show_final_screen(phase1_winner, phase2_winner, player1_name, player2_name)
    pygame.quit()


if __name__ == "__main__":
    main()