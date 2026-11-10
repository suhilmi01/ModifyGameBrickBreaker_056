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

class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 100
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill='#ff9f1c', outline='white')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:       # bola ikut bergerak sebelum game mulai
                self.ball.move(offset, 0)

    def move_to(self, x):
        """Pindahkan paddle ke posisi x (untuk kontrol mouse), tetap di dalam layar."""
        coords = self.get_position()
        width = self.canvas.winfo_width()
        center = (coords[0] + coords[2]) * 0.5
        offset = x - center
        offset = max(-coords[0], min(width - coords[2], offset))  # batasi ke layar
        if offset != 0:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

class Brick(GameObject):
    # Warna menurut sisa nyawa balok: 1 = hijau, 2 = kuning, 3 = ungu
    COLORS = {1: '#2ecc71', 2: '#f1c40f', 3: '#9b59b6'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill=Brick.COLORS[hits], tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits <= 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])

class Game(tk.Frame):
    MAX_LIVES = 3

    def __init__(self, master):
        super(Game, self).__init__(master)
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#1a1a2e',
                                width=self.width, height=self.height,
                                highlightthickness=0)
        self.canvas.pack()
        self.pack()

        # Kontrol: panah, tombol A/D, dan mouse. Spasi = mulai / main lagi.
        self.canvas.bind('<Left>', lambda _: self.move_paddle(-25))
        self.canvas.bind('<Right>', lambda _: self.move_paddle(25))
        self.canvas.bind('<a>', lambda _: self.move_paddle(-25))
        self.canvas.bind('<d>', lambda _: self.move_paddle(25))
        self.canvas.bind('<Motion>', lambda e: self.move_paddle_to(e.x))
        self.canvas.bind('<space>', lambda _: self.on_space())
        # [BARU] Klik kiri = mulai / main lagi, klik kanan = jeda / lanjut
        self.canvas.bind('<Button-1>', lambda _: self.on_space())
        self.canvas.bind('<Button-3>', lambda _: self.toggle_pause())
        self.canvas.config(cursor='none')   # [BARU] sembunyikan kursor di area game
        # [BARU] Tombol jeda: P atau Esc
        self.canvas.bind('<Return>', lambda _: self.toggle_pause())    # Enter
        self.canvas.bind('<KP_Enter>', lambda _: self.toggle_pause())  # Enter di numpad
        self.loop_id = None          # ID timer game_loop (untuk dibatalkan saat jeda)
        self.canvas.focus_set()

        self.new_game()

    # ---------- Persiapan game ----------
    def new_game(self):
        """Reset semuanya: nyawa kembali 3, balok disusun ulang."""
        self.canvas.delete('all')
        self.items = {}
        self.ball = None
        self.lives = Game.MAX_LIVES
        self.state = 'ready'   # ready / playing / paused / waiting / won / lost

        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle

        # 4 baris balok: ungu (3 hit), kuning (2 hit), hijau (1 hit) x2
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)
            self.add_brick(x + 37.5, 110, 1)

        self.draw_lives()
        self.draw_text(self.width / 2, 385,
                       'Mouse / Panah = gerak  |  Klik kiri = mulai  |  Enter / Klik kanan = Jeda', size=10, tag='hint')
        self.prepare_round()

    def prepare_round(self):
        """Siapkan bola baru di atas paddle dan tunggu pemain menekan Spasi."""
        self.add_ball()
        self.draw_text(300, 200, 'Klik / Spasi untuk mulai', size=30, tag='msg')
        self.state = 'ready'

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        pc = self.paddle.get_position()
        x = (pc[0] + pc[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    # ---------- Tampilan ----------
    def draw_text(self, x, y, text, size=40, tag=None):
        return self.canvas.create_text(x, y, text=text, font=('Forte', size),
                                       fill='white', tags=tag or '')

    def draw_lives(self):
        """Gambar nyawa sebagai bulatan merah (sisa nyawa = jumlah bulatan)."""
        self.canvas.delete('life')
        self.canvas.create_text(40, 20, text='Nyawa:', font=('Forte', 12),
                                fill='white', tags='life')
        for i in range(self.lives):
            x = 85 + i * 24
            self.canvas.create_oval(x, 11, x + 16, 27, fill='#ff4d6d',
                                    outline='white', tags='life')

    def clear_message(self):
        self.canvas.delete('msg')

    # ---------- Alur game ----------
    def on_space(self):
        if self.state == 'ready':
            self.start_game()
        elif self.state in ('won', 'lost'):
            self.new_game()          # main lagi dari awal

    def move_paddle(self, offset):
        # Paddle tidak boleh bergerak saat game dijeda
        if self.state != 'paused':
            self.paddle.move(offset)

    def move_paddle_to(self, x):
        if self.state != 'paused':
            self.paddle.move_to(x)

    def toggle_pause(self):
        """[BARU] Jeda / lanjutkan game dengan Enter."""
        if self.state == 'playing':
            self.state = 'paused'
            if self.loop_id is not None:
                self.after_cancel(self.loop_id)   # hentikan timer loop
                self.loop_id = None
            self.draw_text(300, 180, 'JEDA', tag='pause')
            self.draw_text(300, 230, 'Tekan Enter untuk lanjut', size=18, tag='pause')
        elif self.state == 'paused':
            self.canvas.delete('pause')
            self.state = 'playing'
            self.game_loop()                      # lanjutkan loop

    def start_game(self):
        self.clear_message()
        self.paddle.ball = None      # bola lepas dari paddle
        self.state = 'playing'
        self.game_loop()

    def game_loop(self):
        if self.state != 'playing':
            return
        self.check_collisions()

        if len(self.canvas.find_withtag('brick')) == 0:
            self.state = 'won'
            self.draw_text(300, 180, 'You win!', tag='msg')
            self.draw_text(300, 230, 'Klik / Spasi untuk main lagi', size=18, tag='msg')
        elif self.ball.get_position()[3] >= self.height:
            self.lose_life()
        else:
            self.ball.update()
            self.loop_id = self.after(30, self.game_loop)

    def lose_life(self):
        self.lives -= 1
        self.draw_lives()
        if self.lives <= 0:
            self.state = 'lost'
            self.draw_text(300, 180, 'Game Over!', tag='msg')
            self.draw_text(300, 230, 'Klik / Spasi untuk main lagi', size=18, tag='msg')
        else:
            self.state = 'waiting'
            # Jeda 1 detik, lalu bola baru muncul di paddle
            self.after(1000, self.prepare_round)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Hello, Jarvis!')
    root.resizable(False, False)
    game = Game(root)
    game.mainloop()



