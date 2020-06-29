# Azul game model. 
import numpy as np
from enum import Enum

from constants import *

class Tile(Enum):
    # Tile.blue.name = "blue"
    # Tile.blue.value = 1
    blue = 1
    yellow = 2
    red = 3
    black = 4
    teal = 5
    white = 6 # first player tile

class PatternLine:
    # A line on a player's board which contains tiles of one type. 
    # The max number of tiles is capacity, and the current number is num
    def __init__(self, capacity, tile, num):
        self.capacity = capacity
        self.tile = tile
        self.num = num

    @classmethod
    def empty(cls, capacity):
        return cls(capacity=capacity, tile=None, num=0)

    def open_for_tile(self, tile):
        if self.num == self.capacity:
            return False
        if not self.tile:
            return True
        return self.tile == tile

    def add_tiles(self, count, tile):
        # Add tile_count many tiles of the given type to the pattern line.
        # Return a list of leftover tiles.
        assert (self.open_for_tile(tile)), "Cannot add tiles of a different type"
        self.tile = tile
        if count <= self.capacity - self.num:
            self.num += count
            return []
        else:
            leftover = [tile] * (count + self.num - self.capacity)
            self.num = self.capacity
            return leftover

    def is_full(self):
        return self.capacity == self.num

    def clear(self):
        self.tile = None
        self.num = 0

    def copy(self):
        return PatternLine(self.capacity, self.tile, self.num)

class PlayerBoard:
    # Wall is the NUM_TILES-by-NUM_TILES grid of placed tiles
    # Pattern lines are NUM_TILES many rows of tiles that have not been placed on the wall
    # Floor line is a line of unused tiles
    def __init__(self, wall, score, pattern_lines, floor_line):
        self.wall = wall
        self.score = score
        self.pattern_lines = pattern_lines
        self.floor_line = floor_line

    @classmethod
    def empty(cls):
        return cls(
            np.zeros((NUM_TILES, NUM_TILES), dtype=int),
            0,
            [PatternLine.empty(capacity=i) for i in range(1, NUM_TILES+1)],
            [])

    def add_to_floor_line(self, tile, num_tiles):
        # add tiles to floor line
        # Return the extra tile which don't fit on floor line
        num_to_place = min(num_tiles, FLOOR_CAPACITY - len(self.floor_line))
        num_to_return = num_tiles - num_to_place
        self.floor_line += ([tile] * num_to_place)
        return [tile] * num_to_return

    def add_to_pattern_line(self, line_idx, tile, num_tiles):
        extra_tiles = self.pattern_lines[line_idx].add_tiles(num_tiles, tile)
        self.floor_line += extra_tiles
        # There is a possible error here.  
        # should pass this through the add_to_floor_line method and send leftovers to discard pile

    def has_complete_row(self):
        return True in (self.wall != 0).all(axis=1)

    def tiles_in_a_row(self, row, col):
        num = 1
        for i in range(col+1, NUM_TILES):
            if self.wall[row, i]:
                num += 1
            else:
                break
        for i in range(col-1, -1, -1):
            if self.wall[row, i]:
                num += 1
            else:
                break
        return num

    def tiles_in_a_col(self, row, col):
        num = 1
        for i in range(row+1, NUM_TILES):
            if self.wall[i, col]:
                num += 1
            else:
                break
        for i in range(row-1, -1, -1):
            if self.wall[i, col]:
                num += 1
            else:
                break
        return num

    def tile_placement_score(self, row, col):
        # return the score of placing a tile in the (row, col) position of the wall
        row_connected = self.tiles_in_a_row(row, col)
        col_connected = self.tiles_in_a_col(row, col)
        if row_connected == 1:
            return col_connected
        elif col_connected == 1:
            return row_connected
        else:
            return row_connected + col_connected

    def add_to_wall(self, row, tile):
        # Add the tile to the row of the wall
        # Return the score of placing the tile in this position
        column = (tile.value + row - 1) % 5
        self.wall[row,column] = tile.value
        return self.tile_placement_score(row, column)

    def floor_penalty(self):
        num_floor_tiles = min(len(self.floor_line), FLOOR_CAPACITY)
        return sum(FLOOR_PENALTIES[:num_floor_tiles])

    def score_round(self):
        # Do the end of round cleanup and scoring for the playerboard
        # Return the tiles that should go to the discard pile
        discard_tiles = []
        round_score = 0
        for row, line in enumerate(self.pattern_lines):
            if line.is_full():
                round_score += self.add_to_wall(row, line.tile)
                discard_tiles += [line.tile] * (line.num - 1)
                line.clear()
        if self.floor_line:
            round_score += self.floor_penalty()
            discard_tiles += [tile for tile in self.floor_line if tile != Tile.white]
            self.floor_line = []
        self.score = max(self.score + round_score, 0)
        return discard_tiles

    def complete_all_tiles(self):
        count = 0
        for tile in list(Tile):
            if np.sum(self.wall == tile.value) == NUM_TILES:
                count += 1
        return count

    def complete_columns(self):
        return np.sum((self.wall != 0).all(axis=0))

    def complete_rows(self):
        return np.sum((self.wall != 0).all(axis=1))

    def score_endgame(self):
        all_tiles = self.complete_all_tiles()
        columns = self.complete_columns()
        rows = self.complete_rows()
        self.score += (ALL_TILES_BONUS*all_tiles + COLUMN_BONUS*columns + ROW_BONUS*rows)

    def copy(self):
        return PlayerBoard(
            np.copy(self.wall), 
            self.score, 
            [line.copy() for line in self.pattern_lines], 
            self.floor_line.copy())

class Model:
    # boards is a list of one PlayerBoard for every player
    # factories is a list of NUM_FACTORIES lists.  
    # Each internal list contains at most TILES_PER_FACTORY tiles
    # center is a list of tiles
    # draw_pile is a list of tiles
    # discard_pile is a list of tiles
    # next_player is an int in range(NUM_PLAYERS)
    def __init__(
            self,
            boards,
            factories,
            center,
            draw_pile,
            discard_pile,
            next_player):
        self.boards = boards
        self.factories = factories
        self.center = center
        self.draw_pile = draw_pile
        self.discard_pile = discard_pile
        self.next_player = next_player

    @classmethod
    def start(cls):
        return cls(
            [PlayerBoard.empty() for _ in range(NUM_PLAYERS)],
            [[]] * NUM_FACTORIES,
            [Tile.white],
            [Tile.blue, Tile.yellow, Tile.red, Tile.black, Tile.teal] * TILES_PER_COLOR,
            [],
            0)

    def is_valid_move(self, move, player):
        # returns True if a move is valid for player in the current game state
        if self.next_player != player:
            return False
        if not move:
            return False
        if move.factory is None:
            return False
        player_board = self.boards[player]
        if move.pattern_line == -1:
            return True
        if move.tile.value in player_board.wall[move.pattern_line]:
            return False
        pattern_line = player_board.pattern_lines[move.pattern_line]
        return pattern_line.open_for_tile(move.tile)

    def make_move(self, move):
        # play out the given move on the PlayerBoard corresponding to the index of player
        player_board = self.boards[self.next_player]
        if move.from_center():
            assert (move.tile in self.center), "No {} tiles in the center".format(move.tile.name)
            if Tile.white in self.center:
                player_board.floor_line.append(Tile.white)
            num_tiles = self.center.count(move.tile)
            self.center = [tile for tile in self.center if tile not in [Tile.white, move.tile]]
        else:
            assert (move.tile in self.factories[move.factory])
            num_tiles = self.factories[move.factory].count(move.tile)
            extra_tiles = [tile for tile in self.factories[move.factory] if tile != move.tile]
            self.center += extra_tiles
            self.factories[move.factory] = []
        if move.to_floor_line():
            tiles_to_discard = player_board.add_to_floor_line(move.tile, num_tiles)
            self.discard_pile += tiles_to_discard
        else:
            player_board.add_to_pattern_line(move.pattern_line, move.tile, num_tiles)
        self.next_player = (self.next_player + 1) % NUM_PLAYERS

    def setup_round(self):
        # setup for a new round
        if len(self.draw_pile) < NUM_FACTORIES * TILES_PER_FACTORY:
            self.replenish_draw_pile()
        self.fill_factories()
        self.center = [Tile.white]

    def fill_factories(self):
        # Fill the factories with tiles from the draw pile
        assert (len(self.draw_pile) >= NUM_FACTORIES * TILES_PER_FACTORY), "Not enough tiles in draw pile to fill factories"
        indices = np.random.permutation(len(self.draw_pile))
        for i in range(NUM_FACTORIES):
            factory_indices = indices[TILES_PER_FACTORY*i:TILES_PER_FACTORY*(i+1)]
            self.factories[i] = [self.draw_pile[idx] for idx in factory_indices]
        self.draw_pile = [self.draw_pile[idx] for idx in indices[TILES_PER_FACTORY*NUM_FACTORIES:]]

    def replenish_draw_pile(self):
        self.draw_pile += self.discard_pile
        self.discard_pile = []

    def game_over(self):
        for board in self.boards:
            if board.has_complete_row():
                return True
        return False

    def round_over(self):
        for factory in self.factories:
            if factory:
                return False
        if self.center:
            return False
        return True

    def cleanup_round(self):
        # Set the next_player based on who has the white tile.
        # Update the score of each playerboard.
        # Clear completed pattern lines, and update each player's wall
        self.next_player = self.player_with_white_tile()
        for player_board in self.boards:
            self.discard_pile += player_board.score_round()

    def player_with_white_tile(self):
        for i in range(NUM_PLAYERS):
            if Tile.white in self.boards[i].floor_line:
                return i

    def score_endgame(self):
        for player_board in self.boards:
            player_board.score_endgame()

    def winner(self):
        scores = [board.score for board in self.boards]
        return scores.index(max(scores))

    def available_factories(self):
        factory_indices = [i for i in range(NUM_FACTORIES) if self.factories[i]]
        if self.center:
            factory_indices.append(-1)
        return sorted(factory_indices)

class Move:
    # A move consists of a 
    # 1) A factory index (-1 for center)
    # 2) A tile type
    # 3) A pattern line index (-1 for floor line)
    def __init__(self, factory, tile, pattern_line):
        self.factory = factory
        self.tile = tile
        self.pattern_line = pattern_line

    def from_center(self):
        return self.factory == -1

    def to_floor_line(self):
        return self.pattern_line == -1