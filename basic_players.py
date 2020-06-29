from model import Tile, Move
from constants import *

import numpy as np

class Random_Player:
	def move(self, gamestate):
		print(len(self.possible_moves(gamestate)))
		# Given the gamestate as an instance of Model, return a random Move
		possible_factories = [i for i in range(NUM_FACTORIES) if gamestate.factories[i]]
		if len(gamestate.center) > 1 or Tile.white not in gamestate.center:
		    possible_factories.append(-1)
		factory = np.random.choice(possible_factories)
		if factory == -1:
		    tile = np.random.choice([tile for tile in gamestate.center if tile != Tile.white])
		else:
		    tile = np.random.choice(gamestate.factories[factory])
		board = gamestate.boards[gamestate.next_player]
		possible_pattern_lines = [i for i in range(NUM_TILES) if board.pattern_lines[i].open_for_tile(tile)]
		possible_pattern_lines.append(-1)
		pattern_line = np.random.choice(possible_pattern_lines)
		return Move(factory, tile, pattern_line)

class Heuristic_Player:
	def possible_moves(self, gamestate):
		moves = []
		for factory_idx, factory in enumerate(gamestate.factories):
			for tile in set(factory):
				for line_idx in range(-1, 5):
					move = Move(factory_idx, tile, line_idx)
					if gamestate.is_valid_move(move, gamestate.next_player):
						moves.append(move)
		for tile in set([t for t in gamestate.center if t != Tile.white]):
			for line_idx in range(-1, 5):
				move = Move(-1, tile, line_idx)
				if gamestate.is_valid_move(move, gamestate.next_player):
					moves.append(move)
		return moves

	def num_tiles_in_move(self, move, gamestate):
		if move.from_center():
			return len([t for t in gamestate.center if t == move.tile])
		else:
			return len([t for t in gamestate.factories[move.factory] if t == move.tile])

	def predicted_bonus(self, board):
		bonus = 0
		for row in range(NUM_TILES):
			capacity = NUM_TILES * (row+1)
			num = np.sum(board.wall[row,:] != 0) * (row+1)
			num += board.pattern_lines[row].num
			bonus += ROW_BONUS*(num/capacity)**2
		for col in range(NUM_TILES):
			num = 0
			for row in range(NUM_TILES):
				if board.wall[row, col] != 0:
					num += (row+1)
				elif board.pattern_lines[row].tile:
					tile_val = board.pattern_lines[row].tile.value
					if (tile_val + row - 1) % 5 == col:
						num += board.pattern_lines[row].num
			bonus += COLUMN_BONUS*(num/15)**2
		for tile in list(Tile):
			num = 0
			for row in range(NUM_TILES):
				if tile.value in board.wall[row]:
					num += (row+1)
				elif tile == board.pattern_lines[row].tile:
					num += board.pattern_lines[row].num
			bonus += ALL_TILES_BONUS*(num/15)**2
		return bonus

	def move_score(self, move, gamestate):
		board = gamestate.boards[gamestate.next_player].copy()
		num_tiles = self.num_tiles_in_move(move, gamestate)
		if move.to_floor_line():
		    board.add_to_floor_line(move.tile, num_tiles)
		else:
		    board.add_to_pattern_line(move.pattern_line, move.tile, num_tiles)
		board.score_round()
		score = board.score
		return score + self.predicted_bonus(board)

	def move(self, gamestate):
		moves = self.possible_moves(gamestate)
		#print(f"num moves = {len(moves)}")
		max_score = -10
		for move in moves:
			score = self.move_score(move, gamestate)
			if score > max_score:
				max_score = score
				best_move = move
		return best_move