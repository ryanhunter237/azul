from model import Tile, Move
from constants import *

import numpy as np

class Random_Player:
	def move(self, gamestate):
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