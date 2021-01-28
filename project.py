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
            self.current_skin, self.s2, self.s3 = 'yellow_bird_sheet3x1.png', 0, 0
            for line in reader:
                if line['nickname'] == self.nickname:
                    self.record, self.money = int(line['record']), int(line['money'])
                    self.current_skin, self.s2, self.s3 = \
                        line['current_skin'], int(line['s2']), int(line['s3'])
                else:
                    csvlines.append(line)


# файл с сохранениями каждый запуск перезаписывается а новые данные будут записаны в конец
# обновленные профили сохраняются только после выхода
csvlines = []
nickname = input('Введите ник (не более 14 символов): ')
if len(nickname.strip()) == 0 or len(nickname.strip()) > 14:
    print('еррор')
    sys.exit()
player = Player(nickname.strip())
pg.init()
size = width, height = 700, 500
screen = pg.display.set_mode(size)


def load_image(name, colorkey=None):  # загрузка изображений
    fullname = os.path.join('images', name)
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
            player.current_skin), (150, 40)), 3, 1, 50, 40, birds)
        self.rect = pg.Rect(50, 200, 50, 40)
        self.vy, self.flapping = 2, False
        self.score_count, self.update_count = 0, 0

    def flap(self):  # прыжок
        self.flapping = True
        self.vy = -10

    def game_over(self):
        showing, new_record = True, False
        if self.score_count > player.record:  # установка рекорда
            player.record = self.score_count
            new_record = True
        money = round(self.score_count * (random.randint(80, 120) / 100))
        # счет игрока умноженный на случайный коэфф. прибавляется к кол-ву монет
        player.money += money
        if money != 0:
            Shadow(screen.get_width() - 110, 46, '+' + str(money))
        Button((262, 218), 250, 64, (175, 54, 54), 'Играть снова', start_playing)
        Button((188, 218), 64, 64, (55, 42, 42), '<', show_menu)  # выход в главное меню
        while showing:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    if player.record != 0 and player.money != 0:
                        csvlines.append({'nickname': player.nickname, 'record': player.record,
                                         'money': player.money, 'current_skin': player.current_skin,
                                         's2': player.s2, 's3': player.s3})
                    writer = csv.DictWriter(open('data.csv', 'w', encoding='utf-8'),
                                            fieldnames=['nickname', 'record', 'money', 'current_skin', 's2', 's3'],
                                            delimiter=';', quotechar='"')
                    writer.writeheader()
                    writer.writerows(csvlines)  # сохранение данных игрока в csv файл
                    pg.quit()
                    quit()
                if event.type == pg.MOUSEMOTION:  # курсор
                    if pg.mouse.get_focused():
                        cursor.rect.x, cursor.rect.y = event.pos
                    else:
                        cursor.rect.x = -100
            screen.blit(background, (background_x, 0))
            screen.blit(background, (background_x + screen.get_width(), 0))
            birds.draw(screen)
            tubes.draw(screen)
            coins.draw(screen)
            buttons.draw(screen)
            buttons.update()
            font = pg.font.Font('font.ttf', 40)  # отображаемый ник
            text = font.render(str(player.nickname), True, (5, 50, 14))
            screen.blit(text, (30, 14))
            font = pg.font.Font('font.ttf', 38)  # рекорд игрока
            if new_record:
                text = font.render('Новый рекорд!!!', True, (5, 50, 14))
            else:
                text = font.render('Рекорд: ' + str(player.record), True, (5, 50, 14))
            screen.blit(text, (30, 45))
            font = pg.font.Font('font.ttf', 100)  # счетчик пройденных препятствий
            text = font.render(str(self.score_count), True, (5, 50, 14))
            text_x = width // 2 - text.get_width() // 2
            screen.blit(text, (text_x, 20))
            if player.money > 999999:
                player.money = 999999
            font = pg.font.Font('font.ttf', 42)  # кол-во монет
            text = font.render(str(player.money).rjust(6, '0'),
                               True, (5, 50, 14))
            screen.blit(text, (screen.get_width() - 104, 20))
            screen.blit(coin, (573, 28))
            other_sprites.update()
            other_sprites.draw(screen)
            clock.tick(FPS)
            pg.display.flip()

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
            Shadow(self.rect.x + 10, self.rect.y - 60, '+10', moving=True)
        if pg.sprite.spritecollideany(self, tubes) or \
                self.rect.y < 0 or self.rect.y + self.rect.h > 500:  # столкновение
            self.game_over()


class Tube(pg.sprite.Sprite):  # препятствие
    def __init__(self, image, y):
        super().__init__(tubes)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = 700, y

    def update(self):
        self.rect = self.rect.move(-3, 0)
        if self.rect.x + self.rect.width < 0:
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
        if self.rect.x + self.rect.width < 0:
            self.kill()


class Shadow(pg.sprite.Sprite):  # тень при изменении кол-ва монет
    def __init__(self, x, y, text, moving=False):
        super().__init__(other_sprites)
        self.image = pg.Surface((100, 40), pg.SRCALPHA)
        self.rect = pg.Rect(x, y, 50, 40)
        self.alpha, self.text, self.moving = 255, text, moving
        self.font = pg.font.Font('font.ttf', 50)

    def update(self):
        text = self.font.render(self.text, True, pg.Color(230, 180, 40, self.alpha))
        self.image.blit(text, (0, 0))
        if self.moving:
            self.rect = self.rect.move(-3, 0)
        self.alpha -= 3
        if self.alpha <= 0:
            self.kill()


class Button(pg.sprite.Sprite):  # кнопка
    def __init__(self, pos, width, height, color, text, func, n=None):
        super().__init__(buttons)
        self.image, self.n = pg.Surface((width, height), pg.SRCALPHA), n
        self.image.fill(color)
        self.rect, self.func = pg.Rect(pos[0], pos[1], width, height), func
        pg.draw.rect(self.image, (100, 100, 100), pg.Rect(0, 0, width, height), 3)
        font = pg.font.Font('font.ttf', 50)
        text = font.render(text, True, (255, 255, 255))
        self.image.blit(text, (self.image.get_width() // 2 - text.get_width() // 2,
                               self.image.get_height() // 2 - text.get_height() // 2))

    def update(self):
        mouse_pos = pg.mouse.get_pos()
        if self.rect.x < mouse_pos[0] < self.rect.x + self.rect.width and \
                self.rect.y < mouse_pos[1] < self.rect.y + self.rect.height:
            pg.draw.rect(screen, (255, 255, 255), self.rect, 3)  # рамка при наведении на кнопку
            if pg.mouse.get_pressed(3)[0] == 1:
                if self.n is not None:
                    self.func(self.n)
                else:
                    self.func()


def show_menu():
    showing = True
    global buttons, background_x
    buttons = pg.sprite.Group()
    Button((220, 282), 260, 50, (175, 54, 54), 'Играть', start_playing)
    Button((220, 342), 260, 50, (55, 42, 42), 'Магазин', shop)
    Button((220, 402), 260, 50, (55, 42, 42), 'Лидеры', leaderboard)
    while showing:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if player.record != 0 and player.money != 0:
                    csvlines.append({'nickname': player.nickname, 'record': player.record,
                                     'money': player.money, 'current_skin': player.current_skin,
                                     's2': player.s2, 's3': player.s3})
                writer = csv.DictWriter(open('data.csv', 'w', encoding='utf-8'),
                                        fieldnames=['nickname', 'record', 'money', 'current_skin', 's2', 's3'],
                                        delimiter=';', quotechar='"')
                writer.writeheader()
                writer.writerows(csvlines)  # сохранение данных игрока в csv файл
                pg.quit()
                quit()
            if event.type == pg.MOUSEMOTION:  # курсор
                if pg.mouse.get_focused():
                    cursor.rect.x, cursor.rect.y = event.pos
                else:
                    cursor.rect.x = -100
        if background_x - 0.5 <= -700:
            background_x = 0
        background_x -= 0.5
        screen.blit(background, (background_x, 0))  # передвижение заднего фона
        screen.blit(background, (background_x + screen.get_width(), 0))
        font = pg.font.Font('font.ttf', 120)
        text = font.render('Flappy Bird', True, (5, 50, 14))
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, 40))
        font = pg.font.Font('font.ttf', 40)  # отображаемый ник
        text = font.render(str(player.nickname), True, (5, 50, 14))
        screen.blit(text, (30, 14))
        buttons.draw(screen)
        buttons.update()
        other_sprites.update()
        other_sprites.draw(screen)
        clock.tick(FPS)
        pg.display.flip()


def start_playing():
    global birds, tubes, borders, coins, buttons, background_x
    birds, tubes = pg.sprite.Group(), pg.sprite.Group()
    borders, coins = pg.sprite.Group(), pg.sprite.Group()
    buttons = pg.sprite.Group()
    bird = Bird()
    pg.time.set_timer(TUBE_SPAWN, 1600)  # таймер спавна препятствий
    background_x = 0
    playing = True
    while playing:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if player.record != 0 and player.money != 0:
                    csvlines.append({'nickname': player.nickname, 'record': player.record,
                                     'money': player.money, 'current_skin': player.current_skin,
                                     's2': player.s2, 's3': player.s3})
                writer = csv.DictWriter(open('data.csv', 'w', encoding='utf-8'),
                                        fieldnames=['nickname', 'record', 'money', 'current_skin', 's2', 's3'],
                                        delimiter=';', quotechar='"')
                writer.writeheader()
                writer.writerows(csvlines)  # сохранение данных игрока в csv файл
                pg.quit()
                quit()
            if event.type == pg.MOUSEMOTION:  # курсор
                if pg.mouse.get_focused():
                    cursor.rect.x, cursor.rect.y = event.pos
                else:
                    cursor.rect.x = -100
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
        buttons.draw(screen)
        buttons.update()
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
        if player.money > 999999:
            player.money = 999999
        font = pg.font.Font('font.ttf', 42)  # кол-во монет
        text = font.render(str(player.money).rjust(6, '0'),
                           True, (5, 50, 14))
        screen.blit(text, (screen.get_width() - 104, 20))
        screen.blit(coin, (573, 28))
        other_sprites.update()
        other_sprites.draw(screen)
        clock.tick(FPS)
        pg.display.flip()


def buy_skin(number):
    if player.money >= 5000:
        player.money -= 5000
        Shadow(screen.get_width() - 110, 46, '-5000')
        if number == 2:
            player.s2 = 1
        if number == 3:
            player.s3 = 1


def select_skin(number):  # выбор текущего скина
    if number == 1 and player.current_skin != 'yellow_bird_sheet3x1.png':
        player.current_skin = 'yellow_bird_sheet3x1.png'
    if number == 2 and player.current_skin != 'green_bird_sheet3x1.png':
        player.current_skin = 'green_bird_sheet3x1.png'
    if number == 3 and player.current_skin != 'red_bird_sheet3x1.png':
        player.current_skin = 'red_bird_sheet3x1.png'


def shop():
    global buttons, background_x
    showing, buttons = True, pg.sprite.Group()
    Button((50, 200), 60, 60, (55, 42, 42), '<', show_menu)  # выход в главное меню
    button1 = Button((140, 380), 130, 54, (175, 54, 54), 'Выбрать', select_skin, 1)
    button2 = Button((285, 380), 130, 54, (175, 54, 54), '5000', buy_skin, 2)
    button3 = Button((430, 380), 130, 54, (175, 54, 54), '5000', buy_skin, 3)
    while showing:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if player.record != 0 and player.money != 0:
                    csvlines.append({'nickname': player.nickname, 'record': player.record,
                                     'money': player.money, 'current_skin': player.current_skin,
                                     's2': player.s2, 's3': player.s3})
                writer = csv.DictWriter(open('data.csv', 'w', encoding='utf-8'),
                                        fieldnames=['nickname', 'record', 'money', 'current_skin', 's2', 's3'],
                                        delimiter=';', quotechar='"')
                writer.writeheader()
                writer.writerows(csvlines)  # сохранение данных игрока в csv файл
                pg.quit()
                quit()
            if event.type == pg.MOUSEMOTION:  # курсор
                if pg.mouse.get_focused():
                    cursor.rect.x, cursor.rect.y = event.pos
                else:
                    cursor.rect.x = -100
        if background_x - 0.5 <= -700:
            background_x = 0
        background_x -= 0.5
        button1.kill()
        button1 = Button((140, 380), 130, 54, (175, 54, 54), 'Выбрать', select_skin, 1)
        if player.s2 == 1:
            button2.kill()
            button2 = Button((285, 380), 130, 54, (175, 54, 54), 'Выбрать', select_skin, 2)
        if player.s3 == 1:
            button3.kill()
            button3 = Button((430, 380), 130, 54, (175, 54, 54), 'Выбрать', select_skin, 3)
        if player.current_skin == 'yellow_bird_sheet3x1.png':
            button1.kill()
        if player.current_skin == 'green_bird_sheet3x1.png':
            button2.kill()
        if player.current_skin == 'red_bird_sheet3x1.png':
            button3.kill()
        screen.blit(background, (background_x, 0))  # передвижение заднего фона
        screen.blit(background, (background_x + screen.get_width(), 0))
        rect = pg.Rect(120, 200, 460, 264)
        pg.draw.rect(screen, (55, 42, 42), rect)
        pg.draw.rect(screen, (100, 100, 100), rect, 4)
        buttons.draw(screen)
        buttons.update()
        font = pg.font.Font('font.ttf', 100)
        text = font.render('Магазин', True, (5, 50, 14))
        text_x = width // 2 - text.get_width() // 2
        screen.blit(text, (text_x, 24))
        font = pg.font.Font('font.ttf', 40)  # отображаемый ник
        text = font.render(str(player.nickname), True, (5, 50, 14))
        screen.blit(text, (30, 14))
        font = pg.font.Font('font.ttf', 42)  # кол-во монет
        text = font.render(str(player.money).rjust(6, '0'),
                           True, (5, 50, 14))
        screen.blit(text, (screen.get_width() - 104, 20))
        screen.blit(coin, (573, 28))
        other_sprites.update()
        other_sprites.draw(screen)
        clock.tick(FPS)
        pg.display.flip()


def leaderboard():  # таблица лидеров
    global buttons, background_x
    showing, buttons = True, pg.sprite.Group()
    Button((80, 140), 60, 60, (55, 42, 42), '<', show_menu)  # выход в главное меню
    while showing:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if player.record != 0 and player.money != 0:
                    csvlines.append({'nickname': player.nickname, 'record': player.record,
                                     'money': player.money, 'current_skin': player.current_skin,
                                     's2': player.s2, 's3': player.s3})
                writer = csv.DictWriter(open('data.csv', 'w', encoding='utf-8'),
                                        fieldnames=['nickname', 'record', 'money', 'current_skin', 's2', 's3'],
                                        delimiter=';', quotechar='"')
                writer.writeheader()
                writer.writerows(csvlines)  # сохранение данных игрока в csv файл
                pg.quit()
                quit()
            if event.type == pg.MOUSEMOTION:  # курсор
                if pg.mouse.get_focused():
                    cursor.rect.x, cursor.rect.y = event.pos
                else:
                    cursor.rect.x = -100
        if background_x - 0.5 <= -700:
            background_x = 0
        background_x -= 0.5
        screen.blit(background, (background_x, 0))  # передвижение заднего фона
        screen.blit(background, (background_x + screen.get_width(), 0))
        rect = pg.Rect(150, 140, 400, 320)
        pg.draw.rect(screen, (55, 42, 42), rect)
        pg.draw.rect(screen, (100, 100, 100), rect, 4)
        with open('data.csv', 'r', encoding='utf-8') as csvfile:
            lines = [(x['nickname'], x['record'])
                     for x in csv.DictReader(csvfile, delimiter=';', quotechar='"')]
            lines = sorted(lines, key=lambda x: int(x[1]))
            lines.reverse()
            font, y = pg.font.Font('font.ttf', 60), 160
        if len(lines) == 0:
            text = font.render('Тут пусто...', True, (255, 255, 255))
            screen.blit(text, (170, y))
        else:
            for i in range(5):
                try:
                    text = font.render('{}) {}: {}'.format(str(i + 1), str(lines[i][0]),
                                                           str(lines[i][1])), True, (255, 255, 255))
                    screen.blit(text, (170, y))
                    y += 55
                except IndexError:
                    break
        buttons.draw(screen)
        buttons.update()
        font = pg.font.Font('font.ttf', 100)
        text = font.render('Лидеры', True, (5, 50, 14))
        text_x = width // 2 - text.get_width() // 2
        screen.blit(text, (text_x, 24))
        font = pg.font.Font('font.ttf', 40)  # отображаемый ник
        text = font.render(str(player.nickname), True, (5, 50, 14))
        screen.blit(text, (30, 14))
        other_sprites.update()
        other_sprites.draw(screen)
        clock.tick(FPS)
        pg.display.flip()


if __name__ == '__main__':
    background = pg.transform.scale(load_image('background.png'), (700, 500))
    background_x = 0
    pg.display.set_caption('Flappy Bird')
    clock = pg.time.Clock()
    birds, tubes = pg.sprite.Group(), pg.sprite.Group()
    borders, coins = pg.sprite.Group(), pg.sprite.Group()
    other_sprites, buttons = pg.sprite.Group(), pg.sprite.Group()
    cursor = pg.sprite.Sprite()
    cursor.image = pg.transform.scale(load_image('cursor.png'), (24, 24))
    cursor.rect = pg.Rect(-100, 0, 24, 24)
    cursor.add(other_sprites)
    pg.mouse.set_visible(False)
    coin = pg.transform.scale(load_image('coin.png'), (16, 22))
    show_menu()
