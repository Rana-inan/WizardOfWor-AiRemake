# src/shooting_character.py
import pygame
from src.character import Character
from src.bullet import Bullet, BulletTargetTypes

class ShootingCharacter(Character):
    def __init__(self, sprite_sheet, shoot_sound=None):
        super().__init__(sprite_sheet)
        self._bullet = None
        self._shoot_sound = shoot_sound
        self._current_shoot_sound = None
    
    @property
    def bullet(self):
        return self._bullet
    
    def fire(self, target_type, speed):
        self._bullet = Bullet(self, target_type, speed)
        
        if self._shoot_sound:
            self._shoot_sound.play()
        
        return self._bullet
    
    def kill_bullet(self):
        self._bullet = None
        if self._current_shoot_sound:
            self._current_shoot_sound.stop()
    
    def is_owned_bullet(self, bullet):
        return bullet is not None and bullet is self._bullet
    
    def is_firing(self):
        return self._bullet is not None