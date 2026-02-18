# src/worluk.py
import pygame
from src.enemy import Enemy
from src.config_manager import ConfigManager
from src.constants import Constants

class Worluk(Enemy):
    def __init__(self, sprite_sheet, color, preferred_direction, score):
        super().__init__(sprite_sheet, color, False, score)
        self.set_speed(100)  # Çok hızlı!
        self.set_animation_speed(30)  # Animasyon da hızlı
        self._preferred_horizontal_direction = preferred_direction
    
    def can_fire_at_player(self, player):
        return False
    
    def draw(self, surface, display_offset_x=0, display_offset_y=0):
        self._current_scale = pygame.Vector2(1, 1)
        self._current_rotation = 0
        super().draw(surface, display_offset_x, display_offset_y)
    
   