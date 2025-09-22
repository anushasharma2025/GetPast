import pygame
import random
import sys
import cv2
import numpy as np
from deepface import DeepFace

swiddth = 1000
sheight = 600
mint = (240, 253, 244)
dgreen = (22, 101, 52)
lgreen = (101, 163, 13)
yell = (254, 240, 138)
red = (239, 68, 68)
white = (255, 255, 255)
blood = (139, 0, 0)
gray = (64, 64, 64)
blue = (135, 206, 235)
brown = (139, 69, 19)
black = (0, 0, 0)
lgbg = (204, 255, 204)
dgbg = (153, 204, 153)
pink = (255, 192, 203)

csize = 15
zsize = 30
maxcrop = 10 
maxzom = 10 
minzom = 4
zomspeedhard = 6
zomspeedeasy = 5
zomspeedHARD = 7
happyvol = 0.5
normalvol = 1.0
sprite_speed_base = 3
sprite_speed_multiplier = 1.5

cropspawnhappy = 400
crop_spawnnormal = 600
crop_spawnfrustrated = 1500
hmetermax = 100
hmetergain = 1.0
hmeterloss = 0.2
frenzytimedur = 5000
frustriggdelay = 1000
frusdur = 3000

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((swiddth, sheight))
pygame.display.set_caption("Rot and Reap")
clock = pygame.time.Clock()

cap = cv2.VideoCapture(0)

try:
    dissonant_font_large = pygame.font.Font("plasma-drip/plasdrip.ttf", 64)
    dissonant_font_medium = pygame.font.Font("plasma-drip/plasdrip.ttf", 36)
except pygame.error:
    dissonant_font_large = pygame.font.Font(None, 64)
    dissonant_font_medium = pygame.font.Font(None, 36)

lfont = pygame.font.Font(None, 72)
mfont = pygame.font.Font(None, 36)
sfont = pygame.font.Font(None, 24)

try:
    pingping = pygame.mixer.Sound('cheerful-ping-356011.mp3')
except pygame.error:
    pingping = None
try:
    boo = pygame.mixer.Sound('scary-horror-theme-song-382733.mp3')
except pygame.error:
    boo = None

try:
    plant_image = pygame.image.load('sprout-removebg-preview.png').convert_alpha()
    plant_size = 50
    plant_image = pygame.transform.scale(plant_image, (plant_size, plant_size))
except pygame.error:
    plant_image = None
try:
    zombie_image = pygame.image.load('zom.png').convert_alpha()
    zombie_image = pygame.transform.scale(zombie_image, (zsize, zsize))
except pygame.error as e:
    zombie_image = None

try:
    dinoblue_image = pygame.image.load('blue.png').convert_alpha()
    dinoblue_size = 70
    dinoblue_image = pygame.transform.scale(dinoblue_image, (dinoblue_size, dinoblue_size))
    rdinoblue_size = 220
    rdinoblue_image = pygame.transform.scale(dinoblue_image, (rdinoblue_size, rdinoblue_size))
except pygame.error:
    dinoblue_image = None

try:
    deeno_image = pygame.image.load('pink.png').convert_alpha()
    deeno_size = 70
    deeno_image = pygame.transform.scale(deeno_image, (deeno_size, deeno_size))
    rdeeno_size = 200
    rdeeno_image = pygame.transform.scale(deeno_image, (rdeeno_size, rdeeno_size))
except pygame.error:
    deeno_image = None

P1_START_POS = (swiddth * 3 // 4, sheight // 2)
P2_START_POS = (swiddth // 4, sheight // 2)
PLAYER_SPEED = 7
FREEZE_DURATION = 3000
WINNING_SCORE = 10

def makecrop():
    webcam_rect_1 = pygame.Rect(20, sheight - 170, 200, 150)
    webcam_rect_2 = pygame.Rect(swiddth - 220, sheight - 170, 200, 150)
    while True:
        x = random.randrange(plant_size // 2, swiddth - plant_size // 2)
        y = random.randrange(plant_size // 2, sheight - plant_size // 2)
        crop_rect = pygame.Rect(x - plant_size // 2, y - plant_size // 2, plant_size, plant_size)
        if not crop_rect.colliderect(webcam_rect_1) and not crop_rect.colliderect(webcam_rect_2):
            break
    vx = random.choice([-1, 1]) * random.uniform(sprite_speed_base, sprite_speed_base * sprite_speed_multiplier)
    vy = random.choice([-1, 1]) * random.uniform(sprite_speed_base, sprite_speed_base * sprite_speed_multiplier)
    return {
        'x': x,
        'y': y,
        'vx': vx,
        'vy': vy,
        'rect': crop_rect,
        'is_harvested': False
    }

def makezom(num):
    zombies = []
    for _ in range(num):
        x = random.randrange(zsize, swiddth - zsize)
        y = random.randrange(zsize, sheight - zsize)
        vx = random.choice([-1, 1]) * random.uniform(sprite_speed_base, sprite_speed_base * sprite_speed_multiplier)
        vy = random.choice([-1, 1]) * random.uniform(sprite_speed_base, sprite_speed_base * sprite_speed_multiplier)
        zombies.append({
            'x': x,
            'y': y,
            'vx': vx,
            'vy': vy,
            'rect': pygame.Rect(x - zsize, y - zsize, zsize, zsize)
        })
    return zombies

def draw_background():
    screen.fill(lgbg)
    pygame.draw.rect(screen, dgbg, (0, sheight // 2, swiddth, sheight // 2))
    pygame.draw.circle(screen, yell, (700, 100), 50)

def draw_players(p1_pos, p2_pos):
    if dinoblue_image:
        screen.blit(dinoblue_image, (p1_pos[0] - dinoblue_size // 2, p1_pos[1] - dinoblue_size // 2))
    else:
        pygame.draw.circle(screen, blue, p1_pos, dinoblue_size // 2)
        
    if deeno_image:
        screen.blit(deeno_image, (p2_pos[0] - deeno_size // 2, p2_pos[1] - deeno_size // 2))
    else:
        pygame.draw.circle(screen, red, p2_pos, deeno_size // 2)

def draw_crops(crops):
    for crop in crops:
        if not crop['is_harvested']:
            if plant_image:
                screen.blit(plant_image, (crop['x'] - plant_size // 2, crop['y'] - plant_size // 2))
            else:
                pygame.draw.circle(screen, lgreen, (int(crop['x']), int(crop['y'])), csize)

def draw_zombies(zombies):
    for zombie in zombies:
        if zombie_image:
            screen.blit(zombie_image, (zombie['x'] - zsize // 2, zombie['y'] - zsize // 2))
        else:
            pygame.draw.circle(screen, gray, (int(zombie['x']), int(zombie['y'])), zsize // 2)
            pygame.draw.circle(screen, red, (int(zombie['x']), int(zombie['y'])), zsize // 4)

def draw_ui(score1, score2, message=""):
    score1_text = sfont.render(f"P1 Score: {score1}", True, dgreen)
    score1_rect = score1_text.get_rect(topright=(swiddth - 20, 20))
    screen.blit(score1_text, score1_rect)

    score2_text = sfont.render(f"P2 Score: {score2}", True, dgreen)
    screen.blit(score2_text, (20, 20))

    if message:
        message_text = lfont.render(message, True, dgreen)
        text_rect = message_text.get_rect(center=(swiddth // 2, sheight // 2))
        screen.blit(message_text, text_rect)

def draw_happiness_meter(meter_value, x, y):
    meter_rect = pygame.Rect(x, y, 200, 20)
    meter_bg_rect = pygame.Rect(meter_rect.x, meter_rect.y, meter_rect.width, meter_rect.height)
    meter_fill_rect = pygame.Rect(meter_rect.x, meter_rect.y, int(meter_rect.width * (meter_value / hmetermax)), meter_rect.height)
    
    pygame.draw.rect(screen, gray, meter_bg_rect, 2)
    pygame.draw.rect(screen, lgreen, meter_fill_rect)
    
    meter_text = sfont.render("Happiness", True, dgreen)
    screen.blit(meter_text, (meter_rect.x, meter_rect.y + 25))

def main():
    crops = []
    zombies = []
    
    p1_pos = list(P1_START_POS)
    p2_pos = list(P2_START_POS)
    p1_score = 0
    p2_score = 0
    
    p1_happiness_meter = 0
    p2_happiness_meter = 0
    
    p1_frozen = False
    p2_frozen = False
    p1_freeze_end_time = 0
    p2_freeze_end_time = 0

    game_over = False
    message = "Click to Start!"
    
    game_state = "intro_1"
    intro_start_time = pygame.time.get_ticks()

    if boo:
        boo.play(-1)

    CROP_SPAWN_EVENT = pygame.USEREVENT + 1
    ZOMBIE_SPAWN_EVENT = pygame.USEREVENT + 2
    
    pygame.time.set_timer(CROP_SPAWN_EVENT, crop_spawnnormal)
    pygame.time.set_timer(ZOMBIE_SPAWN_EVENT, 1000)

    p1_difficulty = "Normal"
    p2_difficulty = "Normal"

    restart_button_rect = pygame.Rect(0, 0, 0, 0)
    exit_button_rect = pygame.Rect(0, 0, 0, 0)
    level_buttons = []

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        draw_background()
        now = pygame.time.get_ticks()
        webcam_rect_1 = pygame.Rect(20, sheight - 170, 200, 150)
        webcam_rect_2 = pygame.Rect(swiddth - 220, sheight - 170, 200, 150)
        webcam_frame_scaled = cv2.resize(frame, (webcam_rect_1.width * 2, webcam_rect_1.height))
        webcam_frame_right_half = webcam_frame_scaled[:, webcam_frame_scaled.shape[1]//2:]
        webcam_frame_left_half = webcam_frame_scaled[:, :webcam_frame_scaled.shape[1]//2]
        try:
            analysis_p2 = DeepFace.analyze(webcam_frame_left_half, actions=['emotion'], enforce_detection=False, silent=True)
            if analysis_p2:
                dominant_emotion_p2 = analysis_p2[0]['dominant_emotion']
                if dominant_emotion_p2 in ['happy', 'surprise']:
                    p2_difficulty = "Happy"
                elif dominant_emotion_p2 == 'neutral':
                    p2_difficulty = "Normal"
                else:
                    p2_difficulty = "Frustrated"
            else:
                p2_difficulty = "No Face"
        except Exception as e:
            p2_difficulty = "No Face"

        try:
            analysis_p1 = DeepFace.analyze(webcam_frame_right_half, actions=['emotion'], enforce_detection=False, silent=True)
            if analysis_p1:
                dominant_emotion_p1 = analysis_p1[0]['dominant_emotion']
                if dominant_emotion_p1 in ['happy', 'surprise']:
                    p1_difficulty = "Happy"
                elif dominant_emotion_p1 == 'neutral':
                    p1_difficulty = "Normal"
                else:
                    p1_difficulty = "Frustrated"
            else:
                p1_difficulty = "No Face"
        except Exception as e:
            p1_difficulty = "No Face"

        if now > p1_freeze_end_time:
            p1_frozen = False
        if now > p2_freeze_end_time:
            p2_frozen = False
        
        if game_state.startswith("intro"):
            screen.fill(black)
            messages = {
                "intro_1": ("It's not a question of if...", 3000, dissonant_font_medium),
                "intro_2": ("...but a matter of when.", 1000, dissonant_font_medium),
                "intro_3": ("The zombie apocalypse is here.\nYour only hope is the last thing you'd do.", 3000, dissonant_font_medium),
                "intro_4": ("Smile.", 2000, dissonant_font_large)
            }
            
            current_message, duration, current_font = messages[game_state]
            if "\n" in current_message:
                lines = current_message.split('\n')
                y_offset = -20
                for line in lines:
                    message_text = current_font.render(line, True, blood)
                    text_rect = message_text.get_rect(center=(swiddth // 2, sheight // 2 + y_offset))
                    screen.blit(message_text, text_rect)
                    y_offset += message_text.get_height() + 10
            else:
                message_text = current_font.render(current_message, True, blood)
                text_rect = message_text.get_rect(center=(swiddth // 2, sheight // 2))
                screen.blit(message_text, text_rect)

            if now - intro_start_time > duration:
                if game_state == "intro_1": game_state = "intro_2"
                elif game_state == "intro_2": game_state = "intro_3"
                elif game_state == "intro_3": game_state = "intro_4"
                elif game_state == "intro_4": 
                    if boo: boo.stop()
                    game_state = "level_select"
                intro_start_time = now

        elif game_state == "level_select":
            screen.fill(black)
            title_text = dissonant_font_large.render("Select a Level", True, blood)
            title_rect = title_text.get_rect(center=(swiddth // 2, 100))
            screen.blit(title_text, title_rect)

            level_button_width = 200
            level_button_height = 60
            button_spacing = 50
            button_y_start = sheight // 2 - (level_button_height + button_spacing)
            
            level_buttons = []

            level1_rect = pygame.Rect(swiddth // 2 - level_button_width // 2, button_y_start, level_button_width, level_button_height)
            pygame.draw.rect(screen, gray, level1_rect)
            level1_text = dissonant_font_medium.render("Level 1", True, blood)
            level1_text_rect = level1_text.get_rect(center=level1_rect.center)
            screen.blit(level1_text, level1_text_rect)
            level_buttons.append(("Level 1", level1_rect))

            level2_rect = pygame.Rect(swiddth // 2 - level_button_width // 2, button_y_start + level_button_height + button_spacing, level_button_width, level_button_height)
            pygame.draw.rect(screen, gray, level2_rect)
            level2_text = dissonant_font_medium.render("Level 2", True, blood)
            level2_text_rect = level2_text.get_rect(center=level2_rect.center)
            screen.blit(level2_text, level2_text_rect)
            level_buttons.append(("Level 2", level2_rect))

            level3_rect = pygame.Rect(swiddth // 2 - level_button_width // 2, button_y_start + 2 * (level_button_height + button_spacing), level_button_width, level_button_height)
            pygame.draw.rect(screen, gray, level3_rect)
            level3_text = dissonant_font_medium.render("Level 3", True, blood)
            level3_text_rect = level3_text.get_rect(center=level3_rect.center)
            screen.blit(level3_text, level3_text_rect)
            level_buttons.append(("Level 3", level3_rect))

            if rdinoblue_image:
                rblue = pygame.transform.rotate(rdinoblue_image,15)
                dinoblue_rect = rblue.get_rect(bottomleft=(0,level2_rect.y-20))
                screen.blit(rblue,dinoblue_rect)
            if rdeeno_image:
                rpink = pygame.transform.rotate(rdeeno_image,-15)
                deeno_rect = rpink.get_rect(bottomright=(swiddth,level2_rect.y-20))
                screen.blit(rpink,deeno_rect)

        elif game_state == "rules":
            screen.fill(black)
            rules_title_text = lfont.render("Game Rules", True, white)
            rules_title_rect = rules_title_text.get_rect(center=(swiddth // 2, sheight // 2 - 150))
            screen.blit(rules_title_text, rules_title_rect)

            rules_text_p1 = mfont.render("Player 1: Collect plants. (Arrow Keys) - BLUE", True, blue)
            rules_text_p2 = mfont.render("Player 2: Collect zombies. (WASD Keys) - PINK", True, pink)
            rules_text_sabotage = mfont.render("Fill your happiness meter to freeze your opponent.", True, white)
            rules_text_score = mfont.render("First to " + str(WINNING_SCORE) + " points wins. Touching the wrong item reduces your score by 2.", True, white)

            screen.blit(rules_text_p1, (swiddth // 2 - rules_text_p1.get_width() // 2, sheight // 2 - 50))
            screen.blit(rules_text_p2, (swiddth // 2 - rules_text_p2.get_width() // 2, sheight // 2 + 0))
            screen.blit(rules_text_sabotage, (swiddth // 2 - rules_text_sabotage.get_width() // 2, sheight // 2 + 50))
            screen.blit(rules_text_score, (swiddth // 2 - rules_text_score.get_width() // 2, sheight // 2 + 100))

            continue_text = mfont.render("Click to Start!", True, white)
            continue_text_rect = continue_text.get_rect(center=(swiddth // 2, sheight // 2 + 150))
            screen.blit(continue_text, continue_text_rect)

        elif game_state == "playing":
            if p1_difficulty == "Happy":
                p1_happiness_meter = min(hmetermax, p1_happiness_meter + hmetergain)
            else:
                p1_happiness_meter = max(0, p1_happiness_meter - hmeterloss)
            
            if p2_difficulty == "Happy":
                p2_happiness_meter = min(hmetermax, p2_happiness_meter + hmetergain)
            else:
                p2_happiness_meter = max(0, p2_happiness_meter - hmeterloss)
            
            if p1_happiness_meter >= hmetermax and not p2_frozen:
                p2_frozen = True
                p2_freeze_end_time = now + FREEZE_DURATION
                p1_happiness_meter = 0
                
            if p2_happiness_meter >= hmetermax and not p1_frozen:
                p1_frozen = True
                p1_freeze_end_time = now + FREEZE_DURATION
                p2_happiness_meter = 0

            keys = pygame.key.get_pressed()
            
            if not p1_frozen:
                if keys[pygame.K_UP]: p1_pos[1] -= PLAYER_SPEED
                if keys[pygame.K_DOWN]: p1_pos[1] += PLAYER_SPEED
                if keys[pygame.K_LEFT]: p1_pos[0] -= PLAYER_SPEED
                if keys[pygame.K_RIGHT]: p1_pos[0] += PLAYER_SPEED
            
            if not p2_frozen:
                if keys[pygame.K_w]: p2_pos[1] -= PLAYER_SPEED
                if keys[pygame.K_s]: p2_pos[1] += PLAYER_SPEED
                if keys[pygame.K_a]: p2_pos[0] -= PLAYER_SPEED
                if keys[pygame.K_d]: p2_pos[0] += PLAYER_SPEED

            p1_pos[0] = max(dinoblue_size // 2, min(swiddth - dinoblue_size // 2, p1_pos[0]))
            p1_pos[1] = max(dinoblue_size // 2, min(sheight - dinoblue_size // 2, p1_pos[1]))
            p2_pos[0] = max(deeno_size // 2, min(swiddth - deeno_size // 2, p2_pos[0]))
            p2_pos[1] = max(deeno_size // 2, min(sheight - deeno_size // 2, p2_pos[1]))
            
            p1_rect = pygame.Rect(p1_pos[0] - dinoblue_size // 2, p1_pos[1] - dinoblue_size // 2, dinoblue_size, dinoblue_size)
            p2_rect = pygame.Rect(p2_pos[0] - deeno_size // 2, p2_pos[1] - deeno_size // 2, deeno_size, deeno_size)

            #zombie_speed = sprite_speed_base * sprite_speed_multiplier
            #crop_speed = sprite_speed_base * sprite_speed_multiplier
            
            for crop in crops:
                crop['x'] += crop['vx']
                crop['y'] += crop['vy']
                if crop['x'] <= csize or crop['x'] >= swiddth - csize: crop['vx'] *= -1
                if crop['y'] <= csize or crop['y'] >= sheight - csize: crop['vy'] *= -1
                crop['rect'].topleft = (int(crop['x']) - csize, int(crop['y']) - csize)
                
            for zombie in zombies:
                zombie['x'] += zombie['vx']
                zombie['y'] += zombie['vy']
                if zombie['x'] <= zsize // 2 or zombie['x'] >= swiddth - zsize // 2: zombie['vx'] *= -1
                if zombie['y'] <= zsize // 2 or zombie['y'] >= sheight - zsize // 2: zombie['vy'] *= -1
                zombie['rect'].topleft = (int(zombie['x']) - zsize // 2, int(zombie['y']) - zsize // 2)

            crops_to_remove = []
            for crop in crops:
                if not crop['is_harvested'] and p1_rect.colliderect(crop['rect']):
                    crop['is_harvested'] = True
                    p1_score += 1
                    crops_to_remove.append(crop)
                
                if not crop['is_harvested'] and p2_rect.colliderect(crop['rect']):
                    p2_score = max(0, p2_score - 2)
                    crops_to_remove.append(crop)
            
            zombies_to_remove = []
            for zombie in zombies:
                if p2_rect.colliderect(zombie['rect']):
                    p2_score += 1
                    zombies_to_remove.append(zombie)
                    
                if p1_rect.colliderect(zombie['rect']):
                    p1_score = max(0, p1_score - 2)
                    zombies_to_remove.append(zombie)
                    
            crops = [crop for crop in crops if crop not in crops_to_remove]
            zombies = [zom for zom in zombies if zom not in zombies_to_remove]

            draw_crops(crops)
            draw_zombies(zombies)
            draw_players(p1_pos, p2_pos)

            if p1_frozen:
                freeze_text = mfont.render("FROZEN!", True, blue)
                screen.blit(freeze_text, (p1_pos[0] - freeze_text.get_width() // 2, p1_pos[1] - dinoblue_size))
            if p2_frozen:
                freeze_text = mfont.render("FROZEN!", True, red)
                screen.blit(freeze_text, (p2_pos[0] - freeze_text.get_width() // 2, p2_pos[1] - deeno_size))

            draw_ui(p1_score, p2_score)
            draw_happiness_meter(p1_happiness_meter, 20, 80)
            draw_happiness_meter(p2_happiness_meter, swiddth - 220, 80)

            if p1_score >= WINNING_SCORE or p2_score >= WINNING_SCORE:
                game_state = "game_over"

        elif game_state == "game_over":
            screen.fill(black)
            title_text = lfont.render("Game Over", True, white)
            title_rect = title_text.get_rect(center=(swiddth // 2, 100))
            screen.blit(title_text, title_rect)

            winner_text = ""
            if p1_score >= WINNING_SCORE and p2_score >= WINNING_SCORE:
                winner_text = "It's a tie!"
            elif p1_score >= WINNING_SCORE:
                winner_text = "Player 1 Wins!"
            elif p2_score >= WINNING_SCORE:
                winner_text = "Player 2 Wins!"

            winner_render = mfont.render(winner_text, True, white)
            winner_rect = winner_render.get_rect(center=(swiddth // 2, sheight // 2 - 50))
            screen.blit(winner_render, winner_rect)

            score_text = mfont.render(f"P1 Score: {p1_score} | P2 Score: {p2_score}", True, white)
            score_rect = score_text.get_rect(center=(swiddth // 2, sheight // 2))
            screen.blit(score_text, score_rect)
            
            restart_button_rect = pygame.Rect(swiddth // 2 - 150, sheight // 2 + 50, 100, 40)
            exit_button_rect = pygame.Rect(swiddth // 2 + 50, sheight // 2 + 50, 100, 40)
            
            pygame.draw.rect(screen, dgreen, restart_button_rect)
            pygame.draw.rect(screen, dgreen, exit_button_rect)
            restart_text = sfont.render("Restart", True, white)
            exit_text = sfont.render("Exit", True, white)
            restart_text_rect = restart_text.get_rect(center=restart_button_rect.center)
            exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
            screen.blit(restart_text, restart_text_rect)
            screen.blit(exit_text, exit_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == "level_select":
                    if level1_rect.collidepoint(event.pos):
                        game_state = "rules"
                elif game_state == "rules":
                    continue_text_rect = mfont.render("Click to Start!", True, white).get_rect(center=(swiddth // 2, sheight // 2 + 150))
                    if continue_text_rect.collidepoint(event.pos):
                        game_state = "playing"
                        p1_score = 0
                        p2_score = 0
                        initial_count = 8
                        crops = [makecrop() for _ in range(initial_count)]
                        zombies = makezom(initial_count)
                        p1_happiness_meter = 0
                        p2_happiness_meter = 0
                        message = ""
                elif game_state == "game_over":
                    if restart_button_rect.collidepoint(event.pos):
                        game_state = "playing"
                        p1_pos = list(P1_START_POS)
                        p2_pos = list(P2_START_POS)
                        p1_score = 0
                        p2_score = 0
                        initial_count = 8
                        crops = [makecrop() for _ in range(initial_count)]
                        zombies = makezom(initial_count)
                        p1_happiness_meter = 0
                        p2_happiness_meter = 0
                        p1_frozen = False
                        p2_frozen = False
                    elif exit_button_rect.collidepoint(event.pos):
                        cap.release()
                        pygame.quit()
                        sys.exit()

            if event.type == CROP_SPAWN_EVENT and game_state == "playing":
                if len(crops) < maxcrop:
                    crops.append(makecrop())
            
            if event.type == ZOMBIE_SPAWN_EVENT and game_state == "playing":
                if len(zombies) < maxzom:
                    zombies.append(makezom(1)[0])

        webcam_frame_right_half_display = webcam_frame_scaled[:, webcam_frame_scaled.shape[1]//2:]
        webcam_frame_left_half_display = webcam_frame_scaled[:, :webcam_frame_scaled.shape[1]//2]

        frame_rgb_left = cv2.cvtColor(webcam_frame_left_half_display, cv2.COLOR_BGR2RGB)
        frame_rgb_right = cv2.cvtColor(webcam_frame_right_half_display, cv2.COLOR_BGR2RGB)

        frame_pygame_left = pygame.image.frombuffer(frame_rgb_left.tobytes(), frame_rgb_left.shape[1::-1], "RGB")
        frame_pygame_right = pygame.image.frombuffer(frame_rgb_right.tobytes(), frame_rgb_right.shape[1::-1], "RGB")
        
        screen.blit(frame_pygame_left, webcam_rect_1.topleft)
        screen.blit(frame_pygame_right, webcam_rect_2.topleft)
        
        pygame.draw.rect(screen, dgreen, webcam_rect_1, 3)
        pygame.draw.rect(screen, dgreen, webcam_rect_2, 3)

        p2_emotion_text = sfont.render(f"P2 Mood: {p2_difficulty.capitalize()}", True, dgreen)
        p2_text_rect = p2_emotion_text.get_rect(center=(webcam_rect_1.centerx, webcam_rect_1.top - 20))
        screen.blit(p2_emotion_text, p2_text_rect)

        p1_emotion_text = sfont.render(f"P1 Mood: {p1_difficulty.capitalize()}", True, dgreen)
        p1_text_rect = p1_emotion_text.get_rect(center=(webcam_rect_2.centerx, webcam_rect_2.top - 20))
        screen.blit(p1_emotion_text, p1_text_rect)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()