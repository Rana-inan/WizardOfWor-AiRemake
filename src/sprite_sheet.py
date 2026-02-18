# src/sprite_sheet.py
import pygame
import math

class SpriteSheet:
    def __init__(self, image_path, sprite_width, sprite_height, sprite_pivot_x=0, sprite_pivot_y=0):
        try:
            self.texture = pygame.image.load(image_path).convert_alpha()
        except pygame.error:
            print(f"Sprite dosyası yüklenemedi: {image_path}")
            # Hata durumunda boş bir yüzey oluştur
            self.texture = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
            
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.sprite_pivot = pygame.Vector2(sprite_pivot_x, sprite_pivot_y)
        
        self.left_margin = sprite_pivot_x
        self.right_margin = sprite_width - sprite_pivot_y
        self.top_margin = sprite_pivot_y
        self.bottom_margin = sprite_height - sprite_pivot_y
        
        self.frames = self._init_frames()
    
    def _init_frames(self):
        frames = []
        x_count = self.texture.get_width() // self.sprite_width
        y_count = self.texture.get_height() // self.sprite_height
        
        for y in range(y_count):
            for x in range(x_count):
                frames.append(pygame.Rect(
                    x * self.sprite_width,
                    y * self.sprite_height,
                    self.sprite_width,
                    self.sprite_height
                ))
        
        return frames
    
    @property
    def frame_count(self):
        return len(self.frames)
    
    def draw_frame(self, frame_index, surface, position, rotation, scale, color):
        if frame_index >= len(self.frames):
            return
        
        # Kare kesimi
        frame_rect = self.frames[frame_index]
        frame = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
        frame.blit(self.texture, (0, 0), frame_rect)
        
        # Renk tonu uygula
        if color != (255, 255, 255):
            # Renklendirme
            colored_frame = frame.copy()
            colored_frame.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
            frame = colored_frame
        
        # Ölçekle
        flip_x = scale.x < 0
        flip_y = scale.y < 0
        scale_x = abs(scale.x)
        scale_y = abs(scale.y)
        
        if scale_x != 1 or scale_y != 1:
            new_width = int(self.sprite_width * scale_x)
            new_height = int(self.sprite_height * scale_y)
            frame = pygame.transform.scale(frame, (new_width, new_height))
        
        # Çevir (flip)
        if flip_x or flip_y:
            frame = pygame.transform.flip(frame, flip_x, flip_y)
        
        # Döndür
        if rotation != 0:
            frame = pygame.transform.rotate(frame, -rotation * 180 / math.pi)
        
        # Çiz
        rect = frame.get_rect()
        rect.center = (position.x, position.y)
        surface.blit(frame, rect.topleft)