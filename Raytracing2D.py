"""
RAYTRACING 2D - VERSIONE EDUCATIVA
===================================
Progetto pensato per imparare, passo dopo passo, i concetti base del ray tracing:

  1. Casting dei raggi (già presente nel progetto originale)
  2. Intersezione raggio-cerchio (equazione quadratica)      -> funzione intersect_ray_circle()
  3. Intersezione raggio-segmento (i "muri")                 -> funzione intersect_ray_segment()
  4. Calcolo della normale in un punto di impatto            -> funzioni normal_at_*()
  5. Riflessione di un raggio (legge della riflessione)      -> funzione reflect()
  6. Attenuazione della luce con la distanza (falloff)       -> nel loop principale
  7. HUD con controlli interattivi per "toccare con mano" ogni concetto

Ogni feature si accende/spegne con un tasto, così puoi isolare un concetto alla volta
e vedere l'effetto sullo schermo in tempo reale. Guarda i commenti dentro alle funzioni:
spiegano la matematica passo passo.

CONTROLLI
---------
  Frecce           : muovi il cerchio principale (giocatore)
  Click sinistro    : aggiungi un cerchio ostacolo nel punto cliccato
  SHIFT + trascina   : disegna un muro (segmento) da un punto A a un punto B
  Click destro      : rimuovi l'oggetto più vicino al cursore
  L                 : attiva/disattiva "la luce segue il mouse"
  R                 : attiva/disattiva le RIFLESSIONI
  N                 : mostra/nascondi le NORMALI nei punti di impatto
  F                 : attiva/disattiva l'ATTENUAZIONE della luce con la distanza
  + / -             : aumenta/diminuisci il numero di raggi (densità)
  C                 : pulisci la scena (rimuove cerchi e muri aggiunti)
  H                 : mostra/nascondi il pannello di aiuto
  ESC               : esci
"""

import math
import pygame

pygame.init()

# ------------------------------------------------------------------
# WINDOW SETTINGS
# ------------------------------------------------------------------
WIDTH, HEIGHT = 1200, 850
SCREEN_TITLE = "RayTracing 2D - Educational Edition"
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(SCREEN_TITLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 16)
font_bold = pygame.font.SysFont("consolas", 18, bold=True)

# ------------------------------------------------------------------
# COLORS
# ------------------------------------------------------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 60, 60)
GREEN = (0, 255, 0)
BLUE = (80, 160, 255)
LIGHT_GREEN = (144, 238, 144)
LIGHT_GREY = (211, 211, 211)
YELLOW = (255, 220, 60)
CYAN = (80, 255, 255)
ORANGE = (255, 165, 0)
PANEL_BG = (20, 20, 20, 180)  # con alpha, per pannello semi-trasparente


# ------------------------------------------------------------------
# CLASSI DEGLI OGGETTI DELLA SCENA
# ------------------------------------------------------------------
class Circle:
    """Un ostacolo circolare. width=0 -> pieno, width>0 -> solo bordo."""

    def __init__(self, x, y, radius, width=0, color=LIGHT_GREEN):
        self.x = x
        self.y = y
        self.radius = radius
        self.width = width
        self.color = color


class Wall:
    """Un ostacolo 'a muro': un semplice segmento tra due punti.
    I muri sono il modo classico di rappresentare geometria arbitraria
    nei raytracer 2D didattici (es. i tutorial 'Coding Train')."""

    def __init__(self, x1, y1, x2, y2, color=ORANGE):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color = color


class LightSource:
    def __init__(self, x, y, color, ray_length):
        self.x = x
        self.y = y
        self.color = color
        self.ray_length = ray_length


# ------------------------------------------------------------------
# OGGETTI INIZIALI DELLA SCENA
# ------------------------------------------------------------------
c1 = Circle(200, 200, 50, 0)  # il "giocatore", controllabile con le frecce
l1 = LightSource(500, 400, LIGHT_GREY, max(WIDTH, HEIGHT) * 1.5)

circles = [c1]  # tutti i cerchi della scena (incluso il giocatore)
walls = []      # tutti i muri/segmenti della scena

MOVEMENT_SPEED = 3


# ------------------------------------------------------------------
# MATEMATICA DEL RAYTRACING
# ------------------------------------------------------------------
def intersect_ray_circle(p0, d, circle):
    """Intersezione raggio-cerchio.

    Raggio:   P(t) = p0 + t * d           (d è normalizzato, lunghezza 1)
    Cerchio:  (x - cx)^2 + (y - cy)^2 = r^2

    Sostituendo si ottiene un'equazione di secondo grado in t:
        A*t^2 + B*t + C = 0
    con:
        A = d . d                (= 1, perché d è unitario)
        B = 2 * (L . d)          dove L = p0 - centro_cerchio
        C = (L . L) - r^2

    Il discriminante (delta = B^2 - 4AC) ci dice quante soluzioni reali esistono:
        delta < 0  -> il raggio NON tocca il cerchio
        delta = 0  -> il raggio è tangente (un solo punto)
        delta > 0  -> il raggio attraversa il cerchio (due punti)

    Ritorna la t più piccola e positiva (il punto di impatto più vicino
    alla sorgente), oppure None se non c'è intersezione valida.
    """
    cx, cy, r = circle.x, circle.y, circle.radius
    Lx, Ly = p0[0] - cx, p0[1] - cy

    A = d[0] * d[0] + d[1] * d[1]
    B = 2 * (Lx * d[0] + Ly * d[1])
    C = Lx * Lx + Ly * Ly - r * r

    delta = B * B - 4 * A * C
    if delta < 0:
        return None

    sqrt_delta = math.sqrt(delta)
    t1 = (-B - sqrt_delta) / (2 * A)
    t2 = (-B + sqrt_delta) / (2 * A)

    candidates = [t for t in (t1, t2) if t >= 1e-4]
    if not candidates:
        return None
    return min(candidates)


def intersect_ray_segment(p0, d, wall):
    """Intersezione raggio-segmento (muro).

    Un raggio è:      P = p0 + t * d                (t >= 0)
    Un segmento è:     Q = a + u * (b - a)           (0 <= u <= 1)

    Mettiamo le due rette a sistema e risolviamo con il metodo dei
    determinanti (regola di Cramer), molto usato nei raytracer 2D
    perché è veloce e gestisce bene i segmenti finiti.
    """
    x1, y1 = wall.x1, wall.y1
    x2, y2 = wall.x2, wall.y2
    x3, y3 = p0
    x4, y4 = p0[0] + d[0], p0[1] + d[1]

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        return None  # raggio e muro sono paralleli

    t_num = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
    u_num = (x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)

    t = t_num / denom  # posizione lungo il MURO (0..1)
    u = -u_num / denom  # posizione lungo il RAGGIO (deve essere >= 0)

    if 0 <= t <= 1 and u >= 1e-4:
        px = x1 + t * (x2 - x1)
        py = y1 + t * (y2 - y1)
        return u, (px, py)
    return None


def normal_at_circle_point(point, circle):
    """La normale ad un cerchio in un punto è semplicemente il vettore
    che va dal centro al punto, normalizzato."""
    nx = point[0] - circle.x
    ny = point[1] - circle.y
    length = math.hypot(nx, ny) or 1
    return nx / length, ny / length


def normal_at_wall(wall):
    """La normale di un segmento è perpendicolare alla sua direzione:
    ruotiamo il vettore direzione di 90 gradi. Un segmento ha due normali
    possibili (una per lato); qui ne restituiamo una, coerente."""
    dx = wall.x2 - wall.x1
    dy = wall.y2 - wall.y1
    length = math.hypot(dx, dy) or 1
    return -dy / length, dx / length


def reflect(d, n):
    """Legge della riflessione: R = D - 2*(D . N)*N

    È la stessa formula che descrive un raggio di luce che rimbalza su
    uno specchio: l'angolo di incidenza è uguale all'angolo di riflessione.
    """
    dot = d[0] * n[0] + d[1] * n[1]
    rx = d[0] - 2 * dot * n[0]
    ry = d[1] - 2 * dot * n[1]
    length = math.hypot(rx, ry) or 1
    return rx / length, ry / length


def find_closest_hit(p0, d, max_len):
    """Controlla tutte le forme della scena e ritorna l'intersezione più
    vicina, con tipo di oggetto e normale associata."""
    best_t = max_len
    best_point = None
    best_normal = None
    best_kind = None

    for circle in circles:
        t = intersect_ray_circle(p0, d, circle)
        if t is not None and t < best_t:
            point = (p0[0] + t * d[0], p0[1] + t * d[1])
            best_t = t
            best_point = point
            best_normal = normal_at_circle_point(point, circle)
            best_kind = "circle"

    for wall in walls:
        result = intersect_ray_segment(p0, d, wall)
        if result is not None:
            t, point = result
            if t < best_t:
                best_t = t
                best_point = point
                best_normal = normal_at_wall(wall)
                best_kind = "wall"

    return best_t, best_point, best_normal, best_kind


# ------------------------------------------------------------------
# STATO / IMPOSTAZIONI CONTROLLABILI DA TASTIERA
# ------------------------------------------------------------------
NUM_RAYS = 180          # numero di raggi emessi dalla luce (densità)
show_reflections = False
show_normals = False
use_falloff = True
show_help = True
light_follows_mouse = False

wall_drag_start = None  # punto di partenza mentre disegniamo un muro


def attenuate(base_color, distance, max_distance):
    """Simula l'attenuazione della luce con la distanza (falloff).
    Più il punto è lontano dalla sorgente, più il colore del raggio si
    affievolisce: è una versione semplificata della legge dell'inverso
    del quadrato usata nei raytracer 3D reali."""
    if not use_falloff:
        return base_color
    intensity = max(0.12, 1 - (distance / max_distance))
    return tuple(int(c * intensity) for c in base_color)


def draw_help_panel():
    lines = [
        "CONTROLLI",
        "Frecce: muovi il cerchio principale",
        "Click sx: aggiungi cerchio | SHIFT+trascina: aggiungi muro",
        "Click dx: rimuovi oggetto vicino al cursore",
        "L: luce segue il mouse   (attivo: {})".format(light_follows_mouse),
        "R: riflessioni           (attivo: {})".format(show_reflections),
        "N: mostra normali        (attivo: {})".format(show_normals),
        "F: attenuazione luce     (attiva: {})".format(use_falloff),
        "+/-: numero di raggi     (attuale: {})".format(NUM_RAYS),
        "C: pulisci scena   |   H: nascondi/mostra aiuto   |   ESC: esci",
        "FPS: {:.0f}".format(clock.get_fps()),
    ]
    panel_w, panel_h = 560, 22 * len(lines) + 16
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill(PANEL_BG)
    screen.blit(panel, (10, 10))

    for i, line in enumerate(lines):
        surf = (font_bold if i == 0 else font).render(line, True, WHITE)
        screen.blit(surf, (20, 18 + i * 22))


# ------------------------------------------------------------------
# LOOP PRINCIPALE
# ------------------------------------------------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                show_reflections = not show_reflections
            elif event.key == pygame.K_n:
                show_normals = not show_normals
            elif event.key == pygame.K_f:
                use_falloff = not use_falloff
            elif event.key == pygame.K_h:
                show_help = not show_help
            elif event.key == pygame.K_l:
                light_follows_mouse = not light_follows_mouse
            elif event.key == pygame.K_c:
                circles = [c1]
                walls = []
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                NUM_RAYS = min(1440, NUM_RAYS + 10)
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                NUM_RAYS = max(4, NUM_RAYS - 10)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            mods = pygame.key.get_mods()

            if event.button == 1:  # click sinistro
                if mods & pygame.KMOD_SHIFT:
                    wall_drag_start = (mx, my)
                elif not light_follows_mouse:
                    circles.append(Circle(mx, my, 30, 0, LIGHT_GREEN))

            elif event.button == 3:  # click destro: rimuovi oggetto vicino
                closest_obj = None
                closest_dist = 25  # soglia in pixel
                for circle in circles:
                    if circle is c1:
                        continue
                    dist = math.hypot(circle.x - mx, circle.y - my)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_obj = ("circle", circle)
                for wall in walls:
                    mid_x = (wall.x1 + wall.x2) / 2
                    mid_y = (wall.y1 + wall.y2) / 2
                    dist = math.hypot(mid_x - mx, mid_y - my)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_obj = ("wall", wall)
                if closest_obj:
                    kind, obj = closest_obj
                    if kind == "circle":
                        circles.remove(obj)
                    else:
                        walls.remove(obj)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and wall_drag_start is not None:
                mx, my = event.pos
                sx, sy = wall_drag_start
                if math.hypot(mx - sx, my - sy) > 5:
                    walls.append(Wall(sx, sy, mx, my))
                wall_drag_start = None

    # --- movimento del cerchio principale ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        c1.y -= MOVEMENT_SPEED
    if keys[pygame.K_DOWN]:
        c1.y += MOVEMENT_SPEED
    if keys[pygame.K_RIGHT]:
        c1.x += MOVEMENT_SPEED
    if keys[pygame.K_LEFT]:
        c1.x -= MOVEMENT_SPEED

    # --- la luce può seguire il mouse ---
    if light_follows_mouse:
        mx, my = pygame.mouse.get_pos()
        if not any(math.hypot(mx - c.x, my - c.y) <= c.radius for c in circles):
            l1.x, l1.y = mx, my

    # --- pulizia schermo ---
    screen.fill(BLACK)

    # --- disegno degli ostacoli ---
    for circle in circles:
        pygame.draw.circle(screen, circle.color, (circle.x, circle.y), circle.radius, circle.width)
    for wall in walls:
        pygame.draw.line(screen, wall.color, (wall.x1, wall.y1), (wall.x2, wall.y2), 4)

    # --- sorgente di luce ---
    pygame.draw.circle(screen, YELLOW, (l1.x, l1.y), 6)

    # --- RAY TRACING: per ogni angolo, emetti un raggio dalla luce ---
    angle_step = 360 / NUM_RAYS
    angle = 0.0
    while angle < 360:
        rad = math.radians(angle)
        p0 = (l1.x, l1.y)
        d = (math.cos(rad), math.sin(rad))

        t, hit_point, normal, kind = find_closest_hit(p0, d, l1.ray_length)

        if hit_point is None:
            end_point = (p0[0] + l1.ray_length * d[0], p0[1] + l1.ray_length * d[1])
            dist = l1.ray_length
        else:
            end_point = hit_point
            dist = t

        color = attenuate(l1.color, dist, l1.ray_length)
        pygame.draw.line(screen, color, p0, (int(end_point[0]), int(end_point[1])), 1)

        # --- Riflessione: se il raggio primario ha colpito qualcosa,
        #     calcoliamo un secondo raggio "rimbalzato" e lo disegniamo ---
        if show_reflections and hit_point is not None and normal is not None:
            reflected_dir = reflect(d, normal)
            remaining_len = l1.ray_length - dist
            t2, hit2, normal2, kind2 = find_closest_hit(hit_point, reflected_dir, remaining_len)
            if hit2 is not None:
                end2 = hit2
                total_dist = dist + t2
            else:
                end2 = (hit_point[0] + remaining_len * reflected_dir[0],
                        hit_point[1] + remaining_len * reflected_dir[1])
                total_dist = dist + remaining_len
            reflect_color = attenuate(CYAN, total_dist, l1.ray_length)
            pygame.draw.line(screen, reflect_color, hit_point,
                              (int(end2[0]), int(end2[1])), 1)

        # --- Normali: piccola linea gialla nel punto di impatto ---
        if show_normals and hit_point is not None and normal is not None:
            nx_end = hit_point[0] + normal[0] * 18
            ny_end = hit_point[1] + normal[1] * 18
            pygame.draw.line(screen, YELLOW, hit_point, (nx_end, ny_end), 2)

        angle += angle_step

    # --- disegna il punto in fase di trascinamento del muro ---
    if wall_drag_start is not None:
        pygame.draw.line(screen, ORANGE, wall_drag_start, pygame.mouse.get_pos(), 2)

    # --- HUD ---
    if show_help:
        draw_help_panel()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()