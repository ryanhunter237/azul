import tkinter as tk
import tkinter.font as tkfont

from constants import *

class PatternLines(tk.Canvas):
	def __init__(self, master):
		super().__init__(
			master,
			width=NUM_TILES*TILE_SIZE + (NUM_TILES+1)*PADDING - 2,
			height=NUM_TILES*TILE_SIZE + (NUM_TILES+1)*PADDING - 2,
			bg=BOARD_BG, bd=0, highlightthickness=0)
		self.create_tiles()

	def create_tiles(self):
		for row in range(NUM_TILES):
			for col in range(NUM_TILES - row - 1, NUM_TILES):
				self.create_tile(row, col)

	def create_tile(self, row, col):
		x0, y0 = PADDING + col*(TILE_SIZE+PADDING), PADDING + row*(TILE_SIZE+PADDING) 
		x1, y1 = x0 + TILE_SIZE, y0 + TILE_SIZE
		tile = self.create_rectangle(
			(x0, y0, x1, y1), fill=BOARD_BG, 
			width=1, outline=OUTLINE, tag="tile")

	def clicked_row(self, event):
		tile_idx = event.widget.find_closest(event.x, event.y)[0]
		for i in range(len(PATTERN_LINE_INDICES)):
			if tile_idx in PATTERN_LINE_INDICES[i]:
				return i

	def fill(self, row, color, num):
		for tile_idx in PATTERN_LINE_INDICES[row][:-num]:
			self.itemconfig(tile_idx, fill=BOARD_BG)
		for tile_idx in PATTERN_LINE_INDICES[row][-num:]:
			self.itemconfig(tile_idx, fill=color)

class PlayerBoard(tk.Frame):
	def __init__(self, player_id):
		super().__init__(bg=BOARD_BG)
		self.player_id = player_id
		self.pattern_lines = self.init_pattern_lines()
		self.init_arrows()
		self.wall = self.init_wall()
		self.floor_line = self.init_floor_line()
		self.score_label = self.init_score()
		
	def init_pattern_lines(self):
		pattern_lines = PatternLines(self)
		pattern_lines.grid(row=0, column=0)
		return pattern_lines

	@staticmethod
	def create_arrow(canvas, row):
		x0, y0 = PADDING, PADDING + row*(TILE_SIZE+PADDING)
		x1, y1 = x0, y0 + TILE_SIZE
		x2, y2 = x0 + TILE_SIZE//2, (y0+y1) // 2
		canvas.create_polygon((x0,y0,x1,y1,x2,y2), fill=OUTLINE)

	def init_arrows(self):
		arrows = tk.Canvas(
			self,
			width=2*PADDING + TILE_SIZE//2,
			height=NUM_TILES*TILE_SIZE + (NUM_TILES+1)*PADDING,
			bg=BOARD_BG, bd=0, highlightthickness=0)
		arrows.grid(row=0, column=1)
		for row in range(NUM_TILES):
			PlayerBoard.create_arrow(arrows, row)

	@staticmethod
	def create_wall_tile(canvas, row, col):
		x0, y0 = PADDING + col*(TILE_SIZE+PADDING), PADDING + row*(TILE_SIZE+PADDING) 
		x1, y1 = x0 + TILE_SIZE, y0 + TILE_SIZE
		color = TILE_COLORS[(col-row) % NUM_TILES]
		canvas.create_rectangle(
			(x0, y0, x1, y1), 
			fill=color, stipple='gray25', 
			width=1, outline=OUTLINE, tag="tile")

	def init_wall(self):
		wall = tk.Canvas(
			self,
			width=NUM_TILES*TILE_SIZE + (NUM_TILES+1)*PADDING - 2,
			height=NUM_TILES*TILE_SIZE + (NUM_TILES+1)*PADDING - 2,
			bg=BOARD_BG, bd=0, highlightthickness=0)
		wall.grid(row=0, column=2)
		for row in range(NUM_TILES):
			for col in range(NUM_TILES):
				PlayerBoard.create_wall_tile(wall, row, col)
		return wall

	@staticmethod
	def create_floor_line_spot(canvas, position):
		x0, y0 = PADDING + position*(TILE_SIZE+PADDING), PADDING
		x1, y1 = x0 + TILE_SIZE, y0 + TILE_SIZE
		canvas.create_text(
			((x0+x1)//2, y0 + TEXT_HEIGHT//2),
			text=str(FLOOR_PENALTIES[position]),
			font=tkfont.Font(size=TEXT_HEIGHT, weight='bold'))
		canvas.create_rectangle(
			(x0, y0+TEXT_HEIGHT+PADDING, x1, y1+TEXT_HEIGHT+PADDING), 
			fill=BOARD_BG, width=1, outline=OUTLINE, tag='tile')

	def init_floor_line(self):
		floor_line = tk.Canvas(
			self,
			width=FLOOR_CAPACITY*TILE_SIZE + (FLOOR_CAPACITY+1)*PADDING - 2,
			height=TILE_SIZE + TEXT_HEIGHT + 3*PADDING,
			bg=BOARD_BG, bd=0, highlightthickness=0)
		floor_line.grid(row=1, column=0, columnspan=3, sticky='w')
		for pos in range(FLOOR_CAPACITY):
			PlayerBoard.create_floor_line_spot(floor_line, pos)
		return floor_line

	def init_score(self):
		label = tk.Label(
			self, bg=BOARD_BG,
			text="Player {}\nScore: {}".format(self.player_id, 0),
			font=tkfont.Font(size=TEXT_HEIGHT, weight='bold'))
		label.grid(row=1, column=2, sticky='ns')
		return label

	def fill_floor_line(self, tiles):
		floor_line_indices = self.floor_line.find_withtag("tile")
		for i in range(FLOOR_CAPACITY):
			idx = floor_line_indices[i]
			if i < len(tiles):
				color = tiles[i]
			else:
				color = BOARD_BG
			self.floor_line.itemconfig(idx, fill=color)

	def clear(self):
		for tile_idx in self.pattern_lines.find_withtag("tile"):
			self.pattern_lines.itemconfig(tile_idx, fill=BOARD_BG)
		for tile_idx in self.wall.find_withtag("tile"):
			self.wall.itemconfig(tile_idx, stipple='gray25', width=1)
		for tile_idx in self.floor_line.find_withtag("tile"):
			self.floor_line.itemconfig(tile_idx, fill=BOARD_BG)
		self.score_label.config(
			text="Player {}\nScore: {}".format(self.player_id, 0),
			borderwidth=0, relief="ridge")

	def add_pattern_lines_command(self, func):
		canvas = self.pattern_lines
		for tile in canvas.find_withtag("tile"):
			canvas.tag_bind(tile, "<Button-1>", lambda event, canvas=canvas: func(event, canvas))

	def add_floor_line_command(self, func):
		canvas = self.floor_line
		for tile in canvas.find_withtag("tile"):
			canvas.tag_bind(tile, "<Button-1>", lambda event, canvas=canvas: func(event, canvas))

class Factory(tk.Canvas):
	def __init__(self, master):
		super().__init__(
			master, 
			width=SCALING*TILE_SIZE, height=SCALING*TILE_SIZE,
			bg=BOARD_BG, bd=0, highlightthickness=0)
		self.create_circle()
		self.create_tiles()

	def create_circle(self):
		self.create_oval(
			(PADDING, PADDING, SCALING*TILE_SIZE - PADDING, SCALING*TILE_SIZE - PADDING),
			fill=FACTORY_BG, outline=OUTLINE, width=1)

	def create_tiles(self):
		for row in range(2):
			for col in range(2):
				self.create_tile(row, col)

	def create_tile(self, row, col):
		center_x = center_y = TILE_SIZE*SCALING/2
		x0 = center_x - (TILE_SIZE + 0.5*PADDING) + col*(TILE_SIZE+PADDING)
		y0 = center_y - (TILE_SIZE + 0.5*PADDING) + row*(TILE_SIZE+PADDING)
		x1, y1 = x0+TILE_SIZE, y0+TILE_SIZE
		tile = self.create_rectangle((x0, y0, x1, y1), width=1, fill=BOARD_BG, outline=OUTLINE, tags='tile')
		self.tag_bind(tile, '<Button-1>', lambda event, c=self, i=tile: self.master.click_tile(c, i))

	def click_tile(self, tile_index):
		color = self.itemcget(tile_index, "fill")
		if color == BOARD_BG:
			return
		for factory in self.master.factories:
			for idx in factory.find_withtag("tile"):
				if float(factory.itemcget(idx, "width")) > 1:
					factory.itemconfig(idx, width=1)
					continue
				if factory.itemcget(idx, "fill") == color and factory == self:
					factory.itemconfig(idx, width=BOLD_WIDTH)

class CenterBoard(tk.Frame):
	def __init__(self):
		super().__init__(bg=BOARD_BG)
		self.factories = self.init_factories()
		self.center = self.init_center()

	def init_factories(self):
		factories = []
		grid_positions = [(0,0), (0,1), (1,2), (2,0), (2,1)]
		for row, column in grid_positions:
			factories.append(Factory(self))
			factories[-1].grid(row=row, column=column)
		return factories

	def click_tile(self, clicked_canvas, tile_index):
		color = clicked_canvas.itemcget(tile_index, "fill")
		if color in [BOARD_BG, 'white']:
			return
		for canvas in self.factories + [self.center]:
			for idx in canvas.find_withtag("tile"):
				if float(canvas.itemcget(idx, "width")) > 1:
					canvas.itemconfig(idx, width=1)
					continue
				if canvas == clicked_canvas and canvas.itemcget(idx, "fill") in [color, 'white']:
					canvas.itemconfig(idx, width=BOLD_WIDTH)

	def create_center_tile(self, canvas, row, col):
		x0, y0 = PADDING + col*(TILE_SIZE+PADDING), PADDING + row*(TILE_SIZE+PADDING)
		x1, y1 = x0 + TILE_SIZE, y0 + TILE_SIZE
		tile = canvas.create_rectangle((x0, y0, x1, y1), fill=BOARD_BG, width=1, outline=OUTLINE, tag="tile")
		canvas.tag_bind(tile, '<Button-1>', lambda event, c=canvas, i=tile: self.click_tile(c, i))

	def init_center(self):
		center = tk.Canvas(
			self, width=TILE_SIZE*6 + PADDING*7, height=TILE_SIZE*3 + PADDING*4,
			bg=BOARD_BG, bd=0, highlightthickness=0)
		center.grid(row=1, column=0, columnspan=2)
		center.create_rectangle(
			(0.5*PADDING, 0.5*PADDING, 6*TILE_SIZE + 6.5*PADDING, 3*TILE_SIZE + 3.5*PADDING), 
			width=1, fill=FACTORY_BG, outline=BOARD_BG)
		for row in range(3):
			for col in range(6):
				self.create_center_tile(center, row, col)
		return center

class Menu(tk.Menu):
	def __init__(self, master):
		super().__init__(master)
		self.game_menu = self.game_menu()
		self.add_cascade(label="New Game", menu=self.game_menu)
		self.add_command(label="Exit", command=master.quit)
		master.config(menu=self)

	def game_menu(self):
		game_menu = tk.Menu(self, tearoff=0)
		game_menu.add_command(label="vs Person")
		game_menu.add_command(label="vs Computer")
		return game_menu

	def add_vs_person_command(self, func):
		self.game_menu.entryconfig(0, command=func)

	def add_vs_computer_command(self, func):
		self.game_menu.entryconfig(1, command=func)

class View(tk.Frame):
	def __init__(self, master):
		self.menu = Menu(master)
		self.master = master
		self.boards = [PlayerBoard(0), PlayerBoard(1)]
		self.centerboard = CenterBoard()
		self.boards[0].grid(row=0, column=0, padx=2, pady=2)
		self.boards[1].grid(row=1, column=0, padx=2, pady=2)
		self.centerboard.grid(row=0, column=1, rowspan=2, padx=2, pady=2)

	def selected_factory(self):
		# return the index of the factory which has selected tiles
		# return -1 if the selected tiles are in the center
		for factory_idx, factory in enumerate(self.centerboard.factories):
			for tile in factory.find_withtag("tile"):
				if float(factory.itemcget(tile, "width")) > 1:
					return factory_idx
			for tile in self.centerboard.center.find_withtag("tile"):
				if float(self.centerboard.center.itemcget(tile, "width")) > 1:
					return -1
		print("No factory selected")

	def selected_color(self, factory_idx):
		# return the color of the selected tiles which are not white
		if factory_idx == -1:
			canvas = self.centerboard.center
		else:
			canvas = self.centerboard.factories[factory_idx]
		for tile in canvas.find_withtag("tile"):
			if float(canvas.itemcget(tile, "width")) > 1:
				color = canvas.itemcget(tile, "fill")
				if color != 'white':
					return color

	def update(self):
		tk.update()