# src/character.py
import math
import pygame

class Character:
    def __init__(self, sprite_sheet):
        self._enabled = True
        self._visible = True
        self._sprite_sheet = sprite_sheet
        self._position = pygame.Vector2(0, 0)
        self._current_frame = 0
        self._color = (255, 255, 255)  # Beyaz
        
        self._orientation = pygame.Vector2(0, 0)
        self._move_direction = pygame.Vector2(0, 0)
        self._current_rotation = 0
        self._current_scale = pygame.Vector2(1, 1)
        self._speed = 0
        self._move_step = 0
        self._animation_speed = 0
        
        self.can_change_direction = True
        self.look_to(pygame.Vector2(1, 0))
    
    @property
    def visible(self):
        return self._visible
    
    @visible.setter
    def visible(self, value):
        self._visible = value
    
    @property
    def is_alive(self):
        return self._enabled
    
    @property
    def sprite_sheet(self):
        return self._sprite_sheet
    
    @property
    def position(self):
        return self._position
    
    @property
    def pixel_position_x(self):
        return math.floor(self._position.x)
    
    @property
    def pixel_position_y(self):
        return math.floor(self._position.y)
    
    @property
    def color(self):
        return self._color
    
    @property
    def move_direction(self):
        return self._move_direction
    
    @property
    def current_rotation(self):
        return self._current_rotation
    
    @property
    def current_scale(self):
        return self._current_scale
    
    def set_color(self, color):
        self._color = color
    
    def set_speed(self, speed):
        self._speed = speed
    
    def set_animation_speed(self, animation_speed):
        self._animation_speed = animation_speed
    
    def set_frame(self, frame_index):
        if 0 <= frame_index < self._sprite_sheet.frame_count:
            self._current_frame = frame_index
    
    def move_to(self, position):
        self._position = position
    
    def move_by(self, translation):
        self._position += translation
    
    def look_to(self, direction):
        self._move_direction = direction
        
        if direction.x != 0:
            self._orientation.x = direction.x
            self._current_scale.x = direction.x
            
        if direction.y != 0:
            self._orientation.y = direction.y
            self._current_scale.y = -self._orientation.x * self._orientation.y
        else:
            self._current_scale.y = 1
            
        self._orientation.y = direction.y
        self._current_rotation = self._orientation.x * self._orientation.y * math.pi / 2
    
    def move(self, delta_time=None):
        # Hücre boyutları - level'daki değerlerle aynı
        cell_width = 12
        cell_height = 10
        
        # Grid bazlı hareket
        new_x = self._position.x
        new_y = self._position.y
        
        if self._move_direction.x != 0:
            new_x += self._move_direction.x * cell_width
        if self._move_direction.y != 0:
            new_y += self._move_direction.y * cell_height
        
        # Yeni pozisyonu ata
        self._position.x = new_x
        self._position.y = new_y
    
    def animate(self, delta_time):
        # Grid bazlı hareket için, sadece animasyon frame'ini güncelleriz
        # ama pozisyon arası geçiş animasyonu yapmayız
        self._current_frame = self._current_frame + delta_time * self._animation_speed
        if self._current_frame >= self._sprite_sheet.frame_count:
            self._current_frame = 0
    
    def die(self):
        self._enabled = False
    
 
    # character.py içinde draw metodunu güncelleyin
    def draw(self, surface, display_offset_x=0, display_offset_y=0):
        if self.visible:
            # Manuel offset ile merkezleme
            FRAME_WIDTH = -10   # Sprite genişliği (örnek)
            FRAME_HEIGHT = -10  # Sprite yüksekliği (örnek)

            draw_x = self.pixel_position_x - FRAME_WIDTH // 2 + display_offset_x
            draw_y = self.pixel_position_y - FRAME_HEIGHT // 2 + display_offset_y

            self._sprite_sheet.draw_frame(
                int(math.floor(self._current_frame)),
                surface,
                pygame.Vector2(draw_x, draw_y),
                self._current_rotation,
                self._current_scale,
                self._color
            )