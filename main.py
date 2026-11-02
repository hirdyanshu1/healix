import math
import random
import pygame
import array

pygame.init()

if not pygame.mixer.get_init():
    pygame.mixer.init (
        frequency=22050,
        size = -16,
        channels = 1
    )
SAMPLE_RATE = 22050
muted = False

def make_tone(frequency, duration, volume=0.3):
    samples = array.array("h")
    total_samples = int(SAMPLE_RATE * duration)

    for i in range ( total_samples):
        time = i/ SAMPLE_RATE

        fade_in = min(1.0, i / 200)
        fade_out = min(1.0, (total_samples - i)/ 500)
        fade = min(fade_in, fade_out)
        wave = math.sin(2 * math.pi * frequency * time)
        sample = int( 32767 * volume * fade * wave)
        samples.append(sample)
    return pygame.mixer.Sound(buffer = samples.tobytes())

def make_crash_sound():
    samples = array.array("h")
    total_samples = int (SAMPLE_RATE * 0.35)

    for i in range(total_samples):
        fade = 1.0 -i / total_samples
        noise = random.randint(-32767, 32767)
        samples.append(int(noise* fade *0.45))
    return pygame.mixer.Sound(buffer = samples.tobytes())

engine_sound =[
     make_tone(100, 0.6, 0.15),
     make_tone(110, 0.6, 0.15),
     make_tone(150, 0.6, 0.15),
     make_tone(195, 0.6, 0.15),
]
crash_sound = make_crash_sound()
reverse_beep = make_tone(750, 0.2,0.2)
coin_sound = make_tone(900, 0.15, 0.25)

engine_channel = None
current_engine_level = -1

if engine_channel:
    engine_channel.set_volume(0.0)

window_width = 900
window_height = 600

game_window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("JCB Road Drive")

clock = pygame.time.Clock()
game_is_running = True

jcb_x = window_width / 2
jcb_y = 470
steering_velocity = 0.0
speed = 0.0
max_speed =500.0
acceleration = 520.0
brake_power = 5000.0
steering_speed = 330.0
steering_response = 9.0
road_offset = 0.0
reverse_speed_limit = 120.0
reverse_beep_limit = 0.0

grass_color = (45, 135, 75)
road_color = (60, 62, 68)
line_color = (245, 245, 245)

road_width = 440
road_period = 2 * math.pi / 0.0035


def get_road_centre(world_y):
    return (
        window_width / 2
        + 180 * math.sin(world_y * 0.0035)
        + 75 * math.sin(world_y * 0.007)
    )


def draw_jcb(surface, x, y):
    yellow = (245, 180, 20)
    dark = (30, 32, 35)
    glass = (70, 175, 205)
    metal = (150, 155, 160)
    white = (245, 245, 235)

    for tire_x in (x - 25, x + 17):
        for tire_y in (y - 25, y + 22):
            pygame.draw.rect(
                surface, dark, (tire_x, tire_y, 12, 25), border_radius=4
            )

    pygame.draw.line(surface, yellow, (x + 5, y + 25), (x + 24, y + 43), 9)
    pygame.draw.line(surface, dark, (x + 24, y + 25), (x + 30, y + 53), 7)
    pygame.draw.line(surface, metal, (x - 12, y - 22), (x - 20, y - 39), 3)
    pygame.draw.line(surface, metal, (x + 12, y - 22), (x + 20, y - 39), 9)
    pygame.draw.polygon(
        surface,
        metal,
        [(x - 25, y - 43), (x + 25, y - 43), (x + 22, y - 55), (x - 22, y - 55)],
    )
    pygame.draw.line(surface, dark, (x - 22, y - 54), (x + 22, y - 54), 3)
    pygame.draw.rect(surface, yellow, (x - 18, y - 30, 36, 65), border_radius=7)
    pygame.draw.rect(surface, dark, (x - 13, y - 19, 26, 25), border_radius=4)
    pygame.draw.rect(surface, glass, (x - 9, y - 15, 18, 16), border_radius=3)
    pygame.draw.rect(surface, yellow, (x - 13, y + 10, 18, 16), border_radius=3)

    font = pygame.font.SysFont("arial", 11, bold=True)
    logo = font.render("JCB", True, white)
    surface.blit(logo, logo.get_rect(center=(x, y + 18)))
    pygame.draw.circle(surface, white, (x - 11, y - 29), 3)
    pygame.draw.circle(surface, white, (x + 11, y - 29), 3)


font = pygame.font.SysFont("arial", 22, bold=True)
jcb_half_width = 31

obstacles = []
obstacle_timer = 0.0
obstacle_spawn_delay = 1.5
score =0
game_over = False
distance_km = 0.0
hit_politician = ""
coins = []
coin_timer = 0.0
coin_spawn_timer = 2.5
total_coins = 0

def draw_politician(surface, x,y, politician_type):
    skin = (220, 170, 125)
    white = (245, 245, 245)
    black = (25, 25,25)

    if politician_type ==1 :
        body_color = (235, 235, 220)
        radius = 12
    elif politician_type ==2:
        body_color = (35, 45, 65)
        radius = 14
    else :
        body_color = (180, 45, 65)
        radius = 16

    pygame.draw.circle(surface , skin, (int(x), int(y-15)), radius)
    pygame.draw.arc(
        surface, black,
        (int(x-radius),
        int(y-15 -radius),
        radius *2, radius * 2),
        math.pi, 2 * math.pi, 3
    )
    pygame.draw.circle(surface, black, (int(x-4), int (y-17)), 2)
    pygame.draw.circle(surface, black, (int(x+4), int (y-17)), 2)

    pygame.draw.rect (
        surface, body_color, 
        (int(x-15), int(y-2), 30, 32),
        border_radius = 5
    )

    if politician_type == 2:
        pygame.draw.polygon(
            surface, (190, 35, 45),
            [(int(x-3), int(y)),
             (int(x+3), int(y)),
             (int(x+4), int(y+23)),
             (int(x), int(y+27)),
             (int(x-4), int(y+23))]
        )
    else:
        for button_y in (y+6, y+13, y+20):
            pygame.draw.circle(
                surface, black,
                (int(x), int(button_y)), 1
            )
    label_text = {
        1: "NARENDRA MODI",
        2: "RAHUL GANDHI",
        3: "ARVIND KEJRIWAL"
    }[politician_type]

    label = pygame.font.SysFont("arial", 10, bold=True)
    surface.blit( label.render(label_text, True, white),
                (int(x-35), int(y+34))
                )

def draw_coin(surface, x, y):
    gold = (255, 195, 0)
    light_gold = (255, 230, 90)
    dark_gold = (180, 115, 0)

    pygame.draw.circle(surface, dark_gold, (int(x), int(y)), 15)
    pygame.draw.circle(surface, gold, (int(x), int(y)), 12)
    pygame.draw.circle(surface, light_gold, (int(x), int(y)), 8)

    font = pygame.font.SysFont("arial", 13, bold= True)
    symbol = font.render("$", True, dark_gold)
    surface.blit(
        symbol,
        symbol.get_rect(center=(int(x), int(y)))
    )

while game_is_running:
    delta_time = min(clock.tick(60) / 1000, 0.05)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_is_running = False
        elif event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_r:
                jcb_x = window_width / 2
                speed = 0.0
                steering_velocity = 0.0
                road_offset = 0.0
                obstacles.clear()
                obstacle_timer = 0.0
                score = 0
                distance_km = 0.0
                coins.clear()
                coin_timer = 0.0
                total_coins = 0
                game_over = False
                hit_politician = ""

            elif event.key == pygame.K_m:
                muted = not muted
                if engine_channel:
                    volume = min(0.7, speed/ max_speed * 0.7)
                    engine_channel.set_volume(0.0 if muted else volume)

    keys = pygame.key.get_pressed()

    if game_over:
        if engine_channel:
            engine_channel.set_volume(0.0)

        pygame.display.flip()
        clock.tick(30)
        continue

    if keys[pygame.K_UP] or keys[pygame.K_w]:
        speed = min(max_speed, speed + acceleration * delta_time)
    elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
        if speed >0:
            speed = max(0.0, speed - brake_power * delta_time)
        else:
            speed = max(- reverse_speed_limit, speed - 150 * delta_time)
    else :
        if speed > 0:
            speed = max (0, speed - 70 * delta_time)
        elif speed <0:
            speed = min(0, speed + 70 * delta_time)

    if speed < -5:
        reverse_beep_timer += delta_time

        if reverse_beep_timer >= 0.8:
            if not muted:
                reverse_beep.play()
            reverse_beep_timer = 0.0
    else:
        reverse_beep_timer = 0.0

    if speed < 50:
        engine_level = 0
    elif speed < 100:
        engine_level = 1
    elif speed < 150:
        engine_level = 2
    else :
        engine_level = 3

    if engine_level != current_engine_level:
        if engine_channel:
            engine_channel.stop()            
        engine_channel = engine_sound[engine_level].play(loops = -1)
        current_engine_level = engine_level

    if engine_channel:
        engine_volume = min(0.7, speed/ max_speed * 0.7)    
        engine_channel.set_volume( 0.0 if muted else engine_volume )

    distance_km += max(0,speed) * 0.0001 * delta_time
    score+= max(0, speed) * 0.1 * delta_time

    obstacle_timer +=delta_time

    if obstacle_timer >= obstacle_spawn_delay and speed >50:
        obstacle_timer = 0.0

        spawn_y = -50
        road_centre = get_road_centre(spawn_y + road_offset)

        lane_positions = [
            road_centre - road_width / 4,
            road_centre + road_width / 4,
        ]

        obstacle_x = random.choice(lane_positions)

        obstacles.append({
            "x": obstacle_x,
            "y": spawn_y,
            "type": random.randint(1,3)
        })

    if speed > 50:
        coin_timer += delta_time

        if coin_timer >= coin_spawn_timer:
            coin_timer = 0.0
            spawn_y = -50
            road_centre = get_road_centre(spawn_y + road_offset)
            coin_positions = [
                road_centre - road_width / 4,
                road_centre + road_width / 4
            ]
            coin_x = random.choice(coin_positions)
            coins.append({
                "x": coin_x,
                "y": spawn_y
            })

    steering_input = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(
        keys[pygame.K_LEFT] or keys[pygame.K_a]
    )
    target_steering_velocity = steering_input * steering_speed
    steering_blend = min(1.0, steering_response * delta_time)
    steering_velocity += (
        target_steering_velocity - steering_velocity
    ) * steering_blend
    jcb_x += steering_velocity * delta_time

    road_offset = (road_offset - speed *1.5 * delta_time) % road_period

    for obstacle in obstacles[:]:
        obstacle["y"] += max(speed, 100) * 1.5 * delta_time

        if obstacle["y"] > window_height + 50:
            obstacles.remove(obstacle)
            score +=1
    for obstacle in obstacles :
        if (
            abs(jcb_x - obstacle["x"]) < 38 
            and abs(jcb_y - obstacle["y"]) < 45
        ):
            hit_politician = {
                1: "NARENDRA MODI",
                2: "RAHUL GANDHI",
                3: "ARVIND KEJRIWAL"
            } [obstacle["type"]]

            game_over = True

            if not muted:
                crash_sound.play()

    for coin in coins [:]:
        coin["y"] += max(speed, 100) * 1.5 * delta_time

        if coin["y"] > window_height + 30:
            coins.remove(coin)
            continue

        if (
            abs(jcb_x - coin["x"]) < 35
            and abs(jcb_y - coin["y"]) < 40
        ):
            coins.remove(coin)
            total_coins +=1
            score += 50

            if not muted:
                coin_sound.play()
  
    road_centre_at_jcb = get_road_centre(jcb_y + road_offset)
    road_left = road_centre_at_jcb - road_width / 2
    road_right = road_centre_at_jcb + road_width / 2

    if jcb_x - jcb_half_width <= road_left:
        game_over = True
    if jcb_x + jcb_half_width >= road_right:
            game_over = True

    game_window.fill(grass_color)

    road_points = [
        (get_road_centre(y + road_offset), y)
        for y in range(0, window_height + 11, 10)
    ]
    left_edge = [(int(centre - road_width / 2), y) for centre, y in road_points]
    right_edge = [(int(centre + road_width / 2), y) for centre, y in road_points]

    pygame.draw.polygon(game_window, road_color, left_edge + right_edge[::-1])
    pygame.draw.lines(game_window, line_color, False, left_edge, 4)
    pygame.draw.lines(game_window, line_color, False, right_edge, 4)

    lane_width = road_width / 4
    dash_spacing = 80
    dash_length = 40
    dash_shift = road_offset % dash_spacing

    for lane in range(1, 4):
        lane_offset = -road_width / 2 + lane * lane_width
        for base_y in range(-dash_spacing, window_height + dash_spacing, dash_spacing):
            y1 = int(base_y - dash_shift)
            y2 = y1 + dash_length
            if y2 <= 0 or y1 >= window_height:
                continue

            visible_y1 = max(0, y1)
            visible_y2 = min(window_height, y2)
            centre1 = get_road_centre(visible_y1 + road_offset)
            centre2 = get_road_centre(visible_y2 + road_offset)
            pygame.draw.line(
                game_window,
                line_color,
                (int(centre1 + lane_offset), visible_y1),
                (int(centre2 + lane_offset), visible_y2),
                4,
            )

    for obstacle in obstacles:
        draw_politician(
            game_window,
            int(obstacle["x"]),
            int(obstacle["y"]),
            obstacle["type"]
        )

    draw_jcb(game_window, int(jcb_x), jcb_y)

    for coin in coins:
        draw_coin(
            game_window,
            int(coin["x"]),
            int(coin["y"])
        )

    speed_display = font.render(
        f"Speed: {int(speed * 0.36)} km/h", True, (255, 255, 255)
    )
    game_window.blit(speed_display, (20, 20))

    distance_display = font.render(
        f"Distance: {distance_km : .2f} km",
        True, (255, 255, 255)
    )
    game_window.blit(distance_display, (20,  50))

    score_display = font.render (
        f"Score: {int(score)}", 
        True, (255, 220, 60)
    )
    game_window.blit(score_display, (20, 80))

    coin_display = font.render (
        f"Coins: {total_coins}",
        True,
        (255,215, 0)
    )

    game_window.blit(coin_display, (20, 110))

    pygame.display.flip()

    if game_over:
        overlay = pygame.Surface(
            (window_width, window_height), pygame.SRCALPHA 
        )
        overlay.fill((0, 0, 0, 180))
        game_window.blit(overlay, (0,0))

        title_font = pygame.font.SysFont("arial", 42, bold = True)
        info_font = pygame.font.SysFont("arial", 24, bold = True)

        title = title_font.render ( " GAME OVER !", True, (255, 60, 60))
        if hit_politician :
            cause = info_font.render (
                f"Collision with : {hit_politician}",
                True, (255, 220, 60)
            )
        restart = info_font.render("Press R to restart", True, (255, 220, 60))

        game_window.blit(
            title,
            title.get_rect(center = (window_width // 2, 220)) 
        )
        if hit_politician:
            game_window.blit(
                cause,
                cause.get_rect(center = (window_width // 2,280))
                )
        
        game_window.blit(
                    restart,
                    restart.get_rect(center = (window_width // 2, 340)) 
                )

pygame.quit()
