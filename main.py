import pygame
import math
import random

# 初期化
pygame.init()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('謎の壁 - シューティングブロック崩し')

# 色定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# 壁の設定
WALL_THICKNESS = 20
LEFT_WALL_X = 0
RIGHT_WALL_X = SCREEN_WIDTH - WALL_THICKNESS
TOP_WALL_Y = 0
BOTTOM_Y = SCREEN_HEIGHT

# パドルの設定
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 15
PADDLE_SPEED = 5
paddle_x = SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2
paddle_y = SCREEN_HEIGHT - 50

# 玉の設定
BALL_RADIUS = 8
ball_x = SCREEN_WIDTH // 2
ball_y = paddle_y - BALL_RADIUS - 5
ball_speed = 4
ball_angle = -math.pi / 4  # -45度（上向き）
ball_dx = ball_speed * math.cos(ball_angle)
ball_dy = ball_speed * math.sin(ball_angle)
ball_active = False  # スペースキーで発射

# ブロックの設定
BLOCK_WIDTH = 60
BLOCK_HEIGHT = 25
BLOCK_ROWS = 5
BLOCK_COLS = 10
BLOCK_START_Y = 100
BLOCK_SPACING = 5

blocks = []

# 敵の設定
ENEMY_WIDTH = 40
ENEMY_HEIGHT = 30
enemies = []

# ゲーム状態
lives = 3
score = 0
level_cleared = False

# フォント
font = pygame.font.SysFont(None, 36)

def create_blocks():
    """ブロックを生成"""
    global blocks
    blocks = []
    for row in range(BLOCK_ROWS):
        for col in range(BLOCK_COLS):
            x = LEFT_WALL_X + WALL_THICKNESS + col * (BLOCK_WIDTH + BLOCK_SPACING)
            y = BLOCK_START_Y + row * (BLOCK_HEIGHT + BLOCK_SPACING)
            blocks.append({
                'x': x,
                'y': y,
                'width': BLOCK_WIDTH,
                'height': BLOCK_HEIGHT,
                'active': True
            })

def create_enemies():
    """敵を生成（ブロックの層の間に配置）"""
    global enemies
    enemies = []
    # ブロックの層の間に敵を配置
    for row in range(BLOCK_ROWS - 1):
        enemy_y = BLOCK_START_Y + (row + 1) * (BLOCK_HEIGHT + BLOCK_SPACING) - ENEMY_HEIGHT // 2
        num_enemies = 5
        for i in range(num_enemies):
            x = LEFT_WALL_X + WALL_THICKNESS + (i + 1) * (SCREEN_WIDTH - 2 * WALL_THICKNESS) / (num_enemies + 1)
            enemies.append({
                'x': x,
                'y': enemy_y,
                'width': ENEMY_WIDTH,
                'height': ENEMY_HEIGHT,
                'active': True,
                'trapped': True,  # ブロックに阻まれているか
                'direction': 1,  # 移動方向（1: 右, -1: 左）
                'speed': 1
            })

def draw_walls():
    """壁を描画"""
    # 左壁
    pygame.draw.rect(screen, WHITE, (LEFT_WALL_X, 0, WALL_THICKNESS, SCREEN_HEIGHT))
    # 右壁
    pygame.draw.rect(screen, WHITE, (RIGHT_WALL_X, 0, WALL_THICKNESS, SCREEN_HEIGHT))
    # 上壁
    pygame.draw.rect(screen, WHITE, (0, TOP_WALL_Y, SCREEN_WIDTH, WALL_THICKNESS))

def draw_paddle():
    """パドルを描画"""
    pygame.draw.rect(screen, CYAN, (paddle_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))

def draw_ball():
    """玉を描画"""
    pygame.draw.circle(screen, YELLOW, (int(ball_x), int(ball_y)), BALL_RADIUS)

def draw_blocks():
    """ブロックを描画"""
    for block in blocks:
        if block['active']:
            pygame.draw.rect(screen, GREEN, 
                           (block['x'], block['y'], block['width'], block['height']))
            pygame.draw.rect(screen, WHITE, 
                           (block['x'], block['y'], block['width'], block['height']), 2)

def draw_enemies():
    """敵を描画"""
    for enemy in enemies:
        if enemy['active']:
            color = RED if not enemy['trapped'] else ORANGE
            pygame.draw.rect(screen, color,
                           (enemy['x'], enemy['y'], enemy['width'], enemy['height']))
            pygame.draw.rect(screen, WHITE,
                           (enemy['x'], enemy['y'], enemy['width'], enemy['height']), 2)

def check_ball_wall_collision():
    """玉と壁の衝突判定"""
    global ball_x, ball_y, ball_dx, ball_dy
    
    # 左壁
    if ball_x - BALL_RADIUS <= LEFT_WALL_X + WALL_THICKNESS:
        ball_x = LEFT_WALL_X + WALL_THICKNESS + BALL_RADIUS
        ball_dx = abs(ball_dx)
    
    # 右壁
    if ball_x + BALL_RADIUS >= RIGHT_WALL_X:
        ball_x = RIGHT_WALL_X - BALL_RADIUS
        ball_dx = -abs(ball_dx)
    
    # 上壁
    if ball_y - BALL_RADIUS <= TOP_WALL_Y + WALL_THICKNESS:
        ball_y = TOP_WALL_Y + WALL_THICKNESS + BALL_RADIUS
        ball_dy = abs(ball_dy)

def check_ball_paddle_collision():
    """玉とパドルの衝突判定"""
    global ball_x, ball_y, ball_dx, ball_dy
    
    if (ball_y + BALL_RADIUS >= paddle_y and 
        ball_y - BALL_RADIUS <= paddle_y + PADDLE_HEIGHT and
        ball_x + BALL_RADIUS >= paddle_x and
        ball_x - BALL_RADIUS <= paddle_x + PADDLE_WIDTH):
        
        # パドルのどの位置に当たったかで角度を変える
        hit_pos = (ball_x - paddle_x) / PADDLE_WIDTH  # 0.0 ~ 1.0
        angle = math.pi * (0.5 + hit_pos * 0.5)  # 90度 ~ 180度（上向き）
        ball_dx = ball_speed * math.cos(angle)
        ball_dy = -abs(ball_speed * math.sin(angle))  # 必ず上向き
        ball_y = paddle_y - BALL_RADIUS

def check_ball_block_collision():
    """玉とブロックの衝突判定"""
    global ball_dx, ball_dy, score
    
    for block in blocks:
        if not block['active']:
            continue
        
        # ブロックとの衝突判定
        if (ball_x + BALL_RADIUS >= block['x'] and
            ball_x - BALL_RADIUS <= block['x'] + block['width'] and
            ball_y + BALL_RADIUS >= block['y'] and
            ball_y - BALL_RADIUS <= block['y'] + block['height']):
            
            # どの面に当たったか判定
            block_center_x = block['x'] + block['width'] / 2
            block_center_y = block['y'] + block['height'] / 2
            
            dx = ball_x - block_center_x
            dy = ball_y - block_center_y
            
            if abs(dx) > abs(dy):
                # 左右の面
                ball_dx = -ball_dx
            else:
                # 上下の面
                ball_dy = -ball_dy
            
            block['active'] = False
            score += 10
            return True
    
    return False

def check_ball_enemy_collision():
    """玉と敵の衝突判定"""
    global ball_dx, ball_dy, score
    
    for enemy in enemies:
        if not enemy['active']:
            continue
        
        # 敵との衝突判定
        if (ball_x + BALL_RADIUS >= enemy['x'] and
            ball_x - BALL_RADIUS <= enemy['x'] + enemy['width'] and
            ball_y + BALL_RADIUS >= enemy['y'] and
            ball_y - BALL_RADIUS <= enemy['y'] + enemy['height']):
            
            # どの面に当たったか判定
            enemy_center_x = enemy['x'] + enemy['width'] / 2
            enemy_center_y = enemy['y'] + enemy['height'] / 2
            
            dx = ball_x - enemy_center_x
            dy = ball_y - enemy_center_y
            
            if abs(dx) > abs(dy):
                # 左右の面
                ball_dx = -ball_dx
            else:
                # 上下の面
                ball_dy = -ball_dy
            
            enemy['active'] = False
            score += 20
            return True
    
    return False

def check_enemy_trapped():
    """敵がブロックに阻まれているかチェック"""
    for enemy in enemies:
        if not enemy['active'] or not enemy['trapped']:
            continue
        
        # 敵の上下にブロックがあるかチェック
        has_block_above = False
        has_block_below = False
        
        for block in blocks:
            if not block['active']:
                continue
            
            # 同じ列にあるブロックかチェック
            if (block['x'] < enemy['x'] + enemy['width'] and
                block['x'] + block['width'] > enemy['x']):
                
                if block['y'] < enemy['y']:
                    has_block_above = True
                if block['y'] + block['height'] > enemy['y'] + enemy['height']:
                    has_block_below = True
        
        # 上下両方にブロックがあれば阻まれている
        if not (has_block_above and has_block_below):
            enemy['trapped'] = False

def update_enemies():
    """敵の移動（ギャラクシアン風）"""
    for enemy in enemies:
        if not enemy['active'] or enemy['trapped']:
            continue
        
        # ギャラクシアン風の動き：左右に移動し、端に来たら下に移動
        enemy['x'] += enemy['direction'] * enemy['speed']
        
        # 壁に当たったら方向転換して下に移動
        if enemy['x'] <= LEFT_WALL_X + WALL_THICKNESS:
            enemy['x'] = LEFT_WALL_X + WALL_THICKNESS
            enemy['direction'] = 1
            enemy['y'] += 20
        elif enemy['x'] + enemy['width'] >= RIGHT_WALL_X:
            enemy['x'] = RIGHT_WALL_X - enemy['width']
            enemy['direction'] = -1
            enemy['y'] += 20

def check_level_clear():
    """レベルクリア判定"""
    global level_cleared
    
    # ブロックと敵が全て消えたかチェック
    active_blocks = sum(1 for block in blocks if block['active'])
    active_enemies = sum(1 for enemy in enemies if enemy['active'])
    
    if active_blocks == 0 and active_enemies == 0:
        level_cleared = True

def reset_ball():
    """玉をリセット"""
    global ball_x, ball_y, ball_dx, ball_dy, ball_active
    ball_x = paddle_x + PADDLE_WIDTH // 2
    ball_y = paddle_y - BALL_RADIUS - 5
    ball_angle = -math.pi / 4
    ball_dx = ball_speed * math.cos(ball_angle)
    ball_dy = ball_speed * math.sin(ball_angle)
    ball_active = False

# 初期化
create_blocks()
create_enemies()

# メインループ
clock = pygame.time.Clock()
running = True

while running:
    screen.fill(BLACK)
    
    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not ball_active:
                ball_active = True
    
    # キー入力
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and paddle_x > LEFT_WALL_X + WALL_THICKNESS:
        paddle_x -= PADDLE_SPEED
    if keys[pygame.K_RIGHT] and paddle_x + PADDLE_WIDTH < RIGHT_WALL_X:
        paddle_x += PADDLE_SPEED
    
    # 玉の移動
    if ball_active:
        ball_x += ball_dx
        ball_y += ball_dy
        
        # 衝突判定
        check_ball_wall_collision()
        check_ball_paddle_collision()
        check_ball_block_collision()
        check_ball_enemy_collision()
        
        # 玉が下に落ちた
        if ball_y > BOTTOM_Y:
            lives -= 1
            if lives > 0:
                reset_ball()
            else:
                # ゲームオーバー
                pass
    else:
        # 玉が発射されていない時はパドルに追従
        ball_x = paddle_x + PADDLE_WIDTH // 2
    
    # 敵の更新
    check_enemy_trapped()
    update_enemies()
    
    # レベルクリア判定
    check_level_clear()
    
    # 描画
    draw_walls()
    draw_blocks()
    draw_enemies()
    draw_paddle()
    draw_ball()
    
    # UI表示
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    
    lives_text = font.render(f"Lives: {lives}", True, WHITE)
    screen.blit(lives_text, (10, 50))
    
    if level_cleared:
        clear_text = font.render("LEVEL CLEARED!", True, YELLOW)
        text_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(clear_text, text_rect)
    
    if lives <= 0:
        game_over_text = font.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(game_over_text, text_rect)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
