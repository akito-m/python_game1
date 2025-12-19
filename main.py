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

# HUD（スコア表示用の上部バー）
HUD_HEIGHT = 40

# 壁の設定（HUDの下から開始）
WALL_THICKNESS = 20
LEFT_WALL_X = 0
RIGHT_WALL_X = SCREEN_WIDTH - WALL_THICKNESS
TOP_WALL_Y = HUD_HEIGHT
BOTTOM_Y = SCREEN_HEIGHT

# パドルの設定
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 15
PADDLE_SPEED = 10  # 2倍の移動速度
paddle_x = SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2
paddle_y = SCREEN_HEIGHT - 50
paddle_prev_x = paddle_x  # 前フレームのパドルのX位置
paddle_direction = 0  # パドルの移動方向（-1: 左, 0: 停止, 1: 右）

# 玉の設定
BALL_RADIUS = 16  # 2倍のサイズ
ball_x = SCREEN_WIDTH // 2
ball_y = paddle_y - BALL_RADIUS - 5
ball_speed = 8  # 2倍の速度
ball_angle = -math.pi / 4  # -45度（上向き）
ball_dx = ball_speed * math.cos(ball_angle)
ball_dy = ball_speed * math.sin(ball_angle)
ball_active = False  # スペースキーで発射

# 角度制限（緩やかな角度を防ぐ）
MIN_ANGLE = math.radians(30)  # 最小30度（ブロック・敵との衝突用）
MAX_ANGLE = math.radians(60)  # 最大60度

# パドル反射用の最大傾き（縦方向からのずれ）
PADDLE_MAX_TILT = math.radians(60)  # 中央で真上、端で最大60度傾く

# ブロックの設定
BLOCK_WIDTH = 60
BLOCK_HEIGHT = 25
BLOCK_ROWS = 3  # ブロックだけの行数
BLOCK_COLS = 10
BLOCK_START_Y = 100
BLOCK_SPACING = 5

blocks = []

# 敵の設定
ENEMY_WIDTH = 40
ENEMY_HEIGHT = 30
ENEMY_ROWS = 2  # 敵だけの行数
ENEMY_COLS = 8  # 1行あたりの敵の数
enemies = []

# 行の高さ（ブロックと敵の行の間隔）
ROW_HEIGHT = BLOCK_HEIGHT + BLOCK_SPACING

# ゲーム状態
lives = 3
score = 0
level_cleared = False
game_over = False

# フォント
font = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 24)

# 画像の読み込み
try:
    paddle_img = pygame.image.load('player.png')
    paddle_img = pygame.transform.scale(paddle_img, (PADDLE_WIDTH, PADDLE_HEIGHT))
except:
    paddle_img = None

try:
    ball_img = pygame.image.load('ball.png')
    ball_size = BALL_RADIUS * 2
    ball_img = pygame.transform.scale(ball_img, (ball_size, ball_size))
except:
    ball_img = None

try:
    block_img = pygame.image.load('block.png')
    block_img = pygame.transform.scale(block_img, (BLOCK_WIDTH, BLOCK_HEIGHT))
except:
    block_img = None

try:
    enemy_img = pygame.image.load('enemy.png')
    enemy_img = pygame.transform.scale(enemy_img, (ENEMY_WIDTH, ENEMY_HEIGHT))
except:
    enemy_img = None

def create_blocks():
    """ブロックを生成（ブロックだけの行、右端まで配置）"""
    global blocks
    blocks = []
    # 利用可能な幅を計算（左右の壁の間）
    available_width = RIGHT_WALL_X - (LEFT_WALL_X + WALL_THICKNESS)
    # 右端まで配置するために必要なブロック数を計算
    # ブロック幅とスペースを考慮
    total_block_width = BLOCK_COLS * BLOCK_WIDTH + (BLOCK_COLS - 1) * BLOCK_SPACING
    # 右端まで配置するための調整
    if total_block_width < available_width:
        # 余ったスペースをブロック間のスペースに分配
        extra_space = available_width - total_block_width
        spacing_adjustment = extra_space / (BLOCK_COLS - 1) if BLOCK_COLS > 1 else 0
        actual_spacing = BLOCK_SPACING + spacing_adjustment
    else:
        actual_spacing = BLOCK_SPACING
    
    block_row_index = 0  # ブロック行のインデックス（0, 2, 4...）
    for row in range(BLOCK_ROWS + ENEMY_ROWS):
        # 偶数行（0, 2, 4...）がブロック行
        if row % 2 == 0:
            for col in range(BLOCK_COLS):
                x = LEFT_WALL_X + WALL_THICKNESS + col * (BLOCK_WIDTH + actual_spacing)
                y = BLOCK_START_Y + row * ROW_HEIGHT
                blocks.append({
                    'x': x,
                    'y': y,
                    'width': BLOCK_WIDTH,
                    'height': BLOCK_HEIGHT,
                    'active': True
                })
            block_row_index += 1

def check_enemy_block_collision(enemy_x, enemy_y, exclude_enemy=None):
    """敵とブロックの衝突判定"""
    for block in blocks:
        if not block['active']:
            continue
        if (enemy_x + ENEMY_WIDTH > block['x'] and
            enemy_x < block['x'] + block['width'] and
            enemy_y + ENEMY_HEIGHT > block['y'] and
            enemy_y < block['y'] + block['height']):
            return True
    return False

def check_enemy_enemy_collision(enemy_x, enemy_y, exclude_enemy=None):
    """敵同士の衝突判定"""
    for enemy in enemies:
        if not enemy['active'] or enemy == exclude_enemy:
            continue
        if (enemy_x + ENEMY_WIDTH > enemy['x'] and
            enemy_x < enemy['x'] + enemy['width'] and
            enemy_y + ENEMY_HEIGHT > enemy['y'] and
            enemy_y < enemy['y'] + enemy['height']):
            return True
    return False

def check_enemy_position_valid(enemy_x, enemy_y, exclude_enemy=None):
    """敵の位置が有効かチェック（ブロックや他の敵と重ならないか）"""
    # 壁の内側かチェック
    if enemy_x < LEFT_WALL_X + WALL_THICKNESS or enemy_x + ENEMY_WIDTH > RIGHT_WALL_X:
        return False
    if enemy_y < TOP_WALL_Y + WALL_THICKNESS:
        return False
    
    # パドルに近づきすぎないかチェック（パドルとの間にボールが跳ね返るスペースを確保）
    min_distance_from_paddle = 100
    if enemy_y + ENEMY_HEIGHT > paddle_y - min_distance_from_paddle:
        return False
    
    # ブロックと重ならないかチェック
    if check_enemy_block_collision(enemy_x, enemy_y, exclude_enemy):
        return False
    
    # 他の敵と重ならないかチェック
    if check_enemy_enemy_collision(enemy_x, enemy_y, exclude_enemy):
        return False
    
    return True

def create_enemies():
    """敵を生成（敵だけの行に配置）"""
    global enemies
    enemies = []
    # 奇数行（1, 3, 5...）が敵行
    for row in range(BLOCK_ROWS + ENEMY_ROWS):
        if row % 2 == 1:  # 奇数行が敵行
            base_y = BLOCK_START_Y + row * ROW_HEIGHT + (ROW_HEIGHT - ENEMY_HEIGHT) // 2
            # 敵を均等に配置
            available_width = SCREEN_WIDTH - 2 * WALL_THICKNESS - 2 * WALL_THICKNESS
            enemy_spacing = available_width / (ENEMY_COLS + 1)
            
            for i in range(ENEMY_COLS):
                enemy_x = LEFT_WALL_X + WALL_THICKNESS + (i + 1) * enemy_spacing - ENEMY_WIDTH // 2
                enemy_y = base_y
                
                enemies.append({
                    'x': enemy_x,
                    'y': enemy_y,
                    'width': ENEMY_WIDTH,
                    'height': ENEMY_HEIGHT,
                    'active': True,
                    'trapped': True,  # 初期状態ではブロックに阻まれている
                    'direction': 1 if i % 2 == 0 else -1,  # 移動方向（交互に）
                    'speed': 1,
                    'move_down_timer': 0  # 下に移動するタイマー
                })

def draw_background():
    """黒とグレーのタイル背景を描画"""
    tile_size = 32
    dark = (20, 20, 20)
    mid = (40, 40, 40)
    for y in range(0, SCREEN_HEIGHT, tile_size):
        for x in range(0, SCREEN_WIDTH, tile_size):
            color = dark if (x // tile_size + y // tile_size) % 2 == 0 else mid
            pygame.draw.rect(screen, color, (x, y, tile_size, tile_size))


def draw_walls():
    """壁を描画"""
    # 左壁
    pygame.draw.rect(screen, WHITE, (LEFT_WALL_X, HUD_HEIGHT, WALL_THICKNESS, SCREEN_HEIGHT - HUD_HEIGHT))
    # 右壁
    pygame.draw.rect(screen, WHITE, (RIGHT_WALL_X, HUD_HEIGHT, WALL_THICKNESS, SCREEN_HEIGHT - HUD_HEIGHT))
    # 上壁（HUDのすぐ下）
    pygame.draw.rect(screen, WHITE, (0, TOP_WALL_Y, SCREEN_WIDTH, WALL_THICKNESS))

def draw_paddle():
    """パドルを描画"""
    if paddle_img:
        screen.blit(paddle_img, (paddle_x, paddle_y))
    else:
        pygame.draw.rect(screen, CYAN, (paddle_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))

def draw_ball():
    """玉を描画"""
    if ball_img:
        screen.blit(ball_img, (int(ball_x - BALL_RADIUS), int(ball_y - BALL_RADIUS)))
    else:
        pygame.draw.circle(screen, YELLOW, (int(ball_x), int(ball_y)), BALL_RADIUS)

def draw_blocks():
    """ブロックを描画"""
    for block in blocks:
        if block['active']:
            if block_img:
                screen.blit(block_img, (block['x'], block['y']))
            else:
                pygame.draw.rect(screen, GREEN, 
                               (block['x'], block['y'], block['width'], block['height']))
                pygame.draw.rect(screen, WHITE, 
                               (block['x'], block['y'], block['width'], block['height']), 2)

def draw_enemies():
    """敵を描画"""
    for enemy in enemies:
        if enemy['active']:
            if enemy_img:
                screen.blit(enemy_img, (enemy['x'], enemy['y']))
            else:
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
    """玉とパドルの衝突判定（パドルのどこに当たったかだけで反射を決定）"""
    global ball_x, ball_y, ball_dx, ball_dy
    
    if (ball_y + BALL_RADIUS >= paddle_y and 
        ball_y - BALL_RADIUS <= paddle_y + PADDLE_HEIGHT and
        ball_x + BALL_RADIUS >= paddle_x and
        ball_x - BALL_RADIUS <= paddle_x + PADDLE_WIDTH):
        
        # パドルのどの位置に当たったか（0.0: 左端, 1.0: 右端）
        hit_pos = (ball_x - paddle_x) / PADDLE_WIDTH
        # -1.0（左端）〜 1.0（右端）
        offset = (hit_pos - 0.5) * 2.0
        
        if abs(offset) < 0.05:
            # ほぼ中央なら真上に反射
            ball_dx = 0
            ball_dy = -ball_speed
        else:
            # 中央から離れるほど傾きを大きくする
            tilt = PADDLE_MAX_TILT * abs(offset)  # 0〜最大傾き
            dir_x = -1 if offset < 0 else 1       # 左側に当たれば左、右側なら右
            
            ball_dx = dir_x * ball_speed * math.sin(tilt)
            ball_dy = -ball_speed * math.cos(tilt)
        
        ball_y = paddle_y - BALL_RADIUS

def check_ball_block_collision():
    """玉とブロックの衝突判定"""
    global ball_x, ball_y, ball_dx, ball_dy, score
    
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
            
            # 角度が緩やかになりすぎないようにする
            current_speed = math.sqrt(ball_dx**2 + ball_dy**2)
            if current_speed > 0:
                angle = math.atan2(abs(ball_dy), abs(ball_dx))
                # 角度が小さすぎる場合（水平に近い場合）、最小角度を保証
                if angle < MIN_ANGLE:
                    # 速度を保ちつつ角度を調整
                    if ball_dx > 0:
                        ball_dx = current_speed * math.cos(MIN_ANGLE)
                    else:
                        ball_dx = -current_speed * math.cos(MIN_ANGLE)
                    if ball_dy > 0:
                        ball_dy = current_speed * math.sin(MIN_ANGLE)
                    else:
                        ball_dy = -current_speed * math.sin(MIN_ANGLE)
            
            block['active'] = False
            score += 10
            return True
    
    return False

def check_ball_enemy_collision():
    """玉と敵の衝突判定"""
    global ball_x, ball_y, ball_dx, ball_dy, score
    
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
            
            # 角度が緩やかになりすぎないようにする
            current_speed = math.sqrt(ball_dx**2 + ball_dy**2)
            if current_speed > 0:
                angle = math.atan2(abs(ball_dy), abs(ball_dx))
                # 角度が小さすぎる場合（水平に近い場合）、最小角度を保証
                if angle < MIN_ANGLE:
                    # 速度を保ちつつ角度を調整
                    if ball_dx > 0:
                        ball_dx = current_speed * math.cos(MIN_ANGLE)
                    else:
                        ball_dx = -current_speed * math.cos(MIN_ANGLE)
                    if ball_dy > 0:
                        ball_dy = current_speed * math.sin(MIN_ANGLE)
                    else:
                        ball_dy = -current_speed * math.sin(MIN_ANGLE)
            
            enemy['active'] = False
            score += 20
            return True
    
    return False

def check_enemy_trapped():
    """敵がブロックに阻まれているかチェック（上下のブロック行にブロックが残っているか）"""
    for enemy in enemies:
        if not enemy['active'] or not enemy['trapped']:
            continue
        
        # 敵の上下にブロックがあるかチェック
        has_block_above = False
        has_block_below = False
        
        for block in blocks:
            if not block['active']:
                continue
            
            # 敵の上下のブロック行にあるブロックかチェック
            # 敵のY座標より上にあるブロック行
            if block['y'] < enemy['y']:
                # 同じ列（X座標が重なる）にあるかチェック
                if (block['x'] < enemy['x'] + enemy['width'] and
                    block['x'] + block['width'] > enemy['x']):
                    has_block_above = True
            
            # 敵のY座標より下にあるブロック行
            if block['y'] > enemy['y'] + enemy['height']:
                # 同じ列（X座標が重なる）にあるかチェック
                if (block['x'] < enemy['x'] + enemy['width'] and
                    block['x'] + block['width'] > enemy['x']):
                    has_block_below = True
        
        # 上下のブロック行にブロックが残っていれば阻まれている
        # どちらかのブロック行が全て崩されていれば動けるようになる
        if not (has_block_above and has_block_below):
            enemy['trapped'] = False

def update_enemies():
    """敵の移動（ギャラクシアン風 + 手前に移動）"""
    for enemy in enemies:
        if not enemy['active'] or enemy['trapped']:
            continue
        
        # タイマーを更新
        enemy['move_down_timer'] += 1
        
        # 一定時間ごとに手前に移動を試みる
        move_down = False
        if enemy['move_down_timer'] >= 60:  # 1秒ごと（60フレーム）
            move_down = True
            enemy['move_down_timer'] = 0
        
        # まず横方向の移動を試みる
        new_x = enemy['x'] + enemy['direction'] * enemy['speed']
        new_y = enemy['y']
        
        # 横方向の移動が有効かチェック
        if check_enemy_position_valid(new_x, new_y, enemy):
            enemy['x'] = new_x
        else:
            # 壁に当たったら方向転換
            if new_x <= LEFT_WALL_X + WALL_THICKNESS:
                enemy['x'] = LEFT_WALL_X + WALL_THICKNESS
                enemy['direction'] = 1
            elif new_x + enemy['width'] >= RIGHT_WALL_X:
                enemy['x'] = RIGHT_WALL_X - enemy['width']
                enemy['direction'] = -1
            
            # 横に移動できない場合は下に移動を試みる
            move_down = True
        
        # 下方向への移動を試みる
        if move_down:
            new_y = enemy['y'] + 10  # 下に10ピクセル移動
            if check_enemy_position_valid(enemy['x'], new_y, enemy):
                enemy['y'] = new_y

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


def reset_game():
    """ゲーム全体をリセット"""
    global lives, score, level_cleared, game_over
    lives = 3
    score = 0
    level_cleared = False
    game_over = False
    create_blocks()
    create_enemies()
    reset_ball()

# 初期化
create_blocks()
create_enemies()

# メインループ
clock = pygame.time.Clock()
running = True

while running:
    draw_background()
    
    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if game_over:
                if event.key == pygame.K_SPACE:
                    reset_game()
            else:
                if event.key == pygame.K_SPACE and not ball_active:
                    ball_active = True
    
    # キー入力（パドルの移動方向を追跡）
    keys = pygame.key.get_pressed()
    paddle_prev_x = paddle_x  # 前フレームの位置を保存
    if keys[pygame.K_LEFT] and paddle_x > LEFT_WALL_X + WALL_THICKNESS:
        paddle_x -= PADDLE_SPEED
        paddle_direction = -1  # 左に移動
    elif keys[pygame.K_RIGHT] and paddle_x + PADDLE_WIDTH < RIGHT_WALL_X:
        paddle_x += PADDLE_SPEED
        paddle_direction = 1  # 右に移動
    else:
        paddle_direction = 0  # 停止
    
    # 玉の移動
    if ball_active and not game_over:
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
                game_over = True
                ball_active = False
    else:
        if not game_over:
            # 玉が発射されていない時はパドルに追従
            ball_x = paddle_x + PADDLE_WIDTH // 2
    
    # 敵の更新
    if not game_over:
        check_enemy_trapped()
        update_enemies()
    
    # レベルクリア判定
    if not game_over:
        check_level_clear()
    
    # 描画
    draw_walls()
    draw_blocks()
    draw_enemies()
    draw_paddle()
    draw_ball()
    
    # UI表示（HUD上部に表示）
    score_text = font.render(f"Score: {score}", True, WHITE)
    lives_text = font.render(f"Lives: {lives}", True, WHITE)
    screen.blit(score_text, (10, 8))
    screen.blit(lives_text, (180, 8))
    
    if game_over:
        game_over_text = font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10))
        screen.blit(game_over_text, game_over_rect)

        prompt_text = font_small.render("PUSH SPACE KEY", True, WHITE)
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        screen.blit(prompt_text, prompt_rect)

    elif level_cleared:
        clear_text = font.render("LEVEL CLEARED!", True, YELLOW)
        text_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(clear_text, text_rect)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
