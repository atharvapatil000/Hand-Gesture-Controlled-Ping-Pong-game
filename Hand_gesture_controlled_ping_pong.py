import pygame, sys, random
import numpy as np
import cv2
import math


pygame.init()  # initiates all the pygame modules and is req before we run any kind of game
clock = pygame.time.Clock()


def ball_anim():
    global ball_speed_x, ball_speed_y, lives

    # Movement of the ball
    ball.x = ball_speed_x + ball.x
    ball.y = ball_speed_y + ball.y

    # Collisions
    if ball.top <= 0 or ball.bottom >= screen_height:  # ball is colliding with top and bottom of the screen
        ball_speed_y *= -1

    if ball.left <= 0:
        ball_restart()
        paddle_restart()

    if ball.right >= screen_width:
        lives -= 1
        ball_restart()
        paddle_restart()

    if ball.colliderect(player) or ball.colliderect(opponent):  # ball is colliding on both the paddles
        ball_speed_x *= -1

def quit():
    global lives
    if lives == 0: #if life is 0 then quit
        pygame.quit()
        sys.exit()

def player_anim():

    if player.top <= 0:  # if the player paddle top hits the top of the screen
        player.top = 0
    if player.bottom >= screen_height:  # if the player paddle top hits the bottom of the screen
        player.bottom = screen_height


def opponent_anim():

    if opponent.top < ball.y: #if the top of the opponent is below y cord of ball move the opponent by 10
        opponent.top += 10
    if opponent.top > ball.y: #if the top of the opponent is above y cord of ball move the opponent by 10
        opponent.top -= 10

    if opponent.top <= 0:  # if the player paddle top hits the top of the screen
        opponent.top = 0
    if opponent.bottom >= screen_height:  # if the player paddle top hits the bottom of the screen
        opponent.bottom = screen_height

def ball_restart():
    global  ball_speed_x, ball_speed_y
    ball.center = (screen_width/2, screen_height/2) #restart the ball at the og pos
    ball_speed_y *= random.choice((1,-1)) #ball will start from any direction
    ball_speed_x *= random.choice((1,-1))

def paddle_restart():
    global  player, opponent
    player = pygame.Rect(screen_width - 20, screen_height / 2 - 80, 10, 160)
    opponent = pygame.Rect(10, screen_height / 2 - 70, 10, 160)

def paddle_up():
    player.y = player.y - 10

def paddle_down():
    player.y = player.y + 10

# Setting up the window
screen_width = 1000
screen_height = 800
screen = pygame.display.set_mode(
    (screen_width, screen_height))  # display is a module and set_mode is a method that intializes a surface
pygame.display.set_caption('Hand-gesture controlled ping pong')

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0,0, 255)


# Objects
player = pygame.Rect(screen_width - 20, screen_height / 2 - 80, 10, 160)
opponent = pygame.Rect(10, screen_height / 2 - 70, 10, 160)
ball = pygame.Rect(screen_width / 2 - 12, screen_height / 2 - 12, 24, 24)

# speeds
ball_speed_x = 6 * random.choice((1,-1))
ball_speed_y = 6 * random.choice((1,-1))

# lives
lives = 5
game_font = pygame.font.Font('freesansbold.ttf', 32) #font for live text


# open camera
cap = cv2.VideoCapture(0)
while True:

    # capture frames from the cam
    _, frame = cap.read()

    # Get hand data from the rectangle sub window
    cv2.rectangle(frame, (100, 100), (300, 300), (0, 255, 0), 1)
    crop_image = frame[100:300, 100:300]

    # Apply Gausian blur
    blur = cv2.GaussianBlur(crop_image, (3, 3), 0)

    # change color-space from BGR to HSV
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    lc = np.array([0, 40, 60])
    hc = np.array([20, 150, 255])

    # create mask for skin color
    mask = cv2.inRange(hsv, lc, hc)

    # morphological operations
    kernel = np.ones((5, 5), np.uint8)
    dilation = cv2.dilate(mask, kernel, iterations=1)
    erosion = cv2.erode(dilation, kernel, iterations=1)

    # applying Gaussian Blur to remove noise
    filtered = cv2.GaussianBlur(erosion, (21, 21), 0)

    # thresh
    ret, thresh = cv2.threshold(filtered, 127, 255, 0)

    # FIND contours
    cont, hierarchy = cv2.findContours(filtered, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    try:
        # Find contour of max area i.e hand
        max_cont = max(cont, key=lambda x: cv2.contourArea(x))
        # print("max cont:",max_cont)

        # create bounding rectangle around the max contour
        x, y, w, h = cv2.boundingRect(max_cont)
        cv2.rectangle(crop_image, (x, y), (x + w, y + h), (0, 0, 255), 0)

        # Find Convex hull
        hull = cv2.convexHull(max_cont)
        # print("hull1", hull)

        # draw contours
        draw = np.zeros(crop_image.shape, np.uint8)
        cv2.drawContours(draw, [max_cont], -1, (0, 255, 0), 0)
        cv2.drawContours(draw, [hull], -1, (0, 255, 0), 0)
        # cv2.drawContours(crop_image, [max_cont], -1,(0,255,0), 0)
        # cv2.drawContours(crop_image, [hull], -1, (0,255,0), 0)

        hull = cv2.convexHull(max_cont, returnPoints=False)
        # print("hull2", hull)
        defects = cv2.convexityDefects(max_cont, hull)
        # print('defects', defects)
        defectshape = defects.shape[0]
        # print("defectshape", defectshape)

        # Use cosine rule to find the angle of farthest pt from start pt and end pt
        count_defects = 0

        for i in range(defectshape):
            # print('loop defect', defects[i][0])
            s, e, f, d = defects[i, 0]
            start = tuple(max_cont[s][0])
            # print('loop start', start)
            end = tuple(max_cont[e][0])
            far = tuple(max_cont[f][0])

            a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
            b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
            c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)

            angle = (math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 180) / 3.14

            # if angle < 90 draw a circle

            if angle <= 90:
                count_defects += 1
                cv2.circle(crop_image, far, 1, [0, 0, 255], -1)

            cv2.line(crop_image, start, end, [0, 255, 0], 2)

        if count_defects == 0:
            cv2.putText(frame, 'ONE', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)

        elif count_defects == 1:
            cv2.putText(frame, 'TWO', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
            paddle_up()

        elif count_defects == 2:
            cv2.putText(frame, 'THREE', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
            paddle_down()

        elif count_defects == 3:
            cv2.putText(frame, 'FOUR', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
            player.y = player.y + 20
        elif count_defects == 4:
            cv2.putText(frame, 'FIVE', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
        else:
            pass
    except:
        pass

    ball_anim()
    player_anim()
    opponent_anim()

    # Drawing the objects
    screen.fill(BLACK)
    pygame.draw.rect(screen, RED, player)
    pygame.draw.rect(screen, BLUE, opponent)
    pygame.draw.ellipse(screen, WHITE, ball)
    pygame.draw.aaline(screen, WHITE, (screen_width / 2, 0), (screen_width / 2, screen_height))

    lives_text = game_font.render("lives:" + str(lives), True, WHITE) #forms a surface/template to display the text for lives
    screen.blit(lives_text, (50,10)) #blitting the pixels of lives_text onto the screen

    # updating the window
    pygame.display.flip()  # update the entire screen
    quit()

    # cv2.imshow('frame', frame)
    # cv2.imshow('crop', blur)
    # cv2.imshow('mask', mask)
    # cv2.imshow('dil', dilation)
    # cv2.imshow('ers', erosion)
    # cv2.imshow('fil', filtered)
    # cv2.imshow('th', thresh)
    #cv2.imshow('drawing', draw)
    all_img = np.hstack((draw, crop_image))
    cv2.imshow('control', all_img)

    k = cv2.waitKey(1)

    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()
