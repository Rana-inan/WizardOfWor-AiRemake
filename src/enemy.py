# src/enemy.py
import math
from src.shooting_character import ShootingCharacter
from src.bullet import BulletTargetTypes
from src.config_manager import ConfigManager
from src.constants import Constants
from src.simple_controls import PlayerNumber

class Enemy(ShootingCharacter):
    _common_bullet = None
    
    def __init__(self, sprite_sheet, color, can_become_invisible, score_points):
        super().__init__(sprite_sheet)
        
        self._threshold_speeds = [0] * 5
        self._threshold_speeds[0] = ConfigManager.get_config(Constants.ENEMY_SPEED_1, Constants.DEFAULT_ENEMY_SPEED_1)
        self._threshold_speeds[1] = ConfigManager.get_config(Constants.ENEMY_SPEED_2, Constants.DEFAULT_ENEMY_SPEED_2)
        self._threshold_speeds[2] = ConfigManager.get_config(Constants.ENEMY_SPEED_3, Constants.DEFAULT_ENEMY_SPEED_3)
        self._threshold_speeds[3] = ConfigManager.get_config(Constants.ENEMY_SPEED_4, Constants.DEFAULT_ENEMY_SPEED_4)
        self._threshold_speeds[4] = ConfigManager.get_config(Constants.ENEMY_SPEED_5, Constants.DEFAULT_ENEMY_SPEED_5)
        
        self._can_become_invisible = can_become_invisible
        self.visible = not can_become_invisible
        self._visibility_timer = 0
        self.INVISIBILITY_TIMER = 2.0
        
        self.set_speed(self._threshold_speeds[0])
        self.set_animation_speed(self._threshold_speeds[0])
        self.set_color(color)
        
        self._preferred_horizontal_direction = 0
        self._score_points = score_points
        self.can_fire = True
    
    @property
    def preferred_horizontal_direction(self):
        return self._preferred_horizontal_direction
    
    @property
    def score_points(self):
        return self._score_points
    
    @property
    def visible(self):
        return super().visible
    
    @visible.setter
    def visible(self, value):
        if value:
            self._visibility_timer = 0
        super(Enemy, self.__class__).visible.fset(self, value)
    
    def update(self, delta_time):
        if self._can_become_invisible and self.visible:
            self._visibility_timer += delta_time
            if self._visibility_timer >= self.INVISIBILITY_TIMER:
                self.visible = False
    
    def can_fire_at_player(self, player):
        # Ateş özelliği kontrolü
        if not hasattr(self, 'can_fire') or not self.can_fire:
            return False
        
        # Ana kontroller
        if player is None or player.in_cage or not player.visible or Enemy.is_any_enemy_firing():
            return False
        
        # İlk iki seviyede 3. seviyede Burworlar ateş edemez kontrolü
        # Bu kontrolü sprite sheet üzerinden yapmak daha güvenli olacaktır
        # Ancak enemy nesnesinin hangi tip düşman olduğunu belirleyecek bir özellik eklemeliyiz
        # Direkt erişilebilir bir özellik olmadığı için, bu kontrolü main.py'de yapmak daha iyi
        
        # Eğer düşman doğru yöne bakıyorsa ve oyuncu ile aynı hizadaysa
        if self.move_direction.x != 0 and self.pixel_position_y == player.pixel_position_y:
            if math.copysign(1, self.move_direction.x) == math.copysign(1, player.pixel_position_x - self.pixel_position_x):
                return True
        elif self.move_direction.y != 0 and self.pixel_position_x == player.pixel_position_x:
            if math.copysign(1, self.move_direction.y) == math.copysign(1, player.pixel_position_y - self.pixel_position_y):
                return True
        
        return False
    
    def fire(self):
        Enemy._common_bullet = super().fire(
            BulletTargetTypes.PLAYER, 
            ConfigManager.get_config(Constants.ENEMY_BULLET_SPEED, Constants.DEFAULT_ENEMY_BULLET_SPEED)
        )
        return Enemy._common_bullet
    
    @staticmethod
    def is_enemy_bullet(bullet):
        return bullet is not None and bullet is Enemy._common_bullet
    
    @staticmethod
    def kill_enemy_bullet():
        Enemy._common_bullet = None
    
    def kill_bullet(self):
        super().kill_bullet()
        Enemy.kill_enemy_bullet()
    
    @staticmethod
    def is_any_enemy_firing():
        return Enemy._common_bullet is not None
    
    def set_threshold_speed(self, threshold, modificator):
        new_speed = self._threshold_speeds[threshold] * modificator
        self.set_speed(new_speed)
        self.set_animation_speed(new_speed)
    
    def update_visible(self, player):
        if player is not None and not self.visible:
            if self.pixel_position_y == player.pixel_position_y or self.pixel_position_x == player.pixel_position_x:
                self.visible = True
    

    # enemy.py'deki move metodunu güncelle:

    def move(self, delta_time):
        # 🔥 YUMUŞAK HAREKET: Daha büyük adımlar at - süzülmeyi azalt
        if hasattr(self, '_speed') and self._speed > 0:
            # Hareket adımını büyüt - daha az süzülme efekti
            base_step = 0.4  # 0.2 yerine 0.4 (daha büyük adımlar)
            speed_multiplier = self._speed / 40.0  # 40 referans hız
            movement_step = base_step * speed_multiplier
            
            # Güvenlik sınırları - ama daha büyük değerler
            movement_step = max(0.25, min(movement_step, 0.8))  # Min 0.25, Max 0.8
        else:
            movement_step = 0.4  # Varsayılan büyük adım
        
        # Hareket et
        self._position += self._move_direction * movement_step