import pygame
import random
from pygame.math import Vector2
import time
import threading
import keyboard
import sys

pygame.init()

cell_size = 25
number_of_cells = 25
OFFSET = 75
MIDDLE = Vector2(int(number_of_cells/2), int(number_of_cells/2))

COLOR_S1 = (140, 3, 252)
COLOR_S1H = (252, 3, 223)
COLOR_S2 = (161, 252, 3)
COLOR_S2H = (252, 252, 3)
COLOR_WATER = (3, 165, 252)
COLOR_FISH = (0, 1, 89)

lock_check_position = threading.Lock()  # lock for checking whether a fish will spawn inside a serpent while it moves


class Serpent:
    def __init__(self, color, head_color, starting_x, starting_y, direction):
        self.body = [Vector2(starting_x, starting_y)]
        self.color = color
        self.head_color = head_color
        self.direction = direction
        self.add_segment = False
        self.alive = True

        self.cond_move = threading.Condition()

    def draw(self):
        pygame.draw.rect(screen, self.head_color, (
            OFFSET + self.body[0].x * cell_size, OFFSET + self.body[0].y * cell_size, cell_size, cell_size), 0, 7)
        for segment in self.body[1:]:
            segment_rect = (OFFSET + segment.x * cell_size, OFFSET + segment.y * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, self.color, segment_rect, 0, 7)

    def move(self):
        with self.cond_move:
            with lock_check_position:
                self.body.insert(0, self.body[0] + self.direction)

            if self.add_segment:            # check if the serpent is supposed to grow
                self.add_segment = False    # if so, make it stop growing after this move
            else:
                with lock_check_position:
                    self.body.pop()         # otherwise delete the last segment

            self.cond_move.notify()

    def check_collision_with_edges(self):
        # check if serpent out of bounds horizontally
        with lock_check_position:
            if self.body[0].x >= number_of_cells or self.body[0].x <= -1:
                self.alive = False
            # check if serpent out of bounds vertically
            elif self.body[0].y >= number_of_cells or self.body[0].y <= -1:
                self.alive = False

    def check_collision_with_serpent(self, other_serpent):
        with lock_check_position:
            headless_body = self.body[1:]
            # check if both serpents' heads collided
            if self.body[0] == other_serpent.body[0]:
                self.alive = False
                other_serpent.alive = False
            # check if serpent's head collided with a tail
            if self.body[0] in headless_body or self.body[0] in other_serpent.body[1:]:
                self.alive = False


# basic food for serpents: fish
class Fish:
    def __init__(self, position):
        self.position = position

    def draw(self):
        fish_rect = pygame.Rect(OFFSET + self.position.x * cell_size,
                                OFFSET + self.position.y * cell_size, cell_size, cell_size)
        pygame.draw.rect(screen, COLOR_FISH, fish_rect, 0, 7)


class Game:
    def __init__(self):
        self.serpent1 = Serpent(COLOR_S1, COLOR_S1H, 1, 1, Vector2(1, 0))
        self.serpent2 = Serpent(COLOR_S2, COLOR_S2H, number_of_cells-2, number_of_cells-2, Vector2(-1, 0))
        self.fish = [Fish(MIDDLE)]
        self.lives_S1 = 5
        self.lives_S2 = 5
        self.game_over = False
        self.round_over = False
        self.winner = "Draw"
        self.winner_color = COLOR_FISH

        self.lock_fish = threading.Lock()

    def round_over_resolve(self):
        # choose the round winner based on alive status
        if not (self.serpent1.alive or self.serpent2.alive):
            self.lives_S1 -= 1
            self.lives_S2 -= 1
            self.winner = "Draw"
            self.winner_color = COLOR_FISH
        elif not self.serpent1.alive:
            self.lives_S1 -= 1
            self.winner = "Serpent 2"
            self.winner_color = COLOR_S2H
        elif not self.serpent2.alive:
            self.lives_S2 -= 1
            self.winner = "Serpent 1"
            self.winner_color = COLOR_S1H

        # end the game when at least one player runs out of lives
        if self.lives_S1 == 0 or self.lives_S2 == 0:
            self.game_over = True

        # reset the serpents' position
        self.serpent1.body = [Vector2(1, 1)]
        self.serpent1.direction = Vector2(1, 0)
        self.serpent2.body = [Vector2(number_of_cells-2, number_of_cells-2)]
        self.serpent2.direction = Vector2(-1, 0)

        # reset the serpents' alive status
        self.serpent1.alive = True
        self.serpent2.alive = True

    def check_round_over(self):
        # check if a serpent is dead after they have both moved
        with self.serpent1.cond_move:
            with self.serpent2.cond_move:
                if not self.serpent1.alive or not self.serpent2.alive:
                    self.round_over = True
                self.serpent2.cond_move.wait()
            self.serpent1.cond_move.wait()

    def draw(self):
        self.serpent1.draw()
        self.serpent2.draw()
        for fish in self.fish:
            fish.draw()

    def control(self, serpent, new_direction):
        # change serpent's moving direction after it has moved
        with serpent.cond_move:
            if not serpent.direction + new_direction == Vector2(0, 0):
                serpent.direction = new_direction
            serpent.cond_move.wait()

    def spawn_fish(self, fish_pos):
        with self.lock_fish:
            self.fish.append(Fish(fish_pos))

    def eat_fish(self, serpent):
        # let a serpent grow on collision with a fish and delete the fish
        for fish in self.fish:
            if serpent.body[0] == fish.position:
                serpent.add_segment = True
                with self.lock_fish:
                    self.fish.remove(fish)
                break


def generate_random_cell():
    x = random.randint(0, number_of_cells - 1)
    y = random.randint(0, number_of_cells - 1)
    return Vector2(x, y)


# controller for serpent 1
#   W
# A   D
#   S
def control_s1(game):
    while not game.game_over:
        if keyboard.is_pressed('w'):
            game.control(game.serpent1, Vector2(0, -1))
        elif keyboard.is_pressed('d'):
            game.control(game.serpent1, Vector2(1, 0))
        elif keyboard.is_pressed('s'):
            game.control(game.serpent1, Vector2(0, 1))
        elif keyboard.is_pressed('a'):
            game.control(game.serpent1, Vector2(-1, 0))


# controller for serpent 2
#   I
# J   L
#   K
def control_s2(game):
    while not game.game_over:
        if keyboard.is_pressed('i'):
            game.control(game.serpent2, Vector2(0, -1))
        elif keyboard.is_pressed('l'):
            game.control(game.serpent2, Vector2(1, 0))
        elif keyboard.is_pressed('k'):
            game.control(game.serpent2, Vector2(0, 1))
        elif keyboard.is_pressed('j'):
            game.control(game.serpent2, Vector2(-1, 0))


def move(game, serpent, other):
    while not game.game_over:
        if not game.round_over:
            serpent.move()
            serpent.check_collision_with_edges()
            serpent.check_collision_with_serpent(other)
            game.eat_fish(serpent)
            time.sleep(0.2)


def fish_spawner(game):
    while not game.game_over:
        if not game.round_over:
            time.sleep(3)
            # make sure the fish doesn't spawn inside a serpent
            while True:
                cell = generate_random_cell()
                with lock_check_position:
                    if not (cell in game.serpent1.body or cell in game.serpent2.body):
                        break
            game.spawn_fish(cell)


def check_round_over(game):
    while not game.game_over:
        if not game.round_over:
            game.check_round_over()


game = Game()

screen = pygame.display.set_mode((2*OFFSET + cell_size * number_of_cells, 2*OFFSET + cell_size * number_of_cells))
pygame.display.set_caption("Serpents")
title_font = pygame.font.Font(None, 60)
title_surface = title_font.render("Serpents", True, COLOR_FISH)

# thread for controlling serpent 1
control_s1 = threading.Thread(target=control_s1, args=(game,))
control_s1.start()

# thread for controlling serpent 2
control_s2 = threading.Thread(target=control_s2, args=(game,))
control_s2.start()

# thread for moving serpent 1
move_s1 = threading.Thread(target=move, args=(game, game.serpent1, game.serpent2))
move_s1.start()

# thread for moving serpent 2
move_s2 = threading.Thread(target=move, args=(game, game.serpent2, game.serpent1))
move_s2.start()

# thread for checking if the round is over
is_round_over = threading.Thread(target=check_round_over, args=(game,))
is_round_over.start()

# thread for spawning fish
spawner = threading.Thread(target=fish_spawner, args=(game,))
spawner.start()

# main game loop
while not game.game_over:
    screen.fill(COLOR_WATER)
    pygame.draw.rect(screen, (0, 0, 0),
                     (OFFSET - 5, OFFSET - 5, cell_size * number_of_cells + 10, cell_size * number_of_cells + 10), 5)
    screen.blit(title_surface, (cell_size * number_of_cells/2 - 5, 20))
    score_surface1 = title_font.render(str(game.lives_S1), True, COLOR_S1H)
    score_surface2 = title_font.render(str(game.lives_S2), True, COLOR_S2H)
    screen.blit(score_surface1, (OFFSET + cell_size, 20))
    screen.blit(score_surface2, (cell_size * number_of_cells, 20))

    # when the round is over, choose and display the winner and set the board fot the next round
    if game.round_over:
        game.round_over_resolve()
        winner_surface = title_font.render(str(game.winner), True, game.winner_color)
        screen.blit(winner_surface, (cell_size * number_of_cells/2, cell_size * number_of_cells/2))
        game.fish = [Fish(MIDDLE)]
        game.draw()
        pygame.display.update()
        time.sleep(3)
        game.round_over = False
        game.fish = [Fish(MIDDLE)]

    game.draw()
    pygame.display.update()

# when the game is over, choose and display the winner
if game.lives_S1 > game.lives_S2:
    screen.fill(COLOR_WATER)
    winner_surface = title_font.render(str("Serpent 1 won!"), True, COLOR_S1H)
    screen.blit(winner_surface, (cell_size * 10, cell_size * number_of_cells / 2))
elif game.lives_S1 < game.lives_S2:
    screen.fill(COLOR_WATER)
    winner_surface = title_font.render(str("Serpent 2 won!"), True, COLOR_S2H)
    screen.blit(winner_surface, (cell_size * 10, cell_size * number_of_cells / 2))
else:
    screen.fill(COLOR_WATER)
    winner_surface = title_font.render(str("You both lost :P"), True, COLOR_FISH)
    screen.blit(winner_surface, (cell_size * 10, cell_size * number_of_cells / 2))
pygame.display.update()


control_s1.join()
control_s2.join()
move_s1.join()
move_s2.join()
is_round_over.join()
spawner.join()

time.sleep(5)

pygame.display.quit()
pygame.quit()
sys.exit(0)
