import tkinter as tk


class GameObject(object):
    """Kelas dasar semua objek game (bola, paddle, balok)."""

    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)

class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]   # arah awal: kanan-atas
        self.speed = 10            # [DIUBAH] kecepatan awal 7 -> 10
        self.max_speed = 16        # [DIUBAH] batas maksimal 12 -> 16
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='#00ffd5', outline='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        # Pantul di dinding. Memakai abs() supaya bola tidak "tersangkut" di dinding.
        if coords[0] <= 0:
            self.direction[0] = abs(self.direction[0])
        if coords[2] >= width:
            self.direction[0] = -abs(self.direction[0])
        if coords[1] <= 0:
            self.direction[1] = abs(self.direction[1])
        self.move(self.direction[0] * self.speed,
                  self.direction[1] * self.speed)

    def collide(self, game_objects):
        coords = self.get_position()
        ball_x = (coords[0] + coords[2]) * 0.5
        ball_y = (coords[1] + coords[3]) * 0.5

        paddles = [o for o in game_objects if isinstance(o, Paddle)]
        bricks = [o for o in game_objects if isinstance(o, Brick)]

        # --- Tabrakan dengan paddle ---
        # Sudut pantul ditentukan oleh bagian paddle yang kena:
        # tengah = lurus ke atas, pinggir = miring. Ini bikin game bisa "diarahkan".
        if paddles:
            p = paddles[0]
            pc = p.get_position()
            center = (pc[0] + pc[2]) * 0.5
            ratio = (ball_x - center) / (p.width / 2)
            ratio = max(-1, min(1, ratio))
            if abs(ratio) < 0.15:               # hindari bola lurus 100% vertikal
                ratio = 0.15 if ratio >= 0 else -0.15
            self.direction[0] = ratio
            self.direction[1] = -1              # selalu naik setelah kena paddle

        # --- Tabrakan dengan balok ---
        if bricks:
            if len(bricks) > 1:
                # Kena beberapa balok sekaligus -> pantul vertikal
                avg_y = sum((b.get_position()[1] + b.get_position()[3]) * 0.5
                            for b in bricks) / len(bricks)
                self.direction[1] = 1 if ball_y > avg_y else -1
            else:
                bc = bricks[0].get_position()
                if ball_x > bc[2]:              # kena sisi kanan balok
                    self.direction[0] = 1
                elif ball_x < bc[0]:            # kena sisi kiri balok
                    self.direction[0] = -1
                else:                           # kena atas/bawah balok
                    brick_y = (bc[1] + bc[3]) * 0.5
                    self.direction[1] = 1 if ball_y > brick_y else -1

            for b in bricks:
                b.hit()
                if self.speed < self.max_speed:
                    self.speed += 0.15          # [DIUBAH] percepatan per balok 0.1 -> 0.15



