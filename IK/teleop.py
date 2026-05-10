import pygame
import math
import serial
import time

from IK import RPR

pygame.init()

# arduino = serial.Serial("COM5", 115200)
time.sleep(2)

WIDTH = 1200
HEIGHT = 750

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RPR Robot Simulator")

clock = pygame.time.Clock()

BG = (245, 247, 250)

BLACK = (25, 25, 25)
DARK = (40, 40, 40)

BLUE = (52, 120, 246)
BLUE_DARK = (30, 85, 190)

RED = (240, 90, 90)

GREEN = (60, 200, 120)

GRAY = (180, 185, 195)
LIGHT = (255, 255, 255)

SHADOW = (210, 214, 220)

SCALE = 14

L1 = 20
L2 = 10

rail_min = 0
rail_max = 30

rpr = RPR(L1, L2, rail_min, rail_max)

RAIL_X = 170
RAIL_Y = 620

WORKSPACE_X = RAIL_X + (12 * SCALE)
WORKSPACE_Y = RAIL_Y - (30 * SCALE)

WORKSPACE_WIDTH = (30 - 12) * SCALE
WORKSPACE_HEIGHT = 30 * SCALE

pygame.font.init()

title_font = pygame.font.SysFont("Segoe UI", 28, bold=True)
sub_font = pygame.font.SysFont("Segoe UI", 18)
value_font = pygame.font.SysFont("Consolas", 22)
small_font = pygame.font.SysFont("Segoe UI", 15)

trail = []

last_send = 0

smooth_x = 20
smooth_y = 10

MAX_SPEED = 0.05

smooth_shoulder = 90
smooth_elbow = 90
smooth_wrist = 90

ANGLE_SMOOTHING = 0.10

running = True

while running:

    clock.tick(60)

    screen.fill(BG)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    mx, my = pygame.mouse.get_pos()

    if mx < WORKSPACE_X:
        mx = WORKSPACE_X

    if mx > WORKSPACE_X + WORKSPACE_WIDTH:
        mx = WORKSPACE_X + WORKSPACE_WIDTH

    if my < WORKSPACE_Y:
        my = WORKSPACE_Y

    if my > RAIL_Y:
        my = RAIL_Y

    target_x = (mx - RAIL_X) / SCALE
    target_y = (RAIL_Y - my) / SCALE

    dx = target_x - smooth_x
    dy = target_y - smooth_y

    distance = math.sqrt(dx * dx + dy * dy)

    if distance > MAX_SPEED:

        dx = (dx / distance) * MAX_SPEED
        dy = (dy / distance) * MAX_SPEED

    smooth_x += dx
    smooth_y += dy

    x_cm = smooth_x
    y_cm = smooth_y

    if x_cm < 12:
        x_cm = 12

    if x_cm > 30:
        x_cm = 30

    if y_cm < rail_min:
        y_cm = rail_min

    if y_cm > rail_max:
        y_cm = rail_max

    rail, elbow, shoulder = rpr.inv_kinematic(x_cm, y_cm)

    wrist = 270 - elbow - shoulder

    smooth_shoulder += (shoulder - smooth_shoulder) * ANGLE_SMOOTHING
    smooth_elbow += (elbow - smooth_elbow) * ANGLE_SMOOTHING
    smooth_wrist += (wrist - smooth_wrist) * ANGLE_SMOOTHING

    shoulder_rad = math.radians(smooth_shoulder)

    elbow_internal = smooth_elbow - 180
    elbow_rad = math.radians(elbow_internal)

    rail_px = RAIL_Y - rail * SCALE

    shoulder_x = RAIL_X
    shoulder_y = rail_px

    elbow_x = shoulder_x + (L1 * SCALE) * math.cos(shoulder_rad)
    elbow_y = shoulder_y - (L1 * SCALE) * math.sin(shoulder_rad)

    wrist_x = elbow_x + (L2 * SCALE) * math.cos(shoulder_rad + elbow_rad)
    wrist_y = elbow_y - (L2 * SCALE) * math.sin(shoulder_rad + elbow_rad)

    trail.append((int(wrist_x), int(wrist_y)))

    if len(trail) > 150:
        trail.pop(0)

    current_time = time.time()

    if current_time - last_send > 0.03:

        data = (
            f"R{rail:.1f},"
            f"S{int(smooth_shoulder)},"
            f"E{int(smooth_elbow)},"
            f"W{int(smooth_wrist)}\n"
        )

        # arduino.write(data.encode())

        last_send = current_time

    for i in range(1, len(trail)):

        pygame.draw.line(
            screen,
            (180, 210, 255),
            trail[i - 1],
            trail[i],
            2
        )

    workspace_rect = pygame.Rect(
        WORKSPACE_X,
        WORKSPACE_Y,
        WORKSPACE_WIDTH,
        WORKSPACE_HEIGHT
    )

    pygame.draw.rect(
        screen,
        (225, 232, 245),
        workspace_rect,
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        BLUE,
        workspace_rect,
        3,
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        SHADOW,
        (
            RAIL_X - 35,
            RAIL_Y - rail_max * SCALE - 10,
            70,
            rail_max * SCALE + 50
        ),
        border_radius=14
    )

    pygame.draw.rect(
        screen,
        DARK,
        (
            RAIL_X - 28,
            RAIL_Y - rail_max * SCALE,
            56,
            rail_max * SCALE + 35
        ),
        border_radius=12
    )

    pygame.draw.line(
        screen,
        LIGHT,
        (RAIL_X, RAIL_Y),
        (RAIL_X, RAIL_Y - rail_max * SCALE),
        8
    )

    pygame.draw.rect(
        screen,
        BLUE,
        (
            shoulder_x - 30,
            shoulder_y - 30,
            60,
            60
        ),
        border_radius=10
    )

    pygame.draw.circle(
        screen,
        BLUE_DARK,
        (int(shoulder_x), int(shoulder_y)),
        12
    )

    pygame.draw.line(
        screen,
        BLACK,
        (shoulder_x, shoulder_y),
        (elbow_x, elbow_y),
        14
    )

    pygame.draw.line(
        screen,
        BLUE_DARK,
        (shoulder_x, shoulder_y),
        (elbow_x, elbow_y),
        6
    )

    pygame.draw.line(
        screen,
        BLACK,
        (elbow_x, elbow_y),
        (wrist_x, wrist_y),
        12
    )

    pygame.draw.line(
        screen,
        BLUE,
        (elbow_x, elbow_y),
        (wrist_x, wrist_y),
        5
    )

    pygame.draw.circle(
        screen,
        BLUE_DARK,
        (int(elbow_x), int(elbow_y)),
        15
    )

    pygame.draw.circle(
        screen,
        LIGHT,
        (int(elbow_x), int(elbow_y)),
        5
    )

    pygame.draw.circle(
        screen,
        RED,
        (int(wrist_x), int(wrist_y)),
        10
    )

    pygame.draw.line(
        screen,
        RED,
        (wrist_x, wrist_y),
        (wrist_x, wrist_y + 30),
        3
    )

    pygame.draw.circle(
        screen,
        GREEN,
        (mx, my),
        6
    )

    pygame.draw.circle(
        screen,
        (255, 255, 255),
        (mx, my),
        14,
        2
    )

    panel_x = 760
    panel_y = 55

    pygame.draw.rect(
        screen,
        SHADOW,
        (
            panel_x - 8,
            panel_y - 8,
            320,
            360
        ),
        border_radius=16
    )

    pygame.draw.rect(
        screen,
        LIGHT,
        (
            panel_x - 15,
            panel_y - 15,
            320,
            360
        ),
        border_radius=16
    )

    pygame.draw.rect(
        screen,
        GRAY,
        (
            panel_x - 15,
            panel_y - 15,
            320,
            360
        ),
        2,
        border_radius=16
    )

    title = title_font.render("RPR Robot", True, BLACK)

    screen.blit(title, (panel_x + 15, panel_y))

    subtitle = sub_font.render(
        "Live Hardware Control",
        True,
        (110, 110, 110)
    )

    screen.blit(subtitle, (panel_x + 15, panel_y + 40))

    values = [
        ("X Position", f"{round(x_cm,1)} cm"),
        ("Rail Height", f"{round(rail,1)} cm"),
        ("Shoulder", f"{int(smooth_shoulder)} deg"),
        ("Elbow", f"{int(smooth_elbow)} deg"),
        ("Wrist", f"{int(smooth_wrist)} deg"),
        # ("Serial", "CONNECTED")
    ]

    text_y = panel_y + 95

    for label, value in values:

        pygame.draw.rect(
            screen,
            (248, 250, 252),
            (
                panel_x + 10,
                text_y - 8,
                260,
                36
            ),
            border_radius=8
        )

        label_surface = small_font.render(
            label,
            True,
            (90, 90, 90)
        )

        value_surface = value_font.render(
            value,
            True,
            BLUE_DARK
        )

        screen.blit(label_surface, (panel_x + 18, text_y - 1))
        screen.blit(value_surface, (panel_x + 140, text_y - 6))

        text_y += 46

    footer = small_font.render(
        "Mouse controls real robot",
        True,
        (120, 120, 120)
    )

    screen.blit(footer, (30, HEIGHT - 30))

    pygame.display.update()

# arduino.close()

pygame.quit()
