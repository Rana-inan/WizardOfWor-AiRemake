# src/game_manager.py
import threading
import queue
import time
import pygame

class GameThreadManager:
    """Oyunun farklı bileşenlerini ayrı thread'lerde yönetir - Sadece Audio + Physics"""
    
    def __init__(self):
        # Audio Manager
        self.audio_manager = None
        
        # Physics thread için kuyruk ve lock
        self.physics_queue = queue.Queue(maxsize=10)  # Sınırlı boyut
        self.physics_thread = None
        self.physics_lock = threading.Lock()
        self.physics_results = None
        
        # Durum değişkeni
        self.running = False
    
    def start_threads(self):
        """Audio Manager + Physics Thread'i başlat"""
        self.running = True
        
        # Audio Manager'ı başlat
        from src.audio_manager import AudioManager
        self.audio_manager = AudioManager()
        self.audio_manager.start()
        print("✅ Audio Manager başlatıldı")
        
        # Physics thread'i başlat
        self.physics_thread = threading.Thread(
            target=self._physics_loop,
            daemon=True,
            name="PhysicsThread"
        )
        self.physics_thread.start()
        print("✅ Physics Thread başlatıldı")
        
        print("🚀 GameThreadManager hazır (Audio + Physics)")
    
    def stop_threads(self):
        """Tüm thread'leri güvenli şekilde durdur"""
        print("🛑 Thread'ler durduruluyor...")
        self.running = False
        
        # Audio Manager'ı durdur
        if self.audio_manager:
            self.audio_manager.stop()
            print("  ✅ Audio Manager durduruldu")
        
        # Physics thread'i durdur
        if self.physics_thread and self.physics_thread.is_alive():
            # Shutdown sinyali gönder
            try:
                self.physics_queue.put({'type': 'shutdown'}, timeout=0.1)
            except queue.Full:
                pass
            
            # Thread'in bitmesini bekle
            self.physics_thread.join(timeout=1.0)
            
            if self.physics_thread.is_alive():
                print("  ⚠️ Physics thread zorla sonlandırıldı")
            else:
                print("  ✅ Physics thread durduruldu")
        
        print("🏁 Tüm thread'ler durduruldu")
    
    def _physics_loop(self):
        """Physics işlemlerini yürüten thread döngüsü"""
        print("🧮 Physics thread başladı")
        
        while self.running:
            try:
                # Physics kuyruğundan veri al
                physics_data = self.physics_queue.get(timeout=0.1)
                
                # Shutdown kontrolü
                if physics_data.get('type') == 'shutdown':
                    print("🛑 Physics thread shutdown sinyali aldı")
                    break
                
                # Physics işlemlerini gerçekleştir
                result = self._process_physics_data(physics_data)
                
                # Sonucu main thread'e ilet
                if result:
                    with self.physics_lock:
                        self.physics_results = result
                
                self.physics_queue.task_done()
                
            except queue.Empty:
                # Timeout - normal durum, devam et
                continue
            except Exception as e:
                print(f"❌ Physics thread hatası: {e}")
                time.sleep(0.01)
        
        print("🧮 Physics thread sonlandı")
    
    def _process_physics_data(self, physics_data):
        """Physics hesaplamalarını yap"""
        try:
            data_type = physics_data.get('type')
            
            if data_type == 'collision_check':
                return self._calculate_collisions(physics_data)
            elif data_type == 'bullet_trajectory':
                return self._calculate_bullet_paths(physics_data)
            elif data_type == 'movement_prediction':
                return self._predict_movements(physics_data)
            else:
                print(f"⚠️ Bilinmeyen physics data type: {data_type}")
                return None
                
        except Exception as e:
            print(f"❌ Physics processing hatası: {e}")
            return None
    
    def _calculate_collisions(self, data):
        """Çarpışma hesaplamaları - optimize edilmiş"""
        collisions = []
        bullets = data.get('bullets', [])
        players = data.get('players', [])
        enemies = data.get('enemies', [])
        level = data.get('level')
        
        for bullet in bullets:
            if not bullet:
                continue
                
            bullet_x = bullet.pixel_position_x
            bullet_y = bullet.pixel_position_y
            
            # Duvar çarpışması
            if level and level.has_pixel(bullet_x, bullet_y):
                collisions.append({
                    'type': 'bullet_wall',
                    'bullet': bullet,
                    'position': (bullet_x, bullet_y)
                })
                continue  # Duvar vurulunca diğer kontrolleri atla
            
            # Oyuncu çarpışması
            for player in players:
                if player and player.visible and bullet.origin != player:
                    if bullet.test_hit(player):
                        collisions.append({
                            'type': 'bullet_player',
                            'bullet': bullet,
                            'player': player
                        })
                        break  # Bir oyuncu vurulduysa diğerlerini kontrol etme
            
            # Düşman çarpışması
            for enemy in enemies:
                if enemy and enemy.visible and bullet.origin != enemy:
                    if bullet.test_hit(enemy):
                        collisions.append({
                            'type': 'bullet_enemy',
                            'bullet': bullet,
                            'enemy': enemy
                        })
                        break  # Bir düşman vurulduysa diğerlerini kontrol etme
        
        return {
            'collisions': collisions, 
            'timestamp': time.time(),
            'processed_bullets': len(bullets)
        }
    
    def _calculate_bullet_paths(self, data):
        """Mermi yollarını hesapla - gelecek için"""
        bullet_paths = []
        bullets = data.get('bullets', [])
        
        for bullet in bullets:
            if bullet and hasattr(bullet, '_velocity'):
                # 5 frame ileri hesapla (60fps için)
                future_positions = []
                for i in range(1, 6):
                    dt = 0.016 * i  # 60fps = ~16ms per frame
                    future_x = bullet.pixel_position_x + bullet._velocity.x * dt
                    future_y = bullet.pixel_position_y + bullet._velocity.y * dt
                    future_positions.append((future_x, future_y))
                
                bullet_paths.append({
                    'bullet_id': id(bullet),  # Object referansı yerine ID
                    'current_pos': (bullet.pixel_position_x, bullet.pixel_position_y),
                    'future_positions': future_positions
                })
        
        return {
            'bullet_paths': bullet_paths, 
            'timestamp': time.time()
        }
    
    def _predict_movements(self, data):
        """Hareket tahminleri - AI için"""
        predictions = []
        enemies = data.get('enemies', [])
        
        for enemy in enemies:
            if enemy and enemy.visible and hasattr(enemy, 'move_direction'):
                # Düşmanın muhtemel bir sonraki konumu
                move_dir = enemy.move_direction
                speed = getattr(enemy, '_speed', 20)  # Varsayılan hız
                
                # 1 saniye sonraki tahmini konum
                next_x = enemy.pixel_position_x + move_dir.x * speed
                next_y = enemy.pixel_position_y + move_dir.y * speed
                
                predictions.append({
                    'enemy_id': id(enemy),
                    'current_pos': (enemy.pixel_position_x, enemy.pixel_position_y),
                    'predicted_position': (next_x, next_y),
                    'confidence': 0.8,
                    'enemy_type': enemy.__class__.__name__
                })
        
        return {
            'movement_predictions': predictions, 
            'timestamp': time.time()
        }
    
    def get_thread_status(self):
        """Thread durumlarını döndür - debug için"""
        return {
            'audio_manager_alive': self.audio_manager.running if self.audio_manager else False,
            'physics_thread_alive': self.physics_thread.is_alive() if self.physics_thread else False,
            'physics_queue_size': self.physics_queue.qsize(),
            'running': self.running,
            'active_threads': threading.active_count()
        }
    
    def clear_physics_queue(self):
        """Physics queue'sunu temizle - emergency için"""
        cleared_count = 0
        try:
            while not self.physics_queue.empty():
                self.physics_queue.get(block=False)
                cleared_count += 1
        except queue.Empty:
            pass
        
        if cleared_count > 0:
            print(f"🧹 Physics queue temizlendi: {cleared_count} item kaldırıldı")
        
        return cleared_count