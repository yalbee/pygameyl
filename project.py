import pygame as pg
import sys
import os
import random
import csv

FPS = 60
TUBE_SPAWN = pg.USEREVENT + 1


class Player:  # профиль игрока
    def __init__(self, nickname):
        self.nickname = nickname
        with open('data.csv', 'r', encoding='utf-8') as csvfile:  # загрузка данных игрока из csv файла
            reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
            self.record, self.money = 0, 0
            for line in reader:
                if line['nickname'] == self.nickname:
                    self.record, self.money = int(line['record']), int(line['money'])
                else:
                    csvlines.append(line)


# файл с сохранениями каждый запуск перезаписывается а новые данные будут записаны в конец
csvlines = []
nickname = input('Введите ник (не более 22 символов): ')
if len(nickname.strip()) == 0 or len(nickname.strip()) > 22:
    print('еррор')
    sys.exit()
player = Player(nickname.strip())
pg.init()
size = width, height = 700, 500
screen = pg.display.set_mode(size)


def load_image(name, colorkey=None):  # загрузка изображений
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pg.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def rot_center(image, angle):  # для поворотов птички
    orig_rect = image.get_rect()
    rot_image = pg.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image


class AnimatedSprite(pg.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, sprite_group):
        super().__init__(sprite_group)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pg.Rect(0, 0, sheet.get_width() // columns,
                            sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pg.Rect(
                    frame_location, self.rect.size)))


class Bird(AnimatedSprite):  # птичка
    def __init__(self):
        super().__init__(pg.transform.scale(load_image(
            'bird_sheet3x1.png'), (150, 40)), 3, 1, 50, 40, birds)
        self.rect = pg.Rect(50, 200, 50, 40)
        self.vy, self.flapping = 2, False
        self.score_count, self.update_count = 0, 0

    def flap(self):
        self.flapping = True
        self.vy = -10

    def update(self):
        if self.flapping:
            if self.update_count % 5 == 0:  # анимация
                self.cur_frame = (self.cur_frame + 1) % len(self.frames)
                self.image = self.frames[self.cur_frame]
                self.image = rot_center(self.image, 45)
            self.update_count += 1
        if self.cur_frame % len(self.frames) == 0:  # остановка анимации
            self.flapping, self.update_count = False, 0
        if self.vy == 0 or self.vy == 7 or self.vy == 12:  # повороты птички
            self.image = rot_center(self.image, -45)
        self.rect = self.rect.move(0, self.vy)
        self.vy += 0.5
        if pg.sprite.spritecollide(self, borders, True):  # прошел препятствие
            self.score_count += 1
        if pg.sprite.spritecollide(self, coins, True):  # собрал монетку
            player.money += 10
            Shadow(self.rect.x + 10, self.rect.y - 60, moving=True)
        if pg.sprite.spritecollideany(self, tubes) or \
                self.rect.y < 0 or self.rect.y + self.rect.h > 500:  # столкновение
            if self.score_count > player.record:  # установка рекорда
                player.record = self.score_count
            money = round(self.score_count * (random.randint(80, 120) / 100))
            # счет игрока умноженный на случайный коэфф. прибавляется к кол-ву монет
            player.money += money
            if money != 0:
                Shadow(screen.get_width() - 104, 46, money)
            self.kill()


class Tube(pg.sprite.Sprite):  # препятствие
    def __init__(self, image, y):
        super().__init__(tubes)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = 700, y

    def update(self):
        self.rect = self.rect.move(-3, 0)
        if self.rect.x + 60 < 0:
            self.kill()


class Border(pg.sprite.Sprite):  # флаг прохождения препятствия
    def __init__(self, y):
        super().__init__(borders)
        self.image = pg.Surface((1, 160))
        self.rect = pg.Rect(760, y, 1, 160)

    def update(self):
        self.rect = self.rect.move(-3, 0)
        if self.rect.x < 0:
            self.kill()


class Coin(AnimatedSprite):  # монетка
    def __init__(self, x, y):
        super().__init__(pg.transform.scale(load_image(
            'coin_sheet6x1.png'), (180, 40)), 6, 1, 30, 30, coins)
        self.rect = pg.Rect(x, y, 30, 30)
        self.update_count = 0

    def update(self):
        if self.update_count % 4 == 0:  # анимация
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(-3, 0)
        self.update_count += 1


class Shadow(pg.sprite.Sprite):  # тень после сбора монетки
    def __init__(self, x, y, money=10, moving=False):
        super().__init__(shadows)
        self.image = pg.Surface((50, 40), pg.SRCALPHA)
        self.rect = pg.Rect(x, y, 50, 40)
        self.alpha, self.money, self.moving = 255, money, moving
        self.font = pg.font.Font('font.ttf', 50)

    def update(self):
        text = self.font.render('+' + str(self.money), True, pg.Color(230, 180, 40, self.alpha))
        self.image.blit(text, (0, 0))
        if self.moving:
            self.rect = self.rect.move(-3, 0)
        self.alpha -= 3
        if self.alpha <= 0:
            self.kill()


if __name__ == '__main__':
    background = pg.transform.scale(load_image('background.png'), (700, 500))
    background_x = 0
    screen.blit(background, (0, 0))
    pg.display.set_caption('праэкт')
    clock = pg.time.Clock()
    pg.time.set_timer(TUBE_SPAWN, 1600)  # таймер спавна препятствий
    birds, tubes = pg.sprite.Group(), pg.sprite.Group()
    borders, coins = pg.sprite.Group(), pg.sprite.Group()
    shadows = pg.sprite.Group()
    bird = Bird()
    running = True
    coin = pg.transform.scale(load_image('coin.png'), (16, 22))
    birds.draw(screen)
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1 or event.button == 3:
                    bird.flap()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    bird.flap()
            if event.type == TUBE_SPAWN:
                y = random.randint(140, 360)
                image = pg.transform.scale(load_image('tube.png'), (60, 400))
                Tube(image, y - 480)  # верхнее препятствие
                Border(y - 80)
                image = pg.transform.rotate(image, 180)
                Tube(image, y + 80)  # нижнее препятствие
                if random.choice([True, False, False, False]):
                    # спавн монетки с шансом 25%
                    Coin(860, random.randint(140, 360) - 15)
        if background_x - 0.5 <= -700:
            background_x = 0
        background_x -= 0.5
        screen.blit(background, (background_x, 0))  # передвижение заднего фона
        screen.blit(background, (background_x + screen.get_width(), 0))
        birds.update()
        birds.draw(screen)
        tubes.update()
        tubes.draw(screen)
        coins.update()
        coins.draw(screen)
        borders.update()
        shadows.update()
        shadows.draw(screen)
        font = pg.font.Font('font.ttf', 40)  # отображаемый ник
        text = font.render(str(player.nickname), True, (5, 50, 14))
        screen.blit(text, (30, 14))
        font = pg.font.Font('font.ttf', 38)  # рекорд игрока
        text = font.render('Рекорд: ' + str(player.record), True, (5, 50, 14))
        screen.blit(text, (30, 45))
        font = pg.font.Font('font.ttf', 66)  # счетчик пройденных препятствий
        text = font.render(str(bird.score_count), True, (5, 50, 14))
        text_x = width // 2 - text.get_width() // 2
        screen.blit(text, (text_x, 18))
        font = pg.font.Font('font.ttf', 42)  # кол-во монет
        text = font.render(str(player.money).rjust(6, '0'),
                           True, (5, 50, 14))
        screen.blit(text, (screen.get_width() - 104, 20))
        screen.blit(coin, (573, 28))
        clock.tick(FPS)
        pg.display.flip()
    if player.record != 0 and player.money != 0:
        csvlines.append({'nickname': player.nickname,
                         'record': player.record, 'money': player.money})
    writer = csv.DictWriter(open('data.csv', 'w', encoding='utf-8'),
                            fieldnames=['nickname', 'record', 'money'],
                            delimiter=';', quotechar='"')
    writer.writeheader()
    writer.writerows(csvlines)  # сохранение данных игрока в csv файл
    pg.quit()
