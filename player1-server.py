#program that contains the main game and server
import socket, pygame, sys, threading, json, random as rd, os
#hahaha you can't close the game, you have to close the shell for that...meh good enough for now

pygame.init()
pygame.font.init()
pygame.mixer.init()
audio = "audio"

boom = pygame.mixer.Sound(os.path.join(audio, 'boom.ogg'))
ding = pygame.mixer.Sound(os.path.join(audio, 'ding.ogg'))
win = pygame.mixer.Sound(os.path.join(audio, 'win.ogg'))
theme = pygame.mixer.music.load(os.path.join(audio, 'theme.ogg'))

WIDTH, HEIGHT = 500,500

ADDR, PORT = "127.0.0.1", 1234 #change ADDR to socket.gethostbyname(socket.gethostname()) if using 2 different computers and PORT to anything 0-65536 (preferably >1024 because those are used usually by the system)
print(ADDR,PORT)

threading_event = threading.Event()
running = threading.Event()
running.set()

def getData():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ADDR, PORT))
        print("Waiting for Player 2 to connect...")
        sock.listen()
        addr, port = sock.accept()
        print(f"Client {port} connected.")
        pygame.mixer.music.play(-1)
        threading_event.set()

        while 1:
            data = addr.recv(1024)
            if not data or data == b"Byebye then":
                print("Connection closed by client.")
                sys.exit()

            enemy.rect.center = json.loads(data.decode())["pos"]
            if not running.is_set():
                addr.sendall(b"Byebye") #signal client that i'm closing
                sys.exit()
            else:
                addr.sendall(json.dumps({"pos":player.rect.center, 'ball':(ball.rect.center, ball.color), "scores":(player.score, enemy.score), "time": (ball.start_time, ball.current_time), "ding?": ball.ding}).encode())
                ball.ding = False

def runGame():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Player 1 (Server)")

    clock = pygame.time.Clock()
    k = None
    play = 1

    while 1:
        screen.fill("black")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running.clear() #i'm not running anymore, announce to data thread
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    k = "U"
                if event.key == pygame.K_DOWN:
                    k = "D"
            
            if event.type == pygame.KEYUP:
                k = None

        if not threading_event.is_set():
            screen.blit(fontSurf, fontRect)

        elif player.winner():
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
            pygame.draw.aaline(screen, (120,120,120), (WIDTH//2,0), (WIDTH//2,HEIGHT))   

            screen.blit(player.surf, player.rect)
            screen.blit(enemy.surf, enemy.rect)

            ball.color = (rd.randint(10,255),rd.randint(10,255),rd.randint(10,255))
            ball.surf.fill(ball.color)
            screen.blit(ball.surf, ball.rect)

            pScore_surf = pygame.font.Font(None, 40).render(str(player.score), True, (255,255,255))
            pScore_rect = pScore_surf.get_rect(center=(WIDTH*(1/4),20))
            eScore_surf = pygame.font.Font(None, 40).render(str(enemy.score), True, (255,150,150))
            eScore_rect = eScore_surf.get_rect(center=(WIDTH*(3/4),20))
            screen.blit(pScore_surf, pScore_rect)
            screen.blit(eScore_surf, eScore_rect)
        
            player.move(k)
            ball.move()

            if ball.start_time:
                ball.reset()
                screen.blit(ball.timer_font, ball.timer_rect)

        pygame.display.flip()
        clock.tick(30)

class Player:
    def __init__(self, pos=(WIDTH//2, HEIGHT//2), color="white"):
        self.surf = pygame.Surface((8,90))
        self.surf.fill(color)
        self.rect = self.surf.get_rect(center=pos)
        self.score = 0
        self.speed = 10
    
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
        self.speed_x = 7
        self.speed_y = 7
        self.start_time = None
        self.current_time = pygame.time.get_ticks()
        self.FONT_SIZE = 150
        self.font_size = 150
        self.x = 3
        self.ding = False

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT: #collide with top/bottom
            self.speed_y *= -1

        if self.rect.colliderect(player.rect) and self.speed_x < 0: #collide with player
            pygame.mixer.Sound.play(ding)
            self.ding = True
            if abs(self.rect.left - player.rect.right) < 10:
                self.speed_x *= -1
            elif abs(self.rect.bottom - player.rect.top) < 10 and self.speed_y > 0:
                self.speed_y *= -1
            elif abs(self.rect.top - player.rect.bottom) < 10 and self.speed_y < 0:
                self.speed_y *= -1

        if self.rect.colliderect(enemy.rect) and self.speed_x > 0: #collide with enemy
            pygame.mixer.Sound.play(ding)
            self.ding = True
            if abs(self.rect.right - enemy.rect.left) < 10:
                self.speed_x *= -1
            elif abs(self.rect.bottom - enemy.rect.top) < 10 and self.speed_y > 0:
                self.speed_y *= -1
            elif abs(self.rect.top - enemy.rect.bottom) < 10 and self.speed_y < 0:
                self.speed_y *= -1
        
        if ball.rect.left <= 0:
            pygame.mixer.Sound.play(boom)
            enemy.score += 1
            self.start_time = pygame.time.get_ticks()
            self.reset()
            
        
        if ball.rect.right >= WIDTH: #L haha
            pygame.mixer.Sound.play(boom)
            player.score += 1
            self.start_time = pygame.time.get_ticks()
            self.reset()

    def reset(self):
            self.rect.center = (WIDTH//2, HEIGHT//2)
            self.current_time = pygame.time.get_ticks()
            
            self.font_size -= 10
            if (3-(self.current_time-self.start_time)//1000) < self.x:
                self.x -= 1
                self.font_size = self.FONT_SIZE
            self.timer_font = pygame.font.Font(None, self.font_size).render(str(3-(self.current_time-self.start_time)//1000), True, (120,255,120))
            self.timer_rect = self.timer_font.get_rect(center=(WIDTH//2, HEIGHT//2))
            
            if (self.current_time - self.start_time) < 2500:
                self.speed_x, self.speed_y = 0,0
            else:
                self.speed_x = 7*rd.choice([-1,1])
                self.speed_y = 7*rd.choice([-1,1])
                self.start_time = None
                self.current_time = None
                self.x = 3
                self.font_size = self.FONT_SIZE

player = Player((20, HEIGHT//2))
enemy = Player((WIDTH-20, HEIGHT//2), (255,150,150))

ball = Ball()

fontSurf = pygame.font.Font(None, 30).render("Waiting for Player 2 to connect...", True, (255,150,150))
fontRect = fontSurf.get_rect(center=(WIDTH//2, HEIGHT//2))


if __name__ == "__main__":
    data_process = threading.Thread(target=getData)
    game_process = threading.Thread(target=runGame, daemon=True)

    data_process.start()
    game_process.start()