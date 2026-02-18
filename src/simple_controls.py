# src/simple_controls.py
import pygame
from enum import Enum

class PlayerNumber(Enum):
    PLAYER1 = 0
    PLAYER2 = 1

class PlayerType(Enum):
    HUMAN = 0
    AI = 1

class SimpleControls:
    _keys = {
        pygame.K_LEFT: False,
        pygame.K_RIGHT: False,
        pygame.K_UP: False,
        pygame.K_DOWN: False,
        pygame.K_SPACE: False,
        pygame.K_RETURN: False,
        pygame.K_w: False,
        pygame.K_a: False,
        pygame.K_s: False,
        pygame.K_d: False,
        pygame.K_g: False,
        pygame.K_j: False,
        pygame.K_y: False,
        pygame.K_h: False,
        pygame.K_f: False,
        pygame.K_F1: False,
        pygame.K_F2: False,
        pygame.K_F3: False,
        pygame.K_F4: False,
        pygame.K_F5: False,
        pygame.K_F6: False, 
        pygame.K_ESCAPE: False,
    }

    # Yeni eklenecek değişken
    _key_down_processed = {
        pygame.K_LEFT: False,
        pygame.K_RIGHT: False,
        pygame.K_UP: False,
        pygame.K_DOWN: False,
        pygame.K_SPACE: False,
        pygame.K_RETURN: False,
        pygame.K_w: False,
        pygame.K_a: False,
        pygame.K_s: False,
        pygame.K_d: False,
        pygame.K_g: False,
        pygame.K_j: False,
        pygame.K_y: False, 
        pygame.K_h: False,
        pygame.K_f: False,
        pygame.K_F1: False,
        pygame.K_F2: False,
        pygame.K_F3: False,
        pygame.K_F4: False,
        pygame.K_F5: False,
        pygame.K_F6: False, 
        pygame.K_ESCAPE: False,
    }
    
    # AI kontrolcüsüne referans
    _ai_controller = None
    
    # Oyuncu tiplerini tut
    _player_types = {
        PlayerNumber.PLAYER1: PlayerType.HUMAN,
        PlayerNumber.PLAYER2: PlayerType.HUMAN
    }

    _previous_keys = {}
    _key_just_pressed = {}
    
    @staticmethod
    def set_ai_controller(ai_controller):
        """AI Kontrolcüsünü ayarla"""
        SimpleControls._ai_controller = ai_controller
    
    @staticmethod
    def set_player_type(player_number, player_type):
        """Oyuncu tipini ayarla"""
        SimpleControls._player_types[player_number] = player_type
    
    @staticmethod
    def get_player_type(player_number):
        """Oyuncu tipini döndür"""
        return SimpleControls._player_types.get(player_number, PlayerType.HUMAN)
    
    @staticmethod
    def get_states():
        # Gerçek klavye durumlarını al
        keys = pygame.key.get_pressed()

        # Her bir tuş için güncelleme
        for key in SimpleControls._keys:
            # Tuş şu anda basılı mı?
            current_key_state = keys[key]
            
            # Tuşun eski durumunu kaydet
            SimpleControls._keys[key] = current_key_state
            
            # Tuş bırakıldıysa, işlenme durumunu sıfırla
            if not current_key_state:
                SimpleControls._key_down_processed[key] = False
        
        # Oyuncu 1 kontrolleri
        SimpleControls._keys[pygame.K_LEFT] = keys[pygame.K_LEFT]
        SimpleControls._keys[pygame.K_RIGHT] = keys[pygame.K_RIGHT]
        SimpleControls._keys[pygame.K_UP] = keys[pygame.K_UP]
        SimpleControls._keys[pygame.K_DOWN] = keys[pygame.K_DOWN]
        SimpleControls._keys[pygame.K_SPACE] = keys[pygame.K_SPACE]
        SimpleControls._keys[pygame.K_RETURN] = keys[pygame.K_RETURN]
        
        # Oyuncu 2 WASD kontrolleri
        SimpleControls._keys[pygame.K_w] = keys[pygame.K_w]
        SimpleControls._keys[pygame.K_a] = keys[pygame.K_a]
        SimpleControls._keys[pygame.K_s] = keys[pygame.K_s]
        SimpleControls._keys[pygame.K_d] = keys[pygame.K_d]
        
        # Oyuncu 2 orjinal kontrolleri
        SimpleControls._keys[pygame.K_g] = keys[pygame.K_g]
        SimpleControls._keys[pygame.K_j] = keys[pygame.K_j]
        SimpleControls._keys[pygame.K_y] = keys[pygame.K_y]
        SimpleControls._keys[pygame.K_h] = keys[pygame.K_h]
        SimpleControls._keys[pygame.K_f] = keys[pygame.K_f]
        
        # Sistem kontrolleri
        SimpleControls._keys[pygame.K_F1] = keys[pygame.K_F1]
        SimpleControls._keys[pygame.K_F2] = keys[pygame.K_F2]
        SimpleControls._keys[pygame.K_F3] = keys[pygame.K_F3]
        SimpleControls._keys[pygame.K_F4] = keys[pygame.K_F4]
        SimpleControls._keys[pygame.K_F5] = keys[pygame.K_F5]
        SimpleControls._keys[pygame.K_F6] = keys[pygame.K_F6]  # F6 tuşunu ekledik
        SimpleControls._keys[pygame.K_ESCAPE] = keys[pygame.K_ESCAPE]

        # "Yeni basılmış" tuşları belirle
        for key in SimpleControls._keys:
            SimpleControls._key_just_pressed[key] = (
                SimpleControls._keys[key] and not SimpleControls._previous_keys.get(key, False)
            )

        
        # AI kontrolcüsü varsa, simüle edilmiş tuşları ekle
        if SimpleControls._ai_controller:
            SimpleControls._ai_controller.update_key_states()
            
            # AI tuş durumlarını entegre et
            for key in SimpleControls._ai_controller.key_states:
                # AI kontrolleri insan kontrollerini geçersiz kılar
                # ama sadece ilgili oyuncu AI ise
                if key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_SPACE] and \
                   SimpleControls._player_types[PlayerNumber.PLAYER1] == PlayerType.AI:
                    SimpleControls._keys[key] |= SimpleControls._ai_controller.key_states[key]
                
                elif key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f] and \
                     SimpleControls._player_types[PlayerNumber.PLAYER2] == PlayerType.AI:
                    SimpleControls._keys[key] |= SimpleControls._ai_controller.key_states[key]
    
    @staticmethod
    def is_any_move_key_down(player_number):
        return (SimpleControls.is_left_down(player_number) or
                SimpleControls.is_right_down(player_number) or
                SimpleControls.is_up_down(player_number) or
                SimpleControls.is_down_down(player_number))
    
    @staticmethod
    def is_left_down(player_number):
        if player_number == PlayerNumber.PLAYER1 and SimpleControls._keys[pygame.K_LEFT]:
            return True
        elif player_number == PlayerNumber.PLAYER2 and (SimpleControls._keys[pygame.K_g] or SimpleControls._keys[pygame.K_a]):
            return True
        return False
    
     # Yeni metot: Tuşa basıldı ve henüz işlenmedi mi?
    @staticmethod
    def is_key_newly_pressed(key):
        # Tuş basılı mı ve henüz işlenmemiş mi?
        if SimpleControls._keys.get(key, False) and not SimpleControls._key_down_processed.get(key, False):
            # İşlendi olarak işaretle
            SimpleControls._key_down_processed[key] = True
            return True
        return False
    
    # Yeni hareket kontrolleri - sadece işlenmemiş basışları kontrol eder
    @staticmethod
    def is_left_newly_pressed(player_number):
        if player_number == PlayerNumber.PLAYER1:
            return SimpleControls.is_key_newly_pressed(pygame.K_LEFT)
        elif player_number == PlayerNumber.PLAYER2:
            return (SimpleControls.is_key_newly_pressed(pygame.K_g) or 
                    SimpleControls.is_key_newly_pressed(pygame.K_a))
        return False
    
    @staticmethod
    def is_right_newly_pressed(player_number):
        if player_number == PlayerNumber.PLAYER1:
            return SimpleControls.is_key_newly_pressed(pygame.K_RIGHT)
        elif player_number == PlayerNumber.PLAYER2:
            return (SimpleControls.is_key_newly_pressed(pygame.K_j) or 
                    SimpleControls.is_key_newly_pressed(pygame.K_d))
        return False
    
    @staticmethod
    def is_up_newly_pressed(player_number):
        if player_number == PlayerNumber.PLAYER1:
            return SimpleControls.is_key_newly_pressed(pygame.K_UP)
        elif player_number == PlayerNumber.PLAYER2:
            return (SimpleControls.is_key_newly_pressed(pygame.K_y) or 
                    SimpleControls.is_key_newly_pressed(pygame.K_w))
        return False
    
    @staticmethod
    def is_down_newly_pressed(player_number):
        if player_number == PlayerNumber.PLAYER1:
            return SimpleControls.is_key_newly_pressed(pygame.K_DOWN)
        elif player_number == PlayerNumber.PLAYER2:
            return (SimpleControls.is_key_newly_pressed(pygame.K_h) or 
                    SimpleControls.is_key_newly_pressed(pygame.K_s))
        return False
    
    @staticmethod
    def is_a_newly_pressed(player_number):
        if player_number == PlayerNumber.PLAYER1:
            return SimpleControls.is_key_newly_pressed(pygame.K_SPACE)
        elif player_number == PlayerNumber.PLAYER2:
            return SimpleControls.is_key_newly_pressed(pygame.K_f)
        return False
    
    @staticmethod
    def is_right_down(player_number):
        if player_number == PlayerNumber.PLAYER1 and SimpleControls._keys[pygame.K_RIGHT]:
            return True
        elif player_number == PlayerNumber.PLAYER2 and (SimpleControls._keys[pygame.K_j] or SimpleControls._keys[pygame.K_d]):
            return True
        return False
 
    @staticmethod
    def is_left_just_pressed(player_number):
         if player_number == PlayerNumber.PLAYER1:
                return SimpleControls._key_just_pressed.get(pygame.K_LEFT, False)
         elif player_number == PlayerNumber.PLAYER2:
                return (SimpleControls._key_just_pressed.get(pygame.K_g, False) or 
                    SimpleControls._key_just_pressed.get(pygame.K_a, False))
         return False
    
    @staticmethod
    def is_up_down(player_number):
        if player_number == PlayerNumber.PLAYER1 and SimpleControls._keys[pygame.K_UP]:
            return True
        elif player_number == PlayerNumber.PLAYER2 and (SimpleControls._keys[pygame.K_y] or SimpleControls._keys[pygame.K_w]):
            return True
        return False
    
    @staticmethod
    def is_down_down(player_number):
        if player_number == PlayerNumber.PLAYER1 and SimpleControls._keys[pygame.K_DOWN]:
            return True
        elif player_number == PlayerNumber.PLAYER2 and (SimpleControls._keys[pygame.K_h] or SimpleControls._keys[pygame.K_s]):
            return True
        return False
    
    @staticmethod
    def is_a_down(player_number):
        if player_number == PlayerNumber.PLAYER1 and SimpleControls._keys[pygame.K_SPACE]:
            return True
        elif player_number == PlayerNumber.PLAYER2 and SimpleControls._keys[pygame.K_f]:
            return True
        return False
    
    @staticmethod
    def is_b_down(player_number):
        if player_number == PlayerNumber.PLAYER1 and SimpleControls._keys[pygame.K_RETURN]:
            return True
        elif player_number == PlayerNumber.PLAYER2 and SimpleControls._keys[pygame.K_d]:
            return True
        return False
    
    @staticmethod
    def is_start_down():
        return SimpleControls._keys[pygame.K_F1]
    
    @staticmethod
    def is_select_down():
        return SimpleControls._keys[pygame.K_F2]
    
    @staticmethod
    def is_p1_ai_toggle_down():
        """F3 tuşu Player 1'i AI/insan arasında değiştirir"""
        return SimpleControls._keys[pygame.K_F3]
    
    @staticmethod
    def is_p2_ai_toggle_down():
        """F4 tuşu Player 2'yi AI/insan arasında değiştirir"""
        return SimpleControls._keys[pygame.K_F4]
    
    @staticmethod
    def is_both_ai_toggle_down():
        """F5 tuşu her iki oyuncuyu da AI yapar"""
        return SimpleControls._keys[pygame.K_F5]
    
    @staticmethod
    def is_escape_down():
        return SimpleControls._keys[pygame.K_ESCAPE]
    
    @staticmethod
    def is_cheat_kill_down():
        """F6 tuşu düşmanları öldüren hile"""
        return SimpleControls._keys[pygame.K_F6]