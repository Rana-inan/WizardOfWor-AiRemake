# src/wizard.py 
import pygame
import random
from src.enemy import Enemy
from src.config_manager import ConfigManager
from src.constants import Constants
from src.camera_shake import CameraShake

class Wizard(Enemy):
    def __init__(self, sprite_sheet, level, score):
        super().__init__(sprite_sheet, (255, 255, 255), False, score)
        self.set_speed(ConfigManager.get_config(Constants.WIZARD_SPEED, Constants.DEFAULT_WIZARD_SPEED))
        self.set_animation_speed(10)
        self._preferred_horizontal_direction = 0
        self._teleport_timer = 0
        self._teleport_cooldown = ConfigManager.get_config(Constants.WIZARD_TELEPORT_COOLDOWN, Constants.DEFAULT_WIZARD_TELEPORT_COOLDOWN)
        self._level = level
        self._random = random.Random()
    
    def is_valid_position(self, x, y):
        """Wizard için geçerli pozisyon kontrolü"""
        # Grid koordinatlarına çevir
        grid_x = int(x // self._level._cell_width)
        grid_y = int(y // self._level._cell_height)
        
        # Dış sınır kontrolü - oyun alanı içinde kalmalı
        if grid_x < 1 or grid_x >= self._level._width - 1:
            return False
        if grid_y < 1 or grid_y >= self._level._height - 1:
            return False
        
        # Cage alanı kontrolü - kafeslere girememeli
        if grid_x == 11 and grid_y == 7:  # P1 cage
            return False
        if grid_x == 1 and grid_y == 7:   # P2 cage
            return False
        
        # Cage çıkışlarına da girememeli
        if grid_x == 11 and grid_y == 6:  # P1 cage exit
            return False
        if grid_x == 1 and grid_y == 6:   # P2 cage exit
            return False
            
        return True
    
    def get_valid_random_position(self):
        """Wizard için kısıtlamalara uygun rastgele pozisyon"""
        max_attempts = 50
        
        for _ in range(max_attempts):
            # Güvenli aralıkta rastgele konum seç
            grid_x = 2 + self._random.randint(0, self._level._width - 5)  # 2 to width-3
            grid_y = 2 + self._random.randint(0, self._level._height - 5)  # 2 to height-3
            
            # Cage alanlarından ve çıkışlarından uzak dur
            if self._is_cage_area(grid_x, grid_y):
                continue
            
            position = self._level.get_cell_position(grid_x, grid_y)
            if self.is_valid_position(position.x, position.y):
                return position
        
        # Son çare olarak güvenli merkezi konum döndür
        return self._level.get_cell_position(6, 3)
    
    def _is_cage_area(self, grid_x, grid_y):
        """Cage alanı ve çevresini kontrol et"""
        # P1 cage ve çıkışı
        if (grid_x == 11 and grid_y in [6, 7]) or (grid_x == 10 and grid_y == 7):
            return True
        
        # P2 cage ve çıkışı  
        if (grid_x == 1 and grid_y in [6, 7]) or (grid_x == 2 and grid_y == 7):
            return True
            
        return False
    
    def can_move_to_position(self, new_x, new_y):
        """Wizard'ın belirtilen pozisyona hareket edip edemeyeceğini kontrol et"""
        return self.is_valid_position(new_x, new_y)
    
    def get_valid_direction(self):
        """Geçerli bir hareket yönü döndür"""
        current_x = self.pixel_position_x
        current_y = self.pixel_position_y
        
        # Mümkün hareket yönleri
        directions = [
            pygame.Vector2(1, 0),   # Sağ
            pygame.Vector2(-1, 0),  # Sol
            pygame.Vector2(0, 1),   # Aşağı
            pygame.Vector2(0, -1)   # Yukarı
        ]
        
        valid_directions = []
        cell_width = self._level._cell_width
        cell_height = self._level._cell_height
        
        for direction in directions:
            new_x = current_x + direction.x * cell_width
            new_y = current_y + direction.y * cell_height
            
            if self.can_move_to_position(new_x, new_y):
                valid_directions.append(direction)
        
        # Geçerli yönler varsa rastgele birini seç
        if valid_directions:
            return self._random.choice(valid_directions)
        
        # Hiç geçerli yön yoksa mevcut yönde devam et (güvenlik için)
        return self.move_direction if hasattr(self, 'move_direction') else pygame.Vector2(1, 0)
    
    def update(self, delta_time):
        super().update(delta_time)
        self._teleport_timer += delta_time
        
        if self._teleport_timer > self._teleport_cooldown:
            self._teleport_timer -= self._teleport_cooldown
            
            # Kısıtlamalara uygun rastgele pozisyona teleport
            new_position = self.get_valid_random_position()
            self.move_to(new_position)
            
            # Geçerli bir yön seç
            new_direction = self.get_valid_direction()
            self.look_to(new_direction)
            
            # Ateş et (eğer başka düşman ateş etmiyorsa)
            if not Enemy.is_any_enemy_firing():
                self.fire()
                
            CameraShake.shake(1, 100, 0.2)
    
    def move(self, delta_time):
        """Wizard'ın hareketini kontrol et"""
        # Hareket etmeden önce yeni pozisyonu kontrol et
        movement_scale = 0.2
        new_position = self._position + self._move_direction * movement_scale
        
        if self.can_move_to_position(new_position.x, new_position.y):
            # Güvenli hareket
            self._position = new_position
        else:
            # Geçersiz hareket, yön değiştir
            new_direction = self.get_valid_direction()
            self.look_to(new_direction)
    
    def can_fire_at_player(self, player):
        return False
    
    