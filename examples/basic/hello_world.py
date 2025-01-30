from interstate75 import Interstate75

i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_128X128)
graphics = i75.display

MAGENTA = graphics.create_pen(255, 0, 255)
BLACK = graphics.create_pen(0, 0, 0)
WHITE = graphics.create_pen(255, 255, 255)

while True:
    graphics.set_pen(MAGENTA)
    graphics.text("hello", 1, 0, scale=4)
    graphics.set_pen(WHITE)
    graphics.text("world", 1, 30, scale=4)
    i75.update(graphics)
