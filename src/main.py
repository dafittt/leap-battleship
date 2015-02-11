#!/usr/bin/python
from settings import *
import os
import sys
lib_dir = os.path.abspath(os.path.join(SRC_DIR, "../lib/LeapSDK"))
sys.path.insert(0, lib_dir)
import Leap
import pygame
from battleground import Battleground
from square import Square, SquareState
from ship import Ship
import random
import time
from haptics import Haptic


class Game:

	def __init__(self):
		"""
		Initialize the game.
		"""
		self.setup_window()
		self.controller = Leap.Controller()
		self.bg_player = Battleground(NUM_SQUARES)  # the player's battleground
		self.bg_comp = Battleground(NUM_SQUARES)  # the opponent's battleground
		self.populate_bg(self.bg_comp)
		self.populate_bg(self.bg_player)
		y_offset = (WINDOW_HEIGHT - BG_DIM) / 2
		x_offset = (WINDOW_WIDTH - BG_DIM * 2) / 4
		# top left corner positions of the respective battlegrounds:
		self.bg_player_x = x_offset
		self.bg_player_y = self.bg_comp_y = y_offset
		self.bg_comp_x = WINDOW_WIDTH - BG_DIM - x_offset
		self.bomb_cooldown = BOMB_COOLDOWN

		# AI variables
		self.ai_ignore = [] 	# list of squares that missed or belong to sunken ships
		self.ai_hits = []		# list of hits the AI scored
		self.comp_turn = False
		self.ai_bomb_cooldown = AI_BOMB_INTERVAL
		self.ai_delay_cooldown = AI_DELAY
		self.old_time = 0
		if ENABLE_HAPTICS:
			self.haptics = Haptic(2)

	def reset(self):
		self.bg_player = Battleground(NUM_SQUARES)
		self.bg_comp = Battleground(NUM_SQUARES)
		self.populate_bg(self.bg_comp)
		self.populate_bg(self.bg_player)

	def populate_bg(self, bg):
		"""
		Populate a battleground with random ships.
		:param bg: the battleground to populate
		"""
		it = SHIP_LENS.__iter__()
		ship_len = it.next()
		while True:
			ship = Ship(ship_len)
			direction = random.randint(0, 1)  # 0 = vertical, 1 = horizontal
			if direction == 0:
				start_x = random.randint(0, NUM_SQUARES - 1)
				start_y = random.randint(0, NUM_SQUARES - 1 - ship_len)
			elif direction == 1:
				start_x = random.randint(0, NUM_SQUARES - 1 - ship_len)
				start_y = random.randint(0, NUM_SQUARES - 1)

			squares = []
			for i in xrange(ship_len):
				if direction == 0:
					squares.append(Square(start_x, start_y + i, SquareState.intact))
				elif direction == 1:
					squares.append(Square(start_x + i, start_y, SquareState.intact))

			ship.squares = squares
			if bg.check_intersect(ship):
				continue
			bg.add_ship(ship)

			# Python's fucked up way to check if an iterator reached the end of a container
			try:
				ship_len = it.next()
			except:
				break

	def setup_window(self):
		"""
		Initialize the window.
		"""
		pygame.init()
		if FULLSCREEN:
			self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
		else:
			self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption(WINDOW_TITLE)

	def resolve_position(self, x, y):
		"""
		Resolve the cursor position to a battleground
		:param x: X value of the cursor position in pixels
		:param y: Y value of the cursor position in pixels
		:return: the battleground, or nothing if no battleground was found
		"""
		if self.bg_comp_x <= x <= self.bg_comp_x + BG_DIM:
			if self.bg_comp_y <= y <= self.bg_comp_y + BG_DIM:
				return self.bg_comp
		elif self.bg_player_x <= x <= self.bg_player_x + BG_DIM:
			if self.bg_player_y <= y <= self.bg_player_y + BG_DIM:
				return self.bg_player

	def draw_bg(self, bg, x_offset, y_offset):
		"""
		Draw a battleground at a certain position of the screen
		:param bg: the battleground to draw
		:param x_offset: the x-offset from the left border of the screen
		:param y_offset: the y-offset from the top border of the screen
		:return: nothing
		"""
		field = bg.representation()
		for y in range(NUM_SQUARES):
			for x in range(NUM_SQUARES):
				square = field[x][y]
				if square.state == SquareState.hit:
					color = pygame.Color("orange")
				elif square.state == SquareState.missed:
					color = pygame.Color("purple")
				elif square.state == SquareState.destroyed:
					color = pygame.Color("red")
				elif square.state == SquareState.intact and (bg == self.bg_player or SHOW_ENEMY_BG):
					color = pygame.Color("grey")  # show ship location for debugging purposes
				else:
					color = pygame.Color(57, 145, 208)

				rect = (x * SQUARE_DIM + x_offset, y * SQUARE_DIM + y_offset, SQUARE_DIM, SQUARE_DIM)
				pygame.draw.rect(self.window, color, rect)
				pygame.draw.rect(self.window, pygame.Color("grey"), rect, 2)

	def handle_leap(self):
		"""
		Interpret the input received from the leap motion controller and translate the input to mouse output.
		Pointing translates to mouse movements and thrusting towards the screen translates to mouse clicks.
		:return: nothing
		"""
		if self.controller.is_connected:
			frame = self.controller.frame()
			pointable = frame.pointables.frontmost
			if pointable.is_valid:
				i_box = frame.interaction_box
				leap_point = pointable.stabilized_tip_position
				normalized_point = i_box.normalize_point(leap_point)
				normalized_point *= 1.5
				normalized_point -= Leap.Vector(.25, .25, .25)
				cursor_x = int(normalized_point.x * WINDOW_WIDTH)
				cursor_y = int((1 - normalized_point.y) * WINDOW_HEIGHT)
				pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, {'pos': (cursor_x, cursor_y)}))

				# detect thrust
				vel = pointable.tip_velocity.z
				if vel < -50 and self.bomb_cooldown >= BOMB_COOLDOWN:
					# drop bomb
					pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (cursor_x, cursor_y)}))
					self.bomb_cooldown = 0
				time_diff = (frame.timestamp - self.controller.frame(1).timestamp) / 1000
				self.bomb_cooldown += time_diff

	def ai_drop_bomb(self, bg, coords):
		status = bg.drop_bomb(coords)
		if status == SquareState.missed:
			self.ai_ignore.append(coords)
		elif status == SquareState.destroyed:
			ship = bg.get_ship_at(coords)
			for destroyed in ship.squares:
				coords = (destroyed.x, destroyed.y)
				self.ai_ignore.append(coords)
				for c in self.ai_hits:
					if c[0] == coords[0] and c[1] == coords[1]:
						self.ai_hits.remove(c)
		elif status == SquareState.hit:
			self.ai_hits.append(coords)

	def ai_decide_action(self, bg):
		if len(self.ai_hits) == 0:
			square = (random.randint(0, NUM_SQUARES-1), random.randint(0, NUM_SQUARES-1))
			while True:
				square = (random.randint(0, NUM_SQUARES-1), random.randint(0, NUM_SQUARES-1))
				if square not in self.ai_ignore:
					break
			self.ai_drop_bomb(bg, square)
		else:
			for hit in self.ai_hits:
				tries = 0
				direction = random.randint(0, 3)  # 0=up, 1=right, 2=down, 4=left
				while True:
					if direction == 0:
						target = (hit[0], hit[1] - 1)
					elif direction == 1:
						target = (hit[0] + 1, hit[1])
					elif direction == 2:
						target = (hit[0], hit[1] + 1)
					else:
						target = (hit[0] - 1, hit[1])

					if 0 <= target[0] < NUM_SQUARES and 0 <= target[1] < NUM_SQUARES:
						if target not in self.ai_ignore and target not in self.ai_hits:
							self.ai_drop_bomb(bg, target)
							return
					tries += 1
					if tries == 4:
						break
					direction = (direction + 1) % 4

	def deploy_bomb(self, cursor_x, cursor_y):
		bg = self.resolve_position(cursor_x, cursor_y)
		if bg == self.bg_comp:
			x_coord = int((cursor_x - self.bg_comp_x) / SQUARE_DIM)
			y_coord = int((cursor_y - self.bg_comp_y) / SQUARE_DIM)
			coords = (x_coord, y_coord)
			square = bg.square_at(coords)
			if square.state == SquareState.empty or square.state == SquareState.intact:
				result = bg.drop_bomb(coords)
				if result == SquareState.hit and ENABLE_HAPTICS:
					self.haptics.set('b')
				self.comp_turn = True

	def get_square(self, bg, cursor_x, cursor_y):
		if bg == self.bg_comp:
			x_coord = int((cursor_x - self.bg_comp_x) / SQUARE_DIM)
			y_coord = int((cursor_y - self.bg_comp_y) / SQUARE_DIM)
			return x_coord, y_coord
		return 0, 0

	def vicinity_vibration(self, app_x, app_y):
		bg = self.resolve_position(app_x, app_y)
		if bg == self.bg_comp:
			empty = True
			pos = self.get_square(bg, app_x, app_y)
			point = bg.square_at(pos).state
			if point == SquareState.intact:
				self.haptics.set('9')
			else:
				adjacent = []
				x, y = self.get_square(bg, app_x, app_y)
				adjacent.append(bg.square_at((x - 1, y - 1)))
				adjacent.append(bg.square_at((x, y - 1)))
				adjacent.append(bg.square_at((x + 1, y - 1)))
				adjacent.append(bg.square_at((x - 1, y)))
				adjacent.append(bg.square_at((x + 1, y)))
				adjacent.append(bg.square_at((x - 1, y + 1)))
				adjacent.append(bg.square_at((x, y + 1)))
				adjacent.append(bg.square_at((x + 1, y + 1)))

				for sq in adjacent:
					if sq.state == SquareState.intact:
						empty = False
						break
				if empty:
					self.haptics.set('0')
				else:
					self.haptics.set('4')

	def run(self):
		"""
		Main loop: called several times per second, handles events
		:return: nothing
		"""
		self.window.fill((20, 20, 20))
		self.draw_bg(self.bg_player, self.bg_player_x, self.bg_player_y)
		self.draw_bg(self.bg_comp, self.bg_comp_x, self.bg_comp_y)

		self.handle_leap()

		new_time = int(round(time.time() * 1000))
		delta = new_time - self.old_time  # time since the last update
		self.old_time = new_time

		if GAME_MODE == TURN_MODE:
			if self.comp_turn:
				self.ai_delay_cooldown -= delta
				if self.ai_delay_cooldown <= 0:
					self.ai_decide_action(self.bg_player)
					self.comp_turn = False
					self.ai_delay_cooldown = AI_DELAY
		elif GAME_MODE == TIME_MODE:
			self.ai_bomb_cooldown -= delta
			if self.ai_bomb_cooldown <= 0:
				self.ai_decide_action(self.bg_player)
				self.ai_bomb_cooldown = AI_BOMB_INTERVAL

		app_x, app_y = pygame.mouse.get_pos()

		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					pygame.event.post(pygame.event.Event(pygame.QUIT))
				elif event.key == pygame.K_F1:
					self.reset()
				elif event.key == pygame.K_SPACE:
					self.deploy_bomb(app_x, app_y)
			elif event.type == pygame.QUIT:
				sys.exit(0)
			elif event.type == pygame.MOUSEBUTTONDOWN:
				if GAME_MODE == TURN_MODE and self.comp_turn:
					print "It's not your turn!"
				else:
					cursor_x, cursor_y = event.pos
					self.deploy_bomb(cursor_x, cursor_y)
			elif event.type == pygame.MOUSEMOTION:
					app_x, app_y = event.pos

		if GAME_MODE == TURN_MODE and self.comp_turn:
			color = (200, 200, 200)
			radius = 20
		else:
			color = (255, 255, 255)
			radius = 15
		pygame.draw.circle(self.window, color, (app_x, app_y), radius, 3)
		pygame.display.flip()

		if GAME_MODE == TIME_MODE:
			self.vicinity_vibration(app_x, app_y)


game = Game()


def main():
	while True:
		game.run()

if __name__ == '__main__':
	main()