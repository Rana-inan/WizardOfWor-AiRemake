# src/ai_controller.py
import pygame
from queue import Queue
from src.simple_controls import PlayerNumber
from src.ai_player import AIPlayer1, AIPlayer2, AIAction

class AIController:
    """
    Yapay zeka oyuncusunu yöneten ve kontrol tuşlarını simüle eden sınıf.
    Oyun ana döngüsü ile yapay zeka arasındaki arayüz görevi görür.
    """
    
    def __init__(self):
        """Yapay zeka kontrolcüsünü başlat"""
        # AI oyuncular için kuyruklar
        self.p1_game_state_queue = Queue()
        self.p1_action_queue = Queue()
        self.p2_game_state_queue = Queue()
        self.p2_action_queue = Queue()
        
        # AI oyuncu thread'leri
        self.ai_player1 = None
        self.ai_player2 = None
        
        # Simüle edilmiş tuş durumları
        self.key_states = {
            # Player 1 tuşları
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_SPACE: False,
            
            # Player 2 tuşları
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_f: False,
        }
    
   
    # src/ai_controller.py
    def start_ai_player(self, player_number, ai_type="AI1"):
        """Belirtilen oyuncu numarası için yapay zeka başlat"""
        if player_number == PlayerNumber.PLAYER1:
            if self.ai_player1 is None:
                if ai_type == "AI1":
                    self.ai_player1 = AIPlayer1(
                        PlayerNumber.PLAYER1, 
                        self.p1_game_state_queue, 
                        self.p1_action_queue
                    )
                else:  # ai_type == "AI2"
                    self.ai_player1 = AIPlayer2(
                        PlayerNumber.PLAYER1, 
                        self.p1_game_state_queue, 
                        self.p1_action_queue
                    )
                self.ai_player1.start()
                
        elif player_number == PlayerNumber.PLAYER2:
            if self.ai_player2 is None:
                if ai_type == "AI1":
                    self.ai_player2 = AIPlayer1(
                        PlayerNumber.PLAYER2, 
                        self.p2_game_state_queue, 
                        self.p2_action_queue
                    )
                else:  # ai_type == "AI2"
                    self.ai_player2 = AIPlayer2(
                        PlayerNumber.PLAYER2, 
                        self.p2_game_state_queue, 
                        self.p2_action_queue
                    )
                self.ai_player2.start()
        
    # Diğer metodlar aynı kalır
    def stop_ai_player(self, player_number):
        """Belirtilen oyuncu numarası için yapay zekayı durdur"""
        if player_number == PlayerNumber.PLAYER1 and self.ai_player1:
            self.ai_player1.stop()
            self.ai_player1 = None
        elif player_number == PlayerNumber.PLAYER2 and self.ai_player2:
            self.ai_player2.stop()
            self.ai_player2 = None
    
    def stop_all(self):
        """Tüm yapay zeka oyuncularını durdur"""
        if self.ai_player1:
            self.ai_player1.stop()
            self.ai_player1 = None
        
        if self.ai_player2:
            self.ai_player2.stop()
            self.ai_player2 = None
    
    def update_game_state(self, player_number, game_state):
        """
        Oyun durumunu yapay zekaya ilet
        
        Args:
            player_number: PlayerNumber enum değeri
            game_state: Oyun durumu sözlüğü
        """
        if player_number == PlayerNumber.PLAYER1 and self.ai_player1:
            self.p1_game_state_queue.put(game_state)
        elif player_number == PlayerNumber.PLAYER2 and self.ai_player2:
            self.p2_game_state_queue.put(game_state)
    
    def update_key_states(self):
        """
        Yapay zeka eylemlerini simüle edilmiş tuş basışlarına dönüştür.
        Bu fonksiyon her frame'de çağrılmalıdır.
        """
        # Tüm tuşları sıfırla
        for key in self.key_states:
            self.key_states[key] = False
        
        # Player 1 eylemlerini al ve uygula
        if self.ai_player1:
            try:
                while not self.p1_action_queue.empty():
                    action = self.p1_action_queue.get(block=False)
                    self._apply_action(action, PlayerNumber.PLAYER1)
            except:
                pass
        
        # Player 2 eylemlerini al ve uygula
        if self.ai_player2:
            try:
                while not self.p2_action_queue.empty():
                    action = self.p2_action_queue.get(block=False)
                    self._apply_action(action, PlayerNumber.PLAYER2)
            except:
                pass
    
    def _apply_action(self, action, player_number):
        """
        AI eylemini tuş basışlarına dönüştür
        
        Args:
            action: AIAction enum değeri
            player_number: PlayerNumber enum değeri
        """
        if player_number == PlayerNumber.PLAYER1:
            # Player 1 tuşlarını ayarla
            if action == AIAction.MOVE_UP:
                self.key_states[pygame.K_UP] = True
            elif action == AIAction.MOVE_DOWN:
                self.key_states[pygame.K_DOWN] = True
            elif action == AIAction.MOVE_LEFT:
                self.key_states[pygame.K_LEFT] = True
            elif action == AIAction.MOVE_RIGHT:
                self.key_states[pygame.K_RIGHT] = True
            elif action == AIAction.SHOOT:
                self.key_states[pygame.K_SPACE] = True
        
        elif player_number == PlayerNumber.PLAYER2:
            # Player 2 tuşlarını ayarla
            if action == AIAction.MOVE_UP:
                self.key_states[pygame.K_w] = True
            elif action == AIAction.MOVE_DOWN:
                self.key_states[pygame.K_s] = True
            elif action == AIAction.MOVE_LEFT:
                self.key_states[pygame.K_a] = True
            elif action == AIAction.MOVE_RIGHT:
                self.key_states[pygame.K_d] = True
            elif action == AIAction.SHOOT:
                self.key_states[pygame.K_f] = True
    
    def get_key_state(self, key):
        """
        Belirli bir tuşun durumunu döndür
        
        Args:
            key: pygame.K_* sabitlerinden biri
            
        Returns:
            bool: Tuş basılı mı?
        """
        return self.key_states.get(key, False)