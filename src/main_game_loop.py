# src/main_game_loop.py
import pygame
import time
import threading
from enum import Enum

class GameState(Enum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    VICTORY = 4

class MainGameLoop:
    """Ana oyun döngüsü koordinatörü - Thread orchestration"""
    
    def __init__(self, game_instance):
        self.game = game_instance  # WizardOfWor referansı
        
        # Thread coordination
        self.running = True
        self.game_state = GameState.MENU
        self.target_fps = 60
        self.clock = pygame.time.Clock()
        
        # Performance tracking
        self.frame_count = 0
        self.last_performance_check = time.time()
        self.frame_times = []
        
        # Thread synchronization
        self.main_lock = threading.Lock()
        self.frame_ready = threading.Event()
        
        # Main thread duties
        self.duties = {
            'event_handling': True,
            'thread_coordination': True, 
            'render_orchestration': True,
            'game_state_sync': True,
            'performance_monitoring': True
        }
        
        print("🎮 MainGameLoop initialized")
    
    def run(self):
        """Ana thread döngüsü - koordinasyon odaklı"""
        print("🚀 Main game loop başlatıldı")
        
        try:
            while self.running:
                frame_start_time = time.time()
                
                # 1. EVENT HANDLING (Main thread'in ana sorumluluğu)
                self._handle_events()
                
                # 2. THREAD COORDINATION 
                self._coordinate_threads()
                
                # 3. GAME STATE SYNCHRONIZATION
                self._sync_game_state()
                
                # 4. RENDER ORCHESTRATION (Pygame render main thread'de olmalı)
                self._orchestrate_render()
                
                # 5. PERFORMANCE MONITORING
                self._monitor_performance(frame_start_time)
                
                # 6. FRAME RATE CONTROL
                self.clock.tick(self.target_fps)
                
        except KeyboardInterrupt:
            print("🛑 Ana döngü kullanıcı tarafından durduruldu")
        except Exception as e:
            print(f"❌ Ana döngü hatası: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._shutdown()
    
    def _handle_events(self):
        """Event handling - Main thread'in özel sorumluluğu"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
                
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event.key)
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse(event.pos, event.button)
    
    def _handle_keydown(self, key):
        """Klavye basma olayları"""
        # Debug tuşları
        if key == pygame.K_F10:
            self._debug_all_threads()
        elif key == pygame.K_F11:
            self._toggle_performance_display()
        elif key == pygame.K_ESCAPE:
            if self.game_state == GameState.PLAYING:
                self.game_state = GameState.PAUSED
            elif self.game_state == GameState.PAUSED:
                self.game_state = GameState.PLAYING
        
        # Oyun state'ine göre event'i ilet
        if self.game_state == GameState.MENU:
            self._handle_menu_key(key)
        elif self.game_state == GameState.PLAYING:
            self._handle_game_key(key)
    
    def _handle_keyup(self, key):
        """Klavye bırakma olayları"""
        # SimpleControls'a bildir
        if hasattr(self.game, 'simple_controls'):
            # Key release logic
            pass
    
    def _handle_mouse(self, pos, button):
        """Fare olayları"""
        if self.game_state == GameState.MENU:
            self.game.handle_mouse_event(pos, button)
    
    def _coordinate_threads(self):
        """Thread'ler arası koordinasyon"""
        if not self.game.thread_manager:
            return
        
        # Thread sağlık kontrolü
        thread_status = self.game.thread_manager.get_thread_status()
        
        # Ölü thread varsa uyar
        if not thread_status.get('physics_thread_alive', False):
            print("⚠️ Physics thread öldü!")
        
        if not thread_status.get('audio_manager_alive', False):
            print("⚠️ Audio thread öldü!")
        
        # AI thread'leri kontrol et
        if hasattr(self.game, 'ai_controller'):
            self._coordinate_ai_threads()
        
        # Physics sonuçlarını işle
        self._process_physics_results()
        
        # Physics'e yeni data gönder (gerekirse)
        self._send_physics_data()
    
    def _coordinate_ai_threads(self):
        """AI thread koordinasyonu"""
        if self.game_state != GameState.PLAYING:
            return
            
        # AI'lara oyun durumunu gönder
        self.game.update_ai_game_state()
        
        # AI eylemlerini al
        if self.game.ai_controller:
            self.game.ai_controller.update_key_states()
    
    def _process_physics_results(self):
        """Physics thread sonuçlarını işle"""
        if not self.game.thread_manager:
            return
            
        with self.game.thread_manager.physics_lock:
            if self.game.thread_manager.physics_results:
                self.game._apply_physics_results(
                    self.game.thread_manager.physics_results
                )
                self.game.thread_manager.physics_results = None
    
    def _send_physics_data(self):
        """Physics'e veri gönder"""
        if self.game_state == GameState.PLAYING and self.game.bullets:
            self.game._send_physics_data()
    
    def _sync_game_state(self):
        """Oyun durumunu senkronize et"""
        # Game state geçişlerini kontrol et
        if self.game.game_over and self.game_state != GameState.GAME_OVER:
            self.game_state = GameState.GAME_OVER
            print("🎮 Game state: GAME_OVER")
            
        elif self.game.show_victory_screen and self.game_state != GameState.VICTORY:
            self.game_state = GameState.VICTORY 
            print("🎮 Game state: VICTORY")
            
        elif self.game.game_started and self.game_state != GameState.PLAYING:
            self.game_state = GameState.PLAYING
            print("🎮 Game state: PLAYING")
            
        elif self.game.player_selection_mode and self.game_state != GameState.MENU:
            self.game_state = GameState.MENU
            print("🎮 Game state: MENU")
        
        # State'e göre update'leri çağır
        delta_time = self.clock.get_time() / 1000.0
        
        if self.game_state == GameState.PLAYING:
            self._update_playing_state(delta_time)
        elif self.game_state == GameState.MENU:
            self._update_menu_state(delta_time)
        elif self.game_state == GameState.GAME_OVER:
            self._update_game_over_state(delta_time)
        elif self.game_state == GameState.VICTORY:
            self._update_victory_state(delta_time)
    
    def _update_playing_state(self, delta_time):
        """Oyun state'ini güncelle"""
        # Sadece main thread'in yapması gereken işler
        self.game.update(delta_time)
    
    def _update_menu_state(self, delta_time):
        """Menü state'ini güncelle"""
        if self.game.player_selection_mode:
            self.game.handle_player_selection(delta_time)
        elif self.game.ai_selection_mode:
            self.game.handle_ai_selection(delta_time)
        elif self.game.human_ai_selection_mode:
            self.game.handle_human_ai_selection(delta_time)
    
    def _update_game_over_state(self, delta_time):
        """Game over state'ini güncelle"""
        self.game.game_over_timer -= delta_time
        if self.game.game_over_timer <= 0:
            self.game.game_over = False
            self.game_state = GameState.MENU
    
    def _update_victory_state(self, delta_time):
        """Victory state'ini güncelle"""
        self.game.victory_timer -= delta_time
        if self.game.victory_timer <= 0:
            self.game.show_victory_screen = False
            self.game_state = GameState.MENU
    
    def _orchestrate_render(self):
        """Render orchestration - Pygame render main thread'de"""
        try:
            # Render'ı organize et ama thread'lere dağıtma
            self.game.draw()
            
        except Exception as e:
            print(f"❌ Render orchestration hatası: {e}")
    
    def _monitor_performance(self, frame_start_time):
        """Performance monitoring"""
        frame_time = time.time() - frame_start_time
        self.frame_times.append(frame_time)
        self.frame_count += 1
        
        # Son 60 frame'i tut
        if len(self.frame_times) > 60:
            self.frame_times.pop(0)
        
        # 5 saniyede bir rapor et
        current_time = time.time() 
        if current_time - self.last_performance_check > 5.0:
            self._report_performance()
            self.last_performance_check = current_time
    
    def _report_performance(self):
        """Performance raporu"""
        if not self.frame_times:
            return
            
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        max_frame_time = max(self.frame_times)
        min_frame_time = min(self.frame_times)
        
        print(f"📊 MAIN THREAD PERFORMANCE:")
        print(f"  FPS: {fps:.1f}")
        print(f"  Avg Frame Time: {avg_frame_time*1000:.2f}ms")
        print(f"  Min/Max: {min_frame_time*1000:.2f}ms / {max_frame_time*1000:.2f}ms")
        
        # Thread durumları
        if self.game.thread_manager:
            status = self.game.thread_manager.get_thread_status()
            print(f"  Active Threads: {status['active_threads']}")
            print(f"  Physics Queue: {status['physics_queue_size']}")
    
    def _debug_all_threads(self):
        """Tüm thread'leri debug et"""
        print("\n" + "="*60)
        print("🔍 ALL THREADS DEBUG")
        print("="*60)
        
        # Main thread
        print(f"🎮 Main Thread:")
        print(f"  State: {self.game_state}")
        print(f"  FPS: {self.clock.get_fps():.1f}")
        print(f"  Frame Count: {self.frame_count}")
        
        # Diğer thread'ler
        if self.game.thread_manager:
            status = self.game.thread_manager.get_thread_status()
            print(f"\n🧵 Thread Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
        
        # AI threads
        if hasattr(self.game, 'ai_controller'):
            print(f"\n🤖 AI Threads:")
            print(f"  AI1 Active: {self.game.ai_controller.ai_player1 is not None}")
            print(f"  AI2 Active: {self.game.ai_controller.ai_player2 is not None}")
        
        print("="*60 + "\n")
    
    def _toggle_performance_display(self):
        """Performance display'i aç/kapat"""
        self.game.performance_logging_enabled = not self.game.performance_logging_enabled
        status = "AÇIK" if self.game.performance_logging_enabled else "KAPALI"
        print(f"📊 Performance display: {status}")
    
    def _handle_menu_key(self, key):
        """Menü tuşları"""
        # Menü navigation'ını game instance'a ilet
        pass
    
    def _handle_game_key(self, key):
        """Oyun tuşları"""
        # Game input'ları SimpleControls'a iletilecek
        pass
    
    def _shutdown(self):
        """Main thread shutdown"""
        print("🛑 Main thread kapatılıyor...")
        
        # Diğer thread'leri durdur
        if self.game.thread_manager:
            self.game.thread_manager.stop_threads()
        
        # AI controller'ı durdur
        if hasattr(self.game, 'ai_controller'):
            self.game.ai_controller.stop_all()
        
        print("🏁 Main thread kapatıldı")