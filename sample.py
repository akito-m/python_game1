import pygame
from pygame import mixer
import random
import math

pygame.init()

screen = pygame.display.set_mode((800, 600))
# screen.fill((150, 150, 150))
pygame.display.set_caption('Invaders Game')

# Player
playerImg = pygame.image.load('player.png')
playerX, playerY = 370, 480
PlayerX_change = 0

# Enemy
enemyImg = pygame.image.load('enemy.png')
enemyX = random.randint(0, 736)
enemyY = random.randint(50, 150)
enemyX_change, enemyY_change = 1, 40

# Bullet
bulletImg = pygame.image.load('bullet.png')
bulletX, bulletY = 0, 480
bulletX_change, bulletY_change = 0, 3
bullet_state = 'ready'

# mixer.Sound('laser.wav').play()

# Score
Score_value = 0

def player(x, y):
    screen.blit(playerImg, (x, y))

def enemy(x, y):
    screen.blit(enemyImg, (x, y))

def fire_bullet(x, y):
    global bullet_state
    bullet_state = 'fire'
    screen.blit(bulletImg, (x + 16, y + 10))

def isCollision(enemyX, enemyY, bulletX, bulletY):
    distance = math.sqrt(math.pow(enemyX - bulletX, 2) + math.pow(enemyY - bulletY, 2))
    if distance < 27:
        return True
    return False

running = True
while running:
    screen.fill((0, 0, 0))
    # font = pygame.font.SysFont(None, 80)
    # message = font.render('Hello World', False, (255, 255, 255)) 
    # screen.blit(message, (20, 50))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                PlayerX_change = -1.5
            if event.key == pygame.K_RIGHT:
                PlayerX_change = 1.5
            if event.key == pygame.K_SPACE:
               if bullet_state == 'ready':
                    bulletX = playerX
                    fire_bullet(bulletX, bulletY)

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                PlayerX_change = 0

    # Player
    playerX += PlayerX_change
    if playerX <= 0:
        playerX = 0
    elif playerX >= 736:
        playerX = 736

    # Enemy
    if enemyY > 440:
        break
    enemyX += enemyX_change
    if enemyX <= 0:
        enemyX_change = 1
        enemyY += enemyY_change
    elif enemyX >= 736:
        enemyX_change = -1
        enemyY += enemyY_change

    collision = isCollision(enemyX, enemyY, bulletX, bulletY)
    if collision:
        mixer.Sound('laser.wav').play()
        bulletY = 480
        bullet_state = 'ready'
        Score_value += 1
        enemyX = random.randint(0, 736)
        enemyY = random.randint(50, 150)

    # Bullet Movement
    if bulletY <=0:
        bulletY = 480
        bullet_state = 'ready'

    if bullet_state == 'fire':
        fire_bullet(bulletX, bulletY)
        bulletY -= bulletY_change

    # Score
    font = pygame.font.SysFont(None, 32)
    score = font.render(f"Score: {str(Score_value)}", True, (255, 255, 255))
    screen.blit(score, (20, 50))

    player(playerX, playerY)
    enemy(enemyX, enemyY)
    pygame.display.update()