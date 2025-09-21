import pygame
import sys
import random
import cv2
from deepface import DeepFace
import threading
import time
import numpy as np

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CATCHER_WIDTH = 100
CATCHER_HEIGHT = 20
OBJECT_SIZE = 30
HIGH_SCORE_FILE = "highscore_catch_the_smile.txt"
WEBCAM_VIEW_SIZE = (160, 120)

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# --- Game Modes ---
MODE_NORMAL = "normal"
MODE_TOP_DOWN = "top_down"
MODE_SIDE_TO_SIDE = "side_to_side"

# --- Global variables for emotion detection ---
current_emotion = "neutral"
webcam_frame = None
stop_thread = False
emotion_timer = 0
EMOTION_INTERVAL = 30 # Frames to wait between emotion checks
happy_start_time = None
game_mode = MODE_NORMAL

# --- Emotion Analysis Thread ---
def emotion_analysis_thread(cap):
    """
    Analyzes webcam frames in a separate thread.
    """
    global current_emotion, webcam_frame, stop_thread
    
    while not stop_thread:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        try:
            analysis = DeepFace.analyze(
                rgb_frame, 
                actions=['emotion'], 
                enforce_detection=True,
                detector_backend='opencv'
            )
            if isinstance(analysis, list) and len(analysis) > 0:
                current_emotion = analysis[0]['dominant_emotion']
            else:
                 current_emotion = analysis['dominant_emotion']
        except ValueError as e:
            current_emotion = "no face"
        
        frame = cv2.flip(frame, 1)
        frame_resized = cv2.resize(frame, WEBCAM_VIEW_SIZE)
        webcam_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        
        time.sleep(0.25)

# --- Catcher Class ---
class Catcher(pygame.sprite.Sprite):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.image = pygame.Surface([CATCHER_WIDTH, CATCHER_HEIGHT])
        self.image.fill(WHITE)
        self.speed = 10
        
        if self.mode == MODE_NORMAL:
            self.rect = self.image.get_rect(centerx=SCREEN_WIDTH / 2, bottom=SCREEN_HEIGHT - 10)
        elif self.mode == MODE_TOP_DOWN:
            self.rect = self.image.get_rect(centerx=SCREEN_WIDTH / 2, top=10)
        elif self.mode == MODE_SIDE_TO_SIDE:
            self.rect = self.image.get_rect(centery=SCREEN_HEIGHT / 2, left=10)
            self.image = pygame.transform.rotate(self.image, 90)
            
    def update(self):
        keys = pygame.key.get_pressed()
        
        if self.mode == MODE_NORMAL or self.mode == MODE_TOP_DOWN:
            if keys[pygame.K_LEFT] and self.rect.left > 0:
                self.rect.x -= self.speed
            if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
                self.rect.x += self.speed
        elif self.mode == MODE_SIDE_TO_SIDE:
            if keys[pygame.K_UP] and self.rect.top > 0:
                self.rect.y -= self.speed
            if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
                self.rect.y += self.speed

        # Adjust catcher size based on emotion
        global current_emotion
        if current_emotion == "happy":
            new_dim = 60
        else:
            new_dim = 100
        
        if self.mode == MODE_SIDE_TO_SIDE:
            if self.rect.height != new_dim:
                self.image = pygame.Surface([CATCHER_HEIGHT, new_dim])
                self.image.fill(WHITE)
                self.rect = self.image.get_rect(centery=self.rect.centery, left=self.rect.left)
        else:
            if self.rect.width != new_dim:
                self.image = pygame.Surface([new_dim, CATCHER_HEIGHT])
                self.image.fill(WHITE)
                self.rect = self.image.get_rect(centerx=self.rect.centerx, bottom=self.rect.bottom)


# --- Falling Object Class ---
class FallingObject(pygame.sprite.Sprite):
    def __init__(self, obj_type, mode, speed):
        super().__init__()
        self.obj_type = obj_type
        self.mode = mode
        self.image = pygame.Surface([OBJECT_SIZE, OBJECT_SIZE], pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0)) # Transparent background
        
        if self.obj_type == "smile":
            color = GREEN
            pygame.draw.circle(self.image, color, (OBJECT_SIZE / 2, OBJECT_SIZE / 2), OBJECT_SIZE / 2)
            pygame.draw.circle(self.image, BLACK, (OBJECT_SIZE * 0.35, OBJECT_SIZE * 0.35), OBJECT_SIZE * 0.1)
            pygame.draw.circle(self.image, BLACK, (OBJECT_SIZE * 0.65, OBJECT_SIZE * 0.35), OBJECT_SIZE * 0.1)
            pygame.draw.arc(self.image, BLACK, (OBJECT_SIZE * 0.2, OBJECT_SIZE * 0.4, OBJECT_SIZE * 0.6, OBJECT_SIZE * 0.4), 0, 3.14, 2)
        else:
            color = RED
            pygame.draw.circle(self.image, color, (OBJECT_SIZE / 2, OBJECT_SIZE / 2), OBJECT_SIZE / 2)
            pygame.draw.circle(self.image, BLACK, (OBJECT_SIZE * 0.35, OBJECT_SIZE * 0.35), OBJECT_SIZE * 0.1)
            pygame.draw.circle(self.image, BLACK, (OBJECT_SIZE * 0.65, OBJECT_SIZE * 0.35), OBJECT_SIZE * 0.1)
            pygame.draw.arc(self.image, BLACK, (OBJECT_SIZE * 0.2, OBJECT_SIZE * 0.6, OBJECT_SIZE * 0.6, OBJECT_SIZE * 0.4), 3.14, 6.28, 2)
        
        self.speed = speed
        
        if self.mode == MODE_NORMAL:
            self.rect = self.image.get_rect(centerx=random.randint(OBJECT_SIZE, SCREEN_WIDTH - OBJECT_SIZE), top=0)
        elif self.mode == MODE_TOP_DOWN:
            self.rect = self.image.get_rect(centerx=random.randint(OBJECT_SIZE, SCREEN_WIDTH - OBJECT_SIZE), bottom=SCREEN_HEIGHT)
        elif self.mode == MODE_SIDE_TO_SIDE:
            if random.random() < 0.5: # Pop from the right
                self.rect = self.image.get_rect(centery=random.randint(OBJECT_SIZE, SCREEN_HEIGHT - OBJECT_SIZE), right=SCREEN_WIDTH)
                self.speed = -self.speed
            else: # Pop from the left
                self.rect = self.image.get_rect(centery=random.randint(OBJECT_SIZE, SCREEN_HEIGHT - OBJECT_SIZE), left=0)

    def update(self):
        if self.mode == MODE_NORMAL:
            self.rect.y += self.speed
            if self.rect.top > SCREEN_HEIGHT:
                self.kill()
        elif self.mode == MODE_TOP_DOWN:
            self.rect.y -= self.speed
            if self.rect.bottom < 0:
                self.kill()
        elif self.mode == MODE_SIDE_TO_SIDE:
            self.rect.x += self.speed
            if self.speed > 0 and self.rect.left > SCREEN_WIDTH:
                self.kill()
            elif self.speed < 0 and self.rect.right < 0:
                self.kill()

# --- Utility and Screen Functions ---
def draw_text(surface, text, size, x, y, color=WHITE):
    font = pygame.font.Font(pygame.font.match_font('arial'), size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

def create_button(surface, rect, text, text_color, button_color, hover_color):
    mouse_pos = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    is_hovering = rect.collidepoint(mouse_pos)
    if is_hovering:
        pygame.draw.rect(surface, hover_color, rect, border_radius=10)
    else:
        pygame.draw.rect(surface, button_color, rect, border_radius=10)
    draw_text(surface, text, 20, rect.centerx, rect.centery - 10, text_color)
    return is_hovering and click[0] == 1

def show_menu(screen):
    """Displays the main menu."""
    title_font = pygame.font.Font(pygame.font.match_font('arial'), 64)
    title_surface = title_font.render("Catch the Smile", True, WHITE)
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    
    start_button = pygame.Rect(SCREEN_WIDTH/2 - 100, 350, 200, 50)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(BLACK)
        screen.blit(title_surface, title_rect)
        draw_text(screen, "A dynamic difficulty game", 22, SCREEN_WIDTH/2, SCREEN_HEIGHT / 3 + 20)
        
        if create_button(screen, start_button, "Start Game", BLACK, GREEN, (144, 238, 144)):
            return

        pygame.display.flip()

def show_game_over_screen(screen, score):
    try:
        with open(HIGH_SCORE_FILE, 'r') as f: high_score = int(f.read())
    except (IOError, ValueError): high_score = 0
    new_high_score = score > high_score
    if new_high_score:
        high_score = score
        with open(HIGH_SCORE_FILE, 'w') as f: f.write(str(score))
    
    play_again_button = pygame.Rect(SCREEN_WIDTH/2 - 150, SCREEN_HEIGHT * 3 / 4 - 25, 120, 50)
    exit_button = pygame.Rect(SCREEN_WIDTH/2 + 30, SCREEN_HEIGHT * 3 / 4 - 25, 120, 50)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        screen.fill(BLACK)
        draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5)
        if new_high_score: draw_text(screen, "New High Score!", 26, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3, GREEN)
        
        draw_text(screen, f"Score: {score}", 28, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50)
        draw_text(screen, f"High Score: {high_score}", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 15)

        if create_button(screen, play_again_button, "Play Again", BLACK, GREEN, (144, 238, 144)): return
        if create_button(screen, exit_button, "Exit", WHITE, RED, (255, 105, 97)): pygame.quit(); sys.exit()
        pygame.display.flip()

# --- Main Game Loop ---
def game_loop(screen, clock):
    global game_mode
    all_sprites = pygame.sprite.Group()
    falling_objects = pygame.sprite.Group()
    player = Catcher(game_mode)
    all_sprites.add(player)
    
    score = 0
    
    running = True
    global happy_start_time
    mode_change_time = None
    mode_duration = 0
    
    while running:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        # --- Dynamic Difficulty Logic ---
        # Check if the special mode timer has expired
        if game_mode != MODE_NORMAL and time.time() - mode_change_time > mode_duration:
            game_mode = MODE_NORMAL
            all_sprites.empty()
            falling_objects.empty()
            player = Catcher(game_mode)
            all_sprites.add(player)
            mode_change_time = None
            mode_duration = 0

        # Check for mode change condition only in normal mode
        if game_mode == MODE_NORMAL:
            if current_emotion == "happy":
                if happy_start_time is None:
                    happy_start_time = time.time()
                elif time.time() - happy_start_time > 2:
                    # Randomly choose a new mode after 2 seconds of being happy
                    new_mode = random.choice([MODE_TOP_DOWN, MODE_SIDE_TO_SIDE])
                    game_mode = new_mode
                    mode_change_time = time.time()
                    mode_duration = random.uniform(5, 7)
                    
                    # Reinitialize sprites for the new mode
                    all_sprites.empty()
                    falling_objects.empty()
                    player = Catcher(game_mode)
                    all_sprites.add(player)
            else:
                happy_start_time = None

        # Determine object spawn properties based on emotion and mode
        object_speed = random.randint(4, 8)
        obj_type_to_spawn = random.choices(["smile", "frown"], weights=[0.6, 0.4], k=1)[0]
        current_interval = EMOTION_INTERVAL

        if current_emotion == "happy" and game_mode == MODE_NORMAL:
            # Increase difficulty in normal mode when happy
            object_speed = random.randint(8, 12)
            obj_type_to_spawn = random.choices(["smile", "frown"], weights=[0.2, 0.8], k=1)[0]
            current_interval = 15
        elif current_emotion in ["angry", "sad", "disgust", "fear"]:
            obj_type_to_spawn = random.choices(["smile", "frown"], weights=[0.1, 0.9], k=1)[0]
        
        # Spawn objects based on the determined properties
        global emotion_timer
        emotion_timer += 1
        
        if emotion_timer >= current_interval:
            new_obj = FallingObject(obj_type_to_spawn, game_mode, object_speed)
            all_sprites.add(new_obj)
            falling_objects.add(new_obj)
            emotion_timer = 0
            
        all_sprites.update()
        
        collisions = pygame.sprite.spritecollide(player, falling_objects, True)
        for obj in collisions:
            if obj.obj_type == "smile":
                score += 1
            else:
                running = False
                
        screen.fill(BLACK)
        all_sprites.draw(screen)
        
        draw_text(screen, f"Score: {score}", 24, SCREEN_WIDTH / 2, 10)
        
        if game_mode != MODE_NORMAL:
            draw_text(screen, f"MODE: {game_mode.replace('_', ' ').upper()}", 32, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, BLUE)
            if mode_change_time:
                remaining_time = round(mode_duration - (time.time() - mode_change_time), 1)
                draw_text(screen, f"Time Remaining: {remaining_time}s", 20, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40, WHITE)

        if webcam_frame is not None:
            webcam_surface = pygame.surfarray.make_surface(webcam_frame.swapaxes(0, 1))
            screen.blit(webcam_surface, (SCREEN_WIDTH - WEBCAM_VIEW_SIZE[0] - 10, 10))
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - WEBCAM_VIEW_SIZE[0] - 10, 10, WEBCAM_VIEW_SIZE[0], WEBCAM_VIEW_SIZE[1]), 2)
            
            emotion_text = f"Emotion: {current_emotion}"
            text_x = SCREEN_WIDTH - WEBCAM_VIEW_SIZE[0] / 2 - 10
            text_y = 10 + WEBCAM_VIEW_SIZE[1] + 5
            draw_text(screen, emotion_text, 16, text_x, text_y, WHITE)
            
        pygame.display.flip()
        
    return score

def main():
    global stop_thread
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Catch the Smile")
    clock = pygame.time.Clock()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    analysis_thread = threading.Thread(target=emotion_analysis_thread, args=(cap,), daemon=True)
    analysis_thread.start()

    try:
        while True:
            show_menu(screen)
            score = game_loop(screen, clock)
            show_game_over_screen(screen, score)
    finally:
        stop_thread = True
        analysis_thread.join(timeout=3)
        cap.release()
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    main()
