import time
import re
import machine
import micropython
from micropython import const
from random import randint
from interstate75 import Interstate75, DISPLAY_INTERSTATE75_256X64

machine.freq(266000000)

"""
Conway's Game Of Life for Interstate 75
You can load game of life RLE files below to try different patterns
See https://conwaylife.com/ref/DRH/ to find some RLE examples.
"""

# Setup for the display
i75 = Interstate75(
    display=DISPLAY_INTERSTATE75_256X64, stb_invert=False, panel_type=Interstate75.PANEL_GENERIC)
display = i75.display

# These need to be constants for the viper optimized block below.
WIDTH = const(256)
HEIGHT = const(64)

BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(200, 0, 0)


@micropython.viper
def compute_gol(board: ptr8, new_board: ptr8):  # noqa: F821
    for y in range(HEIGHT):
        alive = 0
        if y > 0:
            alive += board[(y - 1) * WIDTH] & 0x80
            alive += board[(y - 1) * WIDTH + 1] & 0x80

        alive += board[y * WIDTH + 1] & 0x80

        if y < HEIGHT - 1:
            alive += board[(y + 1) * WIDTH] & 0x80
            alive += board[(y + 1) * WIDTH + 1] & 0x80

        cur_val = board[y * WIDTH]
        if alive == 0x180:
            new_board[y * WIDTH] = 0x80
        elif alive == 0x100 and cur_val == 0x80:
            new_board[y * WIDTH] = cur_val
        elif cur_val > 0:
            new_board[y * WIDTH] = cur_val - 1

        for x in range(1, WIDTH - 1):
            alive = 0
            if y > 0:
                alive += board[(y - 1) * WIDTH + x - 1] & 0x80
                alive += board[(y - 1) * WIDTH + x] & 0x80
                alive += board[(y - 1) * WIDTH + x + 1] & 0x80

            alive += board[y * WIDTH + x - 1] & 0x80
            alive += board[y * WIDTH + x + 1] & 0x80

            if y < HEIGHT - 1:
                alive += board[(y + 1) * WIDTH + x - 1] & 0x80
                alive += board[(y + 1) * WIDTH + x] & 0x80
                alive += board[(y + 1) * WIDTH + x + 1] & 0x80

            cur_val = board[y * WIDTH + x]
            if alive == 0x180:
                new_board[y * WIDTH + x] = 0x80
            elif alive == 0x100 and cur_val == 0x80:
                new_board[y * WIDTH + x] = cur_val
            elif cur_val > 0:
                new_board[y * WIDTH + x] = cur_val - 1

        alive = 0
        if y > 0:
            alive += board[y * WIDTH - 2] & 0x80
            alive += board[y * WIDTH - 1] & 0x80
        alive += board[(y + 1) * WIDTH - 2] & 0x80

        if y < HEIGHT - 1:
            alive += board[(y + 2) * WIDTH - 2] & 0x80
            alive += board[(y + 2) * WIDTH - 1] & 0x80

        cur_val = board[(y + 1) * WIDTH - 1]
        if alive == 0x180:
            new_board[(y + 1) * WIDTH - 1] = 0x80
        elif alive == 0x100 and cur_val == 0x80:
            new_board[(y + 1) * WIDTH - 1] = cur_val
        elif cur_val > 0:
            new_board[(y + 1) * WIDTH - 1] = cur_val - 1


class GameOfLife:
    def __init__(self, randomize=True):
        self.board = bytearray(WIDTH * HEIGHT)
        self.back_board = bytearray(WIDTH * HEIGHT)

        if randomize:
            for i in range(WIDTH * HEIGHT):
                if randint(0, 3) == 3:
                    self.board[i] = 0x80

    @micropython.native
    def compute(self):
        compute_gol(self.board, self.back_board)
        self.board, self.back_board = self.back_board, self.board

    @micropython.native
    def display(self, display):
        for y in range(HEIGHT):
            for x in range(WIDTH):
                cur_val = self.board[y * WIDTH + x]
                if cur_val == 0x80:
                    pen = WHITE
                else:
                    pen = display.create_pen(0, 0, cur_val)
                display.set_pen(pen)
                display.pixel(x, y)

    def load_rle(self, filename):
        with open(filename, "r") as f:
            first_line = True
            pattern_width = 0
            pattern_height = 0
            finished = False

            while not finished:
                line = f.readline()
                if len(line) == 0:
                    break

                line = line.strip()
                if line[0] == '#':
                    continue

                if first_line:
                    params = line.split(",")
                    for param in params:
                        key, value = param.split("=")
                        key = key.strip()
                        value = value.strip()
                        if key == 'x':
                            pattern_width = int(value)
                        elif key == 'y':
                            pattern_height = int(value)
                        else:
                            print(f"Unknown header param: {key} = {value}")

                    first_line = False
                    y = (HEIGHT - pattern_height) // 2
                    x = (WIDTH - pattern_width) // 2
                    continue

                start = 0
                while start < len(line):
                    if line[start] == '!':
                        finished = True
                        break

                    m = re.match(r'([0-9]*)([bo$])', line[start:])
                    if m is not None:
                        repeat = 1
                        if len(m.group(1)) > 0:
                            repeat = int(m.group(1))

                        if m.group(2) == '$':
                            y += repeat
                            x = (WIDTH - pattern_width) // 2
                        elif m.group(2) == 'o':
                            for i in range(repeat):
                                self.board[y * WIDTH + x] = 0x80
                                x += 1
                        else:
                            x += repeat

                        start += len(m.group(0))
                    else:
                        raise Exception(f"Pattern parse error at {line[start:]}")


# Set randomize to False if you are going to load a file.
gol = GameOfLife(randomize=True)

# R-pentomino
# gol.board[WIDTH*30 + 128] = 0x80
# gol.board[WIDTH*30 + 129] = 0x80
# gol.board[WIDTH*31 + 127] = 0x80
# gol.board[WIDTH*31 + 128] = 0x80
# gol.board[WIDTH*32 + 128] = 0x80

# gol.load_rle("p120gun.rle")

# time.sleep(4)

gen = 0
while True:
    t_start = time.ticks_ms()
    gol.compute()
    gol.display(display)
    gen += 1
    display.set_pen(RED)
    display.text(f"{gen}", 1, 0, scale=1)
    i75.update()
    t_end = time.ticks_ms()
    print(f"Took {t_end - t_start}ms")
    time.sleep(0.001)
