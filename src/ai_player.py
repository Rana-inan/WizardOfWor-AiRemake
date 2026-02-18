# src/ai_player.py
import pygame
import math
import threading
import time
import random
from queue import Queue, Empty
from enum import Enum
from src.simple_controls import PlayerNumber
from src.pathfinding_greedy import find_path_greedy
from src.pathfinding_greedy import manhattan_distance
from src.pathfinding_astar import find_path_astar


class AIAction(Enum):
    """AI tarafından gerçekleştirilebilecek eylemler"""
    MOVE_UP = 0
    MOVE_DOWN = 1
    MOVE_LEFT = 2
    MOVE_RIGHT = 3
    SHOOT = 4
    NO_ACTION = 5

class AIPlayerBase(threading.Thread):
    """Yapay zeka oyuncusu için temel sınıf"""
    
    def __init__(self, player_number, game_state_queue, action_queue):
        """
        Args:
            player_number: PlayerNumber enumu (PLAYER1 veya PLAYER2)
            game_state_queue: Oyun durumunun iletildiği kuyruk
            action_queue: AI kararlarının iletildiği kuyruk
        """
        super().__init__()
        self.player_number = player_number
        self.game_state_queue = game_state_queue
        self.action_queue = action_queue
        self.running = True
        self.daemon = True  # Ana thread sonlandığında bu thread de sonlanır
        
        # Oyun durumu değişkenleri
        self.player_position = None
        self.player_direction = None
        self.player_in_cage = False
        self.enemies = []
        self.bullets = []
        self.level = None
        self.current_action = AIAction.NO_ACTION
        
        # İşbirliği modu değişkenleri
        self.is_cooperative = False
        self.other_player_position = None
        self.other_player_direction = None
        self.other_player_in_cage = False
        
        # AI ayarları
        self.reaction_time = 0.05  
        self.decision_interval = 0.05  
        self.last_decision_time = 0
        
        # Kalıcı hafıza
        self.memory = {
            'visited_positions': set(),      # Ziyaret edilen pozisyonlar
            'enemy_sightings': {},           # Son görülen düşman pozisyonları
            'path_history': [],              # Son 10 hareket
            'last_firing_time': 0,           # Son ateş zamanı
            'current_goal': None,            # Şu anki hedef (x, y)
            'last_action': AIAction.NO_ACTION, # Son yapılan eylem
            'stuck_counter': 0,              # Aynı yerde takılma sayacı
            'last_position': None,           # Son konum
            'grid_walls': set(),             # Bilinen duvarların konumları
            'grid_size': (13, 8),            # Varsayılan grid boyutu
            'cell_size': (12, 10),           # Hücre boyutu (px)
            'tunnels': [(1, 3), (11, 3)]     # Tünel pozisyonları
        }
        
        # Eylem ağırlıkları - farklı stratejileri ayarlamak için
        self.weights = {
            'shoot_enemy': 8.0,     # Düşman vurma
            'hunt': 6.0,            # Düşman avlama
            'cooperation': 5.0,     # Takım çalışması
            'exploration': 4.0,     # Keşif
        }

        self._original_weights = self.weights.copy()

    def run(self):
        """Thread ana döngüsü - Tepki süresini iyileştir"""
        while self.running:
            # Oyun durumunu al
            try:
                game_state = self.game_state_queue.get(block=False)
                self.update_game_state(game_state)
                self.update_memory()
                
                # Yeni durum geldikten hemen sonra karar ver (bekleme olmadan)
                action = self.decide_action()
                self.action_queue.put(action)
                self.last_decision_time = time.time()
            except Empty:
                # Eğer yeni durum yoksa, karar verme zamanı geldi mi kontrol et
                current_time = time.time()
                if current_time - self.last_decision_time > self.decision_interval:
                    action = self.decide_action()
                    
                    # Takılma tespiti
                    if self.memory['last_position'] == self.player_position:
                        self.memory['stuck_counter'] += 1
                    else:
                        self.memory['stuck_counter'] = 0
                    
                    # Takılmayı çöz
                    if self.memory['stuck_counter'] > 5:
                        action = self.get_unstuck_action()
                        self.memory['stuck_counter'] = 0
                    
                    self.memory['last_action'] = action
                    self.memory['last_position'] = self.player_position
                    
                    self.action_queue.put(action)
                    self.last_decision_time = current_time
            
            # CPU kullanımını azaltmak için çok kısa bir uyku
            time.sleep(0.01)  # 10ms -> 5ms
    
    def update_game_state(self, game_state):
        """Oyun durumunu güncelle"""
        self.player_position = game_state.get('player_position')
        self.player_direction = game_state.get('player_direction')
        self.player_in_cage = game_state.get('player_in_cage')
        self.enemies = game_state.get('enemies', [])
        self.bullets = game_state.get('bullets', [])
        self.level = game_state.get('level')  # Artık bu bir Level sınıfı örneği

        # İşbirliği modu bilgilerini güncelle
        self.is_cooperative = game_state.get('is_cooperative', False)
        self.other_player_position = game_state.get('other_player_position')
        self.other_player_direction = game_state.get('other_player_direction')
        self.other_player_in_cage = game_state.get('other_player_in_cage', False)

        # Grid bilgisini güncelle
        if self.level:
            width = self.level.pixel_width
            height = self.level.pixel_height
            self.memory['grid_size'] = (
                width // self.memory['cell_size'][0],
                height // self.memory['cell_size'][1]
            )

        # AI'nın ilk kez grid üzerinde sabit bir pozisyona yerleştiği anı kaydet
        if not self.memory.get("starting_grid_pos") and not self.player_in_cage and self.player_position:
            grid_x = int(self.player_position[0] // self.memory['cell_size'][0])
            grid_y = int(self.player_position[1] // self.memory['cell_size'][1])
            self.memory["starting_grid_pos"] = (grid_x, grid_y)
            print(f"[AI-{self.player_number}] Başlangıç konumu: ({grid_x}, {grid_y})")

    def update_memory(self):
        """Hafızayı güncelle - oyun durumundan öğrenme"""
        if not self.player_position:
            return
            
        # Ziyaret edilen pozisyonu kaydet
        pos_x, pos_y = self.player_position
        grid_x = int(pos_x // self.memory['cell_size'][0])
        grid_y = int(pos_y // self.memory['cell_size'][1])
        self.memory['visited_positions'].add((grid_x, grid_y))
        
        # Yol geçmişi güncelle
        self.memory['path_history'].append((grid_x, grid_y))
        if len(self.memory['path_history']) > 10:
            self.memory['path_history'].pop(0)
        
        # Düşman görüşlerini güncelle
        current_time = time.time()
        for enemy in self.enemies:
            if enemy.get('visible', True):
                enemy_pos = enemy.get('position')
                if enemy_pos:
                    enemy_x = int(enemy_pos[0] // self.memory['cell_size'][0])
                    enemy_y = int(enemy_pos[1] // self.memory['cell_size'][1])
                    self.memory['enemy_sightings'][(enemy_x, enemy_y)] = current_time
        
        # Duvar öğrenme - hareket kısıtlamalarından öğren
        if self.memory['last_action'] != AIAction.NO_ACTION:
            last_grid_x, last_grid_y = self.memory['path_history'][-2] if len(self.memory['path_history']) > 1 else (grid_x, grid_y)
            
            # Bir yöne hareket etmeye çalıştık ama aynı yerdeyiz, muhtemelen duvar var
            if last_grid_x == grid_x and last_grid_y == grid_y:
                if self.memory['last_action'] == AIAction.MOVE_UP:
                    self.memory['grid_walls'].add((grid_x, grid_y-1, 'horizontal'))
                elif self.memory['last_action'] == AIAction.MOVE_DOWN:
                    self.memory['grid_walls'].add((grid_x, grid_y, 'horizontal'))
                elif self.memory['last_action'] == AIAction.MOVE_LEFT:
                    self.memory['grid_walls'].add((grid_x-1, grid_y, 'vertical'))
                elif self.memory['last_action'] == AIAction.MOVE_RIGHT:
                    self.memory['grid_walls'].add((grid_x, grid_y, 'vertical'))
        
        # Takılma tespiti
        if hasattr(self.memory, 'last_position'):
            if self.memory['last_position'] == self.player_position:
                self.memory['stuck_counter'] = self.memory.get('stuck_counter', 0) + 1
                
                # 10 adımdan fazla takılırsa, rastgele yöne hareket etmeyi dene
                if self.memory['stuck_counter'] > 10:
                    self.memory['stuck_counter'] = 0
                    self.memory['need_random_move'] = True
            else:
                self.memory['stuck_counter'] = 0
                self.memory['need_random_move'] = False
        
        self.memory['last_position'] = self.player_position

    def detect_enemies_around(self):
        """Tüm yönlerde düşmanları tespit et - güvenlik mesafesi ile iyileştirildi"""
        if not self.player_position or not self.enemies:
            return None
            
        player_x, player_y = self.player_position
        
        # Tehdit altındaki düşmanları ve yönlerini bul
        threats = []
        
        for enemy in self.enemies:
            if not enemy.get('visible', True):
                continue
                
            enemy_pos = enemy.get('position', (0, 0))
            if not enemy_pos:
                continue
                
            # Düşmanla mesafe
            dx = enemy_pos[0] - player_x
            dy = enemy_pos[1] - player_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Yatay veya dikey hizada mı?
            is_horizontal_aligned = abs(dy) < 6
            is_vertical_aligned = abs(dx) < 6
            
            # Yakın düşmanlar daha tehlikeli
            threat_level = 100 / (distance + 1)
            
            # Düşman yönü
            direction = None
            
            if is_horizontal_aligned:
                direction = AIAction.MOVE_RIGHT if dx > 0 else AIAction.MOVE_LEFT
                threats.append((enemy, direction, threat_level, distance))
            elif is_vertical_aligned:
                direction = AIAction.MOVE_DOWN if dy > 0 else AIAction.MOVE_UP
                threats.append((enemy, direction, threat_level, distance))
        
        # Tehditleri tehdit seviyesine göre sırala (en tehlikelisi önce)
        threats.sort(key=lambda x: x[2], reverse=True)
        
        return threats[0] if threats else None
  
    def decide_action(self):
        """
        Karar mekanizması: Güvenlik kontrolleri iyileştirilmiş
        """
        # Kafesteyse, çıkmaya çalış
        if self.player_in_cage:
            return AIAction.MOVE_UP
        
        # Grid özelliklerini kontrol et
        if self.is_on_grid_cell():
            actions = {}  # Eylem -> Puan eşleşmesi
            
            # En yakın düşmanı kontrol et - ACİL DURUM KONTROLÜ
            min_distance = float('inf')
            
            for enemy in self.enemies:
                if enemy.get('visible', True):
                    enemy_pos = enemy.get('position', (0, 0))
                    if not enemy_pos:
                        continue
                        
                    player_x, player_y = self.player_position
                    distance = math.sqrt((enemy_pos[0] - player_x)**2 + (enemy_pos[1] - player_y)**2)
                    
                    if distance < min_distance:
                        min_distance = distance
            
            
            # Hareket etmediği süreyi kontrol et
            current_time = time.time()
            if not hasattr(self.memory, 'last_position_change_time'):
                self.memory['last_position_change_time'] = current_time
            
            # Aynı konumda 2 saniyeden uzun süre duruyorsa, keşif yapma isteğini artır
            if self.memory.get('last_position') == self.player_position and current_time - self.memory.get('last_position_change_time', 0) > 2.0:
                self.weights['exploration'] *= 2.0  # Keşif ağırlığını ikiye katla
            else:
                if self.memory.get('last_position') != self.player_position:
                    self.memory['last_position_change_time'] = current_time
                    # Ağırlıkları normale döndür
                    self.weights['exploration'] = self._original_weights.get('exploration', 4.0)
            
            # Rastgele ateş etme şansı - Azaltıldı: %10 olasılık
            if random.random() < 0.1 and time.time() - self.memory.get('last_firing_time', 0) > 0.8:
                self.memory['last_firing_time'] = time.time()
                actions[AIAction.SHOOT] = self.weights['shoot_enemy']
            
            # 360 derece düşman tehdit tespiti - EN YÜKSEK ÖNCELİK
            nearest_threat = self.detect_enemies_around()
            if nearest_threat:
                enemy, direction, threat_level, distance = nearest_threat

                # Düşmana doğru bakıyorsak ve yakınsa, ateş et
                dx, dy = self.player_direction if self.player_direction else (0, 0)

                # Düşmana doğru bakıyorsak ve uygun mesafedeyse ateş et
                if (direction == AIAction.MOVE_RIGHT and dx > 0) or \
                (direction == AIAction.MOVE_LEFT and dx < 0) or \
                (direction == AIAction.MOVE_DOWN and dy > 0) or \
                (direction == AIAction.MOVE_UP and dy < 0):
                    if 10 < distance < 60:  # Güvenli ateş mesafesi
                        actions[AIAction.SHOOT] = self.weights['shoot_enemy'] * 1.8
                        self.memory['last_firing_time'] = time.time()

                # Yeterli mesafe varsa düşmana dön
                elif distance > 10:
                    actions[direction] = self.weights['hunt'] * 1.2

            
            
            # Ateş etme stratejisi - daha dikkatli, sadece yakın düşmanlara
            shoot_action = self.find_shooting_opportunity()
            if shoot_action != AIAction.NO_ACTION:
                if shoot_action == AIAction.SHOOT:
                    actions[shoot_action] = self.weights['shoot_enemy']
                else:
                    # Dönüş eylemi için her yönde düşman olup olmadığını kontrol et
                    direction_safe = self.is_direction_safe(shoot_action)
                    if direction_safe:
                        actions[shoot_action] = self.weights['shoot_enemy'] * 0.8
            
            # Düşman avlama stratejisi - güvenlik kontrolüyle
            hunt_action = self.hunt_closest_enemy()
            if hunt_action != AIAction.NO_ACTION:
                # Avlanma eylemi için her yönde düşman olup olmadığını kontrol et
                if self.is_direction_safe(hunt_action):
                    actions[hunt_action] = self.weights['hunt']
            
            # İşbirliği stratejisi
            if self.is_cooperative and self.other_player_position:
                team_action = self.coordinate_with_teammate()
                if team_action != AIAction.NO_ACTION and self.is_direction_safe(team_action):
                    actions[team_action] = self.weights['cooperation']
            
            # Keşif stratejisi - her zaman en az bir güvenli seçenek olmalı
            explore_action = self.smart_explore()
            if explore_action != AIAction.NO_ACTION:
                actions[explore_action] = self.weights['exploration']
            
            # En yüksek puanlı eylemi seç
            if actions:
                best_action = max(actions.items(), key=lambda x: x[1] + random.uniform(0, 1))
                return best_action[0]
        
        # Grid dışı ise şu anki yönde devam et
        return self.continue_current_direction()
        
    
    def is_direction_safe(self, direction):
        """Belirtilen yönde düşman olup olmadığını kontrol eder"""
        if not self.player_position:
            return True
        
        player_x, player_y = self.player_position
        
        # Yöne göre yeni pozisyon hesapla
        new_x, new_y = player_x, player_y
        if direction == AIAction.MOVE_RIGHT:
            new_x += self.memory['cell_size'][0]
        elif direction == AIAction.MOVE_LEFT:
            new_x -= self.memory['cell_size'][0]
        elif direction == AIAction.MOVE_DOWN:
            new_y += self.memory['cell_size'][1]
        elif direction == AIAction.MOVE_UP:
            new_y -= self.memory['cell_size'][1]
        
        # Bu yöndeki hücrede düşman var mı kontrol et
        for enemy in self.enemies:
            if not enemy.get('visible', True):
                continue
                
            enemy_pos = enemy.get('position', (0, 0))
            if not enemy_pos:
                continue
                
            # Düşmanla olan mesafe
            distance = math.sqrt((enemy_pos[0] - new_x)**2 + (enemy_pos[1] - new_y)**2)
            
            # 15 piksel içinde düşman varsa bu yön güvenli değil
            if distance < 15:
                return False
        
        return True
    
    def is_on_grid_cell(self):
        """Oyuncu grid hücresinde mi kontrol et"""
        if not self.player_position:
            return False
            
        x, y = self.player_position
        return (x % self.memory['cell_size'][0] == 0 and 
                y % self.memory['cell_size'][1] == 0)
    
    def continue_current_direction(self):
        """Şu anki hareket yönünde devam et"""
        if not self.player_direction:
            return AIAction.NO_ACTION
            
        dx, dy = self.player_direction
        
        if dx > 0:
            return AIAction.MOVE_RIGHT
        elif dx < 0:
            return AIAction.MOVE_LEFT
        elif dy > 0:
            return AIAction.MOVE_DOWN
        elif dy < 0:
            return AIAction.MOVE_UP
        
        return AIAction.NO_ACTION
    
    def get_unstuck_action(self):
        """Takılma durumunda kurtulmak için farklı bir yön dene"""
        possible_actions = [AIAction.MOVE_UP, AIAction.MOVE_DOWN, 
                           AIAction.MOVE_LEFT, AIAction.MOVE_RIGHT]
        
        # Son eylem varsa, bunun tersini öncelikle dene
        if self.memory['last_action'] == AIAction.MOVE_UP:
            return AIAction.MOVE_DOWN
        elif self.memory['last_action'] == AIAction.MOVE_DOWN:
            return AIAction.MOVE_UP
        elif self.memory['last_action'] == AIAction.MOVE_LEFT:
            return AIAction.MOVE_RIGHT
        elif self.memory['last_action'] == AIAction.MOVE_RIGHT:
            return AIAction.MOVE_LEFT
        
        # Yoksa rastgele bir yön seç
        return random.choice(possible_actions)
    
    def is_bullet_threat(self, bullet):
        """Mermi bir tehdit mi? - İyileştirilmiş"""
        if not self.player_position:
            return False
            
        # Merminin pozisyonu ve hızı
        bullet_pos = bullet.get('position', (0, 0))
        bullet_vel = bullet.get('velocity', (0, 0))
        
        if not bullet_pos or not bullet_vel:
            return False
            
        # Oyuncu pozisyonu
        player_x, player_y = self.player_position
        
        # Merminin tahmini ilerleme yolu
        future_pos_x = bullet_pos[0] + bullet_vel[0] * 0.5  # 0.5 saniye sonrası
        future_pos_y = bullet_pos[1] + bullet_vel[1] * 0.5
        
        # Yatay tehdit - daha hassas kontrol
        if abs(bullet_pos[1] - player_y) < 12:  # Yaklaşık aynı yatay çizgide
            if ((bullet_vel[0] > 0 and bullet_pos[0] < player_x and future_pos_x >= player_x) or
                (bullet_vel[0] < 0 and bullet_pos[0] > player_x and future_pos_x <= player_x)):
                return True
        
        # Dikey tehdit - daha hassas kontrol
        if abs(bullet_pos[0] - player_x) < 12:  # Yaklaşık aynı dikey çizgide
            if ((bullet_vel[1] > 0 and bullet_pos[1] < player_y and future_pos_y >= player_y) or
                (bullet_vel[1] < 0 and bullet_pos[1] > player_y and future_pos_y <= player_y)):
                return True
        
        return False

    def get_evasion_action(self, threat):
        """Tehditten kaçınma eylemi - İyileştirilmiş"""
        if not self.player_position or not threat:
            return AIAction.NO_ACTION
            
        # Tehdit pozisyonu
        threat_pos = threat.get('position', (0, 0))
        if not threat_pos:
            return AIAction.NO_ACTION
            
        # Oyuncu pozisyonu
        player_x, player_y = self.player_position
        
        # X ve Y eksenlerindeki farklar
        dx = threat_pos[0] - player_x
        dy = threat_pos[1] - player_y
        
        # Tehdidin hareket yönünü al (eğer varsa)
        threat_dir_x, threat_dir_y = 0, 0
        if 'velocity' in threat:
            threat_dir_x = threat.get('velocity')[0]
            threat_dir_y = threat.get('velocity')[1]
        elif 'direction' in threat:
            threat_dir_x = threat.get('direction')[0]
            threat_dir_y = threat.get('direction')[1]
        
        # Harekete göre kaçınma
        if abs(threat_dir_x) > abs(threat_dir_y):
            # Tehdit yatay hareket ediyor, dikey kaç
            if dy > 0:
                return AIAction.MOVE_UP
            else:
                return AIAction.MOVE_DOWN
        elif abs(threat_dir_y) > abs(threat_dir_x):
            # Tehdit dikey hareket ediyor, yatay kaç
            if dx > 0:
                return AIAction.MOVE_LEFT
            else:
                return AIAction.MOVE_RIGHT
    
   
    
    def can_shoot_enemy(self, enemy):
        """Düşmanı vurabilir miyiz? - İyileştirilmiş"""
        if not self.player_position or not enemy:
            return False
            
        # Düşman pozisyonu
        enemy_pos = enemy.get('position', (0, 0))
        if not enemy_pos:
            return False
            
        # Oyuncu pozisyonu
        player_x, player_y = self.player_position
        
        # Aynı hizada mı?
        same_row = abs(enemy_pos[1] - player_y) < 6
        same_col = abs(enemy_pos[0] - player_x) < 6
        
        # Düşman görünür mü?
        if enemy.get('visible', True):
            # Doğru yöne bakıyor muyuz?
            if same_row:
                # Yatay hizada
                if enemy_pos[0] > player_x and self.player_direction[0] > 0:
                    return True  # Sağa bakıyoruz, düşman sağda
                elif enemy_pos[0] < player_x and self.player_direction[0] < 0:
                    return True  # Sola bakıyoruz, düşman solda
            
            if same_col:
                # Dikey hizada
                if enemy_pos[1] > player_y and self.player_direction[1] > 0:
                    return True  # Aşağı bakıyoruz, düşman aşağıda
                elif enemy_pos[1] < player_y and self.player_direction[1] < 0:
                    return True  # Yukarı bakıyoruz, düşman yukarıda
        
        return False
        
    def find_shooting_opportunity(self):
        """Vurulabilecek düşmanları arar - Görüş hattı kontrolü ile"""
        if not self.player_position:
            return AIAction.NO_ACTION

        current_time = time.time()
        if current_time - self.memory.get('last_firing_time', 0) < 0.4:
            return AIAction.NO_ACTION

        for enemy in self.enemies:
            if not enemy.get('visible', True):
                continue

            enemy_pos = enemy.get('position', (0, 0))
            if not enemy_pos:
                continue

            player_x, player_y = self.player_position

            is_horizontal_aligned = abs(enemy_pos[1] - player_y) < 8
            is_vertical_aligned = abs(enemy_pos[0] - player_x) < 8

            # 🔍 Görüş hattı kontrolü: Eğer hizalı ama görünür değilse geç
            if (is_horizontal_aligned or is_vertical_aligned) and not self.is_visible(enemy_pos):
                continue

            if is_horizontal_aligned:
                if enemy_pos[0] > player_x:  # Düşman sağda
                    if self.player_direction[0] <= 0:
                        self.memory['shoot_after_turn'] = True
                        return AIAction.MOVE_RIGHT
                    elif self.memory.pop('shoot_after_turn', False):
                        self.memory['last_firing_time'] = current_time
                        return AIAction.SHOOT
                    else:
                        if random.random() < 0.9:
                            self.memory['last_firing_time'] = current_time
                            return AIAction.SHOOT

                else:  # Düşman solda
                    if self.player_direction[0] >= 0:
                        self.memory['shoot_after_turn'] = True
                        return AIAction.MOVE_LEFT
                    elif self.memory.pop('shoot_after_turn', False):
                        self.memory['last_firing_time'] = current_time
                        return AIAction.SHOOT
                    else:
                        if random.random() < 0.9:
                            self.memory['last_firing_time'] = current_time
                            return AIAction.SHOOT

            elif is_vertical_aligned:
                if enemy_pos[1] > player_y:  # Düşman aşağıda
                    if self.player_direction[1] <= 0:
                        self.memory['shoot_after_turn'] = True
                        return AIAction.MOVE_DOWN
                    elif self.memory.pop('shoot_after_turn', False):
                        self.memory['last_firing_time'] = current_time
                        return AIAction.SHOOT
                    else:
                        if random.random() < 0.9:
                            self.memory['last_firing_time'] = current_time
                            return AIAction.SHOOT

                else:  # Düşman yukarıda
                    if self.player_direction[1] >= 0:
                        self.memory['shoot_after_turn'] = True
                        return AIAction.MOVE_UP
                    elif self.memory.pop('shoot_after_turn', False):
                        self.memory['last_firing_time'] = current_time
                        return AIAction.SHOOT
                    else:
                        if random.random() < 0.9:
                            self.memory['last_firing_time'] = current_time
                            return AIAction.SHOOT

        return AIAction.NO_ACTION


    def hunt_closest_enemy(self):
        """Skor / mesafe oranı en yüksek düşmanı seç ve git"""
        if not self.player_position or not self.enemies:
            return AIAction.NO_ACTION

        best_enemy = None
        best_value = -1
        best_enemy_pos = None

        for enemy in self.enemies:
            if enemy.get('visible', True):
                enemy_pos = enemy.get('position', (0, 0))
                score = enemy.get('score', 100)  # Default skor

                # Uzaklık (grid bazlı)
                cell_width, cell_height = self.memory['cell_size']
                player_x, player_y = self.player_position
                start = (int(player_x // cell_width), int(player_y // cell_height))
                goal = (int(enemy_pos[0] // cell_width), int(enemy_pos[1] // cell_height))

                distance = manhattan_distance(start, goal)
                if distance == 0:
                    continue

                value = score / distance  # Skor / mesafe oranı
                if value > best_value:
                    best_value = value
                    best_enemy = enemy
                    best_enemy_pos = enemy_pos

        if best_enemy:
            return self.navigate_to_position(best_enemy_pos)

        return AIAction.NO_ACTION    
    
    def navigate_to_position(self, target_pos):
        """A* ile hedefe yönel - güvenlik kontrolü ile"""
        if not self.player_position or not target_pos or not self.level:
            return AIAction.NO_ACTION

        player_x, player_y = self.player_position
        target_x, target_y = target_pos

        # Grid pozisyonlarına dönüştür
        cell_width, cell_height = self.memory['cell_size']
        start = (int(player_x // cell_width), int(player_y // cell_height))
        goal = (int(target_x // cell_width), int(target_y // cell_height))

        # Hedefle aynı hücredeyse, hareket gerekmez
        if start == goal:
            return AIAction.NO_ACTION

        # Hareket etmeden önce düşman kontrolü yap
        for enemy in self.enemies:
            if not enemy.get('visible', True):
                continue
                
            enemy_pos = enemy.get('position', (0, 0))
            if not enemy_pos:
                continue
                
            # Düşman mesafesi
            distance = math.sqrt((enemy_pos[0] - player_x)**2 + (enemy_pos[1] - player_y)**2)
            
        
        # Eğer zaten hedef aynıysa ve AI sabitse → tekrar hesaplama
        if (self.memory.get('current_goal') == goal and
            self.memory.get('last_start') == start and
            self.memory.get('cached_path') and
            self.memory['cached_path'][0] == start):
            path = self.memory['cached_path']
        else:
            path = find_path_astar(start, goal, self.level)
            self.memory['cached_path'] = path
            self.memory['current_goal'] = goal
            self.memory['last_start'] = start

        # Yol bulundu mu?
        if not path:
            # Yol yoksa, rastgele hareket et
            return random.choice([AIAction.MOVE_UP, AIAction.MOVE_DOWN, AIAction.MOVE_LEFT, AIAction.MOVE_RIGHT])
        
        # Yön bilgisini önceden hesapla
        next_cell = path[0]
        dx = next_cell[0] - start[0]
        dy = next_cell[1] - start[1]
        
        # Bir sonraki hücrede düşman var mı kontrol et
        next_cell_danger = False
        next_cell_pixel_x = next_cell[0] * cell_width
        next_cell_pixel_y = next_cell[1] * cell_height
        
        for enemy in self.enemies:
            if not enemy.get('visible', True):
                continue
                
            enemy_pos = enemy.get('position', (0, 0))
            if not enemy_pos:
                continue
                
            enemy_grid_x = int(enemy_pos[0] // cell_width)
            enemy_grid_y = int(enemy_pos[1] // cell_height)
            
            # Bir sonraki hücrede veya hemen yanında düşman varsa
            if abs(enemy_grid_x - next_cell[0]) <= 1 and abs(enemy_grid_y - next_cell[1]) <= 1:
                next_cell_danger = True
                break
        
        # Eğer bir sonraki hücre tehlikeliyse, başka bir yöne git
        if next_cell_danger:
            # Açık yönleri bul
            open_directions = []
            if not self.is_wall_at(start[0], start[1]-1) and (start[0], start[1]-1) != next_cell:
                open_directions.append(AIAction.MOVE_UP)
            if not self.is_wall_at(start[0], start[1]+1) and (start[0], start[1]+1) != next_cell:
                open_directions.append(AIAction.MOVE_DOWN)
            if not self.is_wall_at(start[0]-1, start[1]) and (start[0]-1, start[1]) != next_cell:
                open_directions.append(AIAction.MOVE_LEFT)
            if not self.is_wall_at(start[0]+1, start[1]) and (start[0]+1, start[1]) != next_cell:
                open_directions.append(AIAction.MOVE_RIGHT)
            
            if open_directions:
                return random.choice(open_directions)
        
        # Normal hareket yönü
        self.memory['next_facing_direction'] = (dx, dy)
        
        if dx == 1:
            return AIAction.MOVE_RIGHT
        elif dx == -1:
            return AIAction.MOVE_LEFT
        elif dy == 1:
            return AIAction.MOVE_DOWN
        elif dy == -1:
            return AIAction.MOVE_UP

        return AIAction.NO_ACTION

    def is_wall_at(self, grid_x, grid_y):
        """Belirtilen grid hücresinde duvar var mı?"""
        # Grid sınırları dışındaysa, duvar var kabul et
        if (grid_x < 0 or grid_y < 0 or 
            grid_x >= self.memory['grid_size'][0] or 
            grid_y >= self.memory['grid_size'][1]):
            return True
        
        # Bilinen duvarları kontrol et
        for wall_x, wall_y, wall_type in self.memory['grid_walls']:
            if wall_x == grid_x and wall_y == grid_y:
                return True
        
        return False
    
    def coordinate_with_teammate(self):
        """Diğer oyuncuyla koordine olma stratejisi - İyileştirilmiş"""
        if not self.player_position or not self.other_player_position:
            return AIAction.NO_ACTION
        
        # Diğer oyuncuya olan mesafe
        player_x, player_y = self.player_position
        teammate_x, teammate_y = self.other_player_position
        
        distance = math.sqrt((teammate_x - player_x)**2 + (teammate_y - player_y)**2)
        
        # Çok uzaktaysa yaklaş (>60px)
        if distance > 60:
            return self.navigate_to_position(self.other_player_position)
        
        # Optimal mesafedeyse (40-60px), ayrı bir bölgeyi araşt
        elif 40 <= distance <= 60:
            # Takım arkadaşı ile aynı yönde gitmeyi önle
            other_dx, other_dy = self.other_player_direction
            
            # Takım arkadaşının gittiği yönün tersini tercih et
            avoid_directions = []
            if other_dx > 0:
                avoid_directions.append(AIAction.MOVE_RIGHT)
            elif other_dx < 0:
                avoid_directions.append(AIAction.MOVE_LEFT)
            if other_dy > 0:
                avoid_directions.append(AIAction.MOVE_DOWN)
            elif other_dy < 0:
                avoid_directions.append(AIAction.MOVE_UP)
            
            # Tüm yönleri değerlendir
            all_directions = [AIAction.MOVE_UP, AIAction.MOVE_DOWN, AIAction.MOVE_LEFT, AIAction.MOVE_RIGHT]
            valid_directions = [d for d in all_directions if d not in avoid_directions]
            
            if valid_directions:
                return random.choice(valid_directions)
        
        # Çok yakınsa (< 40px), mesafe koy
        elif distance < 40:
            dx = teammate_x - player_x
            dy = teammate_y - player_y
            
            if abs(dx) > abs(dy):
                return AIAction.MOVE_LEFT if dx > 0 else AIAction.MOVE_RIGHT
            else:
                return AIAction.MOVE_UP if dy > 0 else AIAction.MOVE_DOWN
        
        return AIAction.NO_ACTION
    
    def smart_explore(self):
        """Daha akıllı keşif stratejisi - İyileştirilmiş"""
        if not self.player_position:
            return AIAction.NO_ACTION
        
        player_x, player_y = self.player_position
        grid_x = int(player_x // self.memory['cell_size'][0])
        grid_y = int(player_y // self.memory['cell_size'][1])
        
        # Uzun süre aynı yerde kaldıysa, daha rastgele hareket et
        if self.memory.get('stuck_counter', 0) > 2:
            # Daha uzak bir hedef seç
            far_targets = []
            for x in range(self.memory['grid_size'][0]):
                for y in range(self.memory['grid_size'][1]):
                    if abs(x - grid_x) > 3 or abs(y - grid_y) > 3:  # En az 3 hücre uzakta
                        if not self.is_wall_at(x, y):
                            far_targets.append((x, y))
            
            if far_targets:
                target = random.choice(far_targets)
                target_pos = (
                    target[0] * self.memory['cell_size'][0],
                    target[1] * self.memory['cell_size'][1]
                )
                return self.navigate_to_position(target_pos)
        
            return self.navigate_to_position(target_pos)
        
        # Mevcut bir hareket yönü varsa, daha düşük olasılıkla devam et
        if self.player_direction and random.random() < 0.5:  # %70'den %50'ye düşürdük
            return self.continue_current_direction()
        
        # Duvarları göz önünde bulundurarak açık yönleri değerlendir
        open_directions = []
        
        # Yukarı
        if not self.is_wall_at(grid_x, grid_y-1):
            open_directions.append(AIAction.MOVE_UP)
        
        # Aşağı
        if not self.is_wall_at(grid_x, grid_y+1):
            open_directions.append(AIAction.MOVE_DOWN)
        
        # Sol
        if not self.is_wall_at(grid_x-1, grid_y):
            open_directions.append(AIAction.MOVE_LEFT)
        
        # Sağ
        if not self.is_wall_at(grid_x+1, grid_y):
            open_directions.append(AIAction.MOVE_RIGHT)
        
        # Açık yollar varsa rastgele birini seç
        if open_directions:
            # Mevcut yönün tersine dönme ihtimalini azalt
            if self.memory['last_action'] == AIAction.MOVE_UP and AIAction.MOVE_DOWN in open_directions:
                open_directions.remove(AIAction.MOVE_DOWN)
            elif self.memory['last_action'] == AIAction.MOVE_DOWN and AIAction.MOVE_UP in open_directions:
                open_directions.remove(AIAction.MOVE_UP)
            elif self.memory['last_action'] == AIAction.MOVE_LEFT and AIAction.MOVE_RIGHT in open_directions:
                open_directions.remove(AIAction.MOVE_RIGHT)
            elif self.memory['last_action'] == AIAction.MOVE_RIGHT and AIAction.MOVE_LEFT in open_directions:
                open_directions.remove(AIAction.MOVE_LEFT)
            
            # Hiç yön kalmadıysa, tümünü geri ekle
            if not open_directions:
                open_directions = [AIAction.MOVE_UP, AIAction.MOVE_DOWN, AIAction.MOVE_LEFT, AIAction.MOVE_RIGHT]
            
            return random.choice(open_directions)
        
        # Tamamen sıkışmış durumda, rastgele bir yön dene
        return random.choice([AIAction.MOVE_UP, AIAction.MOVE_DOWN, AIAction.MOVE_LEFT, AIAction.MOVE_RIGHT])
     
    def is_visible(self, target_pos):
        """Hedef ile AI arasında duvar var mı kontrol eder (aynı satır/sütun için)"""
        if not self.level or not self.player_position:
            return False

        cell_w, cell_h = self.memory['cell_size']
        x1 = int(self.player_position[0] // cell_w)
        y1 = int(self.player_position[1] // cell_h)
        x2 = int(target_pos[0] // cell_w)
        y2 = int(target_pos[1] // cell_h)

        if x1 == x2:
            step = 1 if y2 > y1 else -1
            for y in range(y1 + step, y2, step):
                if not self.level.is_walkable(x1, y - step, x1, y):
                    return False
            return True

        elif y1 == y2:
            step = 1 if x2 > x1 else -1
            for x in range(x1 + step, x2, step):
                if not self.level.is_walkable(x - step, y1, x, y1):
                    return False
            return True

        return False

    def check_all_directions_and_fire(self):
            """Düşmanı sağ, sol, yukarı ve aşağıdan algıla ve tepki ver (duvar kontrolü ile)"""
            if not self.player_position:
                return AIAction.NO_ACTION

            max_view_distance = 8
            player_x, player_y = self.player_position
            cell_w, cell_h = self.memory['cell_size']

            for enemy in self.enemies:
                if not enemy.get("visible", True):
                    continue

                ex, ey = enemy.get("position", (0, 0))
                dx = ex - player_x
                dy = ey - player_y

                same_row = abs(dy) < (cell_h // 2)
                same_col = abs(dx) < (cell_w // 2)

                # --- SAĞ / SOL kontrolü ---
                if same_row and abs(dx) <= max_view_distance * cell_w:
                    if dx > 0:
                        if self.player_direction != (1, 0):
                            return AIAction.MOVE_RIGHT
                        else:
                            if self.is_visible((ex, ey)):
                                return AIAction.SHOOT
                    else:
                        if self.player_direction != (-1, 0):
                            return AIAction.MOVE_LEFT
                        else:
                            if self.is_visible((ex, ey)):
                                return AIAction.SHOOT

                # --- YUKARI / AŞAĞI kontrolü ---
                elif same_col and abs(dy) <= max_view_distance * cell_h:
                    if dy > 0:
                        if self.player_direction != (0, 1):
                            return AIAction.MOVE_DOWN
                        else:
                            if self.is_visible((ex, ey)):
                                return AIAction.SHOOT
                    else:
                        if self.player_direction != (0, -1):
                            return AIAction.MOVE_UP
                        else:
                            if self.is_visible((ex, ey)):
                                return AIAction.SHOOT

            return AIAction.NO_ACTION



    def attack_other_player(self):
        """Diğer oyuncuya saldırma stratejisi (competitive mod)"""
        if not self.player_position or not self.other_player_position or self.other_player_in_cage:
            return AIAction.NO_ACTION
        
        player_x, player_y = self.player_position
        other_x, other_y = self.other_player_position
        
        # Mesafeyi hesapla
        distance = math.sqrt((other_x - player_x)**2 + (other_y - player_y)**2)
        
        # Çok uzaksa (>60px), izleme yapma
        if distance > 60:
            return AIAction.NO_ACTION
        
        # Ateş edebilme kontrolü - çok hassas hizalama kontrolü
        if abs(other_y - player_y) < 5:  # Yatay hizada
            if other_x > player_x and self.player_direction[0] > 0:
                self.memory['last_firing_time'] = time.time()
                return AIAction.SHOOT
            elif other_x < player_x and self.player_direction[0] < 0:
                self.memory['last_firing_time'] = time.time()
                return AIAction.SHOOT
            else:
                # Doğru yöne dön
                return AIAction.MOVE_RIGHT if other_x > player_x else AIAction.MOVE_LEFT
        
        elif abs(other_x - player_x) < 5:  # Dikey hizada
            if other_y > player_y and self.player_direction[1] > 0:
                self.memory['last_firing_time'] = time.time()
                return AIAction.SHOOT
            elif other_y < player_y and self.player_direction[1] < 0:
                self.memory['last_firing_time'] = time.time()
                return AIAction.SHOOT
            else:
                # Doğru yöne dön
                return AIAction.MOVE_DOWN if other_y > player_y else AIAction.MOVE_UP
        
        # Hizalı değilse, diğer oyuncuya yaklaş
        return self.navigate_to_position(self.other_player_position)
  


    def stop(self):
        """Thread'i durdur"""
        self.running = False


class AIPlayer1(AIPlayerBase):
    """İlk oyuncu (P1) için özelleştirilmiş AI - Daha saldırgan, düşmanlara odaklı"""
    
    def __init__(self, player_number, game_state_queue, action_queue):
        super().__init__(player_number, game_state_queue, action_queue)
        # P1 için özel değişkenler
        self.strategy_timer = 0
        self.strategy_change_interval = 4.0  # 4 saniyede bir strateji değiştir
        self.current_strategy = 0  # 0: Saldırgan, 1: Karma
        
        # Ağırlıkları daha saldırgan yap
        self.weights.update({
            'shoot_enemy': 10.0,    # Düşman vurma - en yüksek öncelik
            'hunt': 10.0,            # Düşman avlama - çok önemli
            'cooperation': 7.0,     # Takım çalışması - daha az önemli
            'exploration': 0.5,     # Keşif - en az önemli
        })
        
        # P1 karakteri için daha sık ateş etme
        self.reaction_time = 0.0  # Daha hızlı tepki
        self.decision_interval = 0.0 # Daha hızlı karar
    
    def decide_action(self):
        # 1. Eğer görüş alanında düşman varsa → ateş et veya dön
        threat_action = self.check_all_directions_and_fire()
        if threat_action != AIAction.NO_ACTION:
            return threat_action

            # 2. Mermi tehdidi varsa kaç
        for bullet in self.bullets:
            if self.is_bullet_threat(bullet):
                evasion_action = self.get_evasion_action(bullet)
                if evasion_action != AIAction.NO_ACTION:
                    return evasion_action

        # 2. Strateji zaman kontrolü
        current_time = time.time()
        self.strategy_timer += current_time - self.last_decision_time if self.last_decision_time > 0 else 0

        # 3. Ana karar mantığı
        action = super().decide_action()


        return action

    

    # P1 için özelleştirilmiş, daha agresif düşman avlama
    def hunt_closest_enemy(self):
        """P1 için daha agresif düşman avlama"""
        if not self.player_position or not self.enemies:
            return AIAction.NO_ACTION
        
        # Standart avlanma mantığını kullan
        action = AIPlayerBase.hunt_closest_enemy(self)

        
        # Eğer bir düşmana doğru gidiyorsak, %25 şansla ateş et
        if action != AIAction.NO_ACTION and random.random() < 0.25:
            # Ateş etmek için yeterli süre geçtiyse
            if time.time() - self.memory.get('last_firing_time', 0) > 0.6:
                self.memory['last_firing_time'] = time.time()
                return AIAction.SHOOT
        
        return action


class AIPlayer2(AIPlayerBase):
    """
    AIPlayer2: Sabit strateji uygular.
    - Başlangıç pozisyonuna göre hedef seçer
    - A* ile hedefe gider
    - Hedefe ulaştığında durur
    - Sağ/soldan gelen düşmanları görürse yönelir ve ateş eder
    """

    def __init__(self, player_number, game_state_queue, action_queue):
        super().__init__(player_number, game_state_queue, action_queue)
        self.initialized = False
        self.my_target = None
        self.mode = "INIT"

    def update_game_state(self, game_state):
        super().update_game_state(game_state)

        if self.player_in_cage:
            self.memory["respawned"] = True
            self.memory["starting_grid_pos"] = None  # 🧠 Başlangıç pozisyonunu sıfırla
            self.memory["cached_path"] = None        # 🔁 Önceki path geçersiz
            self.memory["current_goal"] = None       # 🧭 Hedef de sıfırlansın

        if not self.player_in_cage and self.initialized and self.memory.get("respawned", False):
            print(f"[AI-{self.player_number}] Respawned → Resetting AI state.")
            self.initialized = False
            self.my_target = None
            self.mode = "INIT"
            self.memory["respawned"] = False

    def decide_action(self):
        # 1. Kafesteyse çık
        if self.player_in_cage:
            return AIAction.MOVE_UP

        # 2. Başlangıç konumuna göre hedef belirle (yalnızca bir kez)
        if not self.initialized and not self.player_in_cage:
            starting_pos = self.memory.get("starting_grid_pos")

            if not starting_pos:
                return AIAction.NO_ACTION

            grid_x, _ = starting_pos
            side = "left" if grid_x < self.level._width // 2 else "right"

            LEVEL_TARGETS = {
                "Level1":  { "left": (6, 2), "right": (6, 5) },
                "Level2":  { "left": (6, 5), "right": (6, 4) },
                "Level3":  { "left": (6, 2), "right": (5, 6) },
                "Level4":  { "left": (4, 1), "right": (6, 5) },
                "Level5":  { "left": (6, 3), "right": (4, 6) },
                "Level6":  { "left": (6, 2), "right": (5, 6) },
                "Level7":  { "left": (6, 2), "right": (6, 3) },
                "Level8":  { "left": (6, 4), "right": (8, 2) },
                "Level9":  { "left": (6, 2), "right": (10, 2) },
                "Level10": { "left": (6, 2), "right": (10, 2) },
            }

            level_name = getattr(self.level, "name", "Level1")
            target_set = LEVEL_TARGETS.get(level_name, LEVEL_TARGETS["Level1"])
            self.my_target = target_set[side]

            print(f"[AI-{self.player_number}] Hedef belirlendi: {self.my_target} ({level_name})")
            self.mode = "MOVE_TO_TARGET"
            self.initialized = True

        # 3. Hedefe giderken: düşman varsa ateş et, yoksa ilerle
        if self.mode == "MOVE_TO_TARGET":
            threat_action = self.check_all_directions_and_fire()
            if threat_action != AIAction.NO_ACTION:
                return threat_action

            action = self.navigate_to_position(self.level.get_cell_position(*self.my_target))

            if self.is_on_target_cell():
                self.mode = "GUARD"
                print(f"[AI-{self.player_number}] Hedefe ulaşıldı: {self.my_target}")

            return action

        # 4. Bekleme (koruma) modunda: yine düşmana ateş et
        if self.mode == "GUARD":
            return self.check_all_directions_and_fire()

        return AIAction.NO_ACTION

    def is_on_target_cell(self):
        if not self.player_position or not self.my_target:
            return False

        cell_w, cell_h = self.memory['cell_size']
        px, py = self.player_position
        grid_x = int(px // cell_w)
        grid_y = int(py // cell_h)

        return (grid_x, grid_y) == self.my_target


 

    def navigate_to_position(self, target_pixel_pos):
        if not self.player_position or not self.level or not self.my_target:
            return AIAction.NO_ACTION

        cell_w, cell_h = self.memory['cell_size']

        curr_grid = (
            int(self.player_position[0] // cell_w),
            int(self.player_position[1] // cell_h)
        )

        # 1. Eğer hedefe ulaşıldıysa, hiçbir şey yapma
        if curr_grid == self.my_target:
            return AIAction.NO_ACTION

        # 2. Eğer yol yoksa veya hedef değiştiyse yeniden hesapla
        if (not self.memory.get("cached_path") or 
            self.memory.get("current_goal") != self.my_target):
            path = find_path_astar(curr_grid, self.my_target, self.level)
            self.memory["cached_path"] = path
            self.memory["current_goal"] = self.my_target
            print(f"[A*] path from {curr_grid} to {self.my_target}: {path}")

        # 3. Hala yol yoksa bekle
        if not self.memory["cached_path"]:
            return AIAction.NO_ACTION

        # 4. Aynı hücrede takılmayı önle: Path üzerindeki geçerli ilk adımı bul
        while self.memory["cached_path"] and self.memory["cached_path"][0] == curr_grid:
            self.memory["cached_path"].pop(0)

        if not self.memory["cached_path"]:
            return AIAction.NO_ACTION

        # 5. Sadece 1 adım uzaklıktaki (komşu) hücreyi bul
        next_grid = None
        for step in self.memory["cached_path"]:
            dx = step[0] - curr_grid[0]
            dy = step[1] - curr_grid[1]
            if abs(dx) + abs(dy) == 1:
                next_grid = step
                break

        # 6. Geçerli adım yoksa path geçersiz → sıfırla
        if not next_grid:
            print(f"[AI-{self.player_number}] Path bozuk, sıfırlanıyor.")
            self.memory["cached_path"] = None
            return AIAction.NO_ACTION

        dx = next_grid[0] - curr_grid[0]
        dy = next_grid[1] - curr_grid[1]

        print(f"[AI-{self.player_number}] curr: {curr_grid}, next: {next_grid}, dx: {dx}, dy: {dy}")

        if dx == 1:
            return AIAction.MOVE_RIGHT
        elif dx == -1:
            return AIAction.MOVE_LEFT
        elif dy == 1:
            return AIAction.MOVE_DOWN
        elif dy == -1:
            return AIAction.MOVE_UP

        return AIAction.NO_ACTION
