import math
import random
import socket
import pygame
import cv2
import dbConnect

hostname=socket.gethostname()
IPAddr=socket.gethostbyname(hostname)
pygame.init()
pygame.mixer.init(44100, -16, 2, 1160000)
W, H = 960, 540
pygame.display.set_caption("MediBoom: Medical Shooter Game")
pygame.mouse.set_visible(False)
sc = pygame.display.set_mode((W, H))
map = pygame.Surface((W, H))
lights = pygame.Surface((W, H))
bloods = pygame.Surface((W, H), pygame.SRCALPHA)
pygame.display.set_icon(pygame.image.load("logo.png"))
mI = pygame.transform.scale(pygame.image.load("menu.png").convert_alpha(), (W, H))
loginB = pygame.transform.scale(pygame.image.load("loginB.png").convert_alpha(), (120, 44))
registerB = pygame.transform.scale(pygame.image.load("registerB.png").convert_alpha(), (204, 44))
lamp = pygame.image.load("light.png").convert_alpha()
playButton = pygame.transform.scale(pygame.image.load("play.png").convert_alpha(), (120, 80))
cr = pygame.image.load("crosshair.png").convert_alpha()
bossTrigger = pygame.image.load("fight.png").convert_alpha()
font = pygame.font.Font("Teko-Medium.ttf", 30)

guns = []
bomb = []
melee = []
selected = "knife"

des = {
    #image, projectile type, side effect, type, cd, DPS, effect time
    "Vaccine":[pygame.image.load("Vaccine/pixil-frame-0.png").convert_alpha(),
                  "Splash", "Repel", "Gun",
                  3, 1, 5],
    # image, projectile type, side effect, type, cd, DMG when explode, CD to explode
    "Pill":[pygame.image.load("Pill/pixil-frame-0.png").convert_alpha(),
               "Rocket", "Follow mouse, explode", "Missile",
               5, 5, 5],
    # image, projectile type, side effect, type, cd, DPP, projectile lifetime
    "Stetoscope":[pygame.image.load("Stetoscope/pixil-frame-0.png").convert_alpha(),
                     "Wave", "Boundary bounce", "Gun",
                     2, 0.5, 2],
    # image, projectile type, side effect, type, cd, DPS, effect time, time until puddle gone
    "Shield":[pygame.image.load("Shield/pixil-frame-0.png").convert_alpha(),
                 "Splash", "Froze", "Gun",
                 3, 0.5, 5, 10],
    # image, projectile type, side effect, type, cd, DMG when explode, time until explode, range
    "XRay":[pygame.image.load("xray.png").convert_alpha(),
               "Wave", "Attract, explode", "Bomb",
               5, 7, 10, 50],
    # image, projectile type, side effect, type, cd, DMG/Heal PS, time until explode, range
    "Heal":[pygame.image.load("heal.png").convert_alpha(),
               "Wave", "Drain, explode", "Bomb",
               3, 3, 5, 30],
    # image, projectile type, side effect, type, cd, DMG, trigger key, range
    "c4":[pygame.image.load("c4.png").convert_alpha(),
                "Triggered", "Explode", "Bomb",
                3, 10, "E", 100],
    #image, type, cd, DMG
    "knife":[pygame.image.load("knife.png").convert_alpha(),
             "Melee", 3, 5]}

for k in list(des.keys()):
    if des[k][3] == "Gun" or des[k][3] == "Missile":
        guns.append(k)
    elif des[k][3] == "Bomb":
        bomb.append(k)
    else:
        melee.append(k)

menuTheme = "Theme/19. Race Track Chimes.wav"
gameTheme = ["Theme/12. Floating in the Abyss.wav",
             "Theme/11. Poseidon's Realm.wav",
             "Theme/13. Sunlight at Midnight.wav"]
current_list = []

for i in range(W // 10):
    for k in range(H // 10):
        map.blit(pygame.image.load(f"floor{random.randint(1, 2)}.png").convert_alpha(), (i * 10, k * 10))

for i in range(10):
    bloods.blit(pygame.image.load(f"blood{random.randint(0, 2)}.png").convert_alpha(),
                (random.randint(0, W), random.randint(0, H)))

introM = cv2.VideoCapture("intro.mp4")
success, video_image = introM.read()
clock = pygame.time.Clock()
stage = 1
stages = ["Flu I", "Flu II", "Cancer I", "Cancer II", "Heart I", "Heart II", "Cancer III", "Stadium IV", "Holy Body"]
bossStage = False

types = {"Flu": [[pygame.image.load("Flu/pixil-frame-0.png").convert_alpha(),
                  pygame.image.load("Flu/pixil-frame-1.png").convert_alpha(),
                  pygame.image.load("Flu/pixil-frame-2.png").convert_alpha()], 1, 50, 20,
                  10, 5, pygame.image.load("Flu/virus.png").convert_alpha(), 10, 5],
         "Cancer": [[pygame.image.load("Cancer/pixil-frame-0.png").convert_alpha(),
                  pygame.image.load("Cancer/pixil-frame-1.png").convert_alpha(),
                  pygame.image.load("Cancer/pixil-frame-2.png").convert_alpha()], 1, 100, 50, 15, 20,
                  pygame.image.load("Cancer/paracyte.png").convert_alpha(), 5, 15],
         "Heart": [[pygame.image.load("Heart/pixil-frame-0.png").convert_alpha(),
                  pygame.image.load("Heart/pixil-frame-1.png").convert_alpha(),
                  pygame.image.load("Heart/pixil-frame-2.png").convert_alpha()], 2, 250, 1000000, 50, 35],
         "All": [[pygame.image.load("All/pixil-frame-0.png").convert_alpha(),
                  pygame.image.load("All/pixil-frame-1.png").convert_alpha(),
                  pygame.image.load("All/pixil-frame-2.png").convert_alpha()], 3, 500, 1000000, 999, 999]
         }
m = "Singleplayer"

en = []
bs = []
proj = []
bombs = []
eCount = 0

class DropDown():
    def __init__(self, color_menu, color_option, x, y, w, h, font, main, options):
        self.color_menu = color_menu
        self.color_option = color_option
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.main = main
        self.options = options
        self.draw_menu = False
        self.menu_active = False
        self.active_option = -1

    def draw(self, surf):
        pygame.draw.rect(surf, self.color_menu[self.menu_active], self.rect, 0, 10)
        pygame.draw.rect(surf, (0,0,0), self.rect, 3, 10)
        msg = self.font.render(self.main, 1, (0, 0, 0))
        surf.blit(msg, msg.get_rect(center=self.rect.center))

        if self.draw_menu:
            for i, text in enumerate(self.options):
                rect = self.rect.copy()
                rect.y += (i + 1) * self.rect.height
                pygame.draw.rect(surf, self.color_option[1 if i == self.active_option else 0], rect, 0, 10)
                pygame.draw.rect(surf, (0,0,0), rect, 3, 10)
                msg = self.font.render(text, 1, (0, 0, 0))
                surf.blit(msg, msg.get_rect(center=rect.center))

    def update(self, event_list):
        mpos = pygame.mouse.get_pos()
        self.menu_active = self.rect.collidepoint(mpos)

        self.active_option = -1
        for i in range(len(self.options)):
            rect = self.rect.copy()
            rect.y += (i + 1) * self.rect.height
            if rect.collidepoint(mpos):
                self.active_option = i
                break

        if not self.menu_active and self.active_option == -1:
            self.draw_menu = False

        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.menu_active:
                    self.draw_menu = not self.draw_menu
                elif self.draw_menu and self.active_option >= 0:
                    self.draw_menu = False
                    return self.active_option
        return -1

class Boss:
    def __init__(self, x, y, ty):
        self.anim = 0
        self.type = ty
        self.image = types[ty][0][self.anim]
        self.x, self.y = x, y
        self.HP = types[ty][2]
        self.t = False
        self.xVel, self.yVel = 0, 0
        self.speed = types[ty][1]
        self.sCount = 0
        self.rect = self.image.get_rect()
        self.cd = types[self.type][8]
    def update(self, usr, player):
        global stage, proj
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
        self.sCount += 0.1
        self.anim = round(self.sCount)%3
        self.image = pygame.transform.scale(types[self.type][0][self.anim], (100, 100))
        a = (self.x < player.x)
        d = (self.x > player.x)
        s = (self.y < player.y)
        w = (self.y > player.y)
        self.cd -= 0.1
        if stage == 2 or stage == 4:
            if self.cd <= 0:
                self.cd = types[self.type][8]
                proj.append(Projectile(self.x, self.y, self))
        if d:
            self.t = False
        if a:
            self.t = True
        self.xVel += (a - d)*self.speed
        self.yVel += (s - w) * self.speed
        self.xVel *= 0.3
        self.yVel *= 0.3
        self.x += self.xVel
        self.y += self.yVel
        if self.x < 0:
            self.x = W-1
        elif self.x > W:
            self.x = 1
        if self.y < 0:
            self.y = H-1
        elif self.y > H:
            self.y = 1
        if self.HP <= 0:
            if stage < 9:
                proj = []
                stage += 1
                if stage > dbConnect.check_user(usr)[0]["stage"]:
                    dbConnect.update(usr, "stage", stage)
            else:
                proj = []
                stage = 9
                dbConnect.update(usr, "stage", 9)
        sc.blit(pygame.transform.flip(self.image, self.t, False), (self.x,self.y))

class Minion:
    def __init__(self, x, y, ty):
        self.anim = 0
        self.type = ty
        self.image = types[ty][0][self.anim]
        self.x, self.y = x, y
        self.HP = types[ty][2]//5
        self.t = False
        self.xVel, self.yVel = 0, 0
        self.speed = types[ty][1]*2
        self.sCount = 0
        self.rect = self.image.get_rect()
        self.dmg = types[self.type][3]//5
        self.cd = types[self.type][8]
    def update(self, usr, player):
        self.cd -= 0.1
        if stage == 2 or stage == 4:
            if self.cd <= 0:
                self.cd = types[self.type][8]
                proj.append(Projectile(self.x, self.y, self))
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
        self.sCount += 0.1
        self.anim = round(self.sCount)%3
        self.image = types[self.type][0][self.anim]
        a = (self.x < player.x)
        d = (self.x > player.x)
        s = (self.y < player.y)
        w = (self.y > player.y)
        if d:
            self.t = False
        if a:
            self.t = True
        self.xVel += (a - d)*self.speed
        self.yVel += (s - w) * self.speed
        self.xVel *= 0.3
        self.yVel *= 0.3
        self.x += self.xVel
        self.y += self.yVel
        if self.x < 0:
            self.x = W-1
        elif self.x > W:
            self.x = 1
        if self.y < 0:
            self.y = H-1
        elif self.y > H:
            self.y = 1
        if self.HP <= 0 and self in en:
            check = dbConnect.check_user(usr)[0]
            en.remove(self)
            dbConnect.update(usr, "kills", check["kills"]+1)
            dbConnect.update(usr, "coin", check["coin"]+types[self.type][5])
            dbConnect.update(usr, "XP", check["XP"] + types[self.type][4])
        sc.blit(pygame.transform.flip(self.image, self.t, False), (self.x,self.y))

class Player:
    def __init__(self, x, y, speed, usr):
        self.image = pygame.image.load("player.png").convert_alpha()
        self.x, self.y = x, y
        dbConnect.update(usr, "HP", dbConnect.check_user(usr)[0]["MaxHP"])
        self.HP = dbConnect.check_user(usr)[0]["MaxHP"]
        self.t = False
        self.xVel, self.yVel = 0, 0
        self.speed = speed
    def update(self, usr, boss):
        check = dbConnect.check_user(usr)[0]
        k_d = pygame.key.get_pressed()
        if k_d[pygame.K_d]:
            self.t = False
        if k_d[pygame.K_a]:
            self.t = True
        self.xVel += (k_d[pygame.K_d] - k_d[pygame.K_a])*self.speed
        self.yVel += (k_d[pygame.K_s] - k_d[pygame.K_w]) * self.speed
        self.xVel *= 0.8
        self.yVel *= 0.8
        self.x += self.xVel
        self.y += self.yVel
        if self.x < 0:
            self.x = W-1
        elif self.x > W:
            self.x = 1
        if self.y < 0:
            self.y = H-1
        elif self.y > H:
            self.y = 1
        kR = self.image.get_rect().copy()
        kR.x, kR.y = self.x, self.y
        for e in en:
            if e.rect.colliderect(kR):
                dbConnect.update(usr, "HP", check["HP"]-e.dmg)
        if kR.colliderect(boss.rect):
            dbConnect.update(usr, "HP", check["HP"] - types[boss.type][3])
        check = dbConnect.check_user(usr)[0]
        self.HP = check["HP"]
        pygame.draw.rect(sc, (50, 50, 50), pygame.Rect(self.x, self.y + kR.height + 10, 20, 5))
        pygame.draw.rect(sc, (50, 255, 50), pygame.Rect(self.x, self.y + kR.height + 10, 20*(check["HP"]/check["MaxHP"]), 5))
        sc.blit(pygame.transform.flip(self.image, self.t, False), (self.x,self.y))

class Weapon:
    def __init__(self, type, player):
        self.x = player.x + 7.5
        self.y = player.y + 7.5
        self.type = type
        self.slashTrue = 0
        k = 4
        if type in melee:
            k = 2
        self.cd = des[type][k]
        self.lastCD = des[type][k]
        self.rect = pygame.Rect(0,0,1,1)
    def shoot(self):
        bs.append(Bullet(self.x, self.y, self))
    def slash(self):
        for d in en:
            if d.rect.colliderect(self.rect):
                d.HP -= des[self.type][3]
    def attach(self):
        bombs.append(Bomb(self.x, self.y, self))
    def update(self, player):
        self.slashTrue = (pygame.mouse.get_pressed()[0] and self.cd < 0) * 10
        self.cd -= 0.1
        if pygame.mouse.get_pressed()[0] and self.cd < 0:
            if des[self.type][1] == "Rocket" or des[self.type][3] == "Gun":
                self.shoot()
                self.cd = self.lastCD
            elif des[self.type][3] == "Bomb":
                self.attach()
                self.cd = self.lastCD
            elif des[self.type][1] == "Melee":
                self.slash()
                self.cd = self.lastCD
        self.x = player.x + 7.5
        self.y = player.y + 7.5
        dx = pygame.mouse.get_pos()[0] - self.x
        dy = pygame.mouse.get_pos()[1] - self.y
        a = (180 / math.pi) * math.atan2(-dy, dx)
        # surf, image, pos, originPos, angle
        self.rect = blitRotate(sc, pygame.transform.flip(des[self.type][0], False,
                                             pygame.mouse.get_pos()[0] < self.x-50),
                   (self.x, self.y), (-20 - self.slashTrue, (des[self.type][0].get_height()/2)), a)

class Bullet:
    def __init__(self, x, y, par):
        self.par = par
        self.img = pygame.image.load(f"{par.type}/Bullet.png").convert_alpha()
        self.x = x
        self.y = y
        self.idx = 0
        self.aC = 0
        self.explosion = False
        self.bounce = False
        if des[par.type][1] == "Rocket":
            self.explosion = True
            self.k = des[par.type][6]
            self.trail = []
            self.cdTrail = 0.3
        if des[par.type][1] == "Wave" and des[par.type][3] == "Gun":
            self.bounce = True
            self.size = 1
        dx = pygame.mouse.get_pos()[0] - self.x
        dy = pygame.mouse.get_pos()[1] - self.y
        self.a = (180 / math.pi) * math.atan2(-dy, dx)
        self.angle = math.atan2(pygame.mouse.get_pos()[1]-self.y, pygame.mouse.get_pos()[0] - self.x)
        self.velX = math.cos(self.angle) * 3
        self.velY = math.sin(self.angle) * 3
        self.rect = self.img.get_rect()
        self.collide = False
    def update(self, boss):
        self.rect.x = self.x
        self.rect.y = self.y
        if not self.collide:
            for d in en:
                if d.rect.colliderect(self.rect):
                    self.collide = True
                    d.HP -= des[self.par.type][5]
                    break
        if not self.collide:
            if boss.rect.colliderect(self.rect):
                self.collide = True
                boss.HP -= des[self.par.type][5]
        bounds = sc.get_rect()
        if self.explosion:
            if self.k > 0:
                if not self.collide:
                    self.x += self.velX
                    self.y += self.velY
                    for i in self.trail:
                        if i[2] < 0:
                            self.trail.remove(i)
                        else:
                            i[2] -= 0.1
                            pygame.draw.circle(sc, (255, 255, 255), (i[0], i[1]), i[2])
                    self.cdTrail -= 0.1
                    if self.cdTrail < 0:
                        self.cdTrail = 0.3
                        self.trail.append([self.x, self.y, 3])
                    self.k -= .1
                    dx = pygame.mouse.get_pos()[0] - self.x
                    dy = pygame.mouse.get_pos()[1] - self.y
                    self.a = (180 / math.pi) * math.atan2(-dy, dx)
                    self.angle = math.atan2(pygame.mouse.get_pos()[1]-self.y, pygame.mouse.get_pos()[0] - self.x)
                    self.velX = math.cos(self.angle) * 3
                    self.velY = math.sin(self.angle) * 3
                else:
                    self.k = 0
            else:
                self.velX = 0
                self.velY = 0
                self.trail = []
                self.aC += 0.3
                self.idx = round(self.aC)
                if self.idx >= 7 and self in bs:
                    bs.remove(self)
                self.img = pygame.image.load(f"Explosion/{self.idx}.png")
        elif self.bounce:
            self.x += self.velX
            self.y += self.velY
            self.size += 0.1
            self.img = pygame.transform.scale(pygame.image.load(f"{self.par.type}/Bullet.png").convert_alpha(), (pygame.image.load(f"{self.par.type}/Bullet.png").convert_alpha().get_width()+(pygame.image.load(f"{self.par.type}/Bullet.png").convert_alpha().get_width()*self.size), pygame.image.load(f"{self.par.type}/Bullet.png").convert_alpha().get_height()+(pygame.image.load(f"{self.par.type}/Bullet.png").convert_alpha().get_height()*self.size)))
            if self.size >= 25 and self in bs:
                bs.remove(self)
            if self.x - self.img.get_rect().width < bounds.left or self.x + self.img.get_rect().width > bounds.right:
                self.velX *= -1
            if self.y - self.img.get_rect().height < bounds.top or self.y + self.img.get_rect().height > bounds.bottom:
                self.velY *= -1
        else:
            self.x += self.velX
            self.y += self.velY
        # surf, image, pos, originPos, angle
        blitRotate(sc, self.img, (self.x, self.y), (0, 0), self.a)

class Projectile:
    def __init__(self, x, y, par):
        self.par = par
        self.img = types[par.type][6]
        self.x = x
        self.y = y
        self.idx = 0
        self.aC = 0
        dx = pygame.mouse.get_pos()[0] - self.x
        dy = pygame.mouse.get_pos()[1] - self.y
        self.a = (180 / math.pi) * math.atan2(-dy, dx)
        self.e = 0
        self.angle = 0
        self.velX = math.cos(self.angle) * 3
        self.velY = math.sin(self.angle) * 3
        self.rect = self.img.get_rect()
        self.collide = False
    def update(self, player, usr):
        self.rect.x = self.x
        self.rect.y = self.y
        if not self.collide:
            pR = player.image.get_rect()
            pR.x, pR.y = player.x, player.y
            if pR.colliderect(self.rect):
                self.collide = True
                dbConnect.update(usr, "HP", dbConnect.check_user(usr)[0]["HP"] - types[self.par.type][5])
        if not self.collide:
            self.x += self.velX
            self.y += self.velY
            dx = pygame.mouse.get_pos()[0] - self.x
            dy = pygame.mouse.get_pos()[1] - self.y
            self.a = (180 / math.pi) * math.atan2(-dy, dx)
            self.e += 10
            self.angle = math.atan2(player.y-self.y, player.x - self.x)
            self.velX = math.cos(self.angle) * 3
            self.velY = math.sin(self.angle) * 3
            self.img = pygame.transform.rotate(self.img, self.e)
        else:
            self.velX = 0
            self.velY = 0
            self.aC += 0.3
            self.idx = round(self.aC)
            if self.idx >= 7 and self in bs:
                bs.remove(self)
            self.img = pygame.image.load(f"Explosion/{self.idx}.png")
        # surf, image, pos, originPos, angle
        blitRotate(sc, self.img, (self.x, self.y), (0, 0), self.a)

class Bomb:
    def __init__(self, x, y, par):
        self.par = par
        self.img = des[self.par.type][0]
        self.x = x
        self.y = y
        self.idx = 0
        self.aC = 0
        if des[self.par.type][1] == "Triggered":
            self.trig = pygame.key.get_pressed()[pygame.K_e]
        else:
            self.cd = des[self.par.type][6]
            self.trig = self.cd < 0
        if des[self.par.type][1] == "Wave":
            self.wave = []
            self.cdWave = 1
            self.k = 0
        self.expl = False
    def explode(self):
        self.aC += 0.3
        self.idx = round(self.aC)
        if self.idx >= 7 and self in bombs:
            for i in en:
                if math.sqrt((self.x-i.x)**2 + (self.y - i.y)**2)<=des[self.par.type][7]:
                    i.HP -= des[self.par.type][5]
            bombs.remove(self)
        self.img = pygame.image.load(f"Explosion/{self.idx}.png")
    def update(self, player):
        if des[self.par.type][1] == "Wave" and not self.expl:
            self.cdWave -= 0.1
            if self.cdWave < 0:
                self.cdWave = 1
                self.wave.append([self.x+(self.img.get_width()/2), self.y+(self.img.get_height()/2), self.k])
            for i in self.wave:
                if i[2] < des[self.par.type][7]:
                    i[2] += 1
                    pygame.draw.circle(sc, (150, 20, 20), (i[0], i[1]), i[2], 3)
        if "Drain" in des[self.par.type][2]:
            for i in en:
                if math.sqrt((self.x-i.x)**2 + (self.y - i.y)**2)<=des[self.par.type][7]:
                    i.HP -= des[self.par.type][5]
            if math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2) <= des[self.par.type][7]:
                player.HP += des[self.par.type][5]
        if des[self.par.type][1] == "Triggered":
            self.trig = pygame.key.get_pressed()[pygame.K_e]
        else:
            self.cd -= 0.1
            self.trig = self.cd < 0
        if self.trig:
            self.expl = True
        if self.expl:
            self.explode()
            if des[self.par.type][1] == "Wave":
                self.wave = []
        sc.blit(self.img, (self.x, self.y))

class Floor:
    def __init__(self, x, y):
        self.x = x*50
        self.y = y*50
    def update(self):
        sc.blit(pygame.image.load("floor.png").convert_alpha(), (self.x, self.y))

class MuteButton:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.mute = False
        self.img = None
        self.r = None
    def update(self):
        if self.mute:
            self.img = pygame.image.load("mute.png").convert_alpha()
            pygame.mixer.music.set_volume(0)
        else:
            self.img = pygame.image.load("unmute.png").convert_alpha()
            pygame.mixer.music.set_volume(100)
        self.r = self.img.get_rect().copy()
        self.r.x, self.r.y = self.x, self.y
        sc.blit(self.img, (self.x, self.y))

COLOR_INACTIVE = (166, 166, 166)
COLOR_ACTIVE = (200, 200, 200)
COLOR_LIST_INACTIVE = (255, 100, 100)
COLOR_LIST_ACTIVE = (255, 150, 150)
#color_menu, color_option, x, y, w, h, font, main, options
mode = DropDown(
    [COLOR_INACTIVE, COLOR_ACTIVE],
    [COLOR_LIST_INACTIVE, COLOR_LIST_ACTIVE],
    25, 135, 215, 50,
    font,
    "Singleplayer Mode", ["Singleplayer", "Online"])
lbTypeDrop = DropDown(
    [COLOR_INACTIVE, COLOR_ACTIVE],
    [COLOR_LIST_INACTIVE, COLOR_LIST_ACTIVE],
    W-120, 133, 70, 40,
    font,
    "stage", ["stage", "coin", "kills", "level"])
mBt = MuteButton(W-20, 20)

def blitRotate(surf, image, pos, originPos, angle):
    image_rect = image.get_rect(topleft=(pos[0] - originPos[0], pos[1] - originPos[1]))
    offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center
    rotated_offset = offset_center_to_pivot.rotate(-angle)
    rotated_image_center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)
    surf.blit(rotated_image, rotated_image_rect)
    return rotated_image_rect

def intro():
    run = 1
    while run:
        success, video_image = introM.read()
        try:
            video_surf = pygame.image.frombuffer(
                video_image.tobytes(), video_image.shape[1::-1], "BGR")
            sc.blit(pygame.transform.scale(video_surf, (W, H)), (0, 0))
            pygame.display.update()
            clock.tick(20)
        except:
            run = 0
    login()

def login():
    run = 1
    password = ''
    username = ''
    enterPswd = False
    enterUsername = False
    clrU = (255,255,255)
    clrP = (255,255,255)
    while run:
        sc.fill((0, 0, 0))
        sc.blit(pygame.transform.scale(pygame.image.load("login.png").convert_alpha(), (W, H)), (0,0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = 0
            elif event.type == pygame.KEYDOWN:
                if enterPswd:
                    if event.key == pygame.K_BACKSPACE and len(password) > -1:
                        password = password[:-1]
                    else:
                        password += event.unicode
                if enterUsername:
                    if event.key == pygame.K_BACKSPACE and len(username) > -1:
                        username = username[:-1]
                    else:
                        username += event.unicode
        selfW, selfH = 250, 25
        usernameRect = pygame.Rect((W//2)-(selfW//2), (H//2)-(selfH//2)-20, selfW, selfH)
        passwordRect = pygame.Rect((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) + 20, selfW, selfH)
        if usernameRect.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)) and pygame.mouse.get_pressed()[0]:
            enterUsername = True
            enterPswd = False
        if passwordRect.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)) and pygame.mouse.get_pressed()[0]:
            enterUsername = False
            enterPswd = True
        pygame.draw.rect(sc, (50, 50, 50), usernameRect)
        if enterUsername:
            pygame.draw.rect(sc, clrU, usernameRect, 1)
        pygame.draw.rect(sc, (50, 50, 50), passwordRect)
        if enterPswd:
            pygame.draw.rect(sc, clrP, passwordRect, 1)
        if username == "":
            sc.blit(font.render("username", True, (150, 150, 150)),
                    ((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) - 28))
        else:
            sc.blit(font.render(username, True, (255, 255, 255)),
                    ((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) - 28))
        if password == "":
            sc.blit(font.render("password", True, (150, 150, 150)),
                    ((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) + 12))
        else:
            sc.blit(font.render(password, True, (255, 255, 255)),
                    ((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) + 12))
        sc.blit(loginB, ((W//2)-(loginB.get_width()//2), (H // 2) - (selfH // 2) + 80))
        lbR = loginB.get_rect().copy()
        lbR.x, lbR.y = (W//2)-(loginB.get_width()//2), (H // 2) - (selfH // 2) + 80
        if lbR.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)) and pygame.mouse.get_pressed()[0]:
            k = dbConnect.check_user(username)
            if len(k) == 0:
                clrP = (255, 0, 0)
                clrU = (255, 0, 0)
            elif password != k[0]["password"]:
                clrU = (255, 255, 255)
                clrP = (255, 0, 0)
            else:
                menu(username)
                run = 0
        f = font.render("or Register", True, (50, 255, 50))
        fr = f.get_rect().copy()
        fr.x, fr.y = (W // 2) - (f.get_width() // 2), (H // 2) - (selfH // 2) + 150
        sc.blit(f, ((W // 2) - (f.get_width() // 2), (H // 2) - (selfH // 2) + 150))
        if fr.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)) and pygame.mouse.get_pressed()[0]:
            register()
            run = 0
        sc.blit(cr, (pygame.mouse.get_pos()))
        pygame.display.update()
        clock.tick(60)

def register():
    run = 1
    password = ''
    username = ''
    enterPswd = False
    enterUsername = False
    while run:
        sc.fill((0, 0, 0))
        sc.blit(pygame.transform.scale(pygame.image.load("register.png").convert_alpha(), (W, H)), (0,0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = 0
            elif event.type == pygame.KEYDOWN:
                if enterPswd:
                    if event.key == pygame.K_RETURN:
                        dbConnect.add_user(username, password)
                    elif event.key == pygame.K_BACKSPACE and len(password) > -1:
                        password = password[:-1]
                    else:
                        password += event.unicode
                if enterUsername:
                    if event.key == pygame.K_BACKSPACE and len(username) > -1:
                        username = username[:-1]
                    else:
                        username += event.unicode
        selfW, selfH = 250, 25
        usernameRect = pygame.Rect((W//2)-(selfW//2), (H//2)-(selfH//2)-20, selfW, selfH)
        passwordRect = pygame.Rect((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) + 20, selfW, selfH)
        if usernameRect.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)) and pygame.mouse.get_pressed()[0]:
            enterUsername = True
            enterPswd = False
        if passwordRect.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)) and pygame.mouse.get_pressed()[0]:
            enterUsername = False
            enterPswd = True
        pygame.draw.rect(sc, (50, 50, 50), usernameRect)
        if enterUsername:
            pygame.draw.rect(sc, (255,255,255), usernameRect, 1)
        pygame.draw.rect(sc, (50, 50, 50), passwordRect)
        if enterPswd:
            pygame.draw.rect(sc, (255,255,255), passwordRect, 1)
        if username == "":
            sc.blit(font.render("username", True, (150, 150, 150)),
                    ((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) - 28))
        else:
            sc.blit(font.render(username, True, (255, 255, 255)),
                    ((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) - 28))
        if password == "":
            sc.blit(font.render("password", True, (150, 150, 150)),
                    ((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) + 12))
        else:
            sc.blit(font.render(password, True, (255, 255, 255)),
                    ((W // 2) - (selfW // 2), (H // 2) - (selfH // 2) + 12))
        sc.blit(registerB, ((W // 2) - (registerB.get_width() // 2), (H // 2) - (selfH // 2) + 80))
        rbR = registerB.get_rect().copy()
        rbR.x, rbR.y = (W // 2) - (registerB.get_width() // 2), (H // 2) - (selfH // 2) + 80
        if rbR.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)) and pygame.mouse.get_pressed()[0]:
            k = dbConnect.check_user(username)
            if len(k) == 0:
                dbConnect.add_user(username, password)
                if password == "":
                    password = "can not empty"
            else:
                username = "already exist"
            # menu(username)
            # run = 0
        f = font.render("or Login", True, (50, 255, 50))
        fr = f.get_rect().copy()
        fr.x, fr.y = (W // 2) - (f.get_width() // 2), (H // 2) - (selfH // 2) + 150
        sc.blit(f, ((W // 2) - (f.get_width() // 2), (H // 2) - (selfH // 2) + 150))
        if fr.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)) and \
                pygame.mouse.get_pressed()[0]:
            login()
            run = 0
        sc.blit(cr, (pygame.mouse.get_pos()))
        pygame.display.update()
        clock.tick(60)

def menu(usr):
    global selected
    lbType = "stage"
    pygame.mixer.music.stop()
    run = 1
    pygame.mixer.music.load(menuTheme)
    pygame.mixer.music.play(-1)
    pygame.display.set_caption("MediBoom: Medical Shooter Game")
    while run:
        check = dbConnect.check_user(usr)[0]
        pnt = []
        n = []
        if len(dbConnect.get_sorted()) > 10:
            for i in range(10):
                n.append(dbConnect.get_sorted()[i]['username'])
                pnt.append(dbConnect.get_sorted()[i][lbType])
        else:
            for i in range(len(dbConnect.get_sorted())):
                n.append(dbConnect.get_sorted()[i]['username'])
                pnt.append(dbConnect.get_sorted()[i][lbType])
        sc.fill((30,30,30))
        e_l = pygame.event.get()
        for e in e_l:
            if e.type == pygame.QUIT:
                run = 0
            elif e.type == pygame.MOUSEBUTTONDOWN and mBt.r.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)):
                mBt.mute = not mBt.mute
        selected_option = mode.update(e_l)
        if selected_option >= 0:
            m = mode.options[selected_option]
            mode.main = m + " Mode"
        selected_option = lbTypeDrop.update(e_l)
        if selected_option >= 0:
            lbType = lbTypeDrop.options[selected_option]
            lbTypeDrop.main = lbType
        sc.blit(mI, (0,0))
        dx = pygame.mouse.get_pos()[0] - (W // 2)
        dy = pygame.mouse.get_pos()[1] - 250
        a = (180 / math.pi) * math.atan2(-dy, dx)
        # surf, image, pos, originPos, angle
        blitRotate(sc, pygame.transform.flip(pygame.transform.scale(des[selected][0],
                                              (des[selected][0].get_width() * 6, des[selected][0].get_height() * 6)), False,
                                                                                                                       pygame.mouse.get_pos()[0] < W//2),
                   ((W // 2), 250), (-75 - ((pygame.mouse.get_pressed()[0]) * 10), (des[selected][0].get_height() * 3)), a)
        img = pygame.transform.scale(pygame.image.load("player.png").convert_alpha(), (90, 90))
        wR = 60
        cAct = (50, 50, 255)
        imgRect = pygame.Rect(400, 360, wR, wR)
        bX = W/2-(len(guns)/2*wR)
        for k in range(len(guns)):
            imgRect.x = bX+(k*wR)
            if selected == guns[k]:
                pygame.draw.rect(sc, cAct, imgRect, 3)
            else:
                pygame.draw.rect(sc, (255,255,255), imgRect, 3)
            if imgRect.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)):
                if pygame.mouse.get_pressed()[0]:
                    selected = guns[k]
            newRect = des[guns[k]][0].get_rect(center = imgRect.center)
            sc.blit(des[guns[k]][0],newRect)
        bX = W / 2 - (len(bomb) / 2 * wR)
        imgRect.y = 420
        for k in range(len(bomb)):
            imgRect.x = bX + (k * wR)
            if selected == bomb[k]:
                pygame.draw.rect(sc, cAct, imgRect, 3)
            else:
                pygame.draw.rect(sc, (255, 255, 255), imgRect, 3)
            if imgRect.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)):
                if pygame.mouse.get_pressed()[0]:
                    selected = bomb[k]
            newRect = des[bomb[k]][0].get_rect(center=imgRect.center)
            sc.blit(des[bomb[k]][0], newRect)
        bX = W / 2 - (len(melee) / 2 * wR)
        imgRect.y = 480
        for k in range(len(melee)):
            imgRect.x = bX + (k * wR)
            if selected == melee[k]:
                pygame.draw.rect(sc, cAct, imgRect, 3)
            else:
                pygame.draw.rect(sc, (255, 255, 255), imgRect, 3)
            if imgRect.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)):
                if pygame.mouse.get_pressed()[0]:
                    selected = melee[k]
            newRect = des[melee[k]][0].get_rect(center=imgRect.center)
            sc.blit(des[melee[k]][0], newRect)
        sc.blit(pygame.transform.flip(img, pygame.mouse.get_pos()[0] < W//2, False), ((W//2)-45, 200))
        sc.blit(font.render(usr, True, (0,0,0)), (25, 180))
        sc.blit(font.render(f"Rank: {n.index(usr)+1}", True, (0, 0, 0)), (25, 210))
        pygame.draw.rect(sc, (50, 50, 50), pygame.Rect(25, 250, 100, 15))
        pygame.draw.rect(sc, (255, 250, 50), pygame.Rect(25, 250, 100*(
            check["XP"]/check["MaxXP"]
        ), 15))
        sc.blit(font.render(f"Level: {check['level']}", True, (0,0,0)), (130, 240))
        sc.blit(font.render(f"Stage: {check['stage']}", True, (0, 0, 0)), (25, 270))
        sc.blit(font.render(f"Coin: {check['coin']}", True, (0, 0, 0)), (25, 300))
        sc.blit(font.render(f"Kills: {check['kills']}", True, (0, 0, 0)), (25, 330))
        k = 0
        sc.blit(font.render("Leaderboard", True, (0, 0, 0)), (W-250, 135))
        for z in n:
            k += 1
            text = font.render(f"{k}. {z}: {lbType} {pnt[k-1]}", True, (0, 0, 0))
            sc.blit(text, (W - 250, 135+(k*30)))
        mode.draw(sc)
        lbTypeDrop.draw(sc)
        sc.blit(playButton, (W-150, H-100))
        pRect = playButton.get_rect().copy()
        pRect.x, pRect.y = W-150, H-100
        if pRect.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)) and pygame.mouse.get_pressed()[0]:
            game(usr)
            pygame.mixer.music.stop()
            run = 0
        mBt.update()
        sc.blit(cr, (pygame.mouse.get_pos()))
        pygame.display.update()
        clock.tick((60))

def game(usr):
    global current_list, eCount, bossStage, en, stage, proj
    if dbConnect.check_user(usr)[0]["stage"] == 9:
        stage = 9
    player = Player(W // 2, H // 2, 1, usr)
    pygame.mixer.music.stop()
    run = 1
    w = Weapon(selected, player)
    r = 0
    rt = 10
    boss = Boss(5, 5, "Flu")
    while run:
        check = dbConnect.check_user(usr)[0]
        if stage == 1 or stage == 2:
            boss = Boss(5, 5, "Flu")
        elif stage == 3 or stage == 4 or stage == 7:
            boss = Boss(5, 5, "Cancer")
        elif stage == 5 or stage == 6:
            boss = Boss(5, 5, "Heart")
        elif stage == 8:
            boss = Boss(5, 5, "All")
        if not bossStage:
            rt -= 0.1
            if random.randint(0, 5) == 2 and rt < 0:
                en.append(Minion(random.randint(0, W), random.randint(0, H), boss.type))
                r += 1
                eCount += 1
                rt = 10
        pygame.display.set_caption(f"MediBoom: Medical Shooter Game [{m}: stage {stages[stage-1]}]")
        if not pygame.mixer.music.get_busy():
            if not current_list:
                current_list = gameTheme[:]
            current_song = current_list.pop(0)
            pygame.mixer.music.load(current_song)
            pygame.mixer.music.play()
        sc.fill((30,30,30))
        lights.fill((20,20,20))
        e_l = pygame.event.get()
        for e in e_l:
            if e.type == pygame.QUIT:
                run = 0
            elif e.type == pygame.MOUSEBUTTONDOWN and mBt.r.colliderect(pygame.Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)):
                mBt.mute = not mBt.mute
        if random.randint(0, 5) == 2:
            # pygame.draw.circle(lights, (0,0,0), (W, 0), 250)
            lights.blit(lamp, (W-250, -250))
        sc.blit(map, (0,0))
        sc.blit(bloods, (0,0))
        player.update(usr, boss)
        for e in proj:
            e.update(player, usr)
        if bossStage:
            proj = []
            en = []
            boss.update(usr, player)
            if boss.HP <= 0:
                bossStage = False
        else:
            for i in en:
                i.update(usr, player)
        for i in bs:
            i.update(boss)
        for i in bombs:
            i.update(player)
        sc.blit(lights, (0,0), special_flags=pygame.BLEND_RGBA_SUB)
        if not bossStage and r > (25*(stage*3)) and stage < 9 and eCount <= 5:
            sc.blit(bossTrigger, (20, 20))
            rct = bossTrigger.get_rect()
            rct.x, rct.y = 20, 20
            zk = cr.get_rect().copy()
            zk.x, zk.y = pygame.mouse.get_pos()
            if rct.colliderect(zk) and pygame.mouse.get_pressed()[0]:
                bossStage = True
                r = 0
        elif r < (25*(stage*3)):
            pygame.draw.rect(sc, (255, 50, 50), pygame.Rect(40, 20, (((25*(stage*3))-r)/(25*(stage*3)))*(W-45), 10))
        w.update(player)
        mBt.update()
        sc.blit(cr, (pygame.mouse.get_pos()))
        if player.HP <= 0:
            run = 0
            menu(usr)
        if check["XP"] >= check["MaxXP"]:
            last = check["XP"] - check["MaxXP"]
            dbConnect.update(usr, "level", check["level"]+1)
            dbConnect.update(usr, "XP", last)
            dbConnect.update(usr, "MaxXP", check["MaxXP"]+(dbConnect.check_user(usr)[0]["level"]*10))
        pygame.display.update()
        clock.tick((60))
intro()