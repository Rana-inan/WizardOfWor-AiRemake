# src/camera_shake.py
import math
import pygame

class CameraShake:
    Enabled = False
    _is_screen_shaking = False
    _shake_time = 0
    _shake_intensity = 0
    _shake_amplitude = 0
    _shake_duration = 0
    _shake_offset = pygame.Vector2(0, 0)
    
    @staticmethod
    def shake(amplitude, intensity, duration):
        if not CameraShake._is_screen_shaking and CameraShake.Enabled:
            CameraShake._shake_time = 0
            CameraShake._is_screen_shaking = True
            CameraShake._shake_intensity = intensity
            CameraShake._shake_duration = duration
            CameraShake._shake_amplitude = amplitude
    
    @staticmethod
    def update(delta_time):
        if CameraShake._is_screen_shaking and CameraShake.Enabled:
            CameraShake._shake_time += delta_time
            intensity_time = CameraShake._shake_time * CameraShake._shake_intensity
            if CameraShake._shake_duration < 0 or CameraShake._shake_time < CameraShake._shake_duration:
                CameraShake._shake_offset = pygame.Vector2(
                    math.sin(intensity_time), 
                    math.cos(intensity_time)
                ) * CameraShake._shake_amplitude
            else:
                CameraShake._is_screen_shaking = False
                CameraShake._shake_offset = pygame.Vector2(0, 0)
    
    @staticmethod
    def stop_shake():
        CameraShake._is_screen_shaking = False
        CameraShake._shake_offset = pygame.Vector2(0, 0)
    
    @staticmethod
    def get_offset():
        return CameraShake._shake_offset