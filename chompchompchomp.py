
import pygame
import random
import sys
import cv2
import numpy as np
from deepface import DeepFace

swiddth = 800
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
csize = 15
zsize = 50
maxcrop = 40 
maxzom = 10  
minzom = 4  
zomspeedhard = 6
zomspeedeasy = 5
zomspeedHARD = 7
happyvol = 0.5
normalvol = 1.0


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
    print("font error")
    dissonant_font_large = pygame.font.Font(None, 64)
    dissonant_font_medium = pygame.font.Font(None, 36)

lfont = pygame.font.Font(None, 72)
mfont = pygame.font.Font(None, 36)
sfont = pygame.font.Font(None, 24)
try:
    pingping = pygame.mixer.Sound('cheerful-ping-356011.mp3')
except pygame.error:
    print("sound error")
    pingping = None
try:
    boo = pygame.mixer.Sound('scary-horror-theme-song-382733.mp3')
except pygame.error:
    print("sound error")
    boo = None

try:
    plant_image = pygame.image.load('sprout-removebg-preview.png').convert_alpha()
    plant_size = 40
    plant_image = pygame.transform.scale(plant_image, (plant_size, plant_size))
except pygame.error:
    print("image error")
    plant_image = None 
try:
    zombie_image = pygame.image.load('zom.png').convert_alpha()
    zombie_image = pygame.transform.scale(zombie_image, (zsize, zsize))
except pygame.error as e:
    print("image error")
    zombie_image = None

def makecrop():
    webcam_rect = pygame.Rect(swiddth - 220, sheight - 170, 200, 150)
    while True:
        x = random.randrange(plant_size // 2, swiddth - plant_size // 2)
        y = random.randrange(plant_size // 2, sheight - plant_size // 2)
        crop_rect = pygame.Rect(x - plant_size // 2, y - plant_size // 2, plant_size, plant_size)
        if not crop_rect.colliderect(webcam_rect):
            break
    return {
        'x': x,
        'y': y,
        'rect': crop_rect,
        'is_harvested': False
    }

def makezom(num):
    zombies = []
    for _ in range(num):
        x = random.randrange(zsize, swiddth - zsize)
        y = random.randrange(zsize, sheight - zsize)
        vx = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
        vy = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
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

def draw_ui(score, lives, message="", difficulty_mode=""):
    score_text = sfont.render(f"Score: {score}", True, dgreen)
    screen.blit(score_text, (20, 20))
    lives_text = sfont.render(f"Lives: {lives}", True, dgreen)
    screen.blit(lives_text, (20, 50))
    emotion_text = "Happy" if difficulty_mode == "Happy" else difficulty_mode.capitalize()
    emotion_text_surface = sfont.render(f"Mode: {emotion_text}", True, dgreen)
    screen.blit(emotion_text_surface, (20, sheight - 40))

    if message:
        message_text = lfont.render(message, True, dgreen)
        text_rect = message_text.get_rect(center=(swiddth // 2, sheight // 2))
        screen.blit(message_text, text_rect)

def draw_happiness_meter(meter_value):
    """Draws the happiness meter progress bar."""
    meter_rect = pygame.Rect(swiddth - 250, 20, 200, 20)
    meter_bg_rect = pygame.Rect(meter_rect.x, meter_rect.y, meter_rect.width, meter_rect.height)
    meter_fill_rect = pygame.Rect(meter_rect.x, meter_rect.y, int(meter_rect.width * (meter_value / hmetermax)), meter_rect.height)
    
    pygame.draw.rect(screen, gray, meter_bg_rect, 2)
    pygame.draw.rect(screen, lgreen, meter_fill_rect)
    
    meter_text = sfont.render("Happiness", True, dgreen)
    screen.blit(meter_text, (meter_rect.x, meter_rect.y + 25))

def main():
    """Main game loop."""
    crops = []
    zombies = []
    score = 10
    lives = 3
    game_over = False
    message = "Click to Start!"

    happiness_meter = 0
    frenzy_mode_active = False
    frenzy_mode_start_time = 0

    zombie_eaten_crop_counter = 0 
    
    game_state = "intro_1"
    intro_start_time = pygame.time.get_ticks()
    if boo:
        boo.play(-1)
    CROP_SPAWN_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(CROP_SPAWN_EVENT, crop_spawnnormal)
    frustrated_trigger_start_time = None
    frustrated_effect_end_time = 0
    frustrated_effect = None
    previous_difficulty = None
    last_hit_time = 0
    restart_button_rect = pygame.Rect(0, 0, 0, 0)
    exit_button_rect = pygame.Rect(0, 0, 0, 0)
    while True:
        
        ret, frame = cap.read()
        if not ret:
            continue
       
        draw_background() 
        
       
        mouse_pos = pygame.mouse.get_pos()
        if game_state == "playing":
            pygame.draw.circle(screen, dgreen, mouse_pos, csize // 2, 2)
        
       
        help_button_text = sfont.render("?", True, white)
        help_button_rect = help_button_text.get_rect(topright=(swiddth - 20, 20))
        pygame.draw.circle(screen, dgreen, help_button_rect.center, 15)
        screen.blit(help_button_text, help_button_rect)

        now = pygame.time.get_ticks()
        current_difficulty = "Not Detected"

        
        if now < frustrated_effect_end_time:
            current_difficulty = "Frustrated"
            
        else:
            
            try:
                analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, silent=True)
                if analysis:
                    dominant_emotion = analysis[0]['dominant_emotion']
                    if dominant_emotion in ['happy', 'surprise']:
                        current_difficulty = "Happy"
                        frustrated_trigger_start_time = None
                    elif dominant_emotion == 'neutral':
                        current_difficulty = "Normal"
                        frustrated_trigger_start_time = None
                    else:
                        current_difficulty = "Frustrated"
                        if frustrated_trigger_start_time is None:
                            frustrated_trigger_start_time = now
                        elif now - frustrated_trigger_start_time >= frustriggdelay:
                          
                            frustrated_effect_end_time = now + frusdur
                            frustrated_effect = random.choices(['dim_screen', 'speed_up_zombies'], weights=[6, 4], k=1)[0]
                            frustrated_trigger_start_time = None
                else:
                    current_difficulty = "No Face"
                    frustrated_trigger_start_time = None
            except Exception as e:
                current_difficulty = "No Face" 
                frustrated_trigger_start_time = None

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
                if game_state == "intro_1":
                    game_state = "intro_2"
                elif game_state == "intro_2":
                    game_state = "intro_3"
                elif game_state == "intro_3":
                    game_state = "intro_4"
                elif game_state == "intro_4":
                    if boo:
                        boo.stop()
                    game_state = "pre_game"
                intro_start_time = now
        
        if game_state == "playing" and not frenzy_mode_active:
            if current_difficulty == "Happy":
                happiness_meter = min(hmetermax, happiness_meter + hmetergain)
            else:
                happiness_meter = max(0, happiness_meter - hmeterloss)

            if happiness_meter >= hmetermax:
                frenzy_mode_active = True
                frenzy_mode_start_time = now
                happiness_meter = 0 

        if frenzy_mode_active and now - frenzy_mode_start_time >= frenzytimedur:
            frenzy_mode_active = False
            
       
        if game_state == "playing" and current_difficulty != previous_difficulty:
            if current_difficulty == "Happy":
                pygame.time.set_timer(CROP_SPAWN_EVENT, cropspawnhappy)
            elif current_difficulty == "Frustrated":
                pygame.time.set_timer(CROP_SPAWN_EVENT, crop_spawnfrustrated)
            else: 
                pygame.time.set_timer(CROP_SPAWN_EVENT, crop_spawnnormal)
            previous_difficulty = current_difficulty


        if game_state == "playing" or game_state == "pre_game":
            webcam_rect = pygame.Rect(swiddth - 220, sheight - 170, 200, 150)
            
            
            webcam_frame_scaled = cv2.resize(frame, (webcam_rect.width, webcam_rect.height))
            
            
            frame_rgb = cv2.cvtColor(webcam_frame_scaled, cv2.COLOR_BGR2RGB)
            frame_pygame = pygame.image.frombuffer(frame_rgb.tobytes(), frame_rgb.shape[1::-1], "RGB")
            screen.blit(frame_pygame, webcam_rect.topleft)
            pygame.draw.rect(screen, dgreen, webcam_rect, 3) 


      
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if help_button_rect.collidepoint(event.pos):
                    game_state = "help"
                elif game_state == "help":
                    game_state = "pre_game"
                elif game_state == "pre_game":
                    game_state = "playing"
                    game_over = False
                    score = 10
                    lives = 3 
                    crops = [makecrop() for _ in range(5)]
                    message = ""
                    zombie_eaten_crop_counter = 0 
                    zombies = makezom(maxzom)
                    frustrated_effect_end_time = 0 
                    frustrated_trigger_start_time = None
                    frustrated_effect = None
                    previous_difficulty = None 
                elif game_state == "playing":
                    click_pos = event.pos
                   
                    for crop in crops:
                        if not crop['is_harvested'] and crop['rect'].collidepoint(click_pos):
                            crop['is_harvested'] = True
                            
                        
                            if frenzy_mode_active:
                                score += 3 
                            elif current_difficulty == "Happy":
                                score += 2
                                if pingping:
                                    pingping.set_volume(happyvol)
                            else:
                                score += 1
                                if pingping:
                                    pingping.set_volume(normalvol)
                            
                            if pingping:
                                pingping.play()
                                
                elif game_state == "game_over":
                    if restart_button_rect.collidepoint(event.pos):
                        game_state = "pre_game"
                        score = 10
                        lives = 3
                        crops = [makecrop() for _ in range(5)]
                        zombies = makezom(maxzom)
                        frustrated_effect_end_time = 0
                        frustrated_trigger_start_time = None
                        frenzy_mode_active = False
                    elif exit_button_rect.collidepoint(event.pos):
                        cap.release()
                        pygame.quit()
                        sys.exit()
            
            if event.type == CROP_SPAWN_EVENT and game_state == "playing":
                if len(crops) < maxcrop:
                    crops.append(makecrop())

        
        if game_state == "playing":  
            if frenzy_mode_active:
                zombie_speed = 0 
            elif current_difficulty == "Frustrated":
                if frustrated_effect == 'speed_up_zombies':
                    zombie_speed = zomspeedHARD
                else: 
                    zombie_speed = zomspeedhard
            elif current_difficulty == "Happy":
                zombie_speed = zomspeedeasy
            else:
                zombie_speed = zomspeedhard

            for zombie in zombies:
                zombie['x'] += zombie['vx'] * zombie_speed
                zombie['y'] += zombie['vy'] * zombie_speed
                
            
                if zombie['x'] <= zsize // 2 or zombie['x'] >= swiddth - zsize // 2:
                    zombie['vx'] *= -1
                if zombie['y'] <= zsize // 2 or zombie['y'] >= sheight - zsize // 2:
                    zombie['vy'] *= -1
                zombie['rect'].topleft = (int(zombie['x']) - zsize // 2, int(zombie['y']) - zsize // 2)

          
                for crop in crops:
                    if not crop['is_harvested'] and zombie['rect'].colliderect(crop['rect']):
                        crop['is_harvested'] = True
                        zombie_eaten_crop_counter += 1
                    
                        if zombie_eaten_crop_counter >= 2:
                            score = max(0, score - 1)
                            zombie_eaten_crop_counter = 0
                        if pingping:
                            pingping.play()

            
            if now - last_hit_time > 1000: 
                mouse_pos = pygame.mouse.get_pos()
                for zombie in zombies:
                    if zombie['rect'].collidepoint(mouse_pos):
                        lives -= 1
                        score = max(0, score - 7)
                        last_hit_time = now
            
            
            crops = [crop for crop in crops if not crop['is_harvested']]
            
            draw_crops(crops)
            draw_zombies(zombies)

           
            if current_difficulty == "Frustrated" and frustrated_effect == 'dim_screen':
                dim_surface = pygame.Surface((swiddth, sheight), pygame.SRCALPHA)
                dim_surface.fill((0, 0, 0, 200))
                screen.blit(dim_surface, (0, 0))

            draw_ui(score, lives, difficulty_mode=current_difficulty)
            draw_happiness_meter(happiness_meter)

            if frenzy_mode_active:
                frenzy_message = lfont.render("FRENZY!", True, red)
                text_rect = frenzy_message.get_rect(center=(swiddth // 2, sheight // 2 + 100))
                screen.blit(frenzy_message, text_rect)
            
            if score <= 0 or lives <= 0:
                if game_state != "game_over":
                    game_state = "game_over"
        
        elif game_state == "game_over":
            
            restart_button_rect = pygame.Rect(swiddth // 2 - 150, sheight // 2 + 50, 100, 40)
            exit_button_rect = pygame.Rect(swiddth // 2 + 50, sheight // 2 + 50, 100, 40)
            
            screen.fill(black) 
            
          
            title_text = lfont.render("Rot and Reap", True, white)
            title_rect = title_text.get_rect(center=(swiddth // 2, 100))
            screen.blit(title_text, title_rect)

            
            game_over_text = lfont.render("You've been reaped!", True, white)
            score_text = mfont.render(f"Your Score: {score}", True, white)
            
         
            game_over_rect = game_over_text.get_rect(center=(swiddth // 2, sheight // 2 - 50))
            score_rect = score_text.get_rect(center=(swiddth // 2, sheight // 2))
            
            screen.blit(game_over_text, game_over_rect)
            screen.blit(score_text, score_rect)
            
          
            pygame.draw.rect(screen, dgreen, restart_button_rect)
            pygame.draw.rect(screen, dgreen, exit_button_rect)
            
            restart_text = sfont.render("Restart", True, white)
            exit_text = sfont.render("Exit", True, white)
            
            restart_text_rect = restart_text.get_rect(center=restart_button_rect.center)
            exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
            
            screen.blit(restart_text, restart_text_rect)
            screen.blit(exit_text, exit_text_rect)

        elif game_state == "help":
            screen.fill(dgreen)
            
            # Title
            title_text = dissonant_font_large.render("How to Play", True, white)
            title_rect = title_text.get_rect(center=(swiddth // 2, 100))
            screen.blit(title_text, title_rect)
            
          
            help_lines = [
                "Your mission is to harvest crops before the zombies destroy them.",
                "Click on a crop to harvest it and gain points.",
                "The game adjusts to your emotions!",
                "If you are happy, zombies move slower, and crops spawn faster.",
                "If you look frustrated, zombies get faster and may dim the screen.",
                "Fill your happiness meter to enter FRENZY MODE!",
                "In FRENZY MODE, zombies are stunned and crops are worth triple points.",
                "But be careful, if a zombie touches you, you lose points and a life.",
                "",
                "Click anywhere to return to the game."
            ]
            
            y_offset = 200
            for line in help_lines:
                line_text = mfont.render(line, True, mint)
                line_rect = line_text.get_rect(center=(swiddth // 2, y_offset))
                screen.blit(line_text, line_rect)
                y_offset += 40
        
        elif game_state == "pre_game":
              draw_ui(score, lives, message)
        
   
        pygame.display.flip()
        
        
        clock.tick(60)

if __name__ == "__main__":
    main()