import pygame
import sys
import random
import cv2
from deepface import DeepFace
import threading
import time
import numpy as np


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CATCHER_WIDTH = 100
CATCHER_HEIGHT = 20
OBJECT_SIZE = 30
HIGH_SCORE_FILE = "highscore_catch_the_smile.txt"
WEBCAM_VIEW_SIZE = (160, 120)


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DARK_YELLOW = (255, 200, 0)
BROWN = (139, 69, 19)


MODE_NORMAL = "normal"
MODE_TOP_DOWN = "top_down"
MODE_SIDE_TO_SIDE = "side_to_side"


current_emotion_player1 = "neutral"
current_emotion_player2 = "neutral"
webcam_frame_player1 = None
webcam_frame_player2 = None
stop_thread = False
emotion_timer = 0
EMOTION_INTERVAL = 30
happy_start_time_player1 = None
happy_start_time_player2 = None
game_mode_player1 = MODE_NORMAL
game_mode_player2 = MODE_NORMAL
mode_change_timer_player1 = None
mode_change_timer_player2 = None


def emotion_analysis_thread(cap):
    
    global current_emotion_player1, current_emotion_player2, webcam_frame_player1, webcam_frame_player2, stop_thread
    
    while not stop_thread:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        try:
            
            h, w, _ = rgb_frame.shape
            
            
            left_half_analysis = rgb_frame[:, :w//2]
            right_half_analysis = rgb_frame[:, w//2:]
            
            
            analysis1 = DeepFace.analyze(
                left_half_analysis, 
                actions=['emotion'], 
                enforce_detection=False,
                detector_backend='opencv'
            )
            current_emotion_player1 = analysis1[0]['dominant_emotion'] if isinstance(analysis1, list) and len(analysis1) > 0 else "no face"

            
            analysis2 = DeepFace.analyze(
                right_half_analysis, 
                actions=['emotion'], 
                enforce_detection=False,
                detector_backend='opencv'
            )
            current_emotion_player2 = analysis2[0]['dominant_emotion'] if isinstance(analysis2, list) and len(analysis2) > 0 else "no face"

        except Exception as e:
            current_emotion_player1 = "no face"
            current_emotion_player2 = "no face"

        
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        
        display_frame_player1 = cv2.resize(frame[:, w//2:], WEBCAM_VIEW_SIZE)
        display_frame_player2 = cv2.resize(frame[:, :w//2], WEBCAM_VIEW_SIZE)
        
        webcam_frame_player1 = cv2.cvtColor(display_frame_player1, cv2.COLOR_BGR2RGB)
        webcam_frame_player2 = cv2.cvtColor(display_frame_player2, cv2.COLOR_BGR2RGB)
        
        time.sleep(0.25)


class Catcher(pygame.sprite.Sprite):
    def __init__(self, mode, player_id):
        super().__init__()
        self.mode = mode
        self.player_id = player_id
        self.image = pygame.Surface([CATCHER_WIDTH, CATCHER_HEIGHT])
        self.image.fill(BROWN)
        self.speed = 10
        
        if self.mode == MODE_NORMAL:
            if self.player_id == 1:
                self.rect = self.image.get_rect(centerx=SCREEN_WIDTH / 4, bottom=SCREEN_HEIGHT - 10)
            else:
                self.rect = self.image.get_rect(centerx=SCREEN_WIDTH * 3 / 4, bottom=SCREEN_HEIGHT - 10)
        elif self.mode == MODE_TOP_DOWN:
            if self.player_id == 1:
                self.rect = self.image.get_rect(centerx=SCREEN_WIDTH / 4, top=10)
            else:
                self.rect = self.image.get_rect(centerx=SCREEN_WIDTH * 3 / 4, top=10)
        elif self.mode == MODE_SIDE_TO_SIDE:
            if self.player_id == 1:
                self.rect = self.image.get_rect(centery=SCREEN_HEIGHT / 2, left=10)
            else:
                self.rect = self.image.get_rect(centery=SCREEN_HEIGHT / 2, right=SCREEN_WIDTH - 10)
            self.image = pygame.transform.rotate(self.image, 90)
            
    def update(self):
        keys = pygame.key.get_pressed()
        
        if self.player_id == 1:
            if self.mode == MODE_NORMAL or self.mode == MODE_TOP_DOWN:
                if keys[pygame.K_a] and self.rect.left > 0:
                    self.rect.x -= self.speed
                if keys[pygame.K_d] and self.rect.right < SCREEN_WIDTH / 2: 
                    self.rect.x += self.speed
            elif self.mode == MODE_SIDE_TO_SIDE:
                if keys[pygame.K_w] and self.rect.top > 0:
                    self.rect.y -= self.speed
                if keys[pygame.K_s] and self.rect.bottom < SCREEN_HEIGHT:
                    self.rect.y += self.speed
        
        elif self.player_id == 2:
            if self.mode == MODE_NORMAL or self.mode == MODE_TOP_DOWN:
                if keys[pygame.K_LEFT] and self.rect.left > SCREEN_WIDTH / 2: 
                    self.rect.x -= self.speed
                if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
                    self.rect.x += self.speed
            elif self.mode == MODE_SIDE_TO_SIDE:
                if keys[pygame.K_UP] and self.rect.top > 0:
                    self.rect.y -= self.speed
                if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
                    self.rect.y += self.speed

        global current_emotion_player1, current_emotion_player2
        current_emotion = current_emotion_player1 if self.player_id == 1 else current_emotion_player2
        
        if current_emotion == "happy":
            new_dim = 60
        else:
            new_dim = 100
        
        if self.mode == MODE_SIDE_TO_SIDE:
            if self.rect.height != new_dim:
                self.image = pygame.Surface([CATCHER_HEIGHT, new_dim])
                self.image.fill(BROWN)
                self.rect = self.image.get_rect(centery=self.rect.centery, left=self.rect.left)
        else:
            if self.rect.width != new_dim:
                self.image = pygame.Surface([new_dim, CATCHER_HEIGHT])
                self.image.fill(BROWN)
                self.rect = self.image.get_rect(centerx=self.rect.centerx, bottom=self.rect.bottom)


class FallingObject(pygame.sprite.Sprite):
    def __init__(self, obj_type, mode, speed, player_side):
        super().__init__()
        self.obj_type = obj_type
        self.mode = mode
        self.image = pygame.Surface([OBJECT_SIZE, OBJECT_SIZE], pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))

        if self.obj_type == "smile":
            color = GREEN
            pygame.draw.circle(self.image, color, (OBJECT_SIZE / 2, OBJECT_SIZE / 2), OBJECT_SIZE / 2)
            pygame.draw.circle(self.image, BLACK, (OBJECT_SIZE * 0.35, OBJECT_SIZE * 0.35), OBJECT_SIZE * 0.1)
            pygame.draw.circle(self.image, BLACK, (OBJECT_SIZE * 0.65, OBJECT_SIZE * 0.35), OBJECT_SIZE * 0.1)
        else:
            color = RED
            pygame.draw.circle(self.image, color, (OBJECT_SIZE / 2, OBJECT_SIZE / 2), OBJECT_SIZE / 2)
            pygame.draw.circle(self.image, BLACK, (OBJECT_SIZE * 0.35, OBJECT_SIZE * 0.35), OBJECT_SIZE * 0.1)
            pygame.draw.circle(self.image, BLACK, (OBJECT_SIZE * 0.65, OBJECT_SIZE * 0.35), OBJECT_SIZE * 0.1)
        
        self.speed = speed
        
        
        if player_side == 1:
            x_range = (0, SCREEN_WIDTH / 2)
        else:
            x_range = (SCREEN_WIDTH / 2, SCREEN_WIDTH)

        if self.mode == MODE_NORMAL:
            self.rect = self.image.get_rect(centerx=random.randint(int(x_range[0]) + OBJECT_SIZE, int(x_range[1]) - OBJECT_SIZE), top=0)
        elif self.mode == MODE_TOP_DOWN:
            self.rect = self.image.get_rect(centerx=random.randint(int(x_range[0]) + OBJECT_SIZE, int(x_range[1]) - OBJECT_SIZE), bottom=SCREEN_HEIGHT)
        elif self.mode == MODE_SIDE_TO_SIDE:
            if player_side == 1:
                
                self.rect = self.image.get_rect(centery=random.randint(OBJECT_SIZE, SCREEN_HEIGHT - OBJECT_SIZE), right=SCREEN_WIDTH / 2)
                self.speed = -self.speed
            else:
                
                self.rect = self.image.get_rect(centery=random.randint(OBJECT_SIZE, SCREEN_HEIGHT - OBJECT_SIZE), left=SCREEN_WIDTH / 2)


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

def show_start_menu(screen):
    title_font = pygame.font.Font(pygame.font.match_font('arial'), 64)
    title_surface = title_font.render("Catch the Smile", True, WHITE)
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    
    multiplayer_button = pygame.Rect(SCREEN_WIDTH / 2 - 50, 350, 100, 50)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(BLACK)
        screen.blit(title_surface, title_rect)
        draw_text(screen, "A dynamic difficulty game", 22, SCREEN_WIDTH/2, SCREEN_HEIGHT / 3 + 20)
        
        if create_button(screen, multiplayer_button, "Play", BLACK, RED, (255, 105, 97)):
            return "multiplayer"

        pygame.display.flip()

def show_game_over_screen(screen, score1, score2):
    high_score = 0
    try:
        with open(HIGH_SCORE_FILE, 'r') as f: high_score = int(f.read())
    except (IOError, ValueError): pass
    
    if score1 > score2:
        winner_score = score1
        winner_text = "Player 1 is the Winner!"
    elif score2 > score1:
        winner_score = score2
        winner_text = "Player 2 is the Winner!"
    else:
        winner_score = score1
        winner_text = "It's a Tie!"

    is_new_high_score = winner_score > high_score
    if is_new_high_score:
        high_score = winner_score
        with open(HIGH_SCORE_FILE, 'w') as f: f.write(str(winner_score))
    
    play_again_button = pygame.Rect(SCREEN_WIDTH/2 - 150, SCREEN_HEIGHT * 3 / 4 - 25, 120, 50)
    exit_button = pygame.Rect(SCREEN_WIDTH/2 + 30, SCREEN_HEIGHT * 3 / 4 - 25, 120, 50)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        
        screen.fill(BLACK)
        draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5)
        
        if is_new_high_score: 
            draw_text(screen, "New High Score!", 26, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3, GREEN)

        draw_text(screen, winner_text, 32, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80, GREEN)
        
        draw_text(screen, f"Player 1 Score: {score1}", 28, SCREEN_WIDTH / 4, SCREEN_HEIGHT / 2 - 20)
        draw_text(screen, f"Player 2 Score: {score2}", 28, SCREEN_WIDTH * 3 / 4, SCREEN_HEIGHT / 2 - 20)
        
        draw_text(screen, f"High Score: {high_score}", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20)

        if create_button(screen, play_again_button, "Play Again", BLACK, GREEN, (144, 238, 144)): return
        if create_button(screen, exit_button, "Exit", WHITE, RED, (255, 105, 97)): pygame.quit(); sys.exit()
        pygame.display.flip()

def game_loop_multiplayer(screen, clock):
    global game_mode_player1, game_mode_player2, happy_start_time_player1, happy_start_time_player2, mode_change_timer_player1, mode_change_timer_player2
    
    all_sprites = pygame.sprite.Group()
    falling_objects_p1 = pygame.sprite.Group()
    falling_objects_p2 = pygame.sprite.Group()
    
    player1 = Catcher(MODE_NORMAL, 1)
    player2 = Catcher(MODE_NORMAL, 2)
    
    all_sprites.add(player1, player2)
    
    score1 = 0
    score2 = 0
    
    player_1_is_out = False
    player_2_is_out = False
    
    start_time = time.time()
    
    while True: 
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                return score1, score2
        
        if player_1_is_out and player_2_is_out:
            return score1, score2
            
        if not player_1_is_out:
            
            if current_emotion_player1 == "happy":
                if game_mode_player1 == MODE_NORMAL:
                    if happy_start_time_player1 is None:
                        happy_start_time_player1 = time.time()
                    elif time.time() - happy_start_time_player1 > 2:
                        new_mode = random.choice([MODE_TOP_DOWN, MODE_SIDE_TO_SIDE])
                        game_mode_player1 = new_mode
                        mode_change_timer_player1 = time.time()
                        all_sprites.remove(player1)
                        player1 = Catcher(game_mode_player1, 1)
                        all_sprites.add(player1)
                        happy_start_time_player1 = None
            else:
                happy_start_time_player1 = None
            
            
            if game_mode_player1 != MODE_NORMAL and mode_change_timer_player1 is not None:
                if time.time() - mode_change_timer_player1 > 7:
                    game_mode_player1 = MODE_NORMAL
                    all_sprites.remove(player1)
                    player1 = Catcher(game_mode_player1, 1)
                    all_sprites.add(player1)
                    mode_change_timer_player1 = None

        if not player_2_is_out:
            
            if current_emotion_player2 == "happy":
                if game_mode_player2 == MODE_NORMAL:
                    if happy_start_time_player2 is None:
                        happy_start_time_player2 = time.time()
                    elif time.time() - happy_start_time_player2 > 2:
                        new_mode = random.choice([MODE_TOP_DOWN, MODE_SIDE_TO_SIDE])
                        game_mode_player2 = new_mode
                        mode_change_timer_player2 = time.time()
                        all_sprites.remove(player2)
                        player2 = Catcher(game_mode_player2, 2)
                        all_sprites.add(player2)
                        happy_start_time_player2 = None
            else:
                happy_start_time_player2 = None
                
            
            if game_mode_player2 != MODE_NORMAL and mode_change_timer_player2 is not None:
                if time.time() - mode_change_timer_player2 > 7:
                    game_mode_player2 = MODE_NORMAL
                    all_sprites.remove(player2)
                    player2 = Catcher(game_mode_player2, 2)
                    all_sprites.add(player2)
                    mode_change_timer_player2 = None
        
        global emotion_timer
        emotion_timer += 1
        if emotion_timer >= EMOTION_INTERVAL:
            obj_type_to_spawn = random.choices(["smile", "frown"], weights=[0.6, 0.4], k=1)[0]
            object_speed = random.randint(4, 8)
            
            
            if not player_1_is_out:
                new_obj_p1 = FallingObject(obj_type_to_spawn, game_mode_player1, object_speed, 1)
                all_sprites.add(new_obj_p1)
                falling_objects_p1.add(new_obj_p1)
            
            if not player_2_is_out:
                new_obj_p2 = FallingObject(obj_type_to_spawn, game_mode_player2, object_speed, 2)
                all_sprites.add(new_obj_p2)
                falling_objects_p2.add(new_obj_p2)

            emotion_timer = 0
            
        all_sprites.update()
        
        collisions1 = pygame.sprite.spritecollide(player1, falling_objects_p1, True)
        if not player_1_is_out:
            for obj in collisions1:
                if obj.obj_type == "smile":
                    score1 += 1
                else:
                    player_1_is_out = True
                    all_sprites.remove(player1)
        
        collisions2 = pygame.sprite.spritecollide(player2, falling_objects_p2, True)
        if not player_2_is_out:
            for obj in collisions2:
                if obj.obj_type == "smile":
                    score2 += 1
                else:
                    player_2_is_out = True
                    all_sprites.remove(player2)
        
        pygame.draw.rect(screen, YELLOW, (0, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
        pygame.draw.rect(screen, DARK_YELLOW, (SCREEN_WIDTH // 2, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))

        
        pygame.draw.line(screen, WHITE, (SCREEN_WIDTH / 2, 0), (SCREEN_WIDTH / 2, SCREEN_HEIGHT), 2)
        
        all_sprites.draw(screen)
        
        
        if not player_1_is_out:
            draw_text(screen, f"Player 1 Score: {score1}", 24, SCREEN_WIDTH / 4, 10)
        else:
            draw_text(screen, "PLAYER 1 OUT!", 24, SCREEN_WIDTH / 4, 10, RED)
            
        if not player_2_is_out:
            draw_text(screen, f"Player 2 Score: {score2}", 24, SCREEN_WIDTH * 3 / 4, 10)
        else:
            draw_text(screen, "PLAYER 2 OUT!", 24, SCREEN_WIDTH * 3 / 4, 10, RED)
        
        draw_text(screen, f"Time: {int(time.time() - start_time)}", 30, SCREEN_WIDTH / 2, 10)
        
        if webcam_frame_player1 is not None:
            webcam_surface1 = pygame.surfarray.make_surface(webcam_frame_player1.swapaxes(0, 1))
            screen.blit(webcam_surface1, (10, 10))
            pygame.draw.rect(screen, WHITE, (10, 10, WEBCAM_VIEW_SIZE[0], WEBCAM_VIEW_SIZE[1]), 2)
            draw_text(screen, f"P1 Emotion: {current_emotion_player1}", 16, 10 + WEBCAM_VIEW_SIZE[0] / 2, 10 + WEBCAM_VIEW_SIZE[1] + 5, WHITE)
            if happy_start_time_player1 is not None:
                draw_text(screen, "you are happy!", 20, 10 + WEBCAM_VIEW_SIZE[0] / 2, 10 + WEBCAM_VIEW_SIZE[1] + 30, GREEN)
            
            webcam_surface2 = pygame.surfarray.make_surface(webcam_frame_player2.swapaxes(0, 1))
            screen.blit(webcam_surface2, (SCREEN_WIDTH - WEBCAM_VIEW_SIZE[0] - 10, 10))
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - WEBCAM_VIEW_SIZE[0] - 10, 10, WEBCAM_VIEW_SIZE[0], WEBCAM_VIEW_SIZE[1]), 2)
            draw_text(screen, f"P2 Emotion: {current_emotion_player2}", 16, SCREEN_WIDTH - WEBCAM_VIEW_SIZE[0] / 2 - 10, 10 + WEBCAM_VIEW_SIZE[1] + 5, WHITE)
            if happy_start_time_player2 is not None:
                draw_text(screen, "you are happy!", 20, SCREEN_WIDTH - WEBCAM_VIEW_SIZE[0] / 2 - 10, 10 + WEBCAM_VIEW_SIZE[1] + 30, GREEN)

        pygame.display.flip()
    
    return score1, score2
    
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
            choice = show_start_menu(screen)
            score1, score2 = game_loop_multiplayer(screen, clock)
            show_game_over_screen(screen, score1, score2)
    finally:
        stop_thread = True
        analysis_thread.join(timeout=3)
        cap.release()
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    main()
