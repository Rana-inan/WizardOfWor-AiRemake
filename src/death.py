# src/death.py
import math
import pygame

class Death:
    ANIMATION_SPEED = 10
    
    def __init__(self, sprite_sheet, x, y, color, orientation, scale):
        self._sprite_sheet = sprite_sheet
        self._position_x = x
        self._position_y = y
        self._current_frame = 0
        self._color = color
        self._enabled = True
        self._scale = scale
        self._orientation = orientation
    
    @property
    def enabled(self):
        return self._enabled
    
    def update(self, delta_time):
        self._current_frame = self._current_frame + delta_time * self.ANIMATION_SPEED
        if self._current_frame > self._sprite_sheet.frame_count:
            self._enabled = False
    

    def draw(self, surface, display_offset_x=0, display_offset_y=0):
        # Character sınıfındaki gibi aynı offset'leri uygula
        FRAME_WIDTH = -10   # Sprite genişliği (örnek) 
        FRAME_HEIGHT = -10  # Sprite yüksekliği (örnek)

        draw_x = self._position_x - FRAME_WIDTH // 2 + display_offset_x
        draw_y = self._position_y - FRAME_HEIGHT // 2 + display_offset_y

        self._sprite_sheet.draw_frame(
            int(math.floor(self._current_frame)),
            surface,
            pygame.Vector2(draw_x, draw_y),
            self._orientation,
            self._scale,
            self._color
        )