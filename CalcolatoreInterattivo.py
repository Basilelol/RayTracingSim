import math
import pygame
import sys

pygame.init()

# --- Impostazioni Finestra ---
WIDTH, HEIGHT = 1200, 800
SCREEN_TITLE = "Ray Tracing Trainer"
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(SCREEN_TITLE)

# --- Colori ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
LIGHT_GREEN = (144, 238, 144)
LIGHT_GREY = (211, 211, 211)
DARK_GREY = (50, 50, 50)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

# --- Font ---
FONT_SIZE_TITLE = 36
FONT_SIZE_TEXT = 18
FONT_SIZE_INPUT = 20
FONT_SIZE_FEEDBACK = 22

FONT_TITLE = pygame.font.Font(None, FONT_SIZE_TITLE)
FONT_TEXT = pygame.font.Font(None, FONT_SIZE_TEXT)
FONT_INPUT = pygame.font.Font(None, FONT_SIZE_INPUT)
FONT_FEEDBACK = pygame.font.Font(None, FONT_SIZE_FEEDBACK)

# --- Impostazioni UI ---
TEXT_AREA_WIDTH = WIDTH // 2.5
GRAPHICS_AREA_WIDTH = WIDTH - TEXT_AREA_WIDTH
GRAPHICS_AREA_X = TEXT_AREA_WIDTH

INPUT_BOX_WIDTH = 120
INPUT_BOX_HEIGHT = 30

# --- Classi Oggetti ---
class Circle:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius

class LightSource:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# --- Input Box Class ---
class InputBox:
    def __init__(self, x, y, w, h, label="", text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = LIGHT_GREY
        self.text = text
        self.label = label
        self.txt_surface = FONT_INPUT.render(text, True, BLACK)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = WHITE if self.active else LIGHT_GREY
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return "SUBMIT"
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = FONT_INPUT.render(self.text, True, BLACK)
        return None

    def draw(self, screen):
        # Draw label
        if self.label:
            label_surface = FONT_TEXT.render(self.label, True, WHITE)
            screen.blit(label_surface, (self.rect.x, self.rect.y - 25))
        
        # Draw input box
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        # Draw cursor if active
        if self.active:
            cursor_x = self.rect.x + 5 + self.txt_surface.get_width()
            cursor_y = self.rect.y + 5
            pygame.draw.line(screen, BLACK, (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 2)

    def get_value(self):
        try:
            return float(self.text.strip()) if self.text.strip() else None
        except ValueError:
            return None

    def set_text(self, text):
        self.text = str(text)
        self.txt_surface = FONT_INPUT.render(self.text, True, BLACK)

    def clear(self):
        self.text = ""
        self.txt_surface = FONT_INPUT.render("", True, BLACK)

# --- Funzione per i calcoli ---
def calculate_ray_circle_intersection(light_source, circle, angle_degrees, ray_length_limit=2000):
    results = {}
    p0_x, p0_y = light_source.x, light_source.y
    cx, cy = circle.x, circle.y
    radius = circle.radius

    results['p0'] = (p0_x, p0_y)
    results['circle_center'] = (cx, cy)
    results['circle_radius'] = radius
    results['angle_degrees'] = angle_degrees

    angle_radians = math.radians(angle_degrees)
    dir_x = math.cos(angle_radians)
    dir_y = math.sin(angle_radians)
    results['D_vector'] = (dir_x, dir_y)

    L_x = p0_x - cx
    L_y = p0_y - cy
    results['L_vector'] = (L_x, L_y)

    A = dir_x**2 + dir_y**2
    B = 2 * (L_x * dir_x + L_y * dir_y)
    C = L_x**2 + L_y**2 - radius**2
    results['A_coeff'] = A
    results['B_coeff'] = B
    results['C_coeff'] = C

    delta = B**2 - 4 * A * C
    results['delta'] = delta

    results['intersection_point'] = None
    results['t_closest'] = None
    results['normal_vector'] = None
    results['incident_vector'] = None
    results['dot_product_IN'] = None
    results['reflected_vector'] = None
    results['intersection_possible'] = False

    if delta >= 0:
        sqrt_delta = math.sqrt(delta)
        t1 = (-B - sqrt_delta) / (2 * A)
        t2 = (-B + sqrt_delta) / (2 * A)
        results['t_values'] = (t1, t2)

        valid_t = []
        if t1 >= 0:
            valid_t.append(t1)
        if t2 >= 0:
            valid_t.append(t2)

        if valid_t:
            t_closest = min(valid_t)
            if t_closest <= ray_length_limit:
                results['t_closest'] = t_closest
                intersection_point_x = p0_x + t_closest * dir_x
                intersection_point_y = p0_y + t_closest * dir_y
                results['intersection_point'] = (intersection_point_x, intersection_point_y)
                results['intersection_possible'] = True

                normal_vec_x = intersection_point_x - cx
                normal_vec_y = intersection_point_y - cy
                normal_mag = math.sqrt(normal_vec_x**2 + normal_vec_y**2)
                if normal_mag != 0:
                    normal_x = normal_vec_x / normal_mag
                    normal_y = normal_vec_y / normal_mag
                    results['normal_vector'] = (normal_x, normal_y)
                else:
                    results['normal_vector'] = (0.0, 0.0)

                incident_x = -dir_x
                incident_y = -dir_y
                results['incident_vector'] = (incident_x, incident_y)

                if results['normal_vector']:
                     dot_product_IN = (incident_x * results['normal_vector'][0]) + (incident_y * results['normal_vector'][1])
                     results['dot_product_IN'] = dot_product_IN

                     reflected_x = incident_x - 2 * dot_product_IN * results['normal_vector'][0]
                     reflected_y = incident_y - 2 * dot_product_IN * results['normal_vector'][1]
                     results['reflected_vector'] = (reflected_x, reflected_y)
    
    return results

# --- Funzioni di Utility per il Disegno ---
def draw_text(surface, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

def draw_point(surface, color, pos, radius=5):
    pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), radius)

def draw_vector(surface, color, start_pos, vector, length_scale=50):
    end_x = start_pos[0] + vector[0] * length_scale
    end_y = start_pos[1] + vector[1] * length_scale
    pygame.draw.line(surface, color, (int(start_pos[0]), int(start_pos[1])), (int(end_x), int(end_y)), 2)
    arrow_size = 10
    angle = math.atan2(vector[1], vector[0])
    pygame.draw.line(surface, color, (int(end_x), int(end_y)),
                     (int(end_x - arrow_size * math.cos(angle - math.pi/6)), int(end_y - arrow_size * math.sin(angle - math.pi/6))), 2)
    pygame.draw.line(surface, color, (int(end_x), int(end_y)),
                     (int(end_x - arrow_size * math.cos(angle + math.pi/6)), int(end_y - arrow_size * math.sin(angle + math.pi/6))), 2)

# --- Funzioni di Check ---
def check_value_single(user_val, correct_val, tolerance=0.01):
    if user_val is None or correct_val is None:
        return False
    return abs(user_val - correct_val) < tolerance

# --- Variabili di Gioco ---
current_ls = LightSource(GRAPHICS_AREA_X + GRAPHICS_AREA_WIDTH // 2, HEIGHT // 2)
current_circle = Circle(GRAPHICS_AREA_X + GRAPHICS_AREA_WIDTH // 4, HEIGHT // 3, 50)
current_angle_degrees = 45

# Stato del quiz
quiz_steps = [
    {"name": "D_vector", "description": "Calcola il Vettore Direzione D", "inputs": ["D_x", "D_y"]},
    {"name": "L_vector", "description": "Calcola il Vettore L (da sorgente a centro cerchio)", "inputs": ["L_x", "L_y"]},
    {"name": "A_coeff", "description": "Calcola il coefficiente A", "inputs": ["A"]},
    {"name": "B_coeff", "description": "Calcola il coefficiente B", "inputs": ["B"]},
    {"name": "C_coeff", "description": "Calcola il coefficiente C", "inputs": ["C"]},
    {"name": "delta", "description": "Calcola il Discriminante (Delta)", "inputs": ["Delta"]},
    {"name": "t_values", "description": "Calcola i valori t1 e t2", "inputs": ["t1", "t2"]},
    {"name": "t_closest", "description": "Qual è il valore t più vicino?", "inputs": ["t_closest"]},
    {"name": "intersection_point", "description": "Calcola il Punto di Intersezione", "inputs": ["P_x", "P_y"]},
    {"name": "incident_vector", "description": "Calcola il vettore Incidente I", "inputs": ["I_x", "I_y"]},
    {"name": "normal_vector", "description": "Calcola il vettore Normale N", "inputs": ["N_x", "N_y"]},
    {"name": "dot_product_IN", "description": "Calcola il Prodotto Scalare (I·N)", "inputs": ["I_dot_N"]},
    {"name": "reflected_vector", "description": "Calcola il vettore Riflesso R", "inputs": ["R_x", "R_y"]}
]

current_step_index = 0
feedback_message = ""
feedback_color = BLACK

# Input boxes dinamiche
input_boxes = []

def create_input_boxes_for_step(step_index):
    global input_boxes
    input_boxes = []
    
    if step_index >= len(quiz_steps):
        return
    
    step = quiz_steps[step_index]
    y_start = 300
    x_start = 20
    
    for i, input_name in enumerate(step["inputs"]):
        y_pos = y_start + i * 60
        input_box = InputBox(x_start, y_pos, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT, input_name + ":")
        input_boxes.append(input_box)

# Crea le prime input boxes
create_input_boxes_for_step(current_step_index)

def get_hint_for_step(step_index, results):
    if step_index >= len(quiz_steps):
        return ""
    
    step_name = quiz_steps[step_index]["name"]
    
    if step_name == "D_vector":
        return f"Angolo: {results['angle_degrees']}°. Usa cos e sin"
    elif step_name == "L_vector":
        p0 = results['p0']
        center = results['circle_center']
        return f"L = P0 - C. P0=({p0[0]:.1f},{p0[1]:.1f}), C=({center[0]:.1f},{center[1]:.1f})"
    elif step_name == "A_coeff":
        d_vec = results['D_vector']
        return f"A = D_x² + D_y². D=({d_vec[0]:.3f},{d_vec[1]:.3f})"
    elif step_name == "B_coeff":
        l_vec = results['L_vector']
        d_vec = results['D_vector']
        return f"B = 2×(L_x×D_x + L_y×D_y). L=({l_vec[0]:.1f},{l_vec[1]:.1f}), D=({d_vec[0]:.3f},{d_vec[1]:.3f})"
    elif step_name == "C_coeff":
        l_vec = results['L_vector']
        return f"C = L_x² + L_y² - R². L=({l_vec[0]:.1f},{l_vec[1]:.1f}), R={results['circle_radius']}"
    elif step_name == "delta":
        return f"Delta = B² - 4AC. A={results['A_coeff']:.1f}, B={results['B_coeff']:.1f}, C={results['C_coeff']:.1f}"
    elif step_name == "t_values":
        return f"t = (-B ± √Delta) / (2A). Delta={results['delta']:.1f}"
    elif step_name == "t_closest":
        return "Il t più piccolo e positivo"
    elif step_name == "intersection_point":
        p0 = results['p0']
        d_vec = results['D_vector']
        return f"P_int = P0 + t_closest × D. P0=({p0[0]:.1f},{p0[1]:.1f}), t={results['t_closest']:.3f}"
    elif step_name == "incident_vector":
        d_vec = results['D_vector']
        return f"I = -D. D=({d_vec[0]:.3f},{d_vec[1]:.3f})"
    elif step_name == "normal_vector":
        return "N punta dal centro al punto di intersezione, normalizzato"
    elif step_name == "dot_product_IN":
        return "I·N = I_x×N_x + I_y×N_y"
    elif step_name == "reflected_vector":
        return "R = I - 2×(I·N)×N"
    
    return ""

def check_step_answer():
    global current_step_index, feedback_message, feedback_color
    
    if current_step_index >= len(quiz_steps):
        return
    
    step = quiz_steps[current_step_index]
    step_name = step["name"]
    
    # Ottieni i valori dalle input boxes
    user_values = []
    for input_box in input_boxes:
        value = input_box.get_value()
        if value is None:
            feedback_message = "Inserisci tutti i valori richiesti!"
            feedback_color = RED
            return
        user_values.append(value)
    
    # Calcola i risultati corretti
    all_results = calculate_ray_circle_intersection(current_ls, current_circle, current_angle_degrees)
    
    # Controlla la risposta
    is_correct = False
    
    if step_name == "D_vector":
        correct = all_results['D_vector']
        is_correct = (check_value_single(user_values[0], correct[0]) and 
                     check_value_single(user_values[1], correct[1]))
    elif step_name == "L_vector":
        correct = all_results['L_vector']
        is_correct = (check_value_single(user_values[0], correct[0]) and 
                     check_value_single(user_values[1], correct[1]))
    elif step_name == "A_coeff":
        is_correct = check_value_single(user_values[0], all_results['A_coeff'])
    elif step_name == "B_coeff":
        is_correct = check_value_single(user_values[0], all_results['B_coeff'])
    elif step_name == "C_coeff":
        is_correct = check_value_single(user_values[0], all_results['C_coeff'])
    elif step_name == "delta":
        is_correct = check_value_single(user_values[0], all_results['delta'])
    elif step_name == "t_values":
        correct = all_results.get('t_values', (0, 0))
        is_correct = ((check_value_single(user_values[0], correct[0]) and check_value_single(user_values[1], correct[1])) or
                     (check_value_single(user_values[0], correct[1]) and check_value_single(user_values[1], correct[0])))
    elif step_name == "t_closest":
        is_correct = check_value_single(user_values[0], all_results.get('t_closest', 0))
    elif step_name == "intersection_point":
        correct = all_results.get('intersection_point', (0, 0))
        if correct:
            is_correct = (check_value_single(user_values[0], correct[0]) and 
                         check_value_single(user_values[1], correct[1]))
    elif step_name == "incident_vector":
        correct = all_results.get('incident_vector', (0, 0))
        if correct:
            is_correct = (check_value_single(user_values[0], correct[0]) and 
                         check_value_single(user_values[1], correct[1]))
    elif step_name == "normal_vector":
        correct = all_results.get('normal_vector', (0, 0))
        if correct:
            is_correct = (check_value_single(user_values[0], correct[0]) and 
                         check_value_single(user_values[1], correct[1]))
    elif step_name == "dot_product_IN":
        is_correct = check_value_single(user_values[0], all_results.get('dot_product_IN', 0))
    elif step_name == "reflected_vector":
        correct = all_results.get('reflected_vector', (0, 0))
        if correct:
            is_correct = (check_value_single(user_values[0], correct[0]) and 
                         check_value_single(user_values[1], correct[1]))
    
    if is_correct:
        feedback_message = "Corretto!"
        feedback_color = GREEN
        current_step_index += 1
        
        if current_step_index >= len(quiz_steps):
            feedback_message = "Hai completato tutti i calcoli! Complimenti!"
            feedback_color = BLUE
        else:
            create_input_boxes_for_step(current_step_index)
    else:
        feedback_message = "Sbagliato. Riprova."
        feedback_color = RED

# --- Main Loop ---
running = True
clock = pygame.time.Clock()

while running:
    all_results = calculate_ray_circle_intersection(current_ls, current_circle, current_angle_degrees)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Handle input box events
        submit_pressed = False
        for input_box in input_boxes:
            action = input_box.handle_event(event)
            if action == "SUBMIT":
                submit_pressed = True
        
        if submit_pressed:
            check_step_answer()

        # Drag and drop for objects
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if mouse_x > GRAPHICS_AREA_X:
                if math.dist((mouse_x, mouse_y), (current_ls.x, current_ls.y)) < 20:
                    current_ls.dragging = True
                elif math.dist((mouse_x, mouse_y), (current_circle.x, current_circle.y)) < current_circle.radius:
                    current_circle.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if hasattr(current_ls, 'dragging'): current_ls.dragging = False
            if hasattr(current_circle, 'dragging'): current_circle.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if hasattr(current_ls, 'dragging') and current_ls.dragging:
                current_ls.x, current_ls.y = event.pos
            elif hasattr(current_circle, 'dragging') and current_circle.dragging:
                current_circle.x, current_circle.y = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                current_angle_degrees = (current_angle_degrees + 5) % 360
            elif event.y < 0:
                current_angle_degrees = (current_angle_degrees - 5 + 360) % 360

    # --- Disegno ---
    screen.fill(DARK_GREY)
    pygame.draw.line(screen, BLACK, (TEXT_AREA_WIDTH, 0), (TEXT_AREA_WIDTH, HEIGHT), 3)

    # --- Area Grafica ---
    graphics_surface = pygame.Surface((GRAPHICS_AREA_WIDTH, HEIGHT))
    graphics_surface.fill(BLACK)

    # Disegna Cerchio
    pygame.draw.circle(graphics_surface, LIGHT_GREEN, 
                       (int(current_circle.x - GRAPHICS_AREA_X), int(current_circle.y)), 
                       current_circle.radius, 0)
    draw_point(graphics_surface, WHITE, (current_circle.x - GRAPHICS_AREA_X, current_circle.y), 3)

    # Disegna Sorgente Luminosa
    draw_point(graphics_surface, YELLOW, (current_ls.x - GRAPHICS_AREA_X, current_ls.y), 7)

    # Disegna il raggio principale
    ray_start_g = (current_ls.x - GRAPHICS_AREA_X, current_ls.y)
    
    if all_results['intersection_possible']:
        pygame.draw.line(graphics_surface, LIGHT_GREY, ray_start_g, 
                        (int(all_results['intersection_point'][0] - GRAPHICS_AREA_X), 
                         int(all_results['intersection_point'][1])), 1)
        draw_point(graphics_surface, RED, 
                  (all_results['intersection_point'][0] - GRAPHICS_AREA_X, 
                   all_results['intersection_point'][1]), 4)
        
        # Disegna vettori progressivamente
        if current_step_index > 0:
            draw_vector(graphics_surface, WHITE, ray_start_g, all_results['D_vector'], 100)
            draw_text(graphics_surface, "D", FONT_TEXT, WHITE, 
                     ray_start_g[0] + all_results['D_vector'][0]*100+5, 
                     ray_start_g[1] + all_results['D_vector'][1]*100+5)
        
        if current_step_index > 1:
            draw_vector(graphics_surface, MAGENTA, ray_start_g, all_results['L_vector'], 1)
            draw_text(graphics_surface, "L", FONT_TEXT, MAGENTA, 
                     ray_start_g[0] + all_results['L_vector'][0]*50+5, 
                     ray_start_g[1] + all_results['L_vector'][1]*50+5)
        
        if current_step_index > 9 and all_results['normal_vector']:
            draw_vector(graphics_surface, CYAN, 
                       (all_results['intersection_point'][0] - GRAPHICS_AREA_X, 
                        all_results['intersection_point'][1]), 
                       all_results['normal_vector'], 50)
        
        if current_step_index > 8 and all_results['incident_vector']:
            draw_vector(graphics_surface, YELLOW, 
                       (all_results['intersection_point'][0] - GRAPHICS_AREA_X, 
                        all_results['intersection_point'][1]), 
                       all_results['incident_vector'], 50)
        
        if current_step_index > 11 and all_results['reflected_vector']:
            draw_vector(graphics_surface, BLUE, 
                       (all_results['intersection_point'][0] - GRAPHICS_AREA_X, 
                        all_results['intersection_point'][1]), 
                       all_results['reflected_vector'], 100)
    else:
        ray_end_g = (ray_start_g[0] + all_results['D_vector'][0] * 1000,
                     ray_start_g[1] + all_results['D_vector'][1] * 1000)
        pygame.draw.line(graphics_surface, LIGHT_GREY, ray_start_g, ray_end_g, 1)

    screen.blit(graphics_surface, (GRAPHICS_AREA_X, 0))

    # --- Area Testuale/Input ---
    draw_text(screen, "Ray Tracing Trainer", FONT_TITLE, WHITE, 20, 20)
    
    if current_step_index < len(quiz_steps):
        step = quiz_steps[current_step_index]
        draw_text(screen, f"Passo {current_step_index + 1}: {step['description']}", FONT_TEXT, WHITE, 20, 80)
        
        hint = get_hint_for_step(current_step_index, all_results)
        draw_text(screen, hint, FONT_TEXT, LIGHT_GREY, 20, 110)
    else:
        draw_text(screen, "Tutti i calcoli completati!", FONT_TEXT, WHITE, 20, 80)

    # Informazioni sulla configurazione
    draw_text(screen, f"Sorgente: ({current_ls.x:.0f}, {current_ls.y:.0f})", FONT_TEXT, WHITE, 20, 150)
    draw_text(screen, f"Cerchio: ({current_circle.x:.0f}, {current_circle.y:.0f}), R: {current_circle.radius:.0f}", FONT_TEXT, WHITE, 20, 170)
    draw_text(screen, f"Angolo: {current_angle_degrees:.0f}°", FONT_TEXT, WHITE, 20, 190)
    draw_text(screen, "Trascina oggetti o usa rotella mouse per angolo", FONT_TEXT, WHITE, 20, 220)

    # Disegna input boxes
    for input_box in input_boxes:
        input_box.draw(screen) 

    # Feedback
    draw_text(screen, feedback_message, FONT_FEEDBACK, feedback_color, 20, 550)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()