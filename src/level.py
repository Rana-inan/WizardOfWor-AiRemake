# src/level.py
import math
import random
import pygame
import os
import sys

class Level:
    CAN_MOVE = 0
    CANT_MOVE_RIGHT = 1
    CANT_MOVE_DOWN = 2
    TIME_BETWEEN_ACCELERATIONS = 10
    MAX_THRESHOLDS = 4
    TUNNEL_COOLDOWN = 2.0
    
    NO_TUNNEL = 0
    TUNNEL_LEFT = 1
    TUNNEL_RIGHT = 2
    
    class CanMoveData:
        def __init__(self):
            self.up = False
            self.down = False
            self.left = False
            self.right = False
            
        def __str__(self):
            return f"Up: {self.up} - Down: {self.down} - Left: {self.left} - Right: {self.right}"
    
    def __init__(self, asset_path, cell_width, cell_height, screen_width, screen_height, random_generator):
        print(f"Level init başlıyor: {asset_path}")
        print(f"Cell boyutları: {cell_width}x{cell_height}")
        
        try:
            self.name = os.path.splitext(os.path.basename(asset_path))[0]  #-----------------------------------------
            self._grid = self._load_level_data(asset_path)

            
            # Grid yüklenemezse
            if not self._grid or len(self._grid) == 0:
                print("Grid yok veya boş, varsayılan grid oluşturuluyor")
                self._grid = [[0 for _ in range(13)] for _ in range(8)]
            
            # Grid boyutları
            self._width = len(self._grid[0]) if self._grid and len(self._grid) > 0 else 13
            self._height = len(self._grid) if self._grid else 8
            
            print(f"Grid boyutları: {self._width}x{self._height}")
            
            # Hücre boyutları
            self._cell_width = cell_width
            self._cell_height = cell_height
            
            # Renk
            self.color = (255, 255, 255)  # Beyaz
            
            # Render hedefini oluştur
            pixel_width = self.pixel_width
            pixel_height = self.pixel_height
            
            print(f"Render hedefi boyutu: {pixel_width}x{pixel_height}")
            
            if pixel_width <= 0 or pixel_height <= 0:
                # Geçersiz değerler varsa düzelt
                pixel_width = max(100, pixel_width)
                pixel_height = max(100, pixel_height)
                print(f"Geçersiz render boyutu düzeltildi: {pixel_width}x{pixel_height}")
            
            self._render_target = pygame.Surface((pixel_width, pixel_height), pygame.SRCALPHA)
            
            # Render verilerini doğrudan tutmuyoruz, kilitleme sorunu oluşmaması için
            self._render_data = []
            
            # Zaman ve eşikleri ayarla
            self._elapsed_time = 0
            self._current_threshold = 0
            
            # Tünel ayarları
            self._tunnel_timer = 0
            self.tunnels_open = True
            self._tunnel_y = 3
            self._tunnel_left_x = 1
            self._tunnel_right_x = 11
            
            self._random = random_generator
            
            # Labirenti çiz
            self._draw()
            
            print("Level init tamamlandı")
            
        except Exception as e:
            print(f"Level init hatası: {e}")
    
    def _load_level_data(self, asset_path):
        grid = []
        
        try:
            # Dosya konumunu yazdır
            print(f"Labirent dosyası yükleniyor: {os.path.abspath(asset_path)}")
            
            with open(asset_path, 'r') as file:
                for line_index, line in enumerate(file):
                    line = line.strip()
                    if not line or line.startswith('--'):
                        continue
                    
                    row = []
                    for char_index, char in enumerate(line):
                        try:
                            # Her hücreyi kontrol et ve yazdır
                            cell_value = int(char)
                            row.append(cell_value)
                            
                            # Sol üst köşe hücreleri
                            if line_index < 2 and char_index < 2:
                                print(f"Hücre ({char_index},{line_index}) = {cell_value}")
                        except ValueError:
                            row.append(0)
                    
                    if row:
                        grid.append(row)
            
            print(f"Yüklenen grid: {len(grid)} satır, her satırda {len(grid[0])} hücre")
        except Exception as e:
            print(f"Level yükleme hatası: {e}")
            grid = [[0 for _ in range(13)] for _ in range(8)]
        
        return grid
    
    @property
    def pixel_width(self):
        return self._width * self._cell_width
    
    @property
    def pixel_height(self):
        return self._height * self._cell_height + self.radar_height
    
    @property
    def radar_height(self):
        return (self._height + 1) * 2
    
    @property
    def current_threshold(self):
        return self._current_threshold
    
    def reset(self, current_stage):
        self._elapsed_time = 0
        self._current_threshold = min(self.MAX_THRESHOLDS, current_stage // 2)
        self._tunnel_timer = 0
        self.tunnels_open = True
    
    def update(self, delta_time):
        if self._current_threshold < self.MAX_THRESHOLDS:
            self._elapsed_time += delta_time
            if self._elapsed_time >= self.TIME_BETWEEN_ACCELERATIONS:
                self._current_threshold = min(self._current_threshold + 1, self.MAX_THRESHOLDS)
                self._elapsed_time -= self.TIME_BETWEEN_ACCELERATIONS
        
        self._tunnel_timer += delta_time
        if self._tunnel_timer > self.TUNNEL_COOLDOWN:
            self.tunnels_open = not self.tunnels_open
            self._tunnel_timer -= self.TUNNEL_COOLDOWN
    
    def get_cell_position(self, x, y):
        return pygame.Vector2(x * self._cell_width, y * self._cell_height)
    
    def is_on_grid_cell(self, position_x, position_y):
        # Tam grid kontrolü
        delta_x = position_x % self._cell_width
        delta_y = position_y % self._cell_height
        
        # Debug
        # if delta_x != 0 or delta_y != 0:
        #     print(f"Grid dışı: ({position_x}, {position_y}), delta: ({delta_x}, {delta_y})")
        
        return delta_x == 0 and delta_y == 0
    
    def get_random_position(self, avoid_player_exits=True):
        """
        Rastgele bir pozisyon döndürür, isteğe bağlı olarak oyuncu çıkış noktalarından uzak durur
        
        Args:
            avoid_player_exits (bool): Oyuncu çıkış noktalarından kaçınılıp kaçınılmayacağı
            
        Returns:
            pygame.Vector2: Rastgele seçilen pozisyon
        """
        max_attempts = 10  # Maksimum deneme sayısı
        
        # Oyuncu kafeslerinin konumları (varsayılan olarak)
        p1_cage_x, p1_cage_y = 11, 7  # Oyuncu 1 kafes konumu
        p2_cage_x, p2_cage_y = 1, 7   # Oyuncu 2 kafes konumu
        
        for _ in range(max_attempts):
            grid_x = 1 + self._random.randint(0, 10)
            grid_y = 1 + self._random.randint(0, 5)
            
            # Eğer oyuncu çıkışlarından kaçınılması isteniyorsa
            if avoid_player_exits:
                # Oyuncu 1 kafesinin çıkışı (bir yukarısı)
                if grid_x == p1_cage_x and grid_y == p1_cage_y - 1:
                    continue
                    
                # Oyuncu 2 kafesinin çıkışı (bir yukarısı)
                if grid_x == p2_cage_x and grid_y == p2_cage_y - 1:
                    continue
                    
                # Kafes çıkışlarının biraz daha geniş bir alanını kontrol et (opsiyonel)
                if ((abs(grid_x - p1_cage_x) <= 1 and abs(grid_y - (p1_cage_y - 1)) <= 1) or 
                    (abs(grid_x - p2_cage_x) <= 1 and abs(grid_y - (p2_cage_y - 1)) <= 1)):
                    continue
            
            # Uygun bir konum bulundu
            return self.get_cell_position(grid_x, grid_y)
        
        # Eğer tüm denemeler başarısız olursa, rastgele bir konum döndür
        grid_x = 1 + self._random.randint(0, 10)
        grid_y = 1 + self._random.randint(0, 5)
        return self.get_cell_position(grid_x, grid_y)
    
    def get_tunnel_position(self, tunnel):
        new_position = pygame.Vector2()
        new_position.y = self._tunnel_y * self._cell_height
        if tunnel == self.TUNNEL_LEFT:
            new_position.x = self._tunnel_left_x * self._cell_width
        elif tunnel == self.TUNNEL_RIGHT:
            new_position.x = self._tunnel_right_x * self._cell_width
        return new_position
    
    def can_move(self, position_x, position_y):
        tunnel_teleport = self.NO_TUNNEL
        can_move = self.CanMoveData()
        
        closest_grid_cell_x = int(position_x // self._cell_width)
        delta_x = position_x % self._cell_width
        closest_grid_cell_y = int(position_y // self._cell_height)
        delta_y = position_y % self._cell_height
        
        # Hareketi belirle
        if delta_x != 0:
            can_move.left = can_move.right = True
            can_move.up = can_move.down = False
        elif delta_y != 0:
            can_move.left = can_move.right = False
            can_move.up = can_move.down = True
        else:
            # Grid hücresinde olan bir karakter
            if (closest_grid_cell_x < 1 or closest_grid_cell_x > self._width - 1 or 
                closest_grid_cell_y < 1 or closest_grid_cell_y > self._height - 1):
                can_move.left = can_move.right = can_move.up = can_move.down = False
            else:
                # Grid hücrelerinin duvar verilerini kontrol et
                if closest_grid_cell_x == self._width - 1:
                    can_move.right = False
                else:
                    can_move.right = (self._grid[closest_grid_cell_y][closest_grid_cell_x] & self.CANT_MOVE_RIGHT) == 0
                
                if closest_grid_cell_y == self._height - 1:
                    can_move.down = False
                else:
                    can_move.down = (self._grid[closest_grid_cell_y][closest_grid_cell_x] & self.CANT_MOVE_DOWN) == 0
                
                if closest_grid_cell_x - 1 < 0:
                    can_move.left = False
                else:
                    can_move.left = (self._grid[closest_grid_cell_y][closest_grid_cell_x - 1] & self.CANT_MOVE_RIGHT) == 0
                
                if closest_grid_cell_y - 1 < 0:
                    can_move.up = False
                else:
                    can_move.up = (self._grid[closest_grid_cell_y - 1][closest_grid_cell_x] & self.CANT_MOVE_DOWN) == 0
                
                # Tünel kontrolü
                if (self.tunnels_open and closest_grid_cell_y == self._tunnel_y):
                    if closest_grid_cell_x == self._tunnel_left_x:
                        tunnel_teleport = self.TUNNEL_LEFT
                    elif closest_grid_cell_x == self._tunnel_right_x:
                        tunnel_teleport = self.TUNNEL_RIGHT
        
        return can_move, tunnel_teleport
    
    def pick_possible_direction_with_tunnel(self, enemy):
        """
        Tünel bilgisi ile birlikte yön döndürür
        Returns: (direction_vector, tunnel_type)
        """
        tunnel = self.NO_TUNNEL
        
        if self.is_on_grid_cell(enemy.pixel_position_x, enemy.pixel_position_y):
            side_of_level = math.copysign(1, self.pixel_width / 2 - enemy.pixel_position_x)
            is_on_wrong_side = enemy.preferred_horizontal_direction != 0 and side_of_level == enemy.preferred_horizontal_direction
            
            if enemy.can_change_direction:
                can_move, tunnel = self.can_move(enemy.pixel_position_x, enemy.pixel_position_y)
                
                print(f"🔍 Enemy grid check: pos=({enemy.pixel_position_x}, {enemy.pixel_position_y}), can_move={can_move}, tunnel={tunnel}")
                
                # Düşman yapay zekası
                if enemy.preferred_horizontal_direction != 0 and tunnel != self.NO_TUNNEL:
                    enemy.can_change_direction = False
                    if tunnel == self.TUNNEL_RIGHT:
                        print(f"🔥 Enemy choosing RIGHT tunnel direction!")
                        return pygame.Vector2(1, 0), tunnel
                    if tunnel == self.TUNNEL_LEFT:
                        print(f"🔥 Enemy choosing LEFT tunnel direction!")
                        return pygame.Vector2(-1, 0), tunnel
                
                possible_directions = []
                
                # Yatay harekette düşmanı kontrol et
                if enemy.move_direction.x > 0 or enemy.move_direction.x < 0:
                    if (enemy.move_direction.x > 0 and (can_move.right or tunnel == self.TUNNEL_RIGHT) or
                        enemy.move_direction.x < 0 and (can_move.left or tunnel == self.TUNNEL_LEFT)):
                        if is_on_wrong_side:
                            if enemy.preferred_horizontal_direction == enemy.move_direction.x:
                                enemy.can_change_direction = False
                                return enemy.move_direction, tunnel
                            elif not can_move.down and not can_move.up:
                                possible_directions.append(enemy.move_direction)
                        else:
                            possible_directions.append(enemy.move_direction)
                    
                    if can_move.up:
                        possible_directions.append(pygame.Vector2(0, -1))
                    if can_move.down:
                        possible_directions.append(pygame.Vector2(0, 1))
                    
                    if not possible_directions:
                        possible_directions.append(-enemy.move_direction)
                
                # Dikey harekette düşmanı kontrol et
                if enemy.move_direction.y > 0 or enemy.move_direction.y < 0:
                    if (enemy.move_direction.y > 0 and can_move.down or 
                        enemy.move_direction.y < 0 and can_move.up):
                        possible_directions.append(enemy.move_direction)
                    
                    if can_move.right or tunnel == self.TUNNEL_RIGHT:
                        if is_on_wrong_side and enemy.preferred_horizontal_direction > 0:
                            enemy.can_change_direction = False
                            print(f"🔥 Enemy forced RIGHT for tunnel!")
                            return pygame.Vector2(1, 0), tunnel
                        else:
                            possible_directions.append(pygame.Vector2(1, 0))
                    
                    if can_move.left or tunnel == self.TUNNEL_LEFT:
                        if is_on_wrong_side and enemy.preferred_horizontal_direction < 0:
                            enemy.can_change_direction = False
                            print(f"🔥 Enemy forced LEFT for tunnel!")
                            return pygame.Vector2(-1, 0), tunnel
                        else:
                            possible_directions.append(pygame.Vector2(-1, 0))
                    
                    if not possible_directions:
                        possible_directions.append(-enemy.move_direction)
                
                # Düşmanın tercih ettiği yön kontrolü
                if len(possible_directions) > 1 and is_on_wrong_side and enemy.preferred_horizontal_direction != 0:
                    try:
                        to_remove = None
                        for dir in possible_directions:
                            if dir.x == -enemy.preferred_horizontal_direction and dir.y == 0:
                                to_remove = dir
                                break
                        
                        if to_remove:
                            possible_directions.remove(to_remove)
                    except:
                        pass  # Silme işlemi başarısız olursa geç
                
                # Rastgele bir yön seç
                if possible_directions:
                    chosen_direction = possible_directions[self._random.randint(0, len(possible_directions) - 1)]
                    enemy.can_change_direction = False
                    
                    print(f"✅ Enemy chose direction: {chosen_direction}, tunnel: {tunnel}")
                    return chosen_direction, tunnel
        else:
            enemy.can_change_direction = True
        
        return enemy.move_direction, self.NO_TUNNEL
    
    def pick_possible_direction(self, enemy, tunnel_out):
        tunnel = self.NO_TUNNEL
        if self.is_on_grid_cell(enemy.pixel_position_x, enemy.pixel_position_y):
            side_of_level = math.copysign(1, self.pixel_width / 2 - enemy.pixel_position_x)
            is_on_wrong_side = enemy.preferred_horizontal_direction != 0 and side_of_level == enemy.preferred_horizontal_direction
            
            if enemy.can_change_direction:
                can_move, tunnel = self.can_move(enemy.pixel_position_x, enemy.pixel_position_y)
                
                # Düşman yapay zekası
                if enemy.preferred_horizontal_direction != 0 and tunnel != self.NO_TUNNEL:
                    enemy.can_change_direction = False
                    if tunnel == self.TUNNEL_RIGHT:
                        return pygame.Vector2(1, 0)
                    if tunnel == self.TUNNEL_LEFT:
                        return pygame.Vector2(-1, 0)
                
                possible_directions = []
                
                # Yatay harekette düşmanı kontrol et
                if enemy.move_direction.x > 0 or enemy.move_direction.x < 0:
                    if (enemy.move_direction.x > 0 and (can_move.right or tunnel == self.TUNNEL_RIGHT) or
                        enemy.move_direction.x < 0 and (can_move.left or tunnel == self.TUNNEL_LEFT)):
                        if is_on_wrong_side:
                            if enemy.preferred_horizontal_direction == enemy.move_direction.x:
                                enemy.can_change_direction = False
                                return enemy.move_direction
                            elif not can_move.down and not can_move.up:
                                possible_directions.append(enemy.move_direction)
                        else:
                            possible_directions.append(enemy.move_direction)
                    
                    if can_move.up:
                        possible_directions.append(pygame.Vector2(0, -1))
                    if can_move.down:
                        possible_directions.append(pygame.Vector2(0, 1))
                    
                    if not possible_directions:
                        possible_directions.append(-enemy.move_direction)
                
                # Dikey harekette düşmanı kontrol et
                if enemy.move_direction.y > 0 or enemy.move_direction.y < 0:
                    if (enemy.move_direction.y > 0 and can_move.down or 
                        enemy.move_direction.y < 0 and can_move.up):
                        possible_directions.append(enemy.move_direction)
                    
                    if can_move.right or tunnel == self.TUNNEL_RIGHT:
                        if is_on_wrong_side and enemy.preferred_horizontal_direction > 0:
                            enemy.can_change_direction = False
                            return pygame.Vector2(1, 0)
                        else:
                            possible_directions.append(pygame.Vector2(1, 0))
                    
                    if can_move.left or tunnel == self.TUNNEL_LEFT:
                        if is_on_wrong_side and enemy.preferred_horizontal_direction < 0:
                            enemy.can_change_direction = False
                            return pygame.Vector2(-1, 0)
                        else:
                            possible_directions.append(pygame.Vector2(-1, 0))
                    
                    if not possible_directions:
                        possible_directions.append(-enemy.move_direction)
                
                # Düşmanın tercih ettiği yön kontrolü
                if len(possible_directions) > 1 and is_on_wrong_side and enemy.preferred_horizontal_direction != 0:
                    try:
                        to_remove = None
                        for dir in possible_directions:
                            if dir.x == -enemy.preferred_horizontal_direction and dir.y == 0:
                                to_remove = dir
                                break
                        
                        if to_remove:
                            possible_directions.remove(to_remove)
                    except:
                        pass  # Silme işlemi başarısız olursa geç
                
                # Rastgele bir yön seç
                if possible_directions:
                    chosen_direction = possible_directions[self._random.randint(0, len(possible_directions) - 1)]
                    enemy.can_change_direction = False
                    
                    tunnel_out = tunnel
                    return chosen_direction
        else:
            enemy.can_change_direction = True
        
        tunnel_out = self.NO_TUNNEL
        return enemy.move_direction
    
    def _draw(self):
        try:
            # Render hedefini temizle - SİYAH ARKAPLAN
            self._render_target.fill((0, 0, 0))
            
            # Labirent duvarlarını çiz - MAVİ DUVARLAR
            wall_color = (73, 81, 209)  # Mavi duvar rengi
            
            # Labirent duvarlarını çiz
            for y in range(self._height):
                for x in range(self._width):
                    # Grid içeriği kontrol et
                    cell_value = self._grid[y][x] if y < len(self._grid) and x < len(self._grid[y]) else 0
                    
                    # Yatay duvarlar (CANT_MOVE_DOWN)
                    if (cell_value & self.CANT_MOVE_DOWN) > 0:
                        pygame.draw.rect(
                            self._render_target,
                            wall_color,  # Mavi
                            (x * self._cell_width, y * self._cell_height + self._cell_height - 1, self._cell_width, 1)
                        )
                    
                    # Dikey duvarlar (CANT_MOVE_RIGHT)
                    if (cell_value & self.CANT_MOVE_RIGHT) > 0:
                        pygame.draw.rect(
                            self._render_target,
                            wall_color,  # Mavi
                            (x * self._cell_width + self._cell_width - 1, y * self._cell_height, 1, self._cell_height)
                        )
            
            # Dış sınırları çiz - aynı kalınlıkta
            # Üst sınır
            pygame.draw.rect(self._render_target, wall_color, (0, 0, self._width * self._cell_width, 1))
            
            # Sol sınır
            pygame.draw.rect(self._render_target, wall_color, (0, 0, 1, self._height * self._cell_height))
            
            # Alt sınır
            pygame.draw.rect(self._render_target, wall_color, (0, self._height * self._cell_height - 1, self._width * self._cell_width, 1))
            
            # Sağ sınır
            pygame.draw.rect(self._render_target, wall_color, (self._width * self._cell_width - 1, 0, 1, self._height * self._cell_height))
            
            # Radar bölgesini çiz
            radar_width = 64
            radar_height = 16
            radar_x = (self._width * self._cell_width - radar_width) // 2
            radar_y = self._height * self._cell_height + 1
            
            # Radar alanı
            pygame.draw.rect(self._render_target, (255, 0, 0), (radar_x, radar_y, radar_width, radar_height))
            
            # Radar çerçevesi
            pygame.draw.rect(self._render_target, (255, 255, 255), (radar_x - 1, radar_y - 1, radar_width + 2, radar_height + 2), 1)
            
            # Sol ve sağ skor panel bölgeleri
            pygame.draw.rect(self._render_target, (0, 0, 255), (0, self._height * self._cell_height, 40, 20))  # Sol mavi
            pygame.draw.rect(self._render_target, (255, 255, 0), (self._width * self._cell_width - 40, self._height * self._cell_height, 40, 20))  # Sağ sarı
            
            print("Labirent çizimi tamamlandı")
        except Exception as e:
            print(f"Labirent çizimi hatası: {e}")
    
    def draw_tunnels(self, color, surface, offset_x, offset_y):
        if not self.tunnels_open:
            try:
                # Sol tünel
                pygame.draw.rect(surface, color, 
                              ((self._tunnel_left_x - 1) * self._cell_width + 8 + offset_x, 
                               self._tunnel_y * self._cell_height + offset_y, 
                               4, 8))
                # Sağ tünel
                pygame.draw.rect(surface, color, 
                              (self._tunnel_right_x * self._cell_width + 8 + offset_x, 
                               self._tunnel_y * self._cell_height + offset_y, 
                               4, 8))
            except Exception as e:
                print(f"Tünel çizimi hatası: {e}")
    
    def draw_radar(self, enemies, surface):
        try:
            # Radar alanının ortasını hesapla
            radar_x = (self._width * self._cell_width) // 2 - 30  # Radar merkezi
            radar_y = self._height * self._cell_height + 10     # Labirentin altında
            
            for enemy in enemies:
                if enemy.visible:  # Sadece görünür düşmanları göster
                    # Düşmanın grid pozisyonunu hesapla
                    grid_x = int(enemy.pixel_position_x // self._cell_width)
                    grid_y = int(enemy.pixel_position_y // self._cell_height)
                    
                    # Düşmanın radar üzerindeki pozisyonunu hesapla
                    dot_x = radar_x + grid_x * 4
                    dot_y = radar_y + grid_y * 2
                    
                    # Düşmanın rengini kullan
                    color = enemy.color
                    
                    # Radar üzerinde düşmanı göster
                    pygame.draw.rect(surface, color, 
                                (dot_x, dot_y, 4, 2))
        except Exception as e:
            print(f"Radar çizimi hatası: {e}")
  
    def has_pixel(self, x, y):
        # Ekranın dışında mı kontrol et
        if x < 0 or y < 0 or x >= self.pixel_width or y >= self.pixel_height:
            return False
        
        # Çarpışma kontrolü
        cell_x = int(x // self._cell_width)
        cell_y = int(y // self._cell_height)
        
        # Geçersiz hücre indeksi kontrolü
        if cell_x < 0 or cell_y < 0 or cell_x >= self._width or cell_y >= self._height:
            return True
        
        # Duvar kontrolleri - sadece tam duvar kenarlarında çarpışma
        px = x % self._cell_width
        py = y % self._cell_height
        
        # Sağ duvar kontrolü - daha dar bir aralık kullan
        if (self._grid[cell_y][cell_x] & self.CANT_MOVE_RIGHT) > 0:
            if px >= 10 and px <= 12:  # Daha dar duvar (orijinali 8-12 aralığı)
                return True
        
        # Alt duvar kontrolü - daha dar bir aralık kullan
        if (self._grid[cell_y][cell_x] & self.CANT_MOVE_DOWN) > 0:
            if py >= 8 and py <= 9:  # Daha dar duvar (orijinali 8-10 aralığı)
                return True
        
        return False

    def is_walkable(self, from_x, from_y, to_x, to_y):
        if (to_x < 0 or to_y < 0 or to_x >= self._width or to_y >= self._height):
            return False

        dx = to_x - from_x
        dy = to_y - from_y

        current = self._grid[from_y][from_x]

        # Sağ gitmek istiyor
        if dx == 1 and (current & self.CANT_MOVE_RIGHT):
            return False

        # Sol gitmek istiyor
        if dx == -1:
            left_cell = self._grid[from_y][to_x]
            if left_cell & self.CANT_MOVE_RIGHT:
                return False

        # Aşağı gitmek istiyor
        if dy == 1 and (current & self.CANT_MOVE_DOWN):
            return False

        # Yukarı gitmek istiyor
        if dy == -1:
            upper_cell = self._grid[to_y][from_x]
            if upper_cell & self.CANT_MOVE_DOWN:
                return False

        return True
   
    def is_inside_walls(self, x, y):
        return (x > self._cell_width and 
                y > self._cell_height and 
                x < (self._width - 1) * self._cell_width - 4 and 
                y < (self._height - 1) * self._cell_height)