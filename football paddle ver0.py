import pygame
import math
import random
import sys
import os
import json

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False


# =========================================================
# Main Settings
# =========================================================

WIDTH = 900
HEIGHT = 700
FPS = 60

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HIGHSCORE_PATH = os.path.join(SCRIPT_DIR, "highscore.json")


# =========================================================
# Ball
# =========================================================

BALL_RADIUS = 16

START_SPEED = 5.0
MIN_SPEED = 3.0
MAX_SPEED = 15.0

SPEED_STEP = 0.5

GOAL_SPEED_MULTIPLIER = 1.08

TRAIL_LENGTH = 10


# =========================================================
# Walls
# =========================================================

WALL_THICKNESS = 10

LEFT_WALL = WALL_THICKNESS
RIGHT_WALL = WIDTH - WALL_THICKNESS

TOP_WALL = WALL_THICKNESS
BOTTOM_WALL = HEIGHT - WALL_THICKNESS


# =========================================================
# Goal
# =========================================================

GOAL_WIDTH = 190
GOAL_DEPTH = 45

GOAL_LEFT = (WIDTH - GOAL_WIDTH) / 2
GOAL_RIGHT = GOAL_LEFT + GOAL_WIDTH


# =========================================================
# Player Paddle
# =========================================================

PADDLE_WIDTH = 150
PADDLE_HEIGHT = 16

PADDLE_BASE_Y = 350
PADDLE_ROW_OFFSET = 30

PADDLE_MIN_SPEED = 7.0
PADDLE_MAX_SPEED = 18.0
PADDLE_SPEED_MULTIPLIER = 1.45

# Paddle acceleration for smoother movement
PADDLE_ACCEL = 2600.0
PADDLE_FRICTION = 2200.0

BIG_PADDLE_MULTIPLIER = 1.55


# =========================================================
# Defenders
# =========================================================

DEFENDER_WIDTH = PADDLE_WIDTH / 3
DEFENDER_HEIGHT = 16

DEFENDER_ROW_1_Y = 235
DEFENDER_ROW_2_Y = 125

DEFENDER_BASE_SPEED = 2.2


# =========================================================
# Lives / Misses
# =========================================================

MAX_MISSES = 5


# =========================================================
# Power-Ups
# =========================================================

POWERUP_SIZE = 28
POWERUP_FALL_SPEED = 3.0
POWERUP_SPAWN_MIN_MS = 9000
POWERUP_SPAWN_MAX_MS = 16000
POWERUP_DURATION_MS = 8000

POWERUP_TYPES = ["big_paddle", "slow_ball"]


# =========================================================
# Colors
# =========================================================

BG_COLOR = (14, 16, 21)
FIELD_COLOR_A = (35, 100, 55)
FIELD_COLOR_B = (32, 92, 51)

STAND_COLOR_A = (46, 40, 58)
STAND_COLOR_B = (38, 33, 48)
STAND_DOT = (90, 85, 105)

WALL_COLOR = (75, 80, 95)

BALL_COLOR = (245, 245, 245)
BALL_PATCH_COLOR = (35, 35, 35)
BALL_OUTLINE = (15, 15, 15)
BALL_TRAIL_COLOR = (255, 255, 255)

PADDLE_COLOR_TOP = (120, 195, 250)
PADDLE_COLOR_BOTTOM = (60, 140, 205)
PADDLE_OUTLINE = (20, 70, 110)
PADDLE_BIG_COLOR_TOP = (255, 215, 120)
PADDLE_BIG_COLOR_BOTTOM = (225, 165, 60)

DEFENDER_COLOR_TOP = (230, 100, 100)
DEFENDER_COLOR_BOTTOM = (175, 55, 55)
DEFENDER_OUTLINE = (120, 25, 25)

GOAL_FRAME = (230, 230, 230)
GOAL_NET = (60, 160, 85)

TEXT_COLOR = (240, 240, 240)
SUBTEXT_COLOR = (170, 175, 185)

GOAL_TEXT = (80, 230, 110)
ATTACK_TEXT = (255, 220, 80)
MISS_TEXT = (235, 90, 90)

POWERUP_COLORS = {
    "big_paddle": (255, 200, 60),
    "slow_ball": (110, 200, 255),
}


# =========================================================
# Pygame
# =========================================================

pygame.init()

try:
    pygame.mixer.init()
    MIXER_OK = True
except pygame.error:
    MIXER_OK = False

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Football Paddle Challenge")

clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 22)
small_font = pygame.font.SysFont("arial", 18)
big_font = pygame.font.SysFont("arial", 52, bold=True)
huge_font = pygame.font.SysFont("arial", 64, bold=True)
title_font = pygame.font.SysFont("arial", 58, bold=True)


# =========================================================
# Synthesized Sounds (No External Files)
# =========================================================

def _make_tone(freq, duration, volume=0.4, kind="sine", decay=True):
    """Generate a short sound without requiring an external audio file."""

    if not (NUMPY_OK and MIXER_OK):
        return None

    sample_rate = 44100
    n_samples = int(sample_rate * duration)

    t = np.linspace(0, duration, n_samples, False)

    if kind == "sine":
        wave = np.sin(freq * t * 2 * np.pi)
    elif kind == "square":
        wave = np.sign(np.sin(freq * t * 2 * np.pi))
    elif kind == "noise":
        wave = np.random.uniform(-1, 1, n_samples)
    else:
        wave = np.sin(freq * t * 2 * np.pi)

    if decay:
        envelope = np.linspace(1, 0, n_samples) ** 1.5
        wave = wave * envelope

    audio = (wave * volume * 32767).astype(np.int16)
    stereo = np.column_stack([audio, audio])

    try:
        sound = pygame.sndarray.make_sound(
            np.ascontiguousarray(stereo)
        )
        return sound
    except Exception:
        return None


class Sounds:

    def __init__(self):

        self.paddle_hit = _make_tone(420, 0.09, 0.35, "square")
        self.defender_hit = _make_tone(260, 0.09, 0.30, "square")
        self.wall_hit = _make_tone(180, 0.06, 0.20, "sine")
        self.goal = _make_tone(660, 0.35, 0.40, "sine")
        self.goal_low = _make_tone(330, 0.35, 0.30, "sine")
        self.miss = _make_tone(140, 0.30, 0.35, "square")
        self.powerup = _make_tone(880, 0.18, 0.30, "sine")
        self.gameover = _make_tone(110, 0.6, 0.35, "square")
        self.menu_select = _make_tone(500, 0.08, 0.25, "sine")

    def play(self, sound):

        if sound is not None:

            try:
                sound.play()
            except Exception:
                pass


SFX = Sounds()


# =========================================================
# High Score
# =========================================================

def load_highscore():

    try:

        with open(HIGHSCORE_PATH, "r") as f:

            data = json.load(f)
            return int(data.get("highscore", 0))

    except Exception:

        return 0


def save_highscore(value):

    try:

        with open(HIGHSCORE_PATH, "w") as f:

            json.dump({"highscore": value}, f)

    except Exception:

        pass


# =========================================================
# Helper Functions
# =========================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def lerp(a, b, t):
    return a + (b - a) * t


def vertical_gradient_rect(
    surface,
    rect,
    color_top,
    color_bottom,
    border_radius=0
):
    """Draw a rectangle with a vertical gradient."""

    x, y, w, h = rect

    temp = pygame.Surface((w, h), pygame.SRCALPHA)

    for row in range(h):

        t = row / max(1, h - 1)

        color = (
            int(lerp(color_top[0], color_bottom[0], t)),
            int(lerp(color_top[1], color_bottom[1], t)),
            int(lerp(color_top[2], color_bottom[2], t)),
        )

        pygame.draw.line(temp, color, (0, row), (w, row))

    if border_radius > 0:

        mask = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.rect(
            mask,
            (255, 255, 255, 255),
            (0, 0, w, h),
            border_radius=border_radius
        )

        temp.blit(
            mask,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_MIN
        )

    surface.blit(temp, (x, y))


def regular_polygon_points(cx, cy, radius, sides, rotation=0.0):
    """Return the vertices of a regular polygon."""

    points = []

    for i in range(sides):

        angle = (
            rotation
            + i * (2 * math.pi / sides)
            - math.pi / 2
        )

        points.append((
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle)
        ))

    return points


def draw_soccer_ball(surface, cx, cy, r, rotation):
    """Draw a classic soccer ball with 3D shading."""

    size = r * 2 + 6
    center = (r + 3, r + 3)

    temp = pygame.Surface((size, size), pygame.SRCALPHA)

    # Base body
    pygame.draw.circle(temp, BALL_COLOR, center, r)

    # Central pentagon
    pent_radius = r * 0.36

    center_pts = regular_polygon_points(
        center[0],
        center[1],
        pent_radius,
        5,
        rotation
    )

    pygame.draw.polygon(
        temp,
        BALL_PATCH_COLOR,
        center_pts
    )

    # Radial seams from the central pentagon
    for (px, py) in center_pts:

        dx, dy = px - center[0], py - center[1]
        dist = math.hypot(dx, dy)

        if dist == 0:
            continue

        ux, uy = dx / dist, dy / dist

        seam_end = (
            center[0] + ux * r * 1.05,
            center[1] + uy * r * 1.05
        )

        pygame.draw.line(
            temp,
            (95, 95, 95),
            (px, py),
            seam_end,
            2
        )

    # Outer pentagons
    ring_radius = r * 0.82
    ring_rotation = rotation + math.pi / 5

    ring_centers = regular_polygon_points(
        center[0],
        center[1],
        ring_radius,
        5,
        ring_rotation
    )

    small_pent_radius = r * 0.40

    for (rcx, rcy) in ring_centers:

        outward_angle = math.atan2(
            rcy - center[1],
            rcx - center[0]
        )

        pts = regular_polygon_points(
            rcx,
            rcy,
            small_pent_radius,
            5,
            outward_angle + math.pi / 2
        )

        pygame.draw.polygon(
            temp,
            BALL_PATCH_COLOR,
            pts
        )

    # Shading for a spherical 3D appearance
    shade = pygame.Surface((size, size), pygame.SRCALPHA)

    pygame.draw.circle(
        shade,
        (0, 0, 0, 60),
        (
            center[0] + int(r * 0.38),
            center[1] + int(r * 0.42)
        ),
        int(r * 0.95)
    )

    pygame.draw.circle(
        shade,
        (255, 255, 255, 0),
        center,
        int(r * 0.3)
    )

    temp.blit(shade, (0, 0))

    highlight_pos = (
        center[0] - int(r * 0.35),
        center[1] - int(r * 0.42)
    )

    pygame.draw.circle(
        temp,
        (255, 255, 255, 110),
        highlight_pos,
        max(2, int(r * 0.32))
    )

    pygame.draw.circle(
        temp,
        (255, 255, 255, 180),
        (
            highlight_pos[0] - 2,
            highlight_pos[1] - 2
        ),
        max(1, int(r * 0.12))
    )

    # Circular mask to remove everything outside the ball
    mask = pygame.Surface((size, size), pygame.SRCALPHA)

    pygame.draw.circle(
        mask,
        (255, 255, 255, 255),
        center,
        r
    )

    temp.blit(
        mask,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_MIN
    )

    surface.blit(
        temp,
        (cx - center[0], cy - center[1])
    )

    # Final sharp outline
    pygame.draw.circle(
        surface,
        BALL_OUTLINE,
        (cx, cy),
        r,
        2
    )


# =========================================================
# Particle System (Confetti and Sparks)
# =========================================================

class Particle:

    __slots__ = (
        "x", "y", "vx", "vy", "life", "max_life",
        "color", "size", "gravity", "shrink"
    )

    def __init__(
        self,
        x,
        y,
        vx,
        vy,
        life,
        color,
        size,
        gravity=0.0,
        shrink=True
    ):

        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity
        self.shrink = shrink

    def update(self, dt):

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt

        return self.life > 0

    def draw(self, surface):

        t = clamp(
            self.life / self.max_life,
            0.0,
            1.0
        )

        alpha = int(255 * t)
        size = self.size * (t if self.shrink else 1.0)

        if size < 0.5:
            return

        temp = pygame.Surface(
            (int(size * 2) + 2, int(size * 2) + 2),
            pygame.SRCALPHA
        )

        color = (
            self.color[0],
            self.color[1],
            self.color[2],
            alpha
        )

        pygame.draw.circle(
            temp,
            color,
            (int(size) + 1, int(size) + 1),
            max(1, int(size))
        )

        surface.blit(
            temp,
            (int(self.x - size), int(self.y - size))
        )


class Ring:
    """Fading ring effect when a collision occurs."""

    __slots__ = (
        "x", "y", "life", "max_life",
        "color", "max_radius"
    )

    def __init__(
        self,
        x,
        y,
        color,
        max_radius=26,
        life=0.35
    ):

        self.x = x
        self.y = y
        self.life = life
        self.max_life = life
        self.color = color
        self.max_radius = max_radius

    def update(self, dt):

        self.life -= dt
        return self.life > 0

    def draw(self, surface):

        t = clamp(
            self.life / self.max_life,
            0.0,
            1.0
        )

        radius = int(
            self.max_radius * (1 - t) + 4
        )

        alpha = int(200 * t)

        if radius <= 0:
            return

        temp = pygame.Surface(
            (radius * 2 + 4, radius * 2 + 4),
            pygame.SRCALPHA
        )

        color = (
            self.color[0],
            self.color[1],
            self.color[2],
            alpha
        )

        pygame.draw.circle(
            temp,
            color,
            (radius + 2, radius + 2),
            radius,
            width=3
        )

        surface.blit(
            temp,
            (
                int(self.x - radius - 2),
                int(self.y - radius - 2)
            )
        )


class ParticleSystem:

    def __init__(self):

        self.particles = []
        self.rings = []

    def spawn_confetti(self, x, y, count=45):

        colors = [
            (255, 90, 90),
            (255, 210, 70),
            (90, 220, 130),
            (90, 170, 255),
            (230, 120, 255),
            (255, 255, 255)
        ]

        for _ in range(count):

            angle = random.uniform(0, math.tau)
            speed = random.uniform(60, 260)

            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 80

            self.particles.append(
                Particle(
                    x,
                    y,
                    vx,
                    vy,
                    life=random.uniform(0.6, 1.3),
                    color=random.choice(colors),
                    size=random.uniform(3, 6),
                    gravity=420,
                    shrink=True
                )
            )

    def spawn_hit_spark(
        self,
        x,
        y,
        color,
        count=10
    ):

        for _ in range(count):

            angle = random.uniform(0, math.tau)
            speed = random.uniform(40, 140)

            self.particles.append(
                Particle(
                    x,
                    y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    life=random.uniform(0.15, 0.35),
                    color=color,
                    size=random.uniform(2, 4),
                    gravity=0,
                    shrink=True
                )
            )

        self.rings.append(
            Ring(x, y, color)
        )

    def update(self, dt):

        self.particles = [
            p for p in self.particles
            if p.update(dt)
        ]

        self.rings = [
            r for r in self.rings
            if r.update(dt)
        ]

    def draw(self, surface):

        for p in self.particles:
            p.draw(surface)

        for r in self.rings:
            r.draw(surface)


# =========================================================
# Screen Shake
# =========================================================

class ScreenShake:

    def __init__(self):

        self.trauma = 0.0

    def add(self, amount):

        self.trauma = clamp(
            self.trauma + amount,
            0.0,
            1.0
        )

    def update(self, dt):

        if self.trauma > 0:

            self.trauma = clamp(
                self.trauma - dt * 1.8,
                0.0,
                1.0
            )

    def offset(self):

        if self.trauma <= 0:
            return 0, 0

        power = self.trauma ** 2

        dx = random.uniform(-1, 1) * 14 * power
        dy = random.uniform(-1, 1) * 14 * power

        return dx, dy


# =========================================================
# Defender Class
# =========================================================

class Defender:

    def __init__(self, x, y, speed, direction=1):

        self.x = float(x)
        self.y = float(y)
        self.speed = speed
        self.direction = direction

    def update(self, dt):

        self.x += (
            self.speed
            * self.direction
            * dt
            * 60
        )

        if self.x <= LEFT_WALL:

            self.x = LEFT_WALL
            self.direction = 1

        elif self.x + DEFENDER_WIDTH >= RIGHT_WALL:

            self.x = RIGHT_WALL - DEFENDER_WIDTH
            self.direction = -1

    def rect(self):

        return pygame.Rect(
            int(self.x),
            int(self.y),
            int(DEFENDER_WIDTH),
            int(DEFENDER_HEIGHT)
        )

    def draw(self, surface):

        rect = self.rect()

        vertical_gradient_rect(
            surface,
            rect,
            DEFENDER_COLOR_TOP,
            DEFENDER_COLOR_BOTTOM,
            border_radius=4
        )

        pygame.draw.rect(
            surface,
            DEFENDER_OUTLINE,
            rect,
            2,
            border_radius=4
        )


def resolve_defender_collisions(defenders):

    rows = {}

    for defender in defenders:

        row_key = round(defender.y)
        rows.setdefault(row_key, []).append(defender)

    for row_defenders in rows.values():

        for _ in range(2):

            for i in range(len(row_defenders)):

                for j in range(i + 1, len(row_defenders)):

                    a = row_defenders[i]
                    b = row_defenders[j]

                    a_left = a.x
                    a_right = a.x + DEFENDER_WIDTH

                    b_left = b.x
                    b_right = b.x + DEFENDER_WIDTH

                    overlap = (
                        min(a_right, b_right)
                        - max(a_left, b_left)
                    )

                    if overlap > 0:

                        separation = (
                            overlap / 2 + 0.5
                        )

                        if a.x < b.x:

                            a.x -= separation
                            b.x += separation

                        else:

                            a.x += separation
                            b.x -= separation

                        a.direction *= -1
                        b.direction *= -1

                        a.x = clamp(
                            a.x,
                            LEFT_WALL,
                            RIGHT_WALL - DEFENDER_WIDTH
                        )

                        b.x = clamp(
                            b.x,
                            LEFT_WALL,
                            RIGHT_WALL - DEFENDER_WIDTH
                        )


def create_defender(number):

    if number <= 3:

        index = number - 1
        y = DEFENDER_ROW_1_Y

    else:

        index = number - 4
        y = DEFENDER_ROW_2_Y

    positions = [
        LEFT_WALL + 70,
        WIDTH / 2 - DEFENDER_WIDTH / 2,
        RIGHT_WALL - 70 - DEFENDER_WIDTH
    ]

    x = positions[index]

    speed = (
        DEFENDER_BASE_SPEED
        + index * 0.35
        + (0.20 if number > 3 else 0.0)
    )

    direction = 1 if number % 2 == 1 else -1

    return Defender(
        x,
        y,
        speed,
        direction
    )


# =========================================================
# Power-Up
# =========================================================

class PowerUp:

    def __init__(self, kind):

        self.kind = kind

        self.x = random.uniform(
            LEFT_WALL + 40,
            RIGHT_WALL - 40
        )

        self.y = TOP_WALL + GOAL_DEPTH + 10

        self.collected = False
        self.pulse = 0.0

    def update(self, dt):

        self.y += POWERUP_FALL_SPEED * dt * 60
        self.pulse += dt * 6

    def rect(self):

        return pygame.Rect(
            int(self.x - POWERUP_SIZE / 2),
            int(self.y - POWERUP_SIZE / 2),
            POWERUP_SIZE,
            POWERUP_SIZE
        )

    def off_screen(self):

        return (
            self.y - POWERUP_SIZE
            > BOTTOM_WALL
        )

    def draw(self, surface):

        color = POWERUP_COLORS.get(
            self.kind,
            (255, 255, 255)
        )

        wobble = math.sin(self.pulse) * 3

        cx = int(self.x)
        cy = int(self.y + wobble)

        r = POWERUP_SIZE // 2

        glow = pygame.Surface(
            (r * 4, r * 4),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow,
            (*color, 70),
            (r * 2, r * 2),
            r * 2
        )

        surface.blit(
            glow,
            (cx - r * 2, cy - r * 2)
        )

        pygame.draw.circle(
            surface,
            color,
            (cx, cy),
            r
        )

        pygame.draw.circle(
            surface,
            (255, 255, 255),
            (cx, cy),
            r,
            2
        )

        label = (
            "B"
            if self.kind == "big_paddle"
            else "S"
        )

        text = small_font.render(
            label,
            True,
            (30, 30, 30)
        )

        surface.blit(
            text,
            (
                cx - text.get_width() // 2,
                cy - text.get_height() // 2
            )
        )


# =========================================================
# Paddle Class
# =========================================================

class Paddle:

    def __init__(self):

        self.x = (
            WIDTH - PADDLE_WIDTH
        ) / 2

        self.y = PADDLE_BASE_Y
        self.vx = 0.0

        self.big_timer = 0.0

    @property
    def width(self):

        if self.big_timer > 0:
            return PADDLE_WIDTH * BIG_PADDLE_MULTIPLIER

        return PADDLE_WIDTH

    def update_y(self, defender_rows):

        self.y = (
            PADDLE_BASE_Y
            + defender_rows * PADDLE_ROW_OFFSET
        )

        self.y = min(
            self.y,
            HEIGHT - 120
        )

    def current_speed(self, ball_speed):

        return clamp(
            ball_speed * PADDLE_SPEED_MULTIPLIER,
            PADDLE_MIN_SPEED,
            PADDLE_MAX_SPEED
        )

    def apply_powerup(self, kind):

        if kind == "big_paddle":

            self.big_timer = (
                POWERUP_DURATION_MS / 1000.0
            )

    def update(self, keys, ball_speed, dt):

        if self.big_timer > 0:

            self.big_timer = max(
                0.0,
                self.big_timer - dt
            )

        max_speed = (
            self.current_speed(ball_speed)
            * 60
        )

        direction = 0

        if (
            keys[pygame.K_LEFT]
            or keys[pygame.K_a]
        ):
            direction -= 1

        if (
            keys[pygame.K_RIGHT]
            or keys[pygame.K_d]
        ):
            direction += 1

        if direction != 0:

            self.vx += (
                direction
                * PADDLE_ACCEL
                * dt
            )

            self.vx = clamp(
                self.vx,
                -max_speed,
                max_speed
            )

        else:

            if self.vx > 0:

                self.vx = max(
                    0.0,
                    self.vx - PADDLE_FRICTION * dt
                )

            elif self.vx < 0:

                self.vx = min(
                    0.0,
                    self.vx + PADDLE_FRICTION * dt
                )

        self.vx = clamp(
            self.vx,
            -max_speed,
            max_speed
        )

        self.x += self.vx * dt

        width = self.width

        self.x = clamp(
            self.x,
            LEFT_WALL,
            RIGHT_WALL - width
        )

    def rect(self):

        return pygame.Rect(
            int(self.x),
            int(self.y),
            int(self.width),
            PADDLE_HEIGHT
        )

    def draw(self, surface):

        rect = self.rect()

        if self.big_timer > 0:

            top_c = PADDLE_BIG_COLOR_TOP
            bottom_c = PADDLE_BIG_COLOR_BOTTOM

        else:

            top_c = PADDLE_COLOR_TOP
            bottom_c = PADDLE_COLOR_BOTTOM

        vertical_gradient_rect(
            surface,
            rect,
            top_c,
            bottom_c,
            border_radius=5
        )

        pygame.draw.rect(
            surface,
            PADDLE_OUTLINE,
            rect,
            2,
            border_radius=5
        )

        if self.big_timer > 0:

            ratio = clamp(
                self.big_timer
                / (POWERUP_DURATION_MS / 1000.0),
                0,
                1
            )

            bar_w = int(
                rect.width * ratio
            )

            pygame.draw.rect(
                surface,
                (255, 255, 255),
                (
                    rect.x,
                    rect.y - 6,
                    bar_w,
                    3
                )
            )


# =========================================================
# Ball Class
# =========================================================

class Ball:

    def __init__(self):

        self.visual_rotation = 0.0
        self.trail = []
        self.slow_timer = 0.0

        self.reset(START_SPEED)

    def reset(self, speed):

        self.x = WIDTH / 2
        self.y = HEIGHT - 100

        self.speed_value = clamp(
            speed,
            MIN_SPEED,
            MAX_SPEED
        )

        angle_deg = random.choice([
            random.uniform(55, 75),
            random.uniform(105, 125)
        ])

        angle = math.radians(angle_deg)

        self.vx = (
            math.cos(angle)
            * self.speed_value
        )

        self.vy = -abs(
            math.sin(angle)
            * self.speed_value
        )

        self.moving = True
        self.scored = False
        self.missed = False

        self.goal_armed = False

        self.last_paddle_hit_frame = -100
        self.last_defender_hit_frame = -100

        self.visual_rotation = random.uniform(
            0,
            math.tau
        )

        self.trail.clear()

        # Decorative vertical bounce phase
        self.bounce_phase = 0.0

    def current_speed(self):

        return math.hypot(
            self.vx,
            self.vy
        )

    def effective_speed_multiplier(self):

        return (
            0.55
            if self.slow_timer > 0
            else 1.0
        )

    def apply_powerup(self, kind):

        if kind == "slow_ball":

            self.slow_timer = (
                POWERUP_DURATION_MS / 1000.0
            )

    def set_speed(self, new_speed):

        new_speed = clamp(
            new_speed,
            MIN_SPEED,
            MAX_SPEED
        )

        current = self.current_speed()

        if current <= 0:
            return

        ratio = new_speed / current

        self.vx *= ratio
        self.vy *= ratio

        self.speed_value = new_speed

    def hit_paddle(
        self,
        paddle,
        particles,
        shake
    ):

        paddle_center = (
            paddle.x + paddle.width / 2
        )

        relative = (
            (self.x - paddle_center)
            / (paddle.width / 2)
        )

        relative = clamp(
            relative,
            -1.0,
            1.0
        )

        max_angle = math.radians(65)
        angle = relative * max_angle

        speed = self.current_speed()

        self.vx = math.sin(angle) * speed
        self.vy = -abs(
            math.cos(angle) * speed
        )

        self.goal_armed = True

        self.y = (
            paddle.y
            - BALL_RADIUS
            - 1
        )

        particles.spawn_hit_spark(
            self.x,
            self.y,
            (140, 210, 255),
            count=8
        )

        shake.add(0.12)

        SFX.play(SFX.paddle_hit)

    def hit_defender(
        self,
        defender,
        particles,
        shake
    ):

        if self.vy >= 0:
            return

        rect = defender.rect()

        center_x = (
            defender.x
            + DEFENDER_WIDTH / 2
        )

        dx = self.x - center_x

        self.y = (
            rect.bottom
            + BALL_RADIUS
            + 1
        )

        self.vy = abs(self.vy)

        relative = clamp(
            dx / (DEFENDER_WIDTH / 2),
            -1.0,
            1.0
        )

        speed = self.current_speed()

        self.vx += (
            relative
            * speed
            * 0.35
        )

        final_speed = math.hypot(
            self.vx,
            self.vy
        )

        if final_speed > 0:

            ratio = speed / final_speed

            self.vx *= ratio
            self.vy *= ratio

        particles.spawn_hit_spark(
            self.x,
            self.y,
            (255, 140, 140),
            count=8
        )

        shake.add(0.08)

        SFX.play(SFX.defender_hit)

    def check_defenders(
        self,
        defenders,
        frame_count,
        particles,
        shake
    ):

        if self.vy >= 0:
            return

        if (
            frame_count
            - self.last_defender_hit_frame
            <= 6
        ):
            return

        ball_rect = pygame.Rect(
            int(self.x - BALL_RADIUS),
            int(self.y - BALL_RADIUS),
            BALL_RADIUS * 2,
            BALL_RADIUS * 2
        )

        for defender in defenders:

            if ball_rect.colliderect(
                defender.rect()
            ):

                self.last_defender_hit_frame = (
                    frame_count
                )

                self.hit_defender(
                    defender,
                    particles,
                    shake
                )

                break

    def update(
        self,
        paddle,
        defenders,
        frame_count,
        dt,
        particles,
        shake
    ):

        if self.slow_timer > 0:

            self.slow_timer = max(
                0.0,
                self.slow_timer - dt
            )

        if not self.moving:
            return None

        mult = (
            self.effective_speed_multiplier()
        )

        step = dt * 60 * mult

        self.x += self.vx * step
        self.y += self.vy * step

        self.trail.append(
            (self.x, self.y)
        )

        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

        self.visual_rotation += (
            self.current_speed()
            * 0.035
            * step
        )

        self.bounce_phase += dt * 10

        if (
            self.y - BALL_RADIUS
            > paddle.y + PADDLE_HEIGHT
        ):

            self.goal_armed = False

        # Left wall
        if (
            self.x - BALL_RADIUS
            <= LEFT_WALL
        ):

            self.x = (
                LEFT_WALL
                + BALL_RADIUS
            )

            self.vx = abs(self.vx)

            SFX.play(SFX.wall_hit)

        # Right wall
        elif (
            self.x + BALL_RADIUS
            >= RIGHT_WALL
        ):

            self.x = (
                RIGHT_WALL
                - BALL_RADIUS
            )

            self.vx = -abs(self.vx)

            SFX.play(SFX.wall_hit)

        # Bottom = player miss
        if (
            self.y + BALL_RADIUS
            >= BOTTOM_WALL
        ):

            self.y = (
                BOTTOM_WALL
                - BALL_RADIUS
            )

            self.vy = -abs(self.vy)

            self.goal_armed = False

            self.missed = True

            SFX.play(SFX.miss)

        # Paddle
        if self.vy > 0:

            paddle_rect = paddle.rect()

            ball_rect = pygame.Rect(
                int(self.x - BALL_RADIUS),
                int(self.y - BALL_RADIUS),
                BALL_RADIUS * 2,
                BALL_RADIUS * 2
            )

            if ball_rect.colliderect(
                paddle_rect
            ):

                if (
                    frame_count
                    - self.last_paddle_hit_frame
                    > 6
                ):

                    self.last_paddle_hit_frame = (
                        frame_count
                    )

                    self.hit_paddle(
                        paddle,
                        particles,
                        shake
                    )

        self.check_defenders(
            defenders,
            frame_count,
            particles,
            shake
        )

        # Top wall / goal
        if (
            self.y - BALL_RADIUS
            <= TOP_WALL
        ):

            goal_min = (
                GOAL_LEFT
                + BALL_RADIUS
            )

            goal_max = (
                GOAL_RIGHT
                - BALL_RADIUS
            )

            inside_goal = (
                goal_min
                <= self.x
                <= goal_max
            )

            if (
                inside_goal
                and self.goal_armed
            ):

                self.scored = True
                self.moving = False

                self.vx = 0
                self.vy = 0

                return "goal"

            else:

                self.y = (
                    TOP_WALL
                    + BALL_RADIUS
                )

                self.vy = abs(self.vy)

        return None

    def draw(self, surface):

        # Movement trail
        for i, (tx, ty) in enumerate(
            self.trail
        ):

            t = (
                (i + 1)
                / max(1, len(self.trail))
            )

            alpha = int(90 * t)

            radius = int(
                BALL_RADIUS
                * 0.55
                * t
            )

            if radius < 1:
                continue

            temp = pygame.Surface(
                (radius * 2 + 2,
                 radius * 2 + 2),
                pygame.SRCALPHA
            )

            pygame.draw.circle(
                temp,
                (*BALL_TRAIL_COLOR, alpha),
                (radius + 1, radius + 1),
                radius
            )

            surface.blit(
                temp,
                (
                    int(tx - radius),
                    int(ty - radius)
                )
            )

        cx = int(self.x)
        cy = int(self.y)
        r = BALL_RADIUS

        # Dynamic shadow
        shadow_scale = (
            0.85
            + 0.15
            * abs(math.sin(self.bounce_phase))
        )

        shadow_surf = pygame.Surface(
            (
                r * 2 + 6,
                int(r * 1.1) + 6
            ),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            shadow_surf,
            (0, 0, 0, 90),
            (
                0,
                0,
                int(r * 2 * shadow_scale),
                int(r * 0.9)
            )
        )

        surface.blit(
            shadow_surf,
            (cx - r, cy + r - 6)
        )

        draw_soccer_ball(
            surface,
            cx,
            cy,
            r,
            self.visual_rotation
        )


# =========================================================
# Field Drawing
# =========================================================

def draw_stands(surface):

    stand_h = WALL_THICKNESS

    for band, (y0, y1) in enumerate([
        (0, 0),
        (0, 0)
    ]):
        pass

    # Top and bottom stands with spectator dots
    for y in (
        0,
        HEIGHT - stand_h
    ):

        pygame.draw.rect(
            surface,
            STAND_COLOR_A,
            (0, y, WIDTH, stand_h)
        )

        for x in range(0, WIDTH, 14):

            color = (
                STAND_DOT
                if (x // 14) % 2 == 0
                else STAND_COLOR_B
            )

            pygame.draw.circle(
                surface,
                color,
                (x + 4, y + stand_h // 2),
                2
            )


def draw_field(surface, frame_count):

    surface.fill(BG_COLOR)

    field_x = WALL_THICKNESS
    field_y = WALL_THICKNESS

    field_w = (
        WIDTH
        - 2 * WALL_THICKNESS
    )

    field_h = (
        HEIGHT
        - 2 * WALL_THICKNESS
    )

    pygame.draw.rect(
        surface,
        FIELD_COLOR_A,
        (
            field_x,
            field_y,
            field_w,
            field_h
        )
    )

    # Grass stripes
    stripe_h = 40

    y = field_y
    index = 0

    while y < field_y + field_h:

        h = min(
            stripe_h,
            field_y + field_h - y
        )

        color = (
            FIELD_COLOR_A
            if index % 2 == 0
            else FIELD_COLOR_B
        )

        pygame.draw.rect(
            surface,
            color,
            (
                field_x,
                y,
                field_w,
                h
            )
        )

        y += stripe_h
        index += 1

    # Center line and center circle
    mid_y = (
        field_y
        + field_h // 2
    )

    pygame.draw.line(
        surface,
        (255, 255, 255, 40),
        (
            field_x,
            mid_y
        ),
        (
            field_x + field_w,
            mid_y
        ),
        2
    )

    pygame.draw.circle(
        surface,
        (255, 255, 255),
        (WIDTH // 2, mid_y),
        55,
        2
    )

    pygame.draw.circle(
        surface,
        (255, 255, 255),
        (WIDTH // 2, mid_y),
        3
    )

    # Penalty box
    box_w = 320
    box_h = 90

    pygame.draw.rect(
        surface,
        (255, 255, 255),
        (
            WIDTH // 2 - box_w // 2,
            field_y,
            box_w,
            box_h
        ),
        2
    )

    # Walls
    pygame.draw.rect(
        surface,
        WALL_COLOR,
        (0, 0, WIDTH, WALL_THICKNESS)
    )

    pygame.draw.rect(
        surface,
        WALL_COLOR,
        (
            0,
            HEIGHT - WALL_THICKNESS,
            WIDTH,
            WALL_THICKNESS
        )
    )

    pygame.draw.rect(
        surface,
        WALL_COLOR,
        (0, 0, WALL_THICKNESS, HEIGHT)
    )

    pygame.draw.rect(
        surface,
        WALL_COLOR,
        (
            WIDTH - WALL_THICKNESS,
            0,
            WALL_THICKNESS,
            HEIGHT
        )
    )

    draw_stands(surface)

    draw_goal(surface)


def draw_net_mesh(
    surface,
    polygons,
    fill_color,
    line_color,
    spacing=13
):
    """Draw a goal net inside the given polygons."""

    xs = [
        p[0]
        for poly in polygons
        for p in poly
    ]

    ys = [
        p[1]
        for poly in polygons
        for p in poly
    ]

    min_x = int(min(xs)) - 2
    max_x = int(max(xs)) + 2

    min_y = int(min(ys)) - 2
    max_y = int(max(ys)) + 2

    w = max(1, max_x - min_x)
    h = max(1, max_y - min_y)

    temp = pygame.Surface(
        (w, h),
        pygame.SRCALPHA
    )

    local_polys = [
        [
            (px - min_x, py - min_y)
            for (px, py) in poly
        ]
        for poly in polygons
    ]

    # Dark net background for depth
    for poly in local_polys:

        pygame.draw.polygon(
            temp,
            fill_color,
            poly
        )

    # Diagonal diamond-shaped net lines
    diag = w + h

    for offset in range(
        -diag,
        diag,
        spacing
    ):

        pygame.draw.line(
            temp,
            line_color,
            (offset, 0),
            (offset + h, h),
            1
        )

        pygame.draw.line(
            temp,
            line_color,
            (offset, h),
            (offset + h, 0),
            1
        )

    # Mask: only show the net inside the polygons
    mask = pygame.Surface(
        (w, h),
        pygame.SRCALPHA
    )

    for poly in local_polys:

        pygame.draw.polygon(
            mask,
            (255, 255, 255, 255),
            poly
        )

    temp.blit(
        mask,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_MIN
    )

    surface.blit(
        temp,
        (min_x, min_y)
    )


def draw_cylinder_bar(
    surface,
    p1,
    p2,
    thickness,
    base_color
):
    """Draw a cylindrical bar with highlights and shadows."""

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    length = math.hypot(dx, dy)

    if length == 0:
        return

    nx = -dy / length
    ny = dx / length

    dark = (
        max(0, base_color[0] - 60),
        max(0, base_color[1] - 60),
        max(0, base_color[2] - 60)
    )

    light = (
        min(255, base_color[0] + 30),
        min(255, base_color[1] + 30),
        min(255, base_color[2] + 30)
    )

    pygame.draw.line(
        surface,
        dark,
        p1,
        p2,
        thickness + 2
    )

    pygame.draw.line(
        surface,
        base_color,
        p1,
        p2,
        thickness
    )

    hi_off = thickness * 0.22

    p1h = (
        p1[0] + nx * hi_off,
        p1[1] + ny * hi_off
    )

    p2h = (
        p2[0] + nx * hi_off,
        p2[1] + ny * hi_off
    )

    pygame.draw.line(
        surface,
        light,
        p1h,
        p2h,
        max(1, thickness // 3)
    )

    pygame.draw.circle(
        surface,
        base_color,
        (int(p1[0]), int(p1[1])),
        thickness // 2 + 1
    )

    pygame.draw.circle(
        surface,
        base_color,
        (int(p2[0]), int(p2[1])),
        thickness // 2 + 1
    )


def draw_goal(surface):
    """Draw a 3D goal with diamond-shaped net and cylindrical posts."""

    inset = 26
    back_y = 5

    front_left = GOAL_LEFT
    front_right = GOAL_RIGHT
    front_y = float(GOAL_DEPTH)

    back_left = GOAL_LEFT + inset
    back_right = GOAL_RIGHT - inset

    # Back net
    back_net_poly = [
        (front_left, front_y),
        (back_left, back_y),
        (back_right, back_y),
        (front_right, front_y)
    ]

    # Side nets
    left_wing_poly = [
        (front_left, front_y),
        (front_left, 0),
        (back_left, 0),
        (back_left, back_y)
    ]

    right_wing_poly = [
        (front_right, front_y),
        (front_right, 0),
        (back_right, 0),
        (back_right, back_y)
    ]

    net_fill = (
        *GOAL_NET,
        55
    )

    net_line = (
        210,
        235,
        215,
        90
    )

    draw_net_mesh(
        surface,
        [
            back_net_poly,
            left_wing_poly,
            right_wing_poly
        ],
        net_fill,
        net_line,
        spacing=12
    )

    # Goal posts
    draw_cylinder_bar(
        surface,
        (front_left, front_y),
        (front_left, 0),
        6,
        GOAL_FRAME
    )

    draw_cylinder_bar(
        surface,
        (front_right, front_y),
        (front_right, 0),
        6,
        GOAL_FRAME
    )

    draw_cylinder_bar(
        surface,
        (front_left, 0),
        (back_left, 0),
        4,
        GOAL_FRAME
    )

    draw_cylinder_bar(
        surface,
        (front_right, 0),
        (back_right, 0),
        4,
        GOAL_FRAME
    )

    # Front goal crossbar
    draw_cylinder_bar(
        surface,
        (front_left, front_y),
        (front_right, front_y),
        7,
        GOAL_FRAME
    )


# =========================================================
# User Interface
# =========================================================

def draw_bar(
    surface,
    x,
    y,
    w,
    h,
    ratio,
    color,
    bg=(60, 60, 70)
):

    pygame.draw.rect(
        surface,
        bg,
        (x, y, w, h),
        border_radius=h // 2
    )

    fill_w = int(
        w * clamp(ratio, 0, 1)
    )

    if fill_w > 0:

        pygame.draw.rect(
            surface,
            color,
            (x, y, fill_w, h),
            border_radius=h // 2
        )


def draw_ui(
    surface,
    score,
    ball,
    paddle,
    defenders,
    defender_rows,
    misses,
    combo,
    highscore
):

    score_text = font.render(
        f"Goals: {score}",
        True,
        TEXT_COLOR
    )

    surface.blit(
        score_text,
        (20, 18)
    )

    hs_text = small_font.render(
        f"Best: {highscore}",
        True,
        SUBTEXT_COLOR
    )

    surface.blit(
        hs_text,
        (20, 44)
    )

    speed_text = small_font.render(
        f"Ball Speed: {ball.current_speed():.1f}",
        True,
        TEXT_COLOR
    )

    surface.blit(
        speed_text,
        (20, 68)
    )

    paddle_speed_text = small_font.render(
        f"Paddle Speed: "
        f"{paddle.current_speed(ball.current_speed()):.1f}",
        True,
        TEXT_COLOR
    )

    surface.blit(
        paddle_speed_text,
        (20, 90)
    )

    defender_text = small_font.render(
        f"Defenders: {len(defenders)}",
        True,
        TEXT_COLOR
    )

    surface.blit(
        defender_text,
        (20, 112)
    )

    if defender_rows > 0:

        row_text = small_font.render(
            f"Defense Rows: {defender_rows}",
            True,
            TEXT_COLOR
        )

        surface.blit(
            row_text,
            (20, 134)
        )

    # Attack status
    if ball.goal_armed:

        status = font.render(
            "ATTACK!",
            True,
            ATTACK_TEXT
        )

    else:

        status = font.render(
            "WAIT FOR PADDLE",
            True,
            SUBTEXT_COLOR
        )

    surface.blit(
        status,
        (
            WIDTH - status.get_width() - 20,
            20
        )
    )

    # Combo
    if combo > 1:

        combo_text = font.render(
            f"Combo x{combo}",
            True,
            GOAL_TEXT
        )

        surface.blit(
            combo_text,
            (
                WIDTH
                - combo_text.get_width()
                - 20,
                50
            )
        )

    # Lives
    lives_left = (
        MAX_MISSES - misses
    )

    for i in range(MAX_MISSES):

        cx = (
            WIDTH
            - 20
            - (MAX_MISSES - i) * 22
        )

        cy = 86

        color = (
            (235, 90, 90)
            if i < lives_left
            else (70, 40, 40)
        )

        pygame.draw.circle(
            surface,
            color,
            (cx, cy),
            7
        )

        pygame.draw.circle(
            surface,
            (20, 20, 20),
            (cx, cy),
            7,
            1
        )

    # Active power-up bars
    bar_y = 108

    if paddle.big_timer > 0:

        ratio = (
            paddle.big_timer
            / (POWERUP_DURATION_MS / 1000.0)
        )

        draw_bar(
            surface,
            WIDTH - 140,
            bar_y,
            120,
            8,
            ratio,
            POWERUP_COLORS["big_paddle"]
        )

        surface.blit(
            small_font.render(
                "Big Paddle",
                True,
                SUBTEXT_COLOR
            ),
            (
                WIDTH - 140,
                bar_y - 16
            )
        )

        bar_y += 24

    if ball.slow_timer > 0:

        ratio = (
            ball.slow_timer
            / (POWERUP_DURATION_MS / 1000.0)
        )

        draw_bar(
            surface,
            WIDTH - 140,
            bar_y,
            120,
            8,
            ratio,
            POWERUP_COLORS["slow_ball"]
        )

        surface.blit(
            small_font.render(
                "Slow Ball",
                True,
                SUBTEXT_COLOR
            ),
            (
                WIDTH - 140,
                bar_y - 16
            )
        )

    controls = small_font.render(
        "A / D or LEFT / RIGHT : Paddle     "
        "UP / DOWN : Speed     "
        "P : Pause     R : Reset",
        True,
        SUBTEXT_COLOR
    )

    surface.blit(
        controls,
        (
            WIDTH // 2
            - controls.get_width() // 2,
            HEIGHT - 30
        )
    )


# =========================================================
# Menu / Game Over Screens
# =========================================================

def draw_overlay(surface, alpha=170):

    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (10, 12, 16, alpha)
    )

    surface.blit(
        overlay,
        (0, 0)
    )


def draw_menu(
    surface,
    highscore,
    pulse
):

    draw_overlay(
        surface,
        210
    )

    title = title_font.render(
        "FOOTBALL PADDLE",
        True,
        (255, 255, 255)
    )

    subtitle = font.render(
        "CHALLENGE",
        True,
        ATTACK_TEXT
    )

    surface.blit(
        title,
        (
            WIDTH // 2
            - title.get_width() // 2,
            190
        )
    )

    surface.blit(
        subtitle,
        (
            WIDTH // 2
            - subtitle.get_width() // 2,
            250
        )
    )

    glow = int(
        150
        + 100 * math.sin(pulse)
    )

    prompt = font.render(
        "Press ENTER to Start",
        True,
        (glow, 255, glow)
    )

    surface.blit(
        prompt,
        (
            WIDTH // 2
            - prompt.get_width() // 2,
            360
        )
    )

    lines = [
        "A / D or LEFT / RIGHT — move paddle",
        "UP / DOWN — adjust ball speed",
        "P — pause      R — restart",
        "Score goals, dodge defenders, grab power-ups!",
    ]

    for i, line in enumerate(lines):

        text = small_font.render(
            line,
            True,
            SUBTEXT_COLOR
        )

        surface.blit(
            text,
            (
                WIDTH // 2
                - text.get_width() // 2,
                420 + i * 26
            )
        )

    hs_text = font.render(
        f"Best Score: {highscore}",
        True,
        TEXT_COLOR
    )

    surface.blit(
        hs_text,
        (
            WIDTH // 2
            - hs_text.get_width() // 2,
            550
        )
    )


def draw_pause(surface):

    draw_overlay(
        surface,
        170
    )

    text = big_font.render(
        "PAUSED",
        True,
        (255, 255, 255)
    )

    surface.blit(
        text,
        (
            WIDTH // 2
            - text.get_width() // 2,
            HEIGHT // 2 - 60
        )
    )

    sub = font.render(
        "Press P to resume",
        True,
        SUBTEXT_COLOR
    )

    surface.blit(
        sub,
        (
            WIDTH // 2
            - sub.get_width() // 2,
            HEIGHT // 2 + 10
        )
    )


def draw_game_over(
    surface,
    score,
    highscore,
    is_new_record
):

    draw_overlay(
        surface,
        210
    )

    text = huge_font.render(
        "GAME OVER",
        True,
        MISS_TEXT
    )

    surface.blit(
        text,
        (
            WIDTH // 2
            - text.get_width() // 2,
            220
        )
    )

    score_text = font.render(
        f"Final Score: {score}",
        True,
        TEXT_COLOR
    )

    surface.blit(
        score_text,
        (
            WIDTH // 2
            - score_text.get_width() // 2,
            310
        )
    )

    if is_new_record:

        record_text = font.render(
            "NEW BEST SCORE!",
            True,
            GOAL_TEXT
        )

        surface.blit(
            record_text,
            (
                WIDTH // 2
                - record_text.get_width() // 2,
                345
            )
        )

    else:

        best_text = font.render(
            f"Best: {highscore}",
            True,
            SUBTEXT_COLOR
        )

        surface.blit(
            best_text,
            (
                WIDTH // 2
                - best_text.get_width() // 2,
                345
            )
        )

    prompt = font.render(
        "Press ENTER or R to play again",
        True,
        SUBTEXT_COLOR
    )

    surface.blit(
        prompt,
        (
            WIDTH // 2
            - prompt.get_width() // 2,
            420
        )
    )


# =========================================================
# Game States
# =========================================================

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"


class Game:

    def __init__(self):

        self.highscore = load_highscore()

        self.particles = ParticleSystem()
        self.shake = ScreenShake()

        self.state = STATE_MENU
        self.menu_pulse = 0.0

        self.new_record = False

        self.next_powerup_at = (
            pygame.time.get_ticks()
            + random.randint(
                POWERUP_SPAWN_MIN_MS,
                POWERUP_SPAWN_MAX_MS
            )
        )

        self.powerups = []

        self.slow_motion_timer = 0.0

        self.reset_game()

    def reset_game(self):

        self.ball = Ball()
        self.paddle = Paddle()
        self.defenders = []

        self.score = 0
        self.combo = 0
        self.misses = 0

        self.frame_count = 0

        self.message = ""
        self.message_timer = 0

        self.powerups.clear()
        self.new_record = False

    def spawn_powerup_if_needed(self):

        now = pygame.time.get_ticks()

        if (
            now >= self.next_powerup_at
            and len(self.powerups) == 0
        ):

            kind = random.choice(
                POWERUP_TYPES
            )

            self.powerups.append(
                PowerUp(kind)
            )

            self.next_powerup_at = (
                now
                + random.randint(
                    POWERUP_SPAWN_MIN_MS,
                    POWERUP_SPAWN_MAX_MS
                )
            )

    def update_powerups(self, dt):

        paddle_rect = self.paddle.rect()

        for p in self.powerups[:]:

            p.update(dt)

            if p.rect().colliderect(
                paddle_rect
            ):

                if p.kind == "big_paddle":

                    self.paddle.apply_powerup(
                        "big_paddle"
                    )

                elif p.kind == "slow_ball":

                    self.ball.apply_powerup(
                        "slow_ball"
                    )

                self.particles.spawn_hit_spark(
                    p.x,
                    p.y,
                    POWERUP_COLORS.get(
                        p.kind,
                        (255, 255, 255)
                    ),
                    count=14
                )

                SFX.play(
                    SFX.powerup
                )

                self.powerups.remove(p)

                continue

            if p.off_screen():

                self.powerups.remove(p)

    def handle_goal(
        self,
        speed_before_update
    ):

        self.score += 1
        self.combo += 1

        self.message = "GOAL!"
        self.message_timer = 80

        self.particles.spawn_confetti(
            self.ball.x,
            TOP_WALL + GOAL_DEPTH / 2
        )

        self.shake.add(0.55)

        self.slow_motion_timer = 0.22

        SFX.play(SFX.goal)
        SFX.play(SFX.goal_low)

        old_speed = max(
            self.ball.speed_value,
            speed_before_update
        )

        new_speed = min(
            old_speed * GOAL_SPEED_MULTIPLIER,
            MAX_SPEED
        )

        if 3 <= self.score <= 8:

            defender_number = (
                self.score - 2
            )

            self.defenders.append(
                create_defender(
                    defender_number
                )
            )

        self.ball.reset(
            new_speed
        )

        self.ball.goal_armed = False

    def handle_miss(self):

        self.combo = 0
        self.misses += 1

        self.message = "MISS!"
        self.message_timer = 45

        if self.misses >= MAX_MISSES:

            self.state = STATE_GAMEOVER

            if self.score > self.highscore:

                self.highscore = self.score
                self.new_record = True

                save_highscore(
                    self.highscore
                )

            SFX.play(
                SFX.gameover
            )

    def update_playing(
        self,
        dt,
        keys
    ):

        self.frame_count += 1

        defender_rows = 0

        if len(self.defenders) > 0:
            defender_rows = 1

        if len(self.defenders) > 3:
            defender_rows = 2

        self.paddle.update_y(
            defender_rows
        )

        self.paddle.update(
            keys,
            self.ball.current_speed(),
            dt
        )

        for defender in self.defenders:

            defender.update(dt)

        resolve_defender_collisions(
            self.defenders
        )

        speed_before_update = (
            self.ball.speed_value
        )

        was_missed_before = (
            self.ball.missed
        )

        self.ball.missed = False

        result = self.ball.update(
            self.paddle,
            self.defenders,
            self.frame_count,
            dt,
            self.particles,
            self.shake
        )

        if (
            self.ball.missed
            and not was_missed_before
        ):

            self.handle_miss()

        if result == "goal":

            self.handle_goal(
                speed_before_update
            )

        self.spawn_powerup_if_needed()

        self.update_powerups(dt)

        if self.message_timer > 0:

            self.message_timer -= 1

            if self.message_timer <= 0:

                self.message = ""

        return defender_rows

    def update(
        self,
        dt,
        keys
    ):

        self.particles.update(dt)
        self.shake.update(dt)

        if self.state == STATE_MENU:

            self.menu_pulse += dt * 3

            return 0

        if self.state == STATE_PAUSED:

            return 0

        if self.state == STATE_GAMEOVER:

            return 0

        # Short slow-motion effect after scoring
        if self.slow_motion_timer > 0:

            self.slow_motion_timer -= dt

            effective_dt = dt * 0.25

        else:

            effective_dt = dt

        return self.update_playing(
            effective_dt,
            keys
        )

    def draw(self, surface):

        offset_x, offset_y = (
            self.shake.offset()
        )

        game_surface = pygame.Surface(
            (WIDTH, HEIGHT)
        )

        draw_field(
            game_surface,
            self.frame_count
        )

        for defender in self.defenders:

            defender.draw(
                game_surface
            )

        for p in self.powerups:

            p.draw(
                game_surface
            )

        self.paddle.draw(
            game_surface
        )

        self.ball.draw(
            game_surface
        )

        self.particles.draw(
            game_surface
        )

        defender_rows = 0

        if len(self.defenders) > 0:
            defender_rows = 1

        if len(self.defenders) > 3:
            defender_rows = 2

        draw_ui(
            game_surface,
            self.score,
            self.ball,
            self.paddle,
            self.defenders,
            defender_rows,
            self.misses,
            self.combo,
            self.highscore
        )

        if self.message == "GOAL!":

            msg = big_font.render(
                "GOAL!",
                True,
                GOAL_TEXT
            )

            game_surface.blit(
                msg,
                (
                    WIDTH // 2
                    - msg.get_width() // 2,
                    HEIGHT // 2 - 45
                )
            )

        elif self.message == "MISS!":

            msg = big_font.render(
                "MISS!",
                True,
                MISS_TEXT
            )

            game_surface.blit(
                msg,
                (
                    WIDTH // 2
                    - msg.get_width() // 2,
                    HEIGHT // 2 - 45
                )
            )

        surface.fill(BG_COLOR)

        surface.blit(
            game_surface,
            (offset_x, offset_y)
        )

        if self.state == STATE_MENU:

            draw_menu(
                surface,
                self.highscore,
                self.menu_pulse
            )

        elif self.state == STATE_PAUSED:

            draw_pause(surface)

        elif self.state == STATE_GAMEOVER:

            draw_game_over(
                surface,
                self.score,
                self.highscore,
                self.new_record
            )

    def handle_keydown(self, key):

        if self.state == STATE_MENU:

            if key in (
                pygame.K_RETURN,
                pygame.K_SPACE
            ):

                self.reset_game()

                self.state = STATE_PLAYING

                SFX.play(
                    SFX.menu_select
                )

            return

        if self.state == STATE_GAMEOVER:

            if key in (
                pygame.K_RETURN,
                pygame.K_r
            ):

                self.reset_game()

                self.state = STATE_PLAYING

                SFX.play(
                    SFX.menu_select
                )

            return

        if key == pygame.K_r:

            self.reset_game()
            self.state = STATE_PLAYING

            return

        if key == pygame.K_p:

            if self.state == STATE_PLAYING:

                self.state = STATE_PAUSED

            elif self.state == STATE_PAUSED:

                self.state = STATE_PLAYING

            SFX.play(
                SFX.menu_select
            )

            return

        if self.state != STATE_PLAYING:

            return

        if key == pygame.K_UP:

            self.ball.set_speed(
                self.ball.current_speed()
                + SPEED_STEP
            )

        elif key == pygame.K_DOWN:

            self.ball.set_speed(
                self.ball.current_speed()
                - SPEED_STEP
            )


# =========================================================
# Main Game Loop
# =========================================================

def main():

    game = Game()

    running = True

    while running:

        dt = (
            clock.tick(FPS)
            / 1000.0
        )

        dt = min(
            dt,
            1 / 30
        )

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    running = False

                else:

                    game.handle_keydown(
                        event.key
                    )

        keys = pygame.key.get_pressed()

        game.update(
            dt,
            keys
        )

        game.draw(
            screen
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()