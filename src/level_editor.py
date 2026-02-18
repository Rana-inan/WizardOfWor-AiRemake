import pygame
import sys
import os
import tkinter as tk
from tkinter import filedialog

class LevelEditor:
    """Wizard of Wor oyununa level editörü"""
    
    # Sabitler
    CELL_SIZE = 40  # Bir hücrenin boyutu (piksel) - büyütüldü
    GRID_WIDTH = 13  # Grid genişliği (hücre)
    GRID_HEIGHT = 8  # Grid yüksekliği (hücre)
    
    # Duvar sabitleri (oyundaki kodlara göre)
    NO_WALL = 0
    RIGHT_WALL = 1  # CANT_MOVE_RIGHT
    BOTTOM_WALL = 2  # CANT_MOVE_DOWN
    BOTH_WALLS = 3  # CANT_MOVE_RIGHT | CANT_MOVE_DOWN
    
    # Renkler
    BACKGROUND_COLOR = (0, 0, 0)  # Siyah
    GRID_LINE_COLOR = (50, 50, 50)  # Koyu gri
    WALL_COLOR = (73, 81, 209)  # Labirent duvarlarının rengi (Mavi)
    TUNNEL_COLOR = (255, 0, 0)  # Tünellerin rengi (Kırmızı)
    UI_COLOR = (220, 176, 73)  # UI elemanları (Sarımsı)
    HELP_COLOR = (255, 255, 255)  # Yardım metni (Beyaz)
    
    def __init__(self):
        """Level editörünü başlat"""
        pygame.init()
        
        # Pencere boyutu - daha büyük ve yan yana yerleşim için
        self.window_width = self.CELL_SIZE * self.GRID_WIDTH + 300  # Grid + UI (genişletildi)
        self.window_height = self.CELL_SIZE * self.GRID_HEIGHT + 150  # Grid + Alt bilgi (genişletildi)
        
        # Pencere simgesi (opsiyonel)
        try:
            icon = pygame.Surface((32, 32))
            icon.fill((73, 81, 209))  # Mavi labirent rengi
            pygame.display.set_icon(icon)
        except:
            pass
            
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Wizard of Wor Level Editor")
        
        # Font
        self.font = pygame.font.SysFont("Consolas", 16)
        self.big_font = pygame.font.SysFont("Consolas", 24, bold=True)
        
        # Grid verisi (2D array)
        self.grid = [[0 for _ in range(self.GRID_WIDTH)] for _ in range(self.GRID_HEIGHT)]
        
        # Tünel koordinatları (varsayılan olarak oyunda olduğu gibi)
        self.tunnel_left_x = 1
        self.tunnel_right_x = 11
        self.tunnel_y = 3
        
        # Kafes (cage) pozisyonları
        self.cage_p1_x = 11
        self.cage_p1_y = 7
        self.cage_p2_x = 1
        self.cage_p2_y = 7
        
        # Düzenleme durumu
        self.current_tool = "right_wall"  # sağ duvar, alt duvar veya tünel
        self.selected_cell = None
        self.file_name = "NewLevel.txt"
        self.message = "Level Editor başlatıldı"
        self.last_message_time = pygame.time.get_ticks()
        
        # Yardım mesajı görünürlüğü
        self.show_help = True  # İlk açılışta yardım mesajını göster
        
        # Varolan levelleri kontrol et 
        level_files = [f for f in os.listdir('.') if f.startswith('Level') and f.endswith('.txt')]
        if level_files:
            self.message = f"Bulunan seviyeler: {', '.join(level_files)}"
    
    def run(self):
        """Ana döngü"""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_event(event.key)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_event(event.pos, event.button)
            
            # Grid ve UI çiz
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def handle_key_event(self, key):
        """Klavye olaylarını işle"""
        if key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
        
        elif key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            # CTRL+S: Kaydet
            self.save_level()
        
        elif key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
            # CTRL+O: Aç
            self.load_level()
        
        elif key == pygame.K_n and pygame.key.get_mods() & pygame.KMOD_CTRL:
            # CTRL+N: Yeni
            self.new_level()
        
        elif key == pygame.K_r:
            # R: Sağ duvar aracı
            self.current_tool = "right_wall"
            self.show_message("Sağ duvar aracı seçildi")
        
        elif key == pygame.K_b:
            # B: Alt duvar aracı
            self.current_tool = "bottom_wall"
            self.show_message("Alt duvar aracı seçildi")
        
        elif key == pygame.K_t:
            # T: Tünel konumu aracı
            self.current_tool = "tunnel"
            self.show_message("Tünel konumu aracı seçildi")
        
        elif key == pygame.K_c:
            # C: Cage (kafes) konumu aracı
            self.current_tool = "cage"
            self.show_message("Kafes konumu aracı seçildi")
        
        elif key == pygame.K_h:
            # H: Yardım mesajını göster/gizle
            self.show_help = not self.show_help
            
        elif key == pygame.K_1 and pygame.key.get_mods() & pygame.KMOD_CTRL:
            # Örnek Level1'i yükle (karşılaştırma için)
            if os.path.exists("Level1.txt"):
                self.file_name = "Level1.txt"
                self.load_specific_level("Level1.txt")
            
        elif key == pygame.K_2 and pygame.key.get_mods() & pygame.KMOD_CTRL:
            # Örnek Level2'yi yükle (karşılaştırma için)
            if os.path.exists("Level2.txt"):
                self.file_name = "Level2.txt"
                self.load_specific_level("Level2.txt")
    
    def handle_mouse_event(self, pos, button):
        """Fare olaylarını işle"""
        # Grid alanında tıklandı mı?
        if pos[0] < self.CELL_SIZE * self.GRID_WIDTH and pos[1] < self.CELL_SIZE * self.GRID_HEIGHT:
            cell_x = pos[0] // self.CELL_SIZE
            cell_y = pos[1] // self.CELL_SIZE
            
            if 0 <= cell_x < self.GRID_WIDTH and 0 <= cell_y < self.GRID_HEIGHT:
                # Aracın tipine göre işlem yap
                if self.current_tool == "right_wall":
                    # Sağ duvar ekleme/kaldırma
                    if cell_x < self.GRID_WIDTH - 1:  # Sağ sınıra dikkat et
                        self.toggle_right_wall(cell_x, cell_y)
                
                elif self.current_tool == "bottom_wall":
                    # Alt duvar ekleme/kaldırma
                    if cell_y < self.GRID_HEIGHT - 1:  # Alt sınıra dikkat et
                        self.toggle_bottom_wall(cell_x, cell_y)
                
                elif self.current_tool == "tunnel":
                    # Tünel konumunu ayarla
                    if button == 1:  # Sol tıklama: Sol tünel
                        self.tunnel_left_x = cell_x
                        self.tunnel_y = cell_y
                        self.show_message(f"Sol tünel pozisyonu: ({cell_x}, {cell_y})")
                    elif button == 3:  # Sağ tıklama: Sağ tünel
                        self.tunnel_right_x = cell_x
                        self.tunnel_y = cell_y
                        self.show_message(f"Sağ tünel pozisyonu: ({cell_x}, {cell_y})")
                
                elif self.current_tool == "cage":
                    # Kafes konumunu ayarla
                    if button == 1:  # Sol tıklama: Oyuncu 1 kafesi
                        self.cage_p1_x = cell_x
                        self.cage_p1_y = cell_y
                        self.show_message(f"Oyuncu 1 kafesi: ({cell_x}, {cell_y})")
                    elif button == 3:  # Sağ tıklama: Oyuncu 2 kafesi
                        self.cage_p2_x = cell_x
                        self.cage_p2_y = cell_y
                        self.show_message(f"Oyuncu 2 kafesi: ({cell_x}, {cell_y})")
        
        # Butonları kontrol et (UI bölgesi)
        else:
            ui_x = self.GRID_WIDTH * self.CELL_SIZE + 20
            button_area = pygame.Rect(ui_x, 60, 160, 30)
            if button_area.collidepoint(pos):
                self.save_level()
                return
            
            button_area.y += 40
            if button_area.collidepoint(pos):
                self.load_level()
                return
                
            button_area.y += 40
            if button_area.collidepoint(pos):
                self.new_level()
                return
                
            # Yardım butonu
            button_area.y = self.window_height - 40
            if button_area.collidepoint(pos):
                self.show_help = not self.show_help
                return
    
    def toggle_right_wall(self, x, y):
        """Belirli bir hücrenin sağ duvarını aç/kapat"""
        if self.grid[y][x] & self.RIGHT_WALL:
            # Duvar varsa kaldır
            self.grid[y][x] &= ~self.RIGHT_WALL
            self.show_message(f"({x}, {y}) sağ duvarı kaldırıldı")
        else:
            # Duvar yoksa ekle
            self.grid[y][x] |= self.RIGHT_WALL
            self.show_message(f"({x}, {y}) sağ duvarı eklendi")
    
    def toggle_bottom_wall(self, x, y):
        """Belirli bir hücrenin alt duvarını aç/kapat"""
        if self.grid[y][x] & self.BOTTOM_WALL:
            # Duvar varsa kaldır
            self.grid[y][x] &= ~self.BOTTOM_WALL
            self.show_message(f"({x}, {y}) alt duvarı kaldırıldı")
        else:
            # Duvar yoksa ekle
            self.grid[y][x] |= self.BOTTOM_WALL
            self.show_message(f"({x}, {y}) alt duvarı eklendi")
    
    def new_level(self):
        """Yeni bir level oluştur"""
        self.grid = [[0 for _ in range(self.GRID_WIDTH)] for _ in range(self.GRID_HEIGHT)]
        
        # Varsayılan tünel konumlarını ayarla
        self.tunnel_left_x = 1
        self.tunnel_right_x = 11
        self.tunnel_y = 3
        
        # Kafes konumlarını sıfırla
        self.cage_p1_x = 11
        self.cage_p1_y = 7
        self.cage_p2_x = 1
        self.cage_p2_y = 7
        
        self.file_name = "NewLevel.txt"
        self.show_message("Yeni level oluşturuldu")
    
    def save_level(self):
        """Mevcut level'ı dosyaya kaydet"""
        # İletişim kutusu yerine otomatik isimlendirme
        if self.file_name == "NewLevel.txt":
            # Mevcut level dosyalarını kontrol et ve bir sonraki numarayı belirle
            level_num = 1
            while os.path.exists(f"Level{level_num}.txt"):
                level_num += 1
            
            self.file_name = f"Level{level_num}.txt"
        
        try:
            with open(self.file_name, 'w') as file:
                # Her bir satırı yaz
                for row in self.grid:
                    file.write(''.join(str(cell) for cell in row) + '\n')
                
                # Kafes ve tünel bilgilerini yorum olarak ekle
                file.write(f"-- Tunnels: Left={self.tunnel_left_x}, Right={self.tunnel_right_x}, Y={self.tunnel_y}\n")
                file.write(f"-- Cages: P1=({self.cage_p1_x},{self.cage_p1_y}), P2=({self.cage_p2_x},{self.cage_p2_y})\n")
            
            self.show_message(f"Level kaydedildi: {self.file_name}")
        except Exception as e:
            self.show_message(f"Kaydetme hatası: {e}")
    
    def load_level(self):
        """Bir level dosyasını yükle"""
        import tkinter as tk
        from tkinter import filedialog
        
        # Tkinter penceresini gizle
        root = tk.Tk()
        root.withdraw()
        
        # Dosya seçim diyaloğunu göster
        file_types = [("Labirent dosyaları", "*.txt"), ("Tüm dosyalar", "*.*")]
        file_name = filedialog.askopenfilename(
            title="Level dosyası seç",
            filetypes=file_types,
            initialdir="."
        )
        
        if not file_name:
            return
        
        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()
                
                # Satırları oku ve grid'i oluştur
                new_grid = []
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('--'):  # Boş satırları veya yorumları atla
                        continue
                    
                    row = []
                    for char in line:
                        try:
                            row.append(int(char))
                        except ValueError:
                            # Sayı olmayan karakterleri 0 olarak değerlendir
                            row.append(0)
                    
                    if row:  # Boş satırları atla
                        new_grid.append(row)
                
                # Grid boyutunu kontrol et
                if len(new_grid) <= self.GRID_HEIGHT and new_grid and len(new_grid[0]) <= self.GRID_WIDTH:
                    self.grid = [[0 for _ in range(self.GRID_WIDTH)] for _ in range(self.GRID_HEIGHT)]
                    
                    # Verileri kopyala
                    for y in range(min(len(new_grid), self.GRID_HEIGHT)):
                        for x in range(min(len(new_grid[y]), self.GRID_WIDTH)):
                            self.grid[y][x] = new_grid[y][x]
                    
                    # Dosya adını sadece isim kısmı olarak al (yol olmadan)
                    self.file_name = os.path.basename(file_name)
                    self.show_message(f"Level yüklendi: {self.file_name}")
                else:
                    self.show_message("Level boyutu uyumsuz!")
                    
        except FileNotFoundError:
            self.show_message(f"Dosya bulunamadı: {file_name}")
        except Exception as e:
            self.show_message(f"Yükleme hatası: {e}")
    
    def load_specific_level(self, filename):
        """Belirli bir level dosyasını yükle"""
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()
                
                # Satırları oku ve grid'i oluştur
                new_grid = []
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('--'):  # Boş satırları veya yorumları atla
                        continue
                    
                    row = []
                    for char in line:
                        try:
                            row.append(int(char))
                        except ValueError:
                            # Sayı olmayan karakterleri 0 olarak değerlendir
                            row.append(0)
                    
                    if row:  # Boş satırları atla
                        new_grid.append(row)
                
                # Grid boyutunu kontrol et
                if len(new_grid) <= self.GRID_HEIGHT and new_grid and len(new_grid[0]) <= self.GRID_WIDTH:
                    self.grid = [[0 for _ in range(self.GRID_WIDTH)] for _ in range(self.GRID_HEIGHT)]
                    
                    # Verileri kopyala
                    for y in range(min(len(new_grid), self.GRID_HEIGHT)):
                        for x in range(min(len(new_grid[y]), self.GRID_WIDTH)):
                            self.grid[y][x] = new_grid[y][x]
                    
                    self.file_name = filename
                    self.show_message(f"Level yüklendi: {filename}")
                else:
                    self.show_message("Level boyutu uyumsuz!")
                    
        except FileNotFoundError:
            self.show_message(f"Dosya bulunamadı: {filename}")
        except Exception as e:
            self.show_message(f"Yükleme hatası: {e}")
    
    def show_message(self, message):
        """Ekran mesajını güncelle"""
        self.message = message
        self.last_message_time = pygame.time.get_ticks()
    
    def draw_walls(self):
        """Tüm duvarları çiz"""
        for y in range(self.GRID_HEIGHT):
            for x in range(self.GRID_WIDTH):
                # Hücre koordinatlarını ekranda göster (opsiyonel)
                coord_text = self.font.render(f"{x},{y}", True, (100, 100, 100))
                self.screen.blit(coord_text, (x * self.CELL_SIZE + 5, y * self.CELL_SIZE + 5))
                
                # Sağ duvar
                if self.grid[y][x] & self.RIGHT_WALL:
                    pygame.draw.rect(
                        self.screen,
                        self.WALL_COLOR,
                        (x * self.CELL_SIZE + self.CELL_SIZE - 1, y * self.CELL_SIZE, 1, self.CELL_SIZE)
                    )
                
                # Alt duvar
                if self.grid[y][x] & self.BOTTOM_WALL:
                    pygame.draw.rect(
                        self.screen,
                        self.WALL_COLOR,
                        (x * self.CELL_SIZE, y * self.CELL_SIZE + self.CELL_SIZE - 1, self.CELL_SIZE, 1)
                    )
        
        # Dış sınır duvarları (daha kalın)
        pygame.draw.rect(
            self.screen,
            self.WALL_COLOR,
            (0, 0, self.GRID_WIDTH * self.CELL_SIZE, 1)
        )
        pygame.draw.rect(
            self.screen,
            self.WALL_COLOR,
            (0, 0, 1, self.GRID_HEIGHT * self.CELL_SIZE)
        )
        pygame.draw.rect(
            self.screen,
            self.WALL_COLOR,
            (0, self.GRID_HEIGHT * self.CELL_SIZE - 1, self.GRID_WIDTH * self.CELL_SIZE, 1)
        )
        pygame.draw.rect(
            self.screen,
            self.WALL_COLOR,
            (self.GRID_WIDTH * self.CELL_SIZE - 1, 0, 1, self.GRID_HEIGHT * self.CELL_SIZE)
        )
    
    def draw(self):
        """Arayüzü çiz"""
        # Ekranı temizle
        self.screen.fill(self.BACKGROUND_COLOR)
        
        # Grid çizgileri - daha belirgin
        for x in range(self.GRID_WIDTH + 1):
            pygame.draw.line(
                self.screen,
                self.GRID_LINE_COLOR,
                (x * self.CELL_SIZE, 0),
                (x * self.CELL_SIZE, self.GRID_HEIGHT * self.CELL_SIZE),
                1  # Çizgi kalınlığı
            )
        
        for y in range(self.GRID_HEIGHT + 1):
            pygame.draw.line(
                self.screen,
                self.GRID_LINE_COLOR,
                (0, y * self.CELL_SIZE),
                (self.GRID_WIDTH * self.CELL_SIZE, y * self.CELL_SIZE),
                1  # Çizgi kalınlığı
            )
            
        # Duvarları çiz
        self.draw_walls()
        
        # Tünelleri çiz
        left_tunnel_rect = pygame.Rect(
            self.tunnel_left_x * self.CELL_SIZE, 
            self.tunnel_y * self.CELL_SIZE, 
            self.CELL_SIZE, 
            self.CELL_SIZE
        )
        pygame.draw.rect(self.screen, self.TUNNEL_COLOR, left_tunnel_rect, 1)
        
        right_tunnel_rect = pygame.Rect(
            self.tunnel_right_x * self.CELL_SIZE, 
            self.tunnel_y * self.CELL_SIZE, 
            self.CELL_SIZE, 
            self.CELL_SIZE
        )
        pygame.draw.rect(self.screen, self.TUNNEL_COLOR, right_tunnel_rect, 1)
        
        # Kafes konumlarını çiz
        p1_cage_rect = pygame.Rect(
            self.cage_p1_x * self.CELL_SIZE, 
            self.cage_p1_y * self.CELL_SIZE, 
            self.CELL_SIZE, 
            self.CELL_SIZE
        )
        pygame.draw.rect(self.screen, (220, 176, 73), p1_cage_rect, 1)  # P1: Sarımsı
        
        p2_cage_rect = pygame.Rect(
            self.cage_p2_x * self.CELL_SIZE, 
            self.cage_p2_y * self.CELL_SIZE, 
            self.CELL_SIZE, 
            self.CELL_SIZE
        )
        pygame.draw.rect(self.screen, (106, 117, 238), p2_cage_rect, 1)  # P2: Mavimsi
        
        # Fare pozisyonundaki hücreyi vurgula
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] < self.CELL_SIZE * self.GRID_WIDTH and mouse_pos[1] < self.CELL_SIZE * self.GRID_HEIGHT:
            cell_x = mouse_pos[0] // self.CELL_SIZE
            cell_y = mouse_pos[1] // self.CELL_SIZE
            
            highlight_rect = pygame.Rect(
                cell_x * self.CELL_SIZE,
                cell_y * self.CELL_SIZE,
                self.CELL_SIZE,
                self.CELL_SIZE
            )
            pygame.draw.rect(self.screen, (100, 100, 100), highlight_rect, 1)
        
        # UI elemanlarını çiz
        ui_x = self.GRID_WIDTH * self.CELL_SIZE + 20
        ui_y = 20
        
        # Başlık
        title_text = self.big_font.render("WoW Level Editor", True, self.UI_COLOR)
        self.screen.blit(title_text, (ui_x, ui_y - 10))
        ui_y += 40
        
        # Kaydet butonu
        save_button = pygame.Rect(ui_x, ui_y, 160, 30)
        pygame.draw.rect(self.screen, self.UI_COLOR, save_button, 2)
        save_text = self.font.render("Kaydet (Ctrl+S)", True, self.UI_COLOR)
        self.screen.blit(save_text, (ui_x + 10, ui_y + 5))
        ui_y += 40
        
        # Yükle butonu
        load_button = pygame.Rect(ui_x, ui_y, 160, 30)
        pygame.draw.rect(self.screen, self.UI_COLOR, load_button, 2)
        load_text = self.font.render("Yükle (Ctrl+O)", True, self.UI_COLOR)
        self.screen.blit(load_text, (ui_x + 10, ui_y + 5))
        ui_y += 40
        
        # Yeni butonu
        new_button = pygame.Rect(ui_x, ui_y, 160, 30)
        pygame.draw.rect(self.screen, self.UI_COLOR, new_button, 2)
        new_text = self.font.render("Yeni (Ctrl+N)", True, self.UI_COLOR)
        self.screen.blit(new_text, (ui_x + 10, ui_y + 5))
        ui_y += 50
        
        # Araç bilgisi
        tool_text = self.font.render(f"Araç: {self.get_tool_name()}", True, self.UI_COLOR)
        self.screen.blit(tool_text, (ui_x, ui_y))
        ui_y += 30
        
        # Dosya bilgisi
        file_text = self.font.render(f"Dosya: {self.file_name}", True, self.UI_COLOR)
        self.screen.blit(file_text, (ui_x, ui_y))
        ui_y += 30
        
        # Tünel bilgisi
        tunnel_text = self.font.render(f"Tüneller: L({self.tunnel_left_x},{self.tunnel_y})", True, self.TUNNEL_COLOR)
        self.screen.blit(tunnel_text, (ui_x, ui_y))
        ui_y += 20
        tunnel_text = self.font.render(f"          R({self.tunnel_right_x},{self.tunnel_y})", True, self.TUNNEL_COLOR)
        self.screen.blit(tunnel_text, (ui_x, ui_y))
        ui_y += 30
        
        # Kafes bilgisi
        cage_text = self.font.render(f"Kafes: P1({self.cage_p1_x},{self.cage_p1_y})", True, (220, 176, 73))
        self.screen.blit(cage_text, (ui_x, ui_y))
        ui_y += 20
        cage_text = self.font.render(f"       P2({self.cage_p2_x},{self.cage_p2_y})", True, (106, 117, 238))
        self.screen.blit(cage_text, (ui_x, ui_y))
        ui_y += 40
        
        # Yardım butonu - En altlta
        help_button = pygame.Rect(ui_x, self.window_height - 40, 160, 30)
        pygame.draw.rect(self.screen, self.HELP_COLOR, help_button, 2)
        help_text = self.font.render("Yardım (H)", True, self.HELP_COLOR)
        self.screen.blit(help_text, (ui_x + 10, self.window_height - 35))
        
        # Alt bilgi çubuğu
        info_y = self.GRID_HEIGHT * self.CELL_SIZE + 10
        
        # İşlem mesajı
        message_text = self.font.render(self.message, True, self.UI_COLOR)
        self.screen.blit(message_text, (10, info_y))
        
        # Yardım penceresini ayrı bir pencerede göster
        if self.show_help:
            # Yardım paneli ayrı bir panel olarak sağ tarafta
            panel_x = ui_x
            panel_y = 250  # Sabit bir yükseklikte başla
            panel_width = 230  # Daha dar yap
            panel_height = 220  # Daha kısa yap
            
            # Panel arka planı
            pygame.draw.rect(
                self.screen,
                (0, 0, 0),  # Siyah arka plan
                (panel_x, panel_y, panel_width, panel_height)
            )
            
            pygame.draw.rect(
                self.screen,
                self.HELP_COLOR,
                (panel_x, panel_y, panel_width, panel_height),
                2  # Sadece kenarlık
            )
            
            # Yardım başlığı
            help_title = self.font.render("YARDIM:", True, self.HELP_COLOR)
            self.screen.blit(help_title, (panel_x + 5, panel_y + 5))
            
            # Yardım metni - daha kısa satırlar
            help_lines = [
                "R: Sağ duvar ekle/kaldır",
                "B: Alt duvar ekle/kaldır",
                "T: Tünel konumu seç",
                "C: Kafes konumu seç",
                "Ctrl+S: Kaydet",
                "Ctrl+O: Yükle",
                "Ctrl+N: Yeni level",
                "Ctrl+1/2: Örnek level",
                "H: Yardımı aç/kapat",
                "ESC: Çıkış"
            ]
            
            y_offset = 25  # Başlıktan sonra daha az boşluk bırak
            for line in help_lines:
                line_text = self.font.render(line, True, self.HELP_COLOR)
                self.screen.blit(line_text, (panel_x + 5, panel_y + y_offset))
                y_offset += 16  # Satır aralığını azalt
                
    def get_tool_name(self):
        """Seçili aracın adını döndür"""
        if self.current_tool == "right_wall":
            return "Sağ Duvar (R)"
        elif self.current_tool == "bottom_wall":
            return "Alt Duvar (B)"
        elif self.current_tool == "tunnel":
            return "Tünel (T)"
        elif self.current_tool == "cage":
            return "Kafes (C)"
        return "?"

# Ana program
if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()