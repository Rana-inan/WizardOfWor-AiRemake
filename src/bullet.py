# src/bullet.py
import math
import pygame
from enum import Enum

class BulletTargetTypes(Enum):
    PLAYER = 0
    ANY = 1

class Bullet:
    def __init__(self, origin, target_type, speed):
        self._color = origin.color
        self._origin = origin
        self._position = origin.position + origin.sprite_sheet.sprite_pivot
        self._velocity = origin.move_direction * speed
        self._target_type = target_type
    
    @property
    def origin(self):
        return self._origin
    
    @property
    def pixel_position_x(self):
        return math.floor(self._position.x)
    
    @property
    def pixel_position_y(self):
        return math.floor(self._position.y)
    
    @property
    def target_type(self):
        return self._target_type
    
    def update(self, delta_time):
        self._position += self._velocity * delta_time
    
    def test_hit(self, character):
        distance_x = abs(character.pixel_position_x - self.pixel_position_x + character.sprite_sheet.sprite_pivot.x)
        distance_y = abs(character.pixel_position_y - self.pixel_position_y + character.sprite_sheet.sprite_pivot.y)
        
        return (distance_x <= character.sprite_sheet.sprite_pivot.x and 
                distance_y <= character.sprite_sheet.sprite_pivot.y)
    
    def draw(self, surface, display_offset_x=0, display_offset_y=0):
        y_offset = 1
        x_offset = 1
        pygame.draw.rect(
            surface,
            self._color,
            (self.pixel_position_x + display_offset_x + x_offset, 
             self.pixel_position_y + display_offset_y + y_offset, 
             1, 1)
        )