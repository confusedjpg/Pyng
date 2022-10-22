#program that contains the controller
import socket, sys, pygame, json, os
HOST, PORT = "127.0.0.1", 1234 #change according to the host
pygame.init()
pygame.font.init()
pygame.mixer.init()
audio = "audio"

boom = pygame.mixer.Sound(os.path.join(audio, 'boom.ogg'))
ding = pygame.mixer.Sound(os.path.join(audio, 'ding.ogg'))
win = pygame.mixer.Sound(os.path.join(audio, 'win.ogg'))
theme = pygame.mixer.music.load(os.path.join(audio, 'theme.ogg'))

WIDTH, HEIGHT = 500,500
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Player 2 (Client)")

class Player:
    def __init__(self, pos=(WIDTH//2, HEIGHT//2), color="white"):
        self.surf = pygame.Surface((8,90))
        self.surf.fill(color)
        self.rect = self.surf.get_rect(center=pos)
        self.speed = 10
        self.score = 0
    
    def move(self, dir):
        match dir:
            case "U":
                self.rect.y -= self.speed
            case "D":
                self.rect.y += self.speed

        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT

    def winner(self):
        if self.score >= 5:
            return True

class Ball:
    def __init__(self, color="white"):
        self.surf = pygame.Surface((15,15))
        self.color = color
        self.surf.fill(color)
        self.rect = self.surf.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.start_time = None
        self.current_time = pygame.time.get_ticks()
        self.FONT_SIZE = 150
        self.font_size = 150
        self.x = 3
        self.ding = False
    
    def reset(self):
            self.font_size -= 10
            if (3-(self.current_time-self.start_time)//1000) < self.x:
                self.x -= 1
                self.font_size = self.FONT_SIZE
            self.timer_font = pygame.font.Font(None, self.font_size).render(str(3-(self.current_time-self.start_time)//1000), True, (150,255,150))
            self.timer_rect = self.timer_font.get_rect(center=(WIDTH//2, HEIGHT//2))
                

player = Player((WIDTH-20, HEIGHT//2))
enemy = Player((20, HEIGHT//2), (255,150,150))

ball = Ball()

clock = pygame.time.Clock()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    print("Connected to server.")
    pygame.mixer.music.play(-1)
    k = None
    play = 1
    lost = 1
    while 1:
        screen.fill("black")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    k = "U"
                if event.key == pygame.K_DOWN:
                    k = "D"

            if event.type == pygame.KEYUP:
                k = None
        
        if player.winner():
            if play:
                pygame.mixer.Sound.play(win)
                play = 0
            winner_font = pygame.font.Font(None, 50).render("You won!", True, (120,255,120))
            winner_rect = winner_font.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(winner_font, winner_rect)
        
        elif enemy.winner():
            winner_font = pygame.font.Font(None, 50).render("The opponent won!", True, (255,120,120))
            winner_rect = winner_font.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(winner_font, winner_rect)
        
        else:
            player.move(k)

            pygame.draw.aaline(screen, (120,120,120), (WIDTH//2,0), (WIDTH//2,HEIGHT))

            screen.blit(player.surf, player.rect)
            screen.blit(enemy.surf, enemy.rect)

            ball.surf.fill(ball.color)
            screen.blit(ball.surf, ball.rect)

            pScore_surf = pygame.font.Font(None, 40).render(str(player.score), True, (255,255,255))
            pScore_rect = pScore_surf.get_rect(center=(WIDTH*(3/4),20))
            eScore_surf = pygame.font.Font(None, 40).render(str(enemy.score), True, (255,150,150))
            eScore_rect = eScore_surf.get_rect(center=(WIDTH*(1/4),20))
            screen.blit(pScore_surf, pScore_rect)
            screen.blit(eScore_surf, eScore_rect)

            if ball.start_time:
                if lost:
                    pygame.mixer.Sound.play(boom)
                    lost = 0
                ball.reset()
                screen.blit(ball.timer_font, ball.timer_rect)
            else:
                ball.x = 3
                ball.font_size = ball.FONT_SIZE
                lost = 1

            if ball.ding:
                pygame.mixer.Sound.play(ding)
                ball.ding = 0

        pygame.display.flip()
        clock.tick(30)

        sock.sendall(json.dumps({"pos":player.rect.center}).encode())
        received = sock.recv(1024)
        if received == b"Byebye":
            sys.exit("Connection closed by server.")
        received = json.loads(received.decode())
        enemy.rect.center = received["pos"]
        ball.rect.center = received["ball"][0]
        ball.color = received["ball"][1]
        enemy.score = received["scores"][0]
        player.score = received["scores"][1]
        ball.start_time = received["time"][0]
        ball.current_time = received["time"][1]
        ball.ding = received["ding?"]
