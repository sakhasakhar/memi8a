import pygame
import sys
import os

from help_func import load_image, load_font, oc_change_hidden_state, \
     oc_delete, oc_load_image, surface_from_clipboard, crop_image

pygame.font.init()
font = load_font('bahnschrift.ttf', 30)


def name_resize(w, h, name):
        rows = [name[:4]]
        size = 30
        fnt = load_font('bahnschrift.ttf', size)
        for c in name[4:]:
            if fnt.size(rows[-1] + c)[0] <= w:
                rows[-1] += c
            else:
                rows.append(c)
        while len(rows) * size > h + 4:
            size = int(size * 0.9 + 1)
            fnt = load_font('bahnschrift.ttf', size)
            rows = [name[:4]]
            for c in name[4:]:
                if fnt.size(rows[-1] + c)[0] < w - size // 2:
                    rows[-1] += c
                else:
                    rows.append(c)
        return [fnt.render(r, True, (255, 255, 255)) for r in rows], size


class Button:
    def __init__(self, coords, name):
        self.coords = coords
        self.name = name
        self.base = load_image(name + '_base.png')
        self.selected = load_image(name + '_selected.png')
        self.current = self.base
        self.size = self.base.get_size()

    def check_mouse(self, mouse):
        if self.coords[0] < mouse[0] < self.coords[0] + self.size[0] and \
                self.coords[1] < mouse[1] < self.coords[1] + self.size[1]:
            return True
        return False

    def check_selected(self, mouse):
        if self.check_mouse(mouse):
            self.current = self.selected
        else:
            self.current = self.base


class OcButton(Button):
    def __init__(self, name):
        self.orig = load_image(name)
        self.current = self.orig
        self.size = self.current.get_size()
        self.coords = (0, 0)
        self.grabbed = False
        self.d_x = 0
        self.d_y = 0
        self.inside_a_meme = False
        self.fname = name

    def move(self, btns, areas):
        self.grabbed = False
        x, y = self.coords
        for area in areas:
            if self in area.positions:
                area.del_oc(self)
        for area in areas:
            if area.check_mouse((x + 50, y + 50)):
                print((area.coords[1] - 60) // 105 + 1)
                area.add(self)
                self.inside_a_meme = True
                return True
        self.inside_a_meme = False
        return False
        
    def change_for_render(self, coords, size=(100, 100)):
        self.coords = coords
        if not self.size == size:
            self.size = size
            self.current = pygame.transform.scale(self.orig, size)
            
            
class OcMenuComplexButton:
    def __init__(self, related_oc, coords):
        self.related_oc = related_oc
        self.coords = coords
        self.img = pygame.transform.scale(load_image(self.related_oc.img), (100, 100))
        self.hiddenpics = [load_image('hidden0.png'), load_image('hidden1.png')]
        self.hidden_n = int(self.related_oc.hidden)
        self.delpic = load_image('del_small.png')
        self.name_render, self.font_size = name_resize(150, 50, related_oc.name)
        self.renderedpic = self.render()
    
    def render(self):  # beta
        sf = pygame.surface.Surface((250, 100))
        sf.blit(self.img, (0, 0))
        sf.blit(self.hiddenpics[self.hidden_n], (100, 50))
        sf.blit(self.delpic, (150, 50))
        for i in range(len(self.name_render)):
            sf.blit(self.name_render[i], (105, i * self.font_size))
        return sf
        
    def change_hidden_state(self):
        oc_change_hidden_state(self.related_oc.id)
        self.related_oc.hidden = not self.related_oc.hidden
        self.hidden_n = int(self.related_oc.hidden)
        self.renderedpic = self.render()

    def delete(self):
        oc_delete(self.related_oc.id)
        
    def change_pic(self):
        pic = surface_from_clipboard()
        if pic:
            self.img = crop_image(pic)
            fname = f'{self.related_oc.id}.png'
            pygame.image.save(self.img, 'images/' + fname)
            self.img = pygame.transform.scale(load_image(self.related_oc.img), (100, 100))
            self.renderedpic = self.render()

    def check_mouse(self, mouse):
        # print(self.related_oc.name, self.coords, mouse)
        if self.coords[0] < mouse[0] < self.coords[0] + 100 and \
                self.coords[1] < mouse[1] < self.coords[1] + 100:
            self.change_pic()
            return 1 # change_pic
        if self.coords[0] + 100 < mouse[0] < self.coords[0] + 150 and \
                self.coords[1] + 50 < mouse[1] < self.coords[1] + 100:
            self.change_hidden_state()
            return 2 # change_hidden_state
        if self.coords[0] + 150 < mouse[0] < self.coords[0] + 200 and \
                self.coords[1] + 50 < mouse[1] < self.coords[1] + 100:
            self.delete()
            return 3 # delete
        return 0 


class Arrow(Button):
    def __init__(self, img, coords, reverse=False):
        self.imgs = pygame.transform.flip(load_image(f'{img}_0.png'), reverse, False), \
                    pygame.transform.flip(load_image(f'{img}_1.png'), reverse, False)
        self.current = self.imgs[0]
        self.coords = coords
        self.size = self.current.get_size()


class Area:
    def __init__(self, coords):  # coords - (x1, y1, x2, y2) x1 y1 - верхний левый угол обязательно
        self.coords = coords
        self.positions = []
        self.baselen = (coords[2] - coords[0]) // (coords[3] - coords[1])  # кол-во квадратиков в одной строке, если не сжимать
        self.baseheight = self.coords[3] - self.coords[1]   # высота зоны
    
    def check_mouse(self, mouse):
        if self.coords[0] < mouse[0] < self.coords[2] and \
                self.coords[1] < mouse[1] < self.coords[3]:
            return True
        return False
    
    def add(self, oc):
        if not (oc in self.positions):
            self.positions.append(oc)
        self.render()
        
    def del_oc(self, oc): # тк функция вызывается уже после проверки на наличие, ошибки быть не должно, так что тут без проверок
        self.positions.remove(oc)
        self.render()
        
    def render(self):
        height = self.baseheight  # высота одного квадратика
        width = height  # ширина одного квадратика (в пределах одной зоны они приведены к одному размеру)
        coef = 1  # сжатие ширины
        n = len(self.positions)  # кол-во квадратиков
        row = self.baselen  # количество квадратиков в строке
        nrows = 1  # количество строк
        if n > self.baselen:  # если мы не можем поместить квадратики в одну строку не сжимая
            # print(n, self.baselen, height, self.coords[2] - self.coords[0])  # ну я так дебажу, а что
            coef = width * n / (self.coords[2] - self.coords[0])  # в случае одной строки считаем во сколько раз длина несжатых квадратов превышает длину зоны
            while coef >= nrows * 2:  # nrows  - это то, во сколько раз сжимается height, следовательно если сжатие width превышает в два раза сжатие height, то картинки 
                nrows += 1            # становятся непропорциональными и надо что-то предпринять, например добавить еще одну строку
                coef = (width * n) / (self.coords[2] - self.coords[0]) / nrows   # тот же коэффициент, но мы все разделили на nrows строк, следовательно коэффициент в nrows раз меньше (я думаю проблема тут, но не факт)
            width = width // max(coef, nrows)  # собственно производим сжатие, НО если мы поделим на nrows у нас будет квадратная картинка, а если на coef - либо сжатая, либо сплющенная, сплющенная хуита так что лучше или квадрат или сжатую если сжатие необходимо, а есть coef > nrows то это так 
            row = (self.coords[2] - self.coords[0]) // width  # считаем количество квадратиков в строке чтобы потом их удобно расставить (возможно проблема тут)
            height = height // nrows  # это всегда так
            # print(n, self.baselen, height, width, coef, nrows, row)
            
        i = 0
        for oc in self.positions:
            coords = (self.coords[0] + width * (i % row), self.coords[1] + height * (i // row))
            oc.change_for_render(coords, (width, height))
            i += 1


class OcCoincidencesButton:
    def __init__(self, x, y, oc):
        self.rect = pygame.Rect(x, y, 100, 150)
        self.oc = oc
        self.active = False
        self.img = pygame.transform.scale(load_image(oc.img), (100, 100))
        self.name_rows, self.font_size = name_resize(100, 50, oc.name)

    def check_selected(self, pos):
        if self.rect.collidepoint(pos):
            self.active = not self.active

    def draw(self, screen):
        if self.active:
            k = 2
            pygame.draw.rect(
                screen, (50, 230, 120),
                (self.rect.x - k, self.rect.y - k, self.rect.w + k + 1, self.rect.h + k * 3), 2)
        screen.blit(self.img, (self.rect.x, self.rect.y))
        for i in range(len(self.name_rows)):
            screen.blit(self.name_rows[i], (self.rect.x, self.rect.y + 100 + self.font_size * i))


