# src/player.py
from src.shooting_character import ShootingCharacter
from src.bullet import BulletTargetTypes
from src.config_manager import ConfigManager
from src.constants import Constants
from src.simple_controls import PlayerNumber

class Player(ShootingCharacter):
    def __init__(self, sprite_sheet, max_lives, shoot_sound, cage_x, cage_y, player_number):
        super().__init__(sprite_sheet, shoot_sound)
        self._max_lives = max_lives
        self._remaining_lives = max_lives
        self._current_score = 0
        self.in_cage = False
        self.time_in_cage = 0
        self.time_to_cage = 0
        
        self._cage_position_x = cage_x
        self._cage_position_y = cage_y
        self._player_number = player_number
        
        self._extra_life_score = ConfigManager.get_config(
            Constants.EXTRA_LIFE_SCORE, 
            Constants.DEFAULT_EXTRA_LIFE_SCORE
        )
    
    @property
    def remaining_lives(self):
        return self._remaining_lives
    
    @property
    def current_score(self):
        return self._current_score
    
    @property
    def cage_position_x(self):
        return self._cage_position_x
    
    @property
    def cage_position_y(self):
        return self._cage_position_y
    
    @property
    def player_number(self):
        return self._player_number
    
    def reset_lives(self):
        self._remaining_lives = self._max_lives
    
    def lose_life(self):
        self._remaining_lives -= 1
    
    def gain_life(self):
        self._remaining_lives += 1
    
    def has_lives_left(self):
        return self._remaining_lives >= 0
    
    def fire(self):
        return super().fire(BulletTargetTypes.ANY, ConfigManager.get_config(
            Constants.PLAYER_BULLET_SPEED, 
            Constants.DEFAULT_PLAYER_BULLET_SPEED
        ))
    
    # Player sınıfındaki increase_score metodunun güncellenmiş versiyonu:
    def increase_score(self, score):
        """Oyuncu puanını artırır ve ekranı günceller"""
        # Önceki skoru sakla
        old_score = self._current_score
        
        # Extra can kontrolü
        if self._current_score < self._extra_life_score and self._current_score + score >= self._extra_life_score:
            self.gain_life()
        
        # Skoru artır
        self._current_score += score
    
    def reset_score(self):
        self._current_score = 0