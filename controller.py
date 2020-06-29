from model import Model, Tile, Move
from view import View, PatternLines
from constants import *
from basic_players import Heuristic_Player

def color_of_tile(test_tile):
    for color, tile in zip(TILE_COLORS, Tile):
        if tile == test_tile:
            return color

def tile_of_color(test_color):
    for tile, color in zip(Tile, TILE_COLORS):
        if color == test_color:
            return tile

class Controller:
    def __init__(self, root):
        self.model = Model.start()
        self.view = View(root)
        self.view.menu.add_vs_person_command(self.setup_pvp_game)
        self.view.menu.add_vs_computer_command(self.setup_pvc_game)

    def setup_pvp_game(self):
        self.model = Model.start()
        for board in self.view.boards:
            board.clear()
            board.add_pattern_lines_command(self.make_player_move)
            board.add_floor_line_command(self.make_player_move)
        self.setup_round()

    def setup_pvc_game(self):
        # assume computer plays second for now
        self.model = Model.start()
        for board in self.view.boards:
            board.clear()
        board = self.view.boards[0]
        board.add_pattern_lines_command(self.make_player_move)
        board.add_floor_line_command(self.make_player_move)
        self.computer_player = Heuristic_Player()
        self.make_computer_move()
        self.setup_round()

    def make_computer_move(self):
        if self.model.next_player == 1:
            move = self.computer_player.move(self.model)
            self.make_move(move)
        self.job = self.view.master.after(1000, self.make_computer_move)

    def setup_round(self):
        self.model.setup_round()
        self.fill_factories()
        self.fill_center()
        self.mark_player()

    def cleanup_round(self):
        self.model.cleanup_round()
        for player in range(2):
            self.fill_floor_line(player)
            self.update_score(player)
            self.fill_wall(player)
            for row in range(NUM_TILES):
                self.fill_pattern_lines(player, row)

    def fill_factories(self):
        for i in range(NUM_FACTORIES):
            self.fill_factory(i)

    def fill_factory(self, factory_idx):
        tiles = self.model.factories[factory_idx]
        factory = self.view.centerboard.factories[factory_idx]
        tile_indices = factory.find_withtag("tile")
        for i in range(TILES_PER_FACTORY):
            if i < len(tiles):
                color = color_of_tile(tiles[i])
            else:
                color = BOARD_BG
            factory.itemconfig(tile_indices[i], fill=color, width=1)
        factory.update()

    def fill_center(self):
        # update view
        center = self.view.centerboard.center
        tile_indices = center.find_withtag("tile")
        for i in range(18):
            if i < len(self.model.center):
                color = color_of_tile(self.model.center[i])
            else:
                color = BOARD_BG
            center.itemconfig(tile_indices[i], fill=color)
            center.itemconfig(tile_indices[i], width=1)
        center.update()

    def fill_pattern_lines(self, player, pattern_line_idx):
        board = self.view.boards[player]
        pattern_line = self.model.boards[player].pattern_lines[pattern_line_idx]
        if pattern_line.tile:
            color = color_of_tile(pattern_line.tile)
        else:
            color = BOARD_BG
        num = pattern_line.num
        board.pattern_lines.fill(pattern_line_idx, color, num)
        board.pattern_lines.update()

    def fill_floor_line(self, player):
        board = self.view.boards[player]
        floor_line = self.model.boards[player].floor_line
        board.fill_floor_line([color_of_tile(tile) for tile in floor_line])
        board.floor_line.update()

    def update_score(self, player):
        board = self.view.boards[player]
        score = self.model.boards[player].score
        board.score_label.config(text="Player {}\nScore: {}".format(player, score))
        board.score_label.update()

    def fill_wall(self, player):
        board = self.view.boards[player]
        model_wall = self.model.boards[player].wall
        tile_indices = board.wall.find_withtag("tile")
        for row in range(NUM_TILES):
            for col in range(NUM_TILES):
                if model_wall[row, col] != 0:
                    idx = tile_indices[row*NUM_TILES + col]
                    board.wall.itemconfig(idx, stipple='', width=BOLD_WIDTH)
        board.wall.update()

    def mark_player(self):
        player = self.model.next_player
        for board in self.view.boards:
            if board.player_id == player:
                board.config(highlightbackground="black")
                board.config(highlightcolor="black")
                board.config(highlightthickness=3)
            else:
                board.config(highlightthickness=0)
            board.update()

    def mark_winner(self):
        for player in range(2):
             self.update_score(player)
        for board in self.view.boards:
            board.config(highlightthickness=0)
        winner = self.model.winner()
        winner_board = self.view.boards[winner]
        winner_board.score_label.config(borderwidth=4)
        winner_board.score_label.config(relief="ridge")

    def selected_move(self, event, move_canvas):
        factory_idx = self.view.selected_factory()
        if factory_idx is None:
            return None
        color = self.view.selected_color(factory_idx)
        if isinstance(move_canvas, PatternLines):
            line_idx = move_canvas.clicked_row(event)
        else:
            line_idx = -1
        player = move_canvas.master.player_id
        return Move(factory_idx, tile_of_color(color), line_idx)

    def make_player_move(self, event, move_line):
        # process a player's move from an event in self.view
        # move_line is the canvas (pattern_lines or floor_line) where the move is played
        move = self.selected_move(event, move_line)
        selected_board = move_line.master.player_id
        if self.model.is_valid_move(move, selected_board):
            self.make_move(move)

    def make_move(self, move):
        player = self.model.next_player
        self.model.make_move(move)
        self.fill_factory(move.factory)
        self.fill_center()
        self.fill_pattern_lines(player, move.pattern_line)
        self.fill_floor_line(player)
        if self.model.round_over():
            self.cleanup_round()
            if self.model.game_over():
                self.model.score_endgame()
                self.mark_winner()
                if hasattr(self, "job"):
                    self.view.master.after_cancel(self.job)
            else:
                self.setup_round()
        self.mark_player()