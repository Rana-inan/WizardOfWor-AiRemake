# main.py
import pygame
import sys
import random
import os
import math
import time
import psutil
from pygame.locals import *
from queue import Queue, Empty
from src.constants import Constants
from src.config_manager import ConfigManager
from src.camera_shake import CameraShake
from src.sprite_sheet import SpriteSheet
from src.character import Character
from src.bullet import Bullet, BulletTargetTypes
from src.shooting_character import ShootingCharacter
from src.simple_controls import SimpleControls, PlayerNumber, PlayerType
from src.player import Player
from src.enemy import Enemy
from src.worluk import Worluk
from src.wizard import Wizard
from src.death import Death
from src.level import Level
from src.music_manager import MusicManager
from src.ai_player import AIPlayer1, AIPlayer2, AIAction
from src.ai_controller import AIController
from src.game_manager import GameThreadManager  # 🔥 YENİ: Thread Manager
from src.message_system import MessageBus, Actor, MessageType  # 🔥 YENİ: Message System
from src.main_game_loop import MainGameLoop

class WizardOfWor:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        # Main game loop coordinator
        self.main_loop = None

        # Asset yükleme durumu - en sona ekleyin
        self.assets_loaded = False
        self.player_selection_mode = True  # Hemen menüyü aç
        
        # Sabitler
        self.SCREEN_WIDTH = 160
        self.SCREEN_HEIGHT = 114
        self.DISPLAY_OFFSET_X = 2
        self.DISPLAY_OFFSET_Y = 7
        
        # Game Over ve skor değişkenleri
        self.game_over = False
        self.game_over_timer = 0
        self.final_score_p1 = 0
        self.final_score_p2 = 0

        # Level limiti ayarları
        self.MAX_LEVELS = 10
        self.game_completed = False
        self.victory_timer = 0
        self.show_victory_screen = False

        self.movement_cooldown = 0.08
        self.player1_last_move_time = 0
        self.player2_last_move_time = 0

        # Level gösterimi için değişkenler
        self.show_level_transition = False
        self.level_transition_alpha = 0
        self.level_transition_timer = 0
        self.level_transition_duration = 3.0

        # Buton alanları için varsayılan değerler
        self.exit_button_area = pygame.Rect(0, 0, 0, 0)
        self.back_button_area = pygame.Rect(0, 0, 0, 0)

        self.speed_timer = 0.0
        self.speed_increase_interval = 15.0
        self.current_speed_level = 1.0
        self.max_speed_level = 3.0
        self.speed_increment = 0.2
        
        # Yapılandırma yükleme
        ConfigManager.load_config("config.ini")
        self.screen_scale = ConfigManager.get_config(Constants.SCREEN_SCALE, Constants.DEFAULT_SCREEN_SCALE)
        
        # Ekran ayarları
        self.screen = pygame.display.set_mode((
            self.SCREEN_WIDTH * self.screen_scale, 
            self.SCREEN_HEIGHT * self.screen_scale
        ))
        pygame.display.set_caption("Wizard of Wor")
        
        # Renkler
        self.PLAYER1_COLOR = (220, 176, 73)
        self.PLAYER2_COLOR = (106, 117, 238)
        self.BURWOR_COLOR = (106, 117, 238)
        self.GARWOR_COLOR = (220, 176, 73)
        self.THORWOR_COLOR = (177, 40, 39)
        
        self.LEVEL_DEFAULT_COLOR = (73, 81, 209)
        self.LEVEL_DOUBLE_SCORE_COLOR = (220, 176, 73)
        self.LEVEL_WORLUK_COLOR = (176, 39, 38)
        
        # Sabit değerler
        self.WORLUK_DEATH_DURATION = 5.0
        self.WORLUK_DEATH_COLOR_DURATION = 0.25
        self.WIZARD_DEATH_COLOR_DURATION = 0.5
        self.WORLUK_DEATH_COLOR = [
            (255, 175, 175), (175, 255, 255), (255, 255, 175),
            (175, 175, 255), (175, 255, 175)
        ]
        
        # Level durumları
        self.LEVEL_KILL_ENEMIES = 0
        self.LEVEL_WORLUK = 1
        self.LEVEL_WIZARD = 2
        self.LEVEL_WORLUK_DEATH = 3
        self.LEVEL_WIZARD_DEATH = 4
        self.LEVEL_WORLUK_ESCAPE = 5
        
        # Oyun zamanlaması
        self.clock = pygame.time.Clock()
        self.last_time = pygame.time.get_ticks()
        
        # Render hedefi
        self.render_target = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Oyun nesneleri
        self.current_level = None
        self.levels = []
        self.player1 = None
        self.player2 = None
        self.score_modifier = 1
        self.apply_double_score = False
        self.enemies = []
        self.deaths = []
        self.bullets = []
        self.random = random.Random()
        
        # Oyun durumu
        self.game_started = False
        self.current_stage = 0
        self.level_state = 0
        self.level_color = self.LEVEL_DEFAULT_COLOR
        self.level_background_color = (0, 0, 0)
        self.level_state_timer = 0
        self.garwor_to_spawn = 0
        self.thorwor_to_spawn = 0
        self.kill_count = 0
        self.enemies_to_kill = 0
        
        # Sprite sheets
        self.player_sheet = None
        self.burwor_sheet = None
        self.thorwor_sheet = None
        self.worluk_sheet = None
        self.wizard_sheet = None
        self.enemy_death_sheet = None
        self.player_death_sheet = None
        self.numbers_sheet = None
        
        # Ses efektleri
        self.player_shoot_sound = None
        self.level_intro_sound = None
        self.player_death_sound = None
        self.worluk_escape_sound = None
        self.worluk_death_sound = None
        self.wizard_death_sound = None
        
        # Müzik yöneticisi
        self.music_manager = MusicManager()

        self.audio_manager = None
        
        # Level başlangıç değişkenleri
        self.level_start_timer = 0
        self.level_starting = False
        
        # Kamera sarsıntısı
        CameraShake.Enabled = ConfigManager.get_config(Constants.CAMERA_SHAKE, Constants.DEFAULT_CAMERA_SHAKE)
        
        # AI kontrolcüsü
        self.ai_controller = AIController()
        SimpleControls.set_ai_controller(self.ai_controller)
        
        # Oyun modu seçimi
        self.player_selection_mode = False
        self.player_selection_timer = 0
        self.ai_selection_mode = False
        self.human_ai_selection_mode = False
        self.ai_selection_timer = 0
        self.human_ai_selection_timer = 0
        self.selected_player_mode = 0
        self.players_can_damage_each_other = False
        
        # 🔥 YENİ: Thread Management Sistemi
        self.thread_manager = None
        self.message_bus = None
        self.thread_communication_enabled = True
        
        # 🔥 YENİ: Performance Monitoring
        self.frame_count = 0
        self.performance_timer = 0.0
        self.last_performance_check = 0
        self.performance_logging_enabled = False
        
        # 🔥 YENİ: Thread için paylaşılan veri yapıları
        self.shared_render_data = {
            'players': [],
            'enemies': [],
            'bullets': [],
            'deaths': [],
            'level': None,
            'timestamp': 0
        }
        
        print("✅ WizardOfWor başlatıldı - Thread sistemi hazır")
        
    def load_assets(self):
        """Sadece menü için minimum yükleme"""
        print("🔄 Minimum asset'ler yükleniyor...")
        
        # Sadece config dosyası zaten yüklendi
        # Diğer her şeyi None olarak bırak
        
        # Sprite sheets - None
        self.player_sheet = None
        self.burwor_sheet = None
        self.thorwor_sheet = None
        self.worluk_sheet = None
        self.wizard_sheet = None
        self.enemy_death_sheet = None
        self.player_death_sheet = None
        self.numbers_sheet = None
        
        # Levels - boş liste
        self.levels = []
        
        # Ses efektleri - None
        self.player_shoot_sound = None
        self.level_intro_sound = None
        self.player_death_sound = None
        self.worluk_escape_sound = None
        self.worluk_death_sound = None
        self.wizard_death_sound = None
        
        # Thread sistemi - henüz başlatma
        self.thread_manager = None
        self.message_bus = None
        self.thread_communication_enabled = False
        
        print("✅ Menü hazır!")
        
        
    def load_game_assets(self):
        """Oyun asset'lerini hızlı yükle - sessizce"""
        if self.assets_loaded:
            return  # Zaten yüklenmişse tekrar yükleme
        
        try:
            # Sprite sheet'leri yükle - hata kontrolü ile
            self.player_sheet = SpriteSheet("assets/images/player.png", 8, 8, 4, 4)
            self.burwor_sheet = SpriteSheet("assets/images/burwor.png", 8, 8, 4, 4)
            self.thorwor_sheet = SpriteSheet("assets/images/thorwor.png", 8, 8, 4, 4)
            self.worluk_sheet = SpriteSheet("assets/images/worluk.png", 8, 8, 4, 4)
            self.wizard_sheet = SpriteSheet("assets/images/wizardofwor.png", 8, 8, 4, 4)
            self.enemy_death_sheet = SpriteSheet("assets/images/monster-death.png", 8, 8, 4, 4)
            self.player_death_sheet = SpriteSheet("assets/images/player-death.png", 8, 8, 4, 4)
            self.numbers_sheet = SpriteSheet("assets/images/numbers.png", 14, 7, 0, 0)
            
            # Level dosyalarını yükle
            self.levels = []
            self.load_all_levels()
            
            # Ses efektlerini yükle - hata durumunda devam et
            try:
                self.player_shoot_sound = pygame.mixer.Sound("assets/sounds/piou.wav")
                self.level_intro_sound = pygame.mixer.Sound("assets/sounds/intro.wav")
                self.player_death_sound = pygame.mixer.Sound("assets/sounds/death.wav")
                self.worluk_escape_sound = pygame.mixer.Sound("assets/sounds/worluk-escape.wav")
                self.worluk_death_sound = pygame.mixer.Sound("assets/sounds/worluk-kill.wav")
                self.wizard_death_sound = pygame.mixer.Sound("assets/sounds/wizard-kill.wav")
            except pygame.error:
                # Ses dosyaları yoksa sessiz devam et
                pass
            
            # Müzik yöneticisini ayarla
            sound_paths = {
                'c_long': "assets/sounds/C-long.wav",
                'g_sharp_long': "assets/sounds/G#-long.wav",
                'worluk_intro': "assets/sounds/worluk-intro.wav", 
                'worluk_loop': "assets/sounds/worluk-loop.wav"
            }
            self.music_manager.load_music_sounds(sound_paths)
            
            # Thread Management Sistemi - hızlı başlatma
            try:
                self.thread_manager = GameThreadManager()
                self.thread_manager.start_threads()
                self.audio_manager = self.thread_manager.audio_manager
                self.message_bus = MessageBus()
                self.thread_communication_enabled = True
                
                if self.audio_manager:
                    sound_files = [
                        "assets/sounds/piou.wav",
                        "assets/sounds/intro.wav", 
                        "assets/sounds/death.wav",
                        "assets/sounds/worluk-escape.wav",
                        "assets/sounds/worluk-kill.wav",
                        "assets/sounds/wizard-kill.wav"
                    ]
                    self.audio_manager.preload_sounds(sound_files)
                    
            except Exception:
                # Thread başlatma başarısızsa thread'siz devam et
                self.thread_communication_enabled = False

            self.assets_loaded = True
            
        except Exception as e:
            print(f"⚠️ Asset yükleme hatası: {e} - Varsayılan değerlerle devam ediliyor")

   

    def _initial_thread_health_check(self):
        """İlk thread sağlık kontrolü"""
        if not self.thread_manager:
            return False
        
        # 1 saniye bekle thread'lerin tamamen başlaması için
        time.sleep(1.0)
        
        threads_status = {
            'physics': self.thread_manager.physics_thread.is_alive() if self.thread_manager.physics_thread else False,
            'audio': self.thread_manager.audio_thread.is_alive() if self.thread_manager.audio_thread else False
        }
        
        alive_count = sum(threads_status.values())
        total_count = len(threads_status)
        
        print(f"📊 Thread durumu: {alive_count}/{total_count} thread aktif")
        for name, status in threads_status.items():
            status_str = "✅ ALIVE" if status else "💀 DEAD"
            print(f"  {name}: {status_str}")
        
        return alive_count >= 3  # En az 3 thread çalışıyor olmalı

    def load_all_levels(self):
        """Tüm Level dosyalarını otomatik yükle"""
        import os
        
        # Mevcut dizindeki tüm Level*.txt dosyalarını bul
        level_files = []
        for filename in os.listdir('.'):
            if filename.startswith('Level') and filename.endswith('.txt'):
                level_files.append(filename)
        
        # Doğal sıralama (Level1, Level2, Level10, Level11, ...)
        def natural_sort_key(filename):
            import re
            numbers = re.findall(r'\d+', filename)
            return int(numbers[0]) if numbers else 0
        
        level_files.sort(key=natural_sort_key)
        
        print(f"Bulunan level dosyaları: {level_files}")
        
        # Her dosyayı yükle
        for level_file in level_files:
            try:
                level = Level(level_file, 12, 10, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.random)
                self.levels.append(level)
                print(f"✓ {level_file} yüklendi")
            except Exception as e:
                print(f"✗ {level_file} yüklenemedi: {e}")
        
        print(f"Toplam {len(self.levels)} level yüklendi")
        
        # En az bir level olmalı
        if not self.levels:
            print("HATA: Hiç level yüklenemedi! Varsayılan level oluşturuluyor...")
            # Varsayılan boş level oluştur
            default_level = Level("Level1.txt", 12, 10, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.random)
            self.levels.append(default_level)

    
    def spawn_player(self, player_number, color, cage_x, cage_y):
        max_lives = ConfigManager.get_config(Constants.PLAYER_MAX_LIVES, Constants.DEFAULT_PLAYER_MAX_LIVES)
        player = Player(self.player_sheet, max_lives, self.player_shoot_sound, cage_x, cage_y, player_number)
        player.set_speed(ConfigManager.get_config(Constants.PLAYER_SPEED, Constants.DEFAULT_PLAYER_SPEED))
        player.set_animation_speed(ConfigManager.get_config(Constants.PLAYER_ANIMATION_SPEED, Constants.DEFAULT_PLAYER_ANIMATION_SPEED))
        player.set_color(color)
        
        return player
    
    def start_game(self, multiplayer):
        self.player1 = self.spawn_player(PlayerNumber.PLAYER1, self.PLAYER1_COLOR, 11, 7)
        if multiplayer:
            self.player2 = self.spawn_player(PlayerNumber.PLAYER2, self.PLAYER2_COLOR, 1, 7)
        else:
            self.player2 = None
        
        self.current_stage = 0
        self.game_completed = False
        self.show_victory_screen = False
        
        self.apply_double_score = False
        self.level_starting = False
        self.init_level()
    
    def init_level(self):

        if self.current_stage >= self.MAX_LEVELS:
            print(f"⚠️ Level limit aşıldı! current_stage={self.current_stage}, MAX_LEVELS={self.MAX_LEVELS}")
            self.complete_game()
            return
        
        # DÜZELTME: Level seçimini tüm yüklü level'lar arasından yap
        level_count = len(self.levels)
        if level_count == 0:
            print("HATA: Hiç level yok!")
            return
        
        # Level seçimi: stage numarasına göre sırayla level'ları kullan
        level_index = self.current_stage % level_count  # Tüm level'lar arasında döngü
        self.current_level = self.levels[level_index]
        
        print(f"Level {self.current_stage + 1}: {level_index + 1}. level dosyası kullanılıyor (toplam {level_count} level)")
        
        self.level_state = 0
        self.current_level.reset(self.current_stage)
        self.to_cage(self.player1)

        self.speed_timer = 0.0
        self.current_speed_level = 1.0
        
        if self.player2:
            self.to_cage(self.player2)
        
        stage = self.current_stage + 1  # Level1 için 1 olarak okunur
        self.burwors_to_spawn = ConfigManager.get_config(f"BURWORS_LEVEL_{stage}", ConfigManager.get_config(Constants.BURWARS, Constants.DEFAULT_BURWARS))
        self.garwor_to_spawn = ConfigManager.get_config(f"GARWORS_LEVEL_{stage}", 0)
        self.thorwor_to_spawn = ConfigManager.get_config(f"THORWORS_LEVEL_{stage}", 0)
        self.worluk_to_spawn = ConfigManager.get_config(f"WORLUK_LEVEL_{stage}", 0)

        self.kill_count = 0
        self.enemies_to_kill = self.burwors_to_spawn + self.garwor_to_spawn + self.thorwor_to_spawn
        
        if self.level_intro_sound:
            self.level_intro_sound.play()
        
        # Seviye geçiş efekti için başlangıç zamanı ve görüntü ayarları
        self.level_start_timer = 1.5  # Düzeltilmiş süre
        self.level_starting = True
        self.level_background_color = (0, 0, 0)
        self.show_level_transition = True
        self.level_transition_alpha = 255  # Tam opak başla
        
        if self.apply_double_score:
            self.score_modifier = 2
            self.level_color = self.LEVEL_DOUBLE_SCORE_COLOR
        else:
            self.score_modifier = 1
            self.level_color = self.LEVEL_DEFAULT_COLOR
        
        self.apply_double_score = False
    
    def start_level(self):
        burwars_count = self.burwors_to_spawn


        for i in range(burwars_count):
            self.spawn_enemy(self.burwor_sheet, self.BURWOR_COLOR, False, ConfigManager.get_config(Constants.BURWOR_SCORE, Constants.DEFAULT_BURWOR_SCORE))
        
        self.level_starting = False
        self.game_started = True
        self.music_manager.start_music(30)

        # Müziği audio thread'de başlat
        if self.audio_manager:
            self.audio_manager.play_music(
                "assets/sounds/C-long.wav",  # Ana tema
                loop=True,
                volume=0.7
            )

    def draw_level_transition(self):
        """Level geçiş ekranını çiz - Hızlandırılmış"""
        # Yarı-saydam siyah arka plan - daha hızlı fade
        transition_surface = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        transition_surface.fill((0, 0, 0, self.level_transition_alpha))
        
        # Mevcut level numarasını göster - daha büyük ve dikkat çekici
        font_big = pygame.font.SysFont("Consolas", 32, bold=True)
        current_stage = self.current_stage + 1  # 0-indexed -> 1-indexed
        level_text = font_big.render(f"LEVEL {current_stage}", True, (255, 255, 0))  # Sarı renk
        
        # Merkeze hizala
        text_rect = level_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
        
        # Text arka planını ekle (daha iyi okunurluk için)
        padding = 15
        pygame.draw.rect(
            transition_surface, 
            (0, 0, 128, 200),  # Koyu mavi, yarı-saydam
            (text_rect.left - padding, text_rect.top - padding, 
            text_rect.width + padding * 2, text_rect.height + padding * 2),
            0,  # Fill
            10   # Rounded corners
        )
        
        # Metni çiz
        transition_surface.blit(level_text, text_rect)
        
        # Ana hedef üzerine çiz
        self.render_target.blit(transition_surface, (0, 0))
    
    def spawn_enemy(self, sprite_sheet, color, can_become_invisible, score):
        enemy = Enemy(sprite_sheet, color, can_become_invisible, score)
        
        # 🔥 YENİ: Her zaman görünür başlasın!
        enemy.visible = True
        enemy._visibility_timer = 0  # Timer sıfırla
        
        # Görünmezlik ayarı - 3. seviyede hiçbir düşman görünmez olmasın
        if self.current_stage == 2:  # 3. seviye
            enemy._can_become_invisible = False  # Görünmez olma özelliğini kapat
        
        # Ateş etme özelliği ayarı (mevcut kod aynı)
        if self.current_stage <= 1:
            enemy.can_fire = False
        elif self.current_stage == 2:
            if sprite_sheet == self.burwor_sheet:
                enemy.can_fire = False
            else:
                enemy.can_fire = True
        else:
            enemy.can_fire = True
        
        # Rastgele bir başlangıç pozisyonu belirle
        enemy.move_to(self.current_level.get_random_position(avoid_player_exits=True))
        
        # Rastgele bir başlangıç yönü belirle
        tunnel_not_used = 0
        enemy.look_to(self.current_level.pick_possible_direction(enemy, tunnel_not_used))
        
        self.enemies.append(enemy)
        return enemy
    
    
    def spawn_worluk(self):
        random_position = self.current_level.get_random_position(avoid_player_exits=True)
        preferred_direction = math.copysign(1, self.current_level.pixel_width / 2 - random_position.x)
        
        if preferred_direction == 0:
            preferred_direction = self.random.choice([-1, 1])
        
        worluk = Worluk(
            self.worluk_sheet, 
            self.GARWOR_COLOR, 
            preferred_direction, 
            ConfigManager.get_config(Constants.WORLUK_SCORE, Constants.DEFAULT_WORLUK_SCORE)
        )
        
        worluk.move_to(random_position)
        tunnel_not_used = 0
        worluk.look_to(self.current_level.pick_possible_direction(worluk, tunnel_not_used))
        
        self.enemies.append(worluk)
        return worluk
    
    # main.py içindeki spawn_wizard metodunu güncelleyin:

    def spawn_wizard(self):
        wizard = Wizard(
            self.wizard_sheet, 
            self.current_level, 
            ConfigManager.get_config(Constants.WIZARD_SCORE, Constants.DEFAULT_WIZARD_SCORE)
        )
        
        # Wizard için güvenli rastgele pozisyon kullan
        wizard.move_to(wizard.get_valid_random_position())
        
        # Geçerli bir yön belirle
        wizard.look_to(wizard.get_valid_direction())
        
        self.enemies.append(wizard)
        return wizard
    
    def to_cage(self, player, timer=0):
        if player:
            if timer > 0:
                player.time_to_cage = timer
                player.visible = False
                return
           
            if player.has_lives_left():
                    player.move_to(self.current_level.get_cell_position(player.cage_position_x, player.cage_position_y))
                    player.look_to(pygame.Vector2(math.copysign(1, 5 - player.cage_position_x), 0))
                    player.set_frame(1)
                    player.visible = True
                    player.in_cage = True
                    player.time_in_cage = 0
            else:
                if self.player2:
                    if self.player1.has_lives_left() or self.player2.has_lives_left():
                            player.die()
                    else:
                            self.end_game()
                else:
                        self.end_game()
    
    def leave_cage(self, player):
        if player:
            player.in_cage = False
            player.move_to(self.current_level.get_cell_position(player.cage_position_x, player.cage_position_y - 1))
    
    def process_player_input(self, player, delta_time):
        # Ateş etme kontrolü - her basışta bir kez ateş et
        if SimpleControls.is_a_newly_pressed(player.player_number) and not player.is_firing():
            player.fire()

         # Ateş sesini audio thread'de çal
            if self.audio_manager:
                self.audio_manager.play_sound(
                    "assets/sounds/piou.wav",
                    volume=0.6
                )
            
            CameraShake.shake(2, 50, 0.1)
        
        # Hareket kontrolü - sadece grid hücresindeyse
        if not self.current_level.is_on_grid_cell(player.pixel_position_x, player.pixel_position_y):
            return
        
        is_moving = False
        just_turning = False
        can_move, tunnel = self.current_level.can_move(player.pixel_position_x, player.pixel_position_y)
        look_to = pygame.Vector2(0, 0)
        
        # DEĞIŞIKLIK: newly_pressed yerine is_down kullanarak sürekli hareket imkanı
        if SimpleControls.is_left_down(player.player_number) and can_move.left:
            look_to.x = -1
            is_moving = True
            just_turning = player.move_direction.x != -1
        
        elif SimpleControls.is_right_down(player.player_number) and can_move.right:
            look_to.x = 1
            is_moving = True
            just_turning = player.move_direction.x != 1
        
        elif SimpleControls.is_down_down(player.player_number) and can_move.down:
            look_to.y = 1
            is_moving = True
            just_turning = player.move_direction.y != 1
        
        elif SimpleControls.is_up_down(player.player_number) and can_move.up:
            look_to.y = -1
            is_moving = True
            just_turning = player.move_direction.y != -1
        
        # Tuşa basıldığında yön değiştir ve/veya hareket et
        if is_moving:
            # Önce yön değiştir
            player.look_to(look_to)
            
            # Eğer sadece yön değişimi yapmıyorsak hareket et
            if not just_turning:
                player.move(delta_time)
                player.animate(delta_time)
    
    def tunnel_teleport(self, character, tunnel):
        if tunnel != Level.NO_TUNNEL:
            # Karakteri karşı tünele ışınla - grid pozisyonuna
            new_position = self.current_level.get_tunnel_position(3 - tunnel)
            character.move_to(new_position)
    
    def check_player_death(self, player):
        if player and player.visible:
            for enemy in self.enemies:
                distance_x = abs(enemy.pixel_position_x - player.pixel_position_x)
                distance_y = abs(enemy.pixel_position_y - player.pixel_position_y)
                
                if distance_x <= 2 and distance_y <= 2:
                    self.kill_player(player)
        
    def kill_player(self, player):
        if player.is_firing():
            player.kill_bullet()
        
        player.lose_life()
        
        # Ölüm animasyonunu oyuncunun mevcut pozisyonunda oluştur
        self.deaths.append(Death(
            self.player_death_sheet, 
            player.pixel_position_x, 
            player.pixel_position_y, 
            (255, 255, 255),  # Beyaz
            player.current_rotation, 
            player.current_scale
        ))
        
        if self.player_death_sound:
            self.player_death_sound.play()
        
        CameraShake.shake(3, 50, 0.5)  # Yarım saniyelik sarsıntı
        
        # Oyuncuyu hemen görünmez yap
        player.visible = False
        
        
        # 1 saniye sonra kafese dön
        self.to_cage(player, 1.0)

        # Ölüm sesini audio thread'de çal
        if self.audio_manager:
            self.audio_manager.play_sound(
                "assets/sounds/death.wav",
                volume=0.8,
                priority=5  # Yüksek öncelik
            )
    
    def kill_enemy(self, enemy):
        enemy.die()
        if enemy.is_firing():
            enemy.kill_bullet()
        
        # WIZARD özel durumu - öldürüldüğünde wizard death state'ine geç
        if isinstance(enemy, Wizard) and self.level_state == self.LEVEL_WIZARD:
            self.level_state = self.LEVEL_WIZARD_DEATH
            self.music_manager.stop_music()
            
            if self.wizard_death_sound:
                self.wizard_death_sound.play()
            
            CameraShake.shake(4, 50, 2.0)  # 2 saniyelik sarsıntı
            self.level_state_timer = 0
            self.kill_player_bullets()
            Enemy.kill_enemy_bullet()
        
        self.enemies.remove(enemy)
    
    def test_bullet_kills_player(self, bullet, player):
        if player and player.visible and bullet.origin != player:
            if bullet.test_hit(player):
                # Eğer bir oyuncu diğerini öldürdüyse, öldüren oyuncuya puan ver
                if isinstance(bullet.origin, Player):
                    # Yanlışlıkla öldürme puanı
                    bullet.origin.increase_score(ConfigManager.get_config(
                        Constants.OTHER_PLAYER_SCORE, 
                        Constants.DEFAULT_OTHER_PLAYER_SCORE
                    ))
                    print(f"Player {bullet.origin.player_number.value + 1} accidentally killed Player {player.player_number.value + 1}!")
                
                self.kill_player(player)
                bullet.origin.kill_bullet()
                return True
        
        return False
    
    def kill_player_bullets(self):
        if self.player1:
            self.player1.kill_bullet()
        
        if self.player2:
            self.player2.kill_bullet()
    
    def next_level_phase(self):
        if self.level_state == self.LEVEL_KILL_ENEMIES:
            # Sadece 3. seviye ve sonrasında Worluk ve sonrasında Wizard çıksın
            if self.current_stage > 1:  # 0=1.seviye, 1=2.seviye, 2=3.seviye
                self.level_state = self.LEVEL_WORLUK
                self.spawn_worluk()
                self.music_manager.stop_music()
                self.music_manager.start_boss_music()
                self.level_color = self.LEVEL_WORLUK_COLOR
            else:
                self.next_level()
        
        elif self.level_state == self.LEVEL_WORLUK:
            if self.random.randint(0, 1) == 0:
                self.level_state = self.LEVEL_WIZARD
                self.spawn_wizard()
            else:
                self.level_state = self.LEVEL_WORLUK_DEATH
                self.music_manager.stop_music()
                
                if self.worluk_death_sound:
                    self.worluk_death_sound.play()
                
                CameraShake.shake(4, 50, 2.0)  # 2 saniyelik sarsıntı
                self.level_state_timer = 0
                self.kill_player_bullets()
                Enemy.kill_enemy_bullet()
        
        # ÖNEMLİ: LEVEL_WIZARD durumunda otomatik geçiş KALDIRILIYOR
        # Wizard sadece öldürüldüğünde veya oyuncuyu öldürdüğünde kaybolmalı
        # elif self.level_state == self.LEVEL_WIZARD:
        #     # Bu bölüm kaldırıldı - Wizard sadece kill_enemy() çağrıldığında ölecek
        
        elif self.level_state == self.LEVEL_WORLUK_DEATH:
            self.next_level()
        
        elif self.level_state == self.LEVEL_WIZARD_DEATH:
            self.next_level()
    
    def worluk_escape(self):
        self.music_manager.stop_music()
        
        if self.worluk_escape_sound:
            self.worluk_escape_sound.play()
        
        self.level_state_timer = 0
        self.level_state = self.LEVEL_WORLUK_ESCAPE
    
    def next_level(self):
        """Level geçiş - 10. leveldan sonra oyunu bitir"""
        # 🔥 YENİ: Level limit kontrolü
        if self.current_stage >= self.MAX_LEVELS - 1:  # 0-indexed, 9 = 10. level
            print(f"🏆 10. Level tamamlandı! Oyun bitti!")
            self.complete_game()
            return
        
        # Normal level geçiş
        self.current_stage += 1
        
        # 🔥 YENİ: Level kontrol mesajı
        print(f"📈 Level {self.current_stage + 1} başlıyor... (Kalan: {self.MAX_LEVELS - self.current_stage - 1})")
        
        self.clear_level()
        self.music_manager.stop_music()
        
        # Level geçiş efektini başlat
        self.show_level_transition = True
        self.level_transition_alpha = 255
        
        self.init_level()

    def complete_game(self):
        """Oyunu başarıyla tamamla"""
        self.clear_level()
        self.game_started = False
        self.game_completed = True
        self.show_victory_screen = True
        self.victory_timer = 10.0  # 10 saniye victory ekranı
        self.music_manager.stop_music()
        
        # AI oyuncularını durdur
        self.ai_controller.stop_all()
        
        # Final skorları kaydet
        self.final_score_p1 = self.player1.current_score if self.player1 else 0
        self.final_score_p2 = self.player2.current_score if self.player2 else 0
        
        # 🔥 YENİ: Victory müziği çal (varsa)
        try:
            victory_sound = pygame.mixer.Sound("assets/sounds/victory.wav")
            victory_sound.play()
        except:
            # Victory sesi yoksa normal intro sesini çal
            if self.level_intro_sound:
                self.level_intro_sound.play()
        
        # 🔥 YENİ: AI performans verilerini kaydet (eğer aktifse)
        if hasattr(self, 'tracking_enabled') and self.tracking_enabled:
            try:
                filename = self.ai_tracker.save_data()
                self.ai_tracker.create_performance_graphs("victory_ai_performance_graphs")
                print(f"🏁 Victory! AI performans verileri kaydedildi: {filename}")
            except Exception as e:
                print(f"❌ Victory performans kaydetme hatası: {e}")
        
        print("🎉 YOU WIN!")

    def draw_victory_screen(self):
        """Victory ekranını çiz"""
        # Ekranı temizle
        self.render_target.fill((0, 0, 0))
        
        # Font ayarları
        font_title = pygame.font.SysFont("Consolas", 16, bold=True)
        font = pygame.font.SysFont("Consolas", 12)

        
        # 🏆 VICTORY başlığı
        title_text = font_title.render("VICTORY!", False, (255, 215, 0))  # Altın rengi
        title_rect = title_text.get_rect(center=(self.SCREEN_WIDTH // 2, 35))
        self.render_target.blit(title_text, title_rect)
        
        
        # Oyuncu 1 skoru
        if self.player1:
            score_text = font.render(f"P1 FINAL SCORE: {self.final_score_p1}", False, self.PLAYER1_COLOR)
            score_rect = score_text.get_rect(center=(self.SCREEN_WIDTH // 2, 50))
            self.render_target.blit(score_text, score_rect)
        
        # Oyuncu 2 skoru (eğer varsa)
        if self.player2:
            score_text = font.render(f"P2 FINAL SCORE: {self.final_score_p2}", False, self.PLAYER2_COLOR)
            score_rect = score_text.get_rect(center=(self.SCREEN_WIDTH // 2, 65))
            self.render_target.blit(score_text, score_rect)
        
        # Toplam skor
        total_score = self.final_score_p1 + self.final_score_p2
        total_text = font.render(f"TOTAL SCORE: {total_score}", False, (255, 255, 255))
        total_rect = total_text.get_rect(center=(self.SCREEN_WIDTH // 2, 80))
        self.render_target.blit(total_text, total_rect)
        
        
        # NEAREST ölçekleme ile çiz
        scaled_target = pygame.transform.scale(
            self.render_target, 
            (self.SCREEN_WIDTH * self.screen_scale, self.SCREEN_HEIGHT * self.screen_scale))
        self.screen.blit(scaled_target, (0, 0))
        pygame.display.flip()
    
    def end_game(self):
        """Oyunu sonlandır ve Game Over ekranını göster"""
        self.clear_level()
        self.game_started = False
        self.current_stage = 0
        self.score_modifier = 1
        self.music_manager.stop_music()
        
        # AI oyuncularını durdur
        self.ai_controller.stop_all()
        
        # Game Over ekranını göster
        self.game_over = True
        self.game_over_timer = 5.0  # Game Over ekranını 5 saniye göster
        
        # Game Over müziği veya sesi çal (opsiyonel)
        if self.player_death_sound:
            self.player_death_sound.play()
        
        # Her iki oyuncunun skorunu kaydet
        self.final_score_p1 = self.player1.current_score if self.player1 else 0
        self.final_score_p2 = self.player2.current_score if self.player2 else 0
    
    def draw_game_over(self):
        """Game Over ekranını çiz - Piksel fontu ile düzeltilmiş"""
        # Ekranı temizle
        self.render_target.fill((0, 0, 0))
        
        # Font ayarları - Consolas daha net görünür ve anti-aliasing kapalı
        font_title = pygame.font.SysFont("Consolas", 18, bold=True)
        font = pygame.font.SysFont("Consolas", 14)
        
        # Game Over yazısı
        title_text = font_title.render("GAME OVER", False, (255, 0, 0))
        title_rect = title_text.get_rect(center=(self.SCREEN_WIDTH // 2, 25))
        self.render_target.blit(title_text, title_rect)
        
        # Oyuncu 1 skoru
        if self.player1:
            score_text = font.render(f"P1 SKOR: {self.final_score_p1}", False, self.PLAYER1_COLOR)
            score_rect = score_text.get_rect(left=20, top=50)
            self.render_target.blit(score_text, score_rect)
        
        # Oyuncu 2 skoru (eğer varsa)
        if self.player2:
            score_text = font.render(f"P2 SKOR: {self.final_score_p2}", False, self.PLAYER2_COLOR)
            score_rect = score_text.get_rect(left=20, top=65)
            self.render_target.blit(score_text, score_rect)
        
        # Toplam skor
        total_score = self.final_score_p1 + self.final_score_p2
        total_text = font.render(f"TOPLAM: {total_score}", False, (255, 255, 255))
        total_rect = total_text.get_rect(left=20, top=80)
        self.render_target.blit(total_text, total_rect)
        
        
        # NEAREST ölçekleme ile çiz
        scaled_target = pygame.transform.scale(
            self.render_target, 
            (self.SCREEN_WIDTH * self.screen_scale, self.SCREEN_HEIGHT * self.screen_scale))
        self.screen.blit(scaled_target, (0, 0))
        pygame.display.flip()
    
    def clear_level(self):
        self.current_level.reset(self.current_stage)
        self.enemies.clear()
        self.bullets.clear()
        self.kill_player_bullets()
        Enemy.kill_enemy_bullet()
    
    def update_enemies_spawn(self):
        if self.level_state > self.LEVEL_KILL_ENEMIES:
            self.apply_double_score = True
            self.next_level_phase()
        else:
            #Tüm düşmanlar öldüyse level biter:
            if self.kill_count == self.enemies_to_kill:
                # Level sonuna gelindi
                if self.current_stage <= 1:  # 1. ve 2. seviyede
                    self.next_level()
                else:
                    self.next_level_phase()
            else:
                if self.kill_count >= 4 - self.current_stage:
                    if self.garwor_to_spawn >= self.thorwor_to_spawn:
                        if self.garwor_to_spawn > 0:
                            # Garwor çıkart
                            # 3. seviyede (current_stage=2) görünmez olmasın
                            can_become_invisible = self.current_stage > 0 and self.current_stage != 2
                            self.spawn_enemy(
                                self.burwor_sheet, 
                                self.GARWOR_COLOR, 
                                can_become_invisible, 
                                ConfigManager.get_config(Constants.GARWOR_SCORE, Constants.DEFAULT_GARWOR_SCORE)
                            )
                            self.garwor_to_spawn -= 1
                    else:
                        if self.thorwor_to_spawn > 0:
                            # Thorwor çıkart
                            # 3. seviyede (current_stage=2) görünmez olmasın
                            can_become_invisible = self.current_stage > 0 and self.current_stage != 2
                            self.spawn_enemy(
                                self.thorwor_sheet, 
                                self.THORWOR_COLOR, 
                                can_become_invisible, 
                                ConfigManager.get_config(Constants.THORWOR_SCORE, Constants.DEFAULT_THORWOR_SCORE)
                            )
                            self.thorwor_to_spawn -= 1
    


    def draw_remaining_lives(self, player, surface):
        if player:
            remaining_lives = player.remaining_lives
            
            # DÜZELTME: time_to_cage durumunda bir can daha göster
            if player.time_to_cage > 0:
                remaining_lives += 1
            
            if player.player_number == PlayerNumber.PLAYER1:  # Sağdaki sarı oyuncu
                # En sağdaki dış duvar sütunu - yukarıdan aşağıya
                base_x = 12  # En sağdaki dış duvar sütunu
                start_y = 6  # Üstten başla
                
                positions = []
                for i in range(4):  # Maksimum 4 pozisyon
                    pos_x = base_x
                    pos_y = start_y + i
                    positions.append((pos_x, pos_y))
                    
            else:  # Soldaki mavi oyuncu (PLAYER2)
                # En soldaki dış duvar sütunu - yukarıdan aşağıya
                base_x = 0   # En soldaki dış duvar sütunu
                start_y = 6  # Üstten başla
                
                positions = []
                for i in range(4):  # Maksimum 4 pozisyon
                    pos_x = base_x
                    pos_y = start_y + i
                    positions.append((pos_x, pos_y))
            
            # DÜZELTME: Kafesteki oyuncuyu gösterme mantığını değiştir
            # Eğer oyuncu kafesteyse, kafesteki canı çizme ama yedek canları çiz
            start_idx = 0  # Her zaman 0'dan başla
            
            # Kafesteki oyuncu için bir pozisyon rezerve et
            if player.in_cage:
                # Kafesteki oyuncu zaten görünüyor, yedek canları ondan sonra çiz
                display_lives = remaining_lives
            else:
                # Kafeste değilse, tüm canları (mevcut + yedek) göster
                display_lives = remaining_lives
            
            # DEBUG: Can sayısını konsola yazdır
            print(f"Player {player.player_number.value + 1}: remaining_lives={remaining_lives}, in_cage={player.in_cage}, display_lives={display_lives}")
            
            # Yedek canları çiz - dikey dizilim
            for i in range(start_idx, min(display_lives, len(positions))):
                # Grid konumunu al
                grid_x, grid_y = positions[i]
                
                # Sınır kontrolü (grid dışına çıkmasın)
                if grid_x < 0 or grid_x >= 13 or grid_y < 0 or grid_y >= 8:
                    continue
                
                # Grid konumunu piksel konumuna çevir
                pixel_position = self.current_level.get_cell_position(grid_x, grid_y)
                
                # 🔥 MERKEZLEME DÜZELTMESİ
                # Hücre boyutu 12x10, sprite'ı hücrenin merkezine yerleştir
                x_center_offset = 6  # 12/2 = 6 piksel
                y_center_offset = 5  # 10/2 = 5 piksel
                
                # Yön belirleme (hangi tarafa bakacak)
                if player.player_number == PlayerNumber.PLAYER1:
                    dir_x = -1  # Sarı oyuncu (sağda) sola bakıyor
                else:
                    dir_x = 1   # Mavi oyuncu (solda) sağa bakıyor
                
                self.player_sheet.draw_frame(
                    1, 
                    surface, 
                    pygame.Vector2(
                        pixel_position.x + x_center_offset + self.DISPLAY_OFFSET_X, 
                        pixel_position.y + y_center_offset + self.DISPLAY_OFFSET_Y
                    ),
                    0, 
                    pygame.Vector2(dir_x, 1), 
                    player.color
                )

    def draw_score(self, surface, player, position_x):
        """Oyuncunun skorunu ve level bilgisini çizer"""
        if player:
            score = player.current_score
            color = player.color
            
            # Skor bölgesini belirle (sarı veya mavi kutu)
            if player.player_number == PlayerNumber.PLAYER1:
                # Sarı kutu - sağ alt köşe
                position = pygame.Vector2(
                    self.SCREEN_WIDTH * self.screen_scale - 15 * self.screen_scale,  # sağ kenardan 15 piksel içeride
                    self.SCREEN_HEIGHT * self.screen_scale - 20 * self.screen_scale   # alt kenardan 25 piksel yukarıda
                )
            else:
                # Mavi kutu - sol alt köşe
                position = pygame.Vector2(
                    15 * self.screen_scale,  # sol kenardan 15 piksel içeride
                    self.SCREEN_HEIGHT * self.screen_scale - 20 * self.screen_scale  # alt kenardan 25 piksel yukarıda
                )
            
            # Skor metni oluştur
            font = pygame.font.SysFont("Consolas", 48)
            score_text = font.render(str(score), False, (255, 255, 255))  # Beyaz renk
            text_rect = score_text.get_rect()
            
            # Skoru hizala
            if player.player_number == PlayerNumber.PLAYER1:
                text_rect.right = position.x  # Sağ hizalama
            else:
                text_rect.left = position.x   # Sol hizalama
            
            text_rect.centery = position.y - 10  # Skoru biraz yukarı kaydır
            
            # Skoru çiz
            surface.blit(score_text, text_rect)
            
            # Level bilgisini çiz - skor altına
            level_font = pygame.font.SysFont("Consolas", 28)
            level_text = level_font.render(f"LEVEL {self.current_stage + 1}", False, color)
            level_rect = level_text.get_rect()
            
            # Level metnini hizala - skor metninin altında
            if player.player_number == PlayerNumber.PLAYER1:
                level_rect.right = position.x  # Sağ hizalama
            else:
                level_rect.left = position.x   # Sol hizalama
            
            level_rect.top = text_rect.bottom + 5  # Skor metninin altı
            
            # Level bilgisini çiz
            surface.blit(level_text, level_rect)
            
    
    def extract_game_state_for_ai(self, player):
        """Yapay zeka için oyun durumunu hazırla"""
        if not player:
            return {}
        
        # Diğer oyuncuyu belirle
        other_player = None
        if player == self.player1 and self.player2:
            other_player = self.player2
        elif player == self.player2 and self.player1:
            other_player = self.player1
        
        # Oyuncu durumu
        game_state = {
            'player_position': (player.pixel_position_x, player.pixel_position_y),
            'player_direction': (player.move_direction.x, player.move_direction.y),
            'player_in_cage': player.in_cage,
            'is_cooperative': self.is_cooperative,  # İşbirliği/Rekabet mod bilgisi
            'enemies': [],
            'bullets': [],
            'level': self.current_level
        }
        
        # Diğer oyuncu bilgisini ekle (eğer varsa)
        if other_player:
            game_state['other_player_position'] = (other_player.pixel_position_x, other_player.pixel_position_y)
            game_state['other_player_direction'] = (other_player.move_direction.x, other_player.move_direction.y)
            game_state['other_player_in_cage'] = other_player.in_cage
        
        # Düşmanlar
        for enemy in self.enemies:
            enemy_data = {
                'position': (enemy.pixel_position_x, enemy.pixel_position_y),
                'direction': (enemy.move_direction.x, enemy.move_direction.y),
                'visible': enemy.visible
            }
            game_state['enemies'].append(enemy_data)
        
        # Mermiler
        for bullet in self.bullets:
            bullet_data = {
                'position': (bullet.pixel_position_x, bullet.pixel_position_y),
                'velocity': (bullet._velocity.x, bullet._velocity.y),
                'target_type': bullet.target_type.name
            }
            game_state['bullets'].append(bullet_data)
        
        return game_state

    def update_ai_game_state(self):
        """Yapay zeka için oyun durumunu güncelle"""
        if SimpleControls.get_player_type(PlayerNumber.PLAYER1) == PlayerType.AI and self.player1:
            game_state = self.extract_game_state_for_ai(self.player1)
            self.ai_controller.update_game_state(PlayerNumber.PLAYER1, game_state)
        
        if SimpleControls.get_player_type(PlayerNumber.PLAYER2) == PlayerType.AI and self.player2:
            game_state = self.extract_game_state_for_ai(self.player2)
            self.ai_controller.update_game_state(PlayerNumber.PLAYER2, game_state)

    def draw_player_selection(self):
        """Ana oyun modu seçim ekranını çiz"""
        # Ekranı temizle
        self.render_target.fill((0, 0, 0))
        
        # Font ayarları
        font_title = pygame.font.SysFont("Consolas", 14, bold=True)
        font = pygame.font.SysFont("Consolas", 12)
        button_font = pygame.font.SysFont("Consolas", 16, bold=True)
        
        # Başlık 
        title_text = font_title.render("WIZARD OF WOR", False, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.SCREEN_WIDTH // 2, 20))
        self.render_target.blit(title_text, title_rect)

        
         # X butonu (sağ üst köşe) 
        exit_button_size = 10  
        exit_button_x = self.SCREEN_WIDTH - exit_button_size - 1
        exit_button_y = 12
        exit_button_rect = pygame.Rect(exit_button_x, exit_button_y, exit_button_size, exit_button_size)
        
        # Buton arka planı (kırmızı kare)
        pygame.draw.rect(self.render_target, (220, 50, 50), exit_button_rect)
        # Buton çerçevesi (beyaz kenar)
        pygame.draw.rect(self.render_target, (255, 255, 255), exit_button_rect, 1)
        
        # X harfi - Daha küçük font
        button_font = pygame.font.SysFont("Consolas", 8, bold=True) 
        exit_text = button_font.render("X", False, (255, 255, 255))
        exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
        self.render_target.blit(exit_text, exit_text_rect)
        
        # Çıkış butonunun tıklanabilir alanını kaydet
        self.exit_button_area = pygame.Rect(
            exit_button_x * self.screen_scale, 
            exit_button_y * self.screen_scale, 
            exit_button_size * self.screen_scale, 
            exit_button_size * self.screen_scale
        )
        
        # Menü öğeleri
        option_color = (220, 176, 73)  # Sarımsı
        y_pos = 34
        y_spacing = 13
        
        options = [
            "F1: SOLO MODE",
            "F2: HUMAN & HUMAN",
            "F3: HUMAN & AI",
            "F4: AI & AI"
        ]
        
        left_margin = 20
        for option in options:
            option_text = font.render(option, False, option_color)
            option_rect = option_text.get_rect()
            option_rect.left = left_margin
            option_rect.top = y_pos
            self.render_target.blit(option_text, option_rect)
            y_pos += y_spacing
        
        # Yanıp sönen bilgi mesajı
        if int(self.player_selection_timer * 2) % 2 == 0:
            info_text = font.render("PRESS A BUTTON", False, (255, 255, 255))
            info_rect = info_text.get_rect(center=(self.SCREEN_WIDTH // 2, 95))
            self.render_target.blit(info_text, info_rect)
        
        # NEAREST ölçekleme ile çiz
        scaled_target = pygame.transform.scale(
            self.render_target, 
            (self.SCREEN_WIDTH * self.screen_scale, self.SCREEN_HEIGHT * self.screen_scale))
        self.screen.blit(scaled_target, (0, 0))
        pygame.display.flip()

    

    def handle_player_selection(self, delta_time):
        """Ana menü seçimini işle"""
        self.player_selection_timer += delta_time
        
        # F1: Solo Mod
        if SimpleControls.is_start_down():
            self.selected_player_mode = 1
            self.start_game_with_mode(1)
        
        # F2: İnsan vs İnsan
        elif SimpleControls.is_select_down():
            self.selected_player_mode = 2
            self.start_game_with_mode(2)
        
        # F3: Human & AI - Alt menüye git
        elif SimpleControls.is_p1_ai_toggle_down():
            self.player_selection_mode = False
            self.human_ai_selection_mode = True  # YENİ: Human & AI alt menüsüne geç
            self.human_ai_selection_timer = 0
        
        # F4: AI & AI - Alt menüye git
        elif SimpleControls.is_p2_ai_toggle_down():
            self.player_selection_mode = False
            self.ai_selection_mode = True
            self.ai_selection_timer = 0
        
        # ESC: Çıkış
        elif SimpleControls.is_escape_down():
            pygame.quit()
            sys.exit()

    def handle_audio_controls(self):
        """Audio kontrolleri (oyun sırasında)"""
        keys = pygame.key.get_pressed()
        
        if self.audio_manager:
            # Volume kontrolleri
            if keys[pygame.K_PLUS] or keys[pygame.K_EQUALS]:
                # Master volume artır
                current_vol = min(1.0, self.audio_manager.master_volume + 0.1)
                self.audio_manager.set_volume('master', current_vol)
            
            elif keys[pygame.K_MINUS]:
                # Master volume azalt
                current_vol = max(0.0, self.audio_manager.master_volume - 0.1)
                self.audio_manager.set_volume('master', current_vol)
            
            elif keys[pygame.K_m]:
                # Müziği kapat/aç
                if self.audio_manager.current_music:
                    self.audio_manager.stop_music(fade_out_time=0.5)
                else:
                    self.audio_manager.play_music("assets/sounds/C-long.wav")

    def handle_ai_selection(self, delta_time):
        """AI alt menüsü seçimini işle"""
        self.ai_selection_timer += delta_time
        
        # F1: AI1 vs AI1
        if SimpleControls.is_start_down():
            self.selected_player_mode = 4
            self.start_game_with_mode(4)
        
        # F2: AI2 vs AI2
        elif SimpleControls.is_select_down():
            self.selected_player_mode = 5
            self.start_game_with_mode(5)
        
        # F3: AI1 vs AI2 - YENİ SEÇENEK
        elif SimpleControls.is_p1_ai_toggle_down():
            self.selected_player_mode = 6
            self.start_game_with_mode(6)
        
        # ESC: Ana menüye dön
        elif SimpleControls.is_escape_down():
            self.ai_selection_mode = False
            self.player_selection_mode = True
            self.player_selection_timer = 0


    def handle_human_ai_selection(self, delta_time):
        """Human & AI alt menüsü seçimini işle"""
        self.human_ai_selection_timer += delta_time
        
        # F1: Human vs AI1
        if SimpleControls.is_start_down():
            self.selected_player_mode = 3  # Human vs AI1
            self.start_game_with_mode(3)
        
        # F2: Human vs AI2
        elif SimpleControls.is_select_down():
            self.selected_player_mode = 7  # YENİ mod numarası: Human vs AI2
            self.start_game_with_mode(7)
        
        # ESC: Ana menüye dön
        elif SimpleControls.is_escape_down():
            self.human_ai_selection_mode = False
            self.player_selection_mode = True
            self.player_selection_timer = 0

    
    def draw_human_ai_selection(self):
        """Human & AI tipleri seçim ekranını çiz"""
        # Ekranı temizle
        self.render_target.fill((0, 0, 0))
        
        # Font ayarları
        font_title = pygame.font.SysFont("Consolas", 14, bold=True)
        font = pygame.font.SysFont("Consolas", 12)
        button_font = pygame.font.SysFont("Consolas", 16, bold=True)
        
        # Başlık 
        title_text = font_title.render("HUMAN & AI MODE", False, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.SCREEN_WIDTH // 2, 20))
        self.render_target.blit(title_text, title_rect)
        
        # Geri butonu 
        back_button_width = 10  
        back_button_height = 10  
        back_button_x = 5
        back_button_y = 13
        back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
        
        # Buton arka planı (mavi kare)
        pygame.draw.rect(self.render_target, (50, 100, 220), back_button_rect)
        # Buton çerçevesi (beyaz kenar)
        pygame.draw.rect(self.render_target, (255, 255, 255), back_button_rect, 1)
        
        # <- işareti
        button_font = pygame.font.SysFont("Consolas", 10, bold=True)
        back_text = button_font.render("<", False, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_button_rect.center)
        self.render_target.blit(back_text, back_text_rect)
        
        # Geri butonunun tıklanabilir alanını kaydet
        self.back_button_area = pygame.Rect(
            back_button_x * self.screen_scale, 
            back_button_y * self.screen_scale, 
            back_button_width * self.screen_scale, 
            back_button_height * self.screen_scale
        )
        
        # Menü öğeleri
        option_color = (220, 176, 73)  # Sarımsı
        y_pos = 40
        y_spacing = 15
        
        options = [
            "F1: HUMAN & AI1",
            "F2: HUMAN & AI2"
        ]
        
        left_margin = 30
        for option in options:
            option_text = font.render(option, False, option_color)
            option_rect = option_text.get_rect()
            option_rect.left = left_margin
            option_rect.top = y_pos
            self.render_target.blit(option_text, option_rect)
            y_pos += y_spacing
        
        # Yanıp sönen bilgi mesajı
        if int(self.human_ai_selection_timer * 2) % 2 == 0:
            info_text = font.render("PRESS A BUTTON", False, (255, 255, 255))
            info_rect = info_text.get_rect(center=(self.SCREEN_WIDTH // 2, 85))
            self.render_target.blit(info_text, info_rect)
        
        # NEAREST ölçekleme ile çiz
        scaled_target = pygame.transform.scale(
            self.render_target, 
            (self.SCREEN_WIDTH * self.screen_scale, self.SCREEN_HEIGHT * self.screen_scale))
        self.screen.blit(scaled_target, (0, 0))
        pygame.display.flip()

    def draw_ai_selection(self):
        """AI tipleri seçim ekranını çiz"""
        # Ekranı temizle
        self.render_target.fill((0, 0, 0))
        
        # Font ayarları
        font_title = pygame.font.SysFont("Consolas", 14, bold=True)
        font = pygame.font.SysFont("Consolas", 12)
        button_font = pygame.font.SysFont("Consolas", 16, bold=True)
        
        # Başlık 
        title_text = font_title.render("AI & AI MODE", False, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.SCREEN_WIDTH // 2, 20))
        self.render_target.blit(title_text, title_rect)
        
        # Geri butonu 
        back_button_width = 10  # 16'dan 10'a küçültüldü  
        back_button_height = 10  # 16'dan 10'a küçültüldü
        back_button_x = 5
        back_button_y = 13
        back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
        
        # Buton arka planı (mavi kare)
        pygame.draw.rect(self.render_target, (50, 100, 220), back_button_rect)
        # Buton çerçevesi (beyaz kenar)
        pygame.draw.rect(self.render_target, (255, 255, 255), back_button_rect, 1)
        
        # <- işareti - Daha küçük font
        button_font = pygame.font.SysFont("Consolas", 10, bold=True)  # Font boyutu 16'dan 10'a düşürüldü
        back_text = button_font.render("<", False, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_button_rect.center)
        self.render_target.blit(back_text, back_text_rect)
        
        # Geri butonunun tıklanabilir alanını kaydet
        self.back_button_area = pygame.Rect(
            back_button_x * self.screen_scale, 
            back_button_y * self.screen_scale, 
            back_button_width * self.screen_scale, 
            back_button_height * self.screen_scale
        )
        
        # Menü öğeleri
        option_color = (220, 176, 73)  # Sarımsı
        y_pos = 40
        y_spacing = 15
        
        options = [
            "F1: AI1 & AI1",
            "F2: AI2 & AI2",
            "F3: AI1 & AI2"
        ]
        
        left_margin = 30
        for option in options:
            option_text = font.render(option, False, option_color)
            option_rect = option_text.get_rect()
            option_rect.left = left_margin
            option_rect.top = y_pos
            self.render_target.blit(option_text, option_rect)
            y_pos += y_spacing
        
        # Yanıp sönen bilgi mesajı
        if int(self.ai_selection_timer * 2) % 2 == 0:
            info_text = font.render("PRESS A BUTTON", False, (255, 255, 255))
            info_rect = info_text.get_rect(center=(self.SCREEN_WIDTH // 2, 95))
            self.render_target.blit(info_text, info_rect)
        
        # NEAREST ölçekleme ile çiz
        scaled_target = pygame.transform.scale(
            self.render_target, 
            (self.SCREEN_WIDTH * self.screen_scale, self.SCREEN_HEIGHT * self.screen_scale))
        self.screen.blit(scaled_target, (0, 0))
        pygame.display.flip()
    
    def start_game_with_mode(self, mode):
        """Belirli bir modda oyunu başlat"""

        # 🔥 OYUN BAŞLARKEN ASSET'LERİ YÜKLE
        if not self.assets_loaded:
            self.load_game_assets()
        
        # Daha önce çalışan oyunu temizle
        if self.game_started:
            self.end_game()
        
        # AI kontrolcüsünü sıfırla
        self.ai_controller.stop_all()

        # Daha önce çalışan oyunu temizle
        if self.game_started:
            self.end_game()
        
        # AI kontrolcüsünü sıfırla
        self.ai_controller.stop_all()
        
        # Modu ayarla ve oyunu başlat
        if mode == 1:  # Solo
            SimpleControls.set_player_type(PlayerNumber.PLAYER1, PlayerType.HUMAN)
            self.start_game(multiplayer=False)  # İkinci oyuncu yok
            
        elif mode == 2:  # İnsan vs İnsan
            SimpleControls.set_player_type(PlayerNumber.PLAYER1, PlayerType.HUMAN)
            SimpleControls.set_player_type(PlayerNumber.PLAYER2, PlayerType.HUMAN)
            self.start_game(multiplayer=True)
            
        elif mode == 3:  # İnsan vs AI
            SimpleControls.set_player_type(PlayerNumber.PLAYER1, PlayerType.HUMAN)
            SimpleControls.set_player_type(PlayerNumber.PLAYER2, PlayerType.AI)
            self.start_game(multiplayer=True)
            self.ai_controller.start_ai_player(PlayerNumber.PLAYER2, ai_type="AI1")  # Varsayılan AI1
            
        elif mode == 4:  # AI1 vs AI1
            SimpleControls.set_player_type(PlayerNumber.PLAYER1, PlayerType.AI)
            SimpleControls.set_player_type(PlayerNumber.PLAYER2, PlayerType.AI)
            self.start_game(multiplayer=True)
            self.ai_controller.start_ai_player(PlayerNumber.PLAYER1, ai_type="AI1")
            self.ai_controller.start_ai_player(PlayerNumber.PLAYER2, ai_type="AI1")
            
        elif mode == 5:  # AI2 vs AI2
            SimpleControls.set_player_type(PlayerNumber.PLAYER1, PlayerType.AI)
            SimpleControls.set_player_type(PlayerNumber.PLAYER2, PlayerType.AI)
            self.start_game(multiplayer=True)
            self.ai_controller.start_ai_player(PlayerNumber.PLAYER1, ai_type="AI2")
            self.ai_controller.start_ai_player(PlayerNumber.PLAYER2, ai_type="AI2")
        
        elif mode == 6:  # AI1 vs AI2 
            SimpleControls.set_player_type(PlayerNumber.PLAYER1, PlayerType.AI)
            SimpleControls.set_player_type(PlayerNumber.PLAYER2, PlayerType.AI)
            self.start_game(multiplayer=True)
            self.ai_controller.start_ai_player(PlayerNumber.PLAYER1, ai_type="AI1")
            self.ai_controller.start_ai_player(PlayerNumber.PLAYER2, ai_type="AI2")
        
        elif mode == 7:  # İnsan vs AI2
            SimpleControls.set_player_type(PlayerNumber.PLAYER1, PlayerType.HUMAN)
            SimpleControls.set_player_type(PlayerNumber.PLAYER2, PlayerType.AI)
            self.start_game(multiplayer=True)
            self.ai_controller.start_ai_player(PlayerNumber.PLAYER2, ai_type="AI2")
        
        # Tüm menü modlarını kapat
        self.player_selection_mode = False
        self.ai_selection_mode = False
        self.human_ai_selection_mode = False  
        
        # DEĞIŞIKLIK: Oyuncular yanlışlıkla birbirlerini öldürebilsin
        self.players_can_damage_each_other = True  

    def update(self, delta_time):

         # 🔥 YENİ: Victory ekranı kontrolü
        if self.show_victory_screen:
            self.victory_timer -= delta_time
            if self.victory_timer <= 0 or any(pygame.key.get_pressed()):
                self.show_victory_screen = False
                self.game_completed = False
                self.player_selection_mode = True
                self.player_selection_timer = 0
                self.ai_selection_mode = False
                self.current_stage = 0  # Stage'i sıfırla
            return
        
        # Game Over ekranını göster
        if self.game_over:
            self.game_over_timer -= delta_time
            if self.game_over_timer <= 0 or any(pygame.key.get_pressed()):
                self.game_over = False
                self.player_selection_mode = True
                self.player_selection_timer = 0
                self.ai_selection_mode = False  # AI seçim menüsü kapalı
            return
        
        # Oyun modu seçim ekranı
        if self.player_selection_mode:
            self.handle_player_selection(delta_time)
            return
        
        # Human & AI tipi seçim ekranı - YENİ
        if self.human_ai_selection_mode:
            self.handle_human_ai_selection(delta_time)
            return
        
        # AI tipi seçim ekranı
        if self.ai_selection_mode:
            self.handle_ai_selection(delta_time)
            return
        
         # Audio kontrolleri
        if self.game_started:
            self.handle_audio_controls()
            
       
        # Kamera sarsıntısını güncelle
        CameraShake.update(delta_time)
        
            # Level durumuna göre güncelleme
        if self.level_state == self.LEVEL_WORLUK_DEATH:
            self.update_worluk_death(delta_time)
        elif self.level_state == self.LEVEL_WIZARD_DEATH:
            self.update_wizard_death(delta_time)
        elif self.level_state == self.LEVEL_WORLUK_ESCAPE:
            self.update_worluk_escape(delta_time)
        else:
            # Normal seviye güncelleme
            if self.level_starting:
                self.level_start_timer -= delta_time
                
                # Sadece timer kontrolü - alpha'yı ayrı hesapla
                if self.level_start_timer <= 0:
                    self.show_level_transition = False
                    self.start_level()
                elif self.show_level_transition:
                    # Timer henüz bitmemişse alpha'yı güncelle
                    progress = max(0, self.level_start_timer / 1.5)
                    self.level_transition_alpha = int(255 * progress)

            else:
                # Oyun sırasında F tuşlarıyla oyuncu tiplerini değiştir
                if self.game_started:
                    if SimpleControls.is_p1_ai_toggle_down():
                        current_type = SimpleControls.get_player_type(PlayerNumber.PLAYER1)
                        new_type = PlayerType.HUMAN if current_type == PlayerType.AI else PlayerType.AI
                        SimpleControls.set_player_type(PlayerNumber.PLAYER1, new_type)
                        
                        if new_type == PlayerType.AI:
                            self.ai_controller.start_ai_player(PlayerNumber.PLAYER1)
                        else:
                            self.ai_controller.stop_ai_player(PlayerNumber.PLAYER1)
                    
                    if SimpleControls.is_p2_ai_toggle_down() and self.player2:
                        current_type = SimpleControls.get_player_type(PlayerNumber.PLAYER2)
                        new_type = PlayerType.HUMAN if current_type == PlayerType.AI else PlayerType.AI
                        SimpleControls.set_player_type(PlayerNumber.PLAYER2, new_type)
                        
                        if new_type == PlayerType.AI:
                            self.ai_controller.start_ai_player(PlayerNumber.PLAYER2)
                        else:
                            self.ai_controller.stop_ai_player(PlayerNumber.PLAYER2)
                
                if self.game_started and not self.level_starting:
                    # 🔥 YENİ: Hızlanma sayacını güncelle
                    self.speed_timer += delta_time
                    
                    # 10 saniye doldu mu kontrol et
                    if self.speed_timer >= self.speed_increase_interval:
                        self.increase_enemy_speed()
                        self.speed_timer = 0.0  # Sayacı sıfırla

                # Çıkış kontrolü
                if SimpleControls.is_escape_down():
                    pygame.quit()
                    sys.exit()
                
                # Hile kontrolü
                if SimpleControls.is_cheat_kill_down() and self.game_started and self.enemies:
                    self.kill_enemy(self.enemies[0])
                    self.kill_count += 1
                    self.update_enemies_spawn()
                
                if self.game_started:
                    # Level güncelleme
                    self.current_level.update(delta_time)
                    
                    # Oyuncu güncelleme
                    self.update_player_to_cage(self.player1, delta_time)
                    self.update_player_to_cage(self.player2, delta_time)
                    
                    self.update_player_in_cage(self.player1, delta_time)
                    self.update_player_in_cage(self.player2, delta_time)
                    
                    # Düşman güncelleme
                    self.update_enemies(delta_time)
                    
                    # Oyuncu ölüm kontrolü
                    self.check_player_death(self.player1)
                    self.check_player_death(self.player2)
                    
                    # Mermi güncelleme
                    self.update_bullets(delta_time)
                    
                    # Müzik güncelleme
                    self.music_manager.update(delta_time, self.current_level.current_threshold)
                    
                    # AI oyuncuları için oyun durumunu güncelle
                    self.update_ai_game_state()
                    self.ai_controller.update_key_states
        
                    # Ölüm animasyonlarını güncelle
                    self.update_deaths(delta_time)

    def increase_enemy_speed(self):
            """Düşmanların hızını artır"""
            # Maksimum hıza ulaştıysak artırma
            if self.current_speed_level >= self.max_speed_level:
                return
            
            # Hız seviyesini artır
            self.current_speed_level += self.speed_increment
            
            # Maksimum hızı aşmasın
            if self.current_speed_level > self.max_speed_level:
                self.current_speed_level = self.max_speed_level
            
            # Bildirimi göster
            self.speed_change_notification = f"DÜŞMANLAR HIZLANDI! x{self.current_speed_level:.1f}"
            self.speed_notification_timer = 2.0
            
            # Ses efekti çal (varsa)
            if self.level_intro_sound:
                self.level_intro_sound.play()
            
            print(f"Düşman hızı artırıldı: x{self.current_speed_level}")

    def handle_mouse_event(self, pos, button):
        """Fare tıklama olaylarını işle"""
        # Ana menüdeyken çıkış butonuna tıklama
        if self.player_selection_mode and hasattr(self, 'exit_button_area'):
            if self.exit_button_area.collidepoint(pos):
                pygame.quit()
                sys.exit()
        
         # Human & AI alt menüsündeyken geri butonuna tıklama - YENİ
        if self.human_ai_selection_mode and hasattr(self, 'back_button_area'):
            if self.back_button_area.collidepoint(pos):
                self.human_ai_selection_mode = False
                self.player_selection_mode = True
                self.player_selection_timer = 0
        
        # AI alt menüsündeyken geri butonuna tıklama
        if self.ai_selection_mode and hasattr(self, 'back_button_area'):
            if self.back_button_area.collidepoint(pos):
                self.ai_selection_mode = False
                self.player_selection_mode = True
                self.player_selection_timer = 0
    
    def update_worluk_death(self, delta_time):
        self.level_state_timer += delta_time
        color_index = int(self.level_state_timer / self.WORLUK_DEATH_COLOR_DURATION) % len(self.WORLUK_DEATH_COLOR)
        background_color = self.WORLUK_DEATH_COLOR[color_index]
        color_alpha = self.level_state_timer / self.WORLUK_DEATH_COLOR_DURATION - int(self.level_state_timer / self.WORLUK_DEATH_COLOR_DURATION)
        background_color = (
            int(background_color[0] * color_alpha),
            int(background_color[1] * color_alpha),
            int(background_color[2] * color_alpha)
        )
        self.level_background_color = background_color
        
        # HIZLANDIRILDI: Ses süresini beklemek yerine kısa bir süre bekle
        if self.level_state_timer > 1.0:  # Ses süresini beklemek yerine 1 saniye
            self.next_level_phase()
    
    def update_wizard_death(self, delta_time):
        self.level_state_timer += delta_time
        color_value = self.level_state_timer / self.WIZARD_DEATH_COLOR_DURATION - int(self.level_state_timer / self.WIZARD_DEATH_COLOR_DURATION)
        self.level_color = (int(color_value * 255), int(color_value * 255), int(color_value * 255))
        
        # HIZLANDIRILDI: Ses süresini beklemek yerine kısa bir süre bekle
        if self.level_state_timer > 1.0:  # Ses süresini beklemek yerine 1 saniye
            self.next_level_phase()
    
    def update_worluk_escape(self, delta_time):
        self.level_state_timer += delta_time
        # HIZLANDIRILDI: Ses süresini beklemek yerine kısa bir süre bekle
        if self.level_state_timer > 0.8:  # Ses süresini beklemek yerine 0.8 saniye
            self.next_level()
    
    def update_player_to_cage(self, player, delta_time):
        if player and player.time_to_cage > 0:
            player.time_to_cage -= delta_time
            if player.time_to_cage <= 0:
                self.to_cage(player)
    

    def update_player_in_cage(self, player, delta_time):
        if player:
            if player.in_cage:
                player.time_in_cage += delta_time
                cage_time = ConfigManager.get_config(Constants.PLAYER_TIME_IN_CAGE, Constants.DEFAULT_PLAYER_TIME_IN_CAGE)
                if (SimpleControls.is_any_move_key_down(player.player_number) and not self.level_starting) or player.time_in_cage >= cage_time:
                    self.leave_cage(player)
            else:
                if player.visible:
                    # Grid bazlı hareket için son hareket zamanını kontrol et
                    last_move_time = self.player1_last_move_time if player.player_number == PlayerNumber.PLAYER1 else self.player2_last_move_time
                    current_time = pygame.time.get_ticks() / 1000.0
                    
                    if current_time - last_move_time >= self.movement_cooldown:
                        self.process_player_input(player, delta_time)
                        
                        # Son hareket zamanını güncelle
                        if player.player_number == PlayerNumber.PLAYER1:
                            self.player1_last_move_time = current_time
                        else:
                            self.player2_last_move_time = current_time
    
    def update_enemies(self, delta_time):
        for enemy in self.enemies[:]:
            enemy.update(delta_time)
            
            # Orijinal hızı al
            base_speed = enemy._threshold_speeds[self.current_level.current_threshold]  
            # Hız çarpanını uygula
            new_speed = base_speed * self.current_speed_level
            enemy.set_speed(new_speed)
            enemy.set_animation_speed(new_speed)
            
            # 🔥 DÜZELTİLMİŞ: Tünel kontrolü
            tunnel = Level.NO_TUNNEL  # Varsayılan değer
            
            if isinstance(enemy, Wizard):
                # Wizard özel hareket kontrolü
                enemy.can_change_direction = True
                
                if not enemy.is_valid_position(enemy.pixel_position_x, enemy.pixel_position_y):
                    safe_position = enemy.get_valid_random_position()
                    enemy.move_to(safe_position)
                    enemy.look_to(enemy.get_valid_direction())
                
                new_move_direction = enemy.move_direction
            else:
                # 🔥 YENİ: Tuple return ile tunnel değerini al
                new_move_direction, tunnel = self.current_level.pick_possible_direction_with_tunnel(enemy)
                enemy.look_to(new_move_direction)
            
            # 🔥 DÜZELTİLMİŞ: Tünel kontrolü - artık tunnel değeri doğru
            if not isinstance(enemy, Wizard):
                print(f"🔍 Enemy at ({enemy.pixel_position_x}, {enemy.pixel_position_y}), direction: {new_move_direction}, tunnel: {tunnel}")
                
                if (new_move_direction.x > 0 and tunnel == Level.TUNNEL_RIGHT) or \
                   (new_move_direction.x < 0 and tunnel == Level.TUNNEL_LEFT):
                    
                    print(f"🕳️ {enemy.__class__.__name__} tüneli kullanıyor! Tunnel: {tunnel}")
                    
                    if isinstance(enemy, Worluk):
                        print("🏃 Worluk kaçıyor!")
                        enemy.die()
                        self.enemies.remove(enemy)
                        self.worluk_escape()
                    else:
                        print(f"↔️ {enemy.__class__.__name__} teleport ediliyor!")
                        self.tunnel_teleport(enemy, tunnel)
                else:
                    enemy.move(delta_time)
            else:
                # Wizard için özel hareket
                enemy.move(delta_time)
            
            enemy.animate(delta_time)
            
            # Ateş etme kontrolü
            if enemy.can_fire_at_player(self.player1):
                enemy.fire()
            
            if self.player2 and enemy.can_fire_at_player(self.player2):
                enemy.fire()
            
            # Görünürlük güncellemesi
            enemy.update_visible(self.player1)
            enemy.update_visible(self.player2)
    
    
    
    def update_deaths(self, delta_time):
        for death in self.deaths[:]:
            death.update(delta_time)
            if not death.enabled:
                self.deaths.remove(death)
    
    def test_thread_communication(self):
        """Thread iletişimini test et"""
        print("\n" + "="*50)
        print("🧪 THREAD COMMUNICATION TEST")
        print("="*50)
        
        # 1. Temel kontroller
        print(f"Thread communication enabled: {self.thread_communication_enabled}")
        print(f"Thread manager exists: {self.thread_manager is not None}")
        
        if not self.thread_communication_enabled:
            print("❌ Thread communication kapalı!")
            return
        
        if not self.thread_manager:
            print("❌ Thread manager yok!")
            return
        
        # 2. Thread durumları
        print("\n📊 Thread Status:")
        threads = {
            'Physics': self.thread_manager.physics_thread,
            'Audio': self.thread_manager.audio_thread
        }
        
        for name, thread in threads.items():
            if thread:
                status = "✅ ALIVE" if thread.is_alive() else "💀 DEAD"
                print(f"  {name}: {status}")
            else:
                print(f"  {name}: ❌ NOT_CREATED")
        
        # 3. Queue test
        print("\n📦 Queue Test:")
        try:
            # Test physics queue
            test_data = {
                'type': 'test',
                'message': 'Hello from main thread!',
                'timestamp': time.time()
            }
            
            self.thread_manager.physics_queue.put(test_data, block=False)
            print("✅ Physics queue: Test data sent")
            
            # Test audio queue  
            self.thread_manager.audio_queue.put(test_data, block=False)
            print("✅ Audio queue: Test data sent")
            
            
        except Exception as e:
            print(f"❌ Queue test failed: {e}")
        
        # 4. Game state test
        print("\n🎮 Game State:")
        print(f"  Game started: {self.game_started}")
        print(f"  Bullets count: {len(self.bullets) if hasattr(self, 'bullets') else 'No bullets'}")
        print(f"  Enemies count: {len(self.enemies) if hasattr(self, 'enemies') else 'No enemies'}")
        print(f"  Current stage: {self.current_stage}")
        
        # 5. update_bullets test
        print("\n🔫 Bullet System Test:")
        if hasattr(self, 'bullets') and len(self.bullets) > 0:
            print(f"  Active bullets: {len(self.bullets)}")
            for i, bullet in enumerate(self.bullets):
                if bullet:
                    print(f"    Bullet {i}: pos=({bullet.pixel_position_x}, {bullet.pixel_position_y})")
            
            # Manual physics data send test
            print("  Testing manual physics data send...")
            try:
                self._send_physics_data()
                print("  ✅ Manual physics data sent")
            except Exception as e:
                print(f"  ❌ Manual physics data failed: {e}")
        else:
            print("  No active bullets to test")
        
        print("="*50 + "\n")

    
    
    def update_bullets(self, delta_time):
        """Mermileri güncelle - Thread entegrasyonu ile [FIXED VERSION]"""
        self.bullets.clear()
        
        # Oyuncu mermilerini ekle  
        if self.player1 and self.player1.is_firing():
            self.bullets.append(self.player1.bullet)
        
        if self.player2 and self.player2.is_firing():
            self.bullets.append(self.player2.bullet)
        
        # Düşman mermisini ekle
        if Enemy.is_any_enemy_firing():
            self.bullets.append(Enemy._common_bullet)
        
        # 🔥 DEBUG: Bullet durumu
        if len(self.bullets) > 0:
            print(f"🔫 BULLETS: {len(self.bullets)} active bullets detected")
        
        # Eğer mermi yoksa hiçbir şey yapma
        if not self.bullets:
            return
        
        # Thread kullanımı durumu kontrolü
        use_threaded_physics = (
            self.thread_communication_enabled and 
            self.thread_manager and 
            len(self.bullets) > 0
        )
        
        # 🔥 DEBUG: Thread kullanım kararı
        print(f"🔧 THREAD DECISION:")
        print(f"  thread_communication_enabled: {self.thread_communication_enabled}")
        print(f"  thread_manager exists: {self.thread_manager is not None}")
        print(f"  bullets count: {len(self.bullets)}")
        print(f"  USE THREADED PHYSICS: {use_threaded_physics}")
        
        if use_threaded_physics:
            print("🚀 USING THREADED PHYSICS PATH")  # Bu mesajı görmeli!
            
            # 1. Mermileri güncelle (pozisyon)
            for bullet in self.bullets[:]:
                bullet.update(delta_time)
                
                # Sadece temel sınır kontrolü main thread'de
                if not self.current_level.is_inside_walls(bullet.pixel_position_x, bullet.pixel_position_y):
                    bullet.origin.kill_bullet()
                    print("💥 Bullet hit wall (main thread)")
                    continue
            
            # 2. Physics thread'e çarpışma hesaplaması gönder
            if self.bullets:
                print("📤 Sending physics data to thread...")  # Bu mesajı görmeli!
                self._send_physics_data()
            
            # 3. Physics thread sonuçlarını al ve uygula
            print("📥 Checking for physics results...")
            with self.thread_manager.physics_lock:
                if self.thread_manager.physics_results:
                    print("🎯 Applying physics results from thread...")
                    self._apply_physics_results(self.thread_manager.physics_results)
                    self.thread_manager.physics_results = None
                else:
                    print("⏳ No physics results ready yet")
        else:
            print("🔄 USING CLASSIC PHYSICS PATH (fallback)")
            # Fallback: Klasik yöntem
            self._update_bullets_classic(delta_time)
    
    
    
    def draw(self):

        # Victory ekranı
        if self.show_victory_screen:
            self.draw_victory_screen()
            return
        
        # Game Over ekranı
        if self.game_over:
            self.draw_game_over()
            return
        
        # Oyuncu seçim ekranı
        if self.player_selection_mode:
            self.draw_player_selection()
            return
        
        # AI seçim ekranı
        if self.ai_selection_mode:
            self.draw_ai_selection()
            return
        
            # Human & AI seçim ekranı - YENİ
        if self.human_ai_selection_mode:
            self.draw_human_ai_selection()
            return

        # Render hedefini temizle - SİYAH ARKAPLAN
        self.render_target.fill((0, 0, 0))  # Siyah arkaplan
        
        # Level varsa çiz
        if self.current_level:
            # Level arka plan rengini siyah bırak, çizimi ekle
            self.render_target.blit(
                self.current_level._render_target,
                (self.DISPLAY_OFFSET_X, self.DISPLAY_OFFSET_Y)
            )
            
            # Tünelleri çiz
            self.current_level.draw_tunnels(
                self.level_color,  
                self.render_target, 
                self.DISPLAY_OFFSET_X, 
                self.DISPLAY_OFFSET_Y
            )
            
            

            if self.game_started:
                # Oyuncuları çiz
                if self.player1 and self.player1.is_alive:
                    self.player1.draw(self.render_target, self.DISPLAY_OFFSET_X, self.DISPLAY_OFFSET_Y)
                
                if self.player2 and self.player2.is_alive:
                    self.player2.draw(self.render_target, self.DISPLAY_OFFSET_X, self.DISPLAY_OFFSET_Y)
                
                # Düşmanları çiz
                for enemy in self.enemies:
                    enemy.draw(self.render_target, self.DISPLAY_OFFSET_X, self.DISPLAY_OFFSET_Y)

                if self.show_level_transition:
                    self.draw_level_transition()
                
                # Mermileri çiz
                for bullet in self.bullets:
                    bullet.draw(self.render_target, self.DISPLAY_OFFSET_X, self.DISPLAY_OFFSET_Y)
                
                # Ölüm animasyonlarını çiz
                for death in self.deaths:
                    death.draw(self.render_target, self.DISPLAY_OFFSET_X, self.DISPLAY_OFFSET_Y)
                
                # Kalan canları göster
                self.draw_remaining_lives(self.player1, self.render_target)
                self.draw_remaining_lives(self.player2, self.render_target)
                
                # Radar göster 
                self.current_level.draw_radar(self.enemies, self.render_target)
        
        # Ana ekrana çiz (kamera sarsıntı efekti ile)
        offset = CameraShake.get_offset()
        scaled_rect = pygame.Rect(
            int(offset.x), 
            int(offset.y), 
            self.SCREEN_WIDTH * self.screen_scale, 
            self.SCREEN_HEIGHT * self.screen_scale
        )
        
        self.screen.fill((0, 0, 0))
        self.screen.blit(pygame.transform.scale(self.render_target, scaled_rect.size), scaled_rect.topleft)
        
        # Skorları göster
        self.draw_score(self.screen, self.player1, 280)
        self.draw_score(self.screen, self.player2, 89)
        
        # Ekranı güncelle
        pygame.display.flip()
    
    def _check_thread_health(self):
        """Thread'lerin sağlıklı çalışıp çalışmadığını kontrol et"""
        if not self.thread_manager:
            return True
        
        try:
            # Thread'lerin yaşayıp yaşamadığını kontrol et
            threads_status = {
                'physics': self.thread_manager.physics_thread.is_alive() if self.thread_manager.physics_thread else False,
                'audio': self.thread_manager.audio_thread.is_alive() if self.thread_manager.audio_thread else False
            }
            
            # Ölü thread varsa uyar
            dead_threads = [name for name, alive in threads_status.items() if not alive]
            if dead_threads:
                print(f"💀 Ölü thread'ler: {dead_threads}")
                return False
            
            # Queue overflow kontrolü
            if hasattr(self.thread_manager, 'render_queue'):
                queue_sizes = {
                    'physics': self.thread_manager.physics_queue.qsize(),
                    'audio': self.thread_manager.audio_queue.qsize()
                }
                
                # Queue overflow uyarısı
                for queue_name, size in queue_sizes.items():
                    if size > 20:  # 20'den fazla item uyarısı
                        print(f"⚠️ Queue overflow: {queue_name} = {size} items")
                        # Kritik overflow durumunda queue'yu temizle
                        if size > 50:
                            self._emergency_queue_cleanup(queue_name)
            
            return True
            
        except Exception as e:
            print(f"❌ Thread sağlık kontrolü hatası: {e}")
            return False
    
    def _emergency_queue_cleanup(self, queue_name):
        """Acil durum queue temizleme"""
        try:
            if queue_name == 'render' and hasattr(self.thread_manager, 'render_queue'):
                # Render queue'dan eski verileri temizle
                cleared_count = 0
                while self.thread_manager.render_queue.qsize() > 5:
                    try:
                        self.thread_manager.render_queue.get(block=False)
                        cleared_count += 1
                    except:
                        break
                print(f"🧹 Emergency cleanup: {cleared_count} items removed from {queue_name} queue")
        except Exception as e:
            print(f"❌ Emergency cleanup failed: {e}")
        
    def _process_thread_communications(self, delta_time):
        """Thread'lerden gelen verileri işle"""
        try:
            if not self.thread_manager:
                return
            
            # Physics thread sonuçlarını işle
            with self.thread_manager.physics_lock:
                if self.thread_manager.physics_results:
                    self._apply_physics_results(self.thread_manager.physics_results)
                    # İşlendikten sonra temizle
                    self.thread_manager.physics_results = None
            
            # AI thread'lerden gelen action'ları işle (mevcut kod)
            if hasattr(self, 'ai_controller'):
                self.ai_controller.update_key_states()
        
        except Exception as e:
            print(f"❌ Thread iletişim hatası: {e}")
    
    def _send_data_to_threads(self):
        """Thread'lere veri gönder"""
        try:
            if not self.thread_manager:
                return
            
            # Render verilerini gönder
            if self.game_started and hasattr(self.thread_manager, 'render_queue'):
                self._send_render_data()
            
            # Physics verilerini gönder
            if self.game_started and self.bullets and hasattr(self.thread_manager, 'physics_queue'):
                self._send_physics_data()
            
            # Audio komutlarını gönder
            if hasattr(self.thread_manager, 'audio_queue'):
                self._send_audio_commands()
        
        except Exception as e:
            print(f"❌ Thread veri gönderme hatası: {e}")


    def _send_physics_data(self):
        """Physics verilerini thread'e gönder"""
        try:
            if not self.bullets:
                return
                    
            physics_data = {
                'type': 'collision_check',
                'bullets': [bullet for bullet in self.bullets if bullet],
                'players': [p for p in [self.player1, self.player2] if p and p.visible],
                'enemies': [e for e in self.enemies if e and e.visible],
                'level': self.current_level,
                'timestamp': time.time()
            }
            
            # 🔥 DEBUG: Physics gönderimi logla
            print(f"🚀 PHYSICS: Sending {len(physics_data['bullets'])} bullets, {len(physics_data['enemies'])} enemies")
            
            try:
                self.thread_manager.physics_queue.put(physics_data, block=False)
                print(f"✅ PHYSICS: Data sent to thread")
            except:
                print(f"⚠️ PHYSICS: Queue full, trying to clear...")
                try:
                    self.thread_manager.physics_queue.get(block=False)
                    self.thread_manager.physics_queue.put(physics_data, block=False)
                    print(f"✅ PHYSICS: Data sent after queue clear")
                except:
                    print(f"❌ PHYSICS: Could not send data")
                        
        except Exception as e:
            print(f"❌ Physics data gönderme hatası: {e}")
    
    
    
    def _send_audio_commands(self):
        """Audio komutlarını thread'e gönder (isteğe bağlı)"""
        # Bu method gelecekte ses komutları için kullanılabilir
        pass


    def _apply_physics_results(self, physics_results):
        """Physics thread sonuçlarını uygula"""
        try:
            if 'collisions' in physics_results:
                collision_count = len(physics_results['collisions'])
                print(f"🎯 PHYSICS: Received {collision_count} collisions from thread")
                
                for collision in physics_results['collisions']:
                    print(f"💥 COLLISION: {collision['type']}")
                    self._handle_threaded_collision(collision)
                    
        except Exception as e:
            print(f"❌ Physics sonuç uygulama hatası: {e}")

    def _handle_threaded_collision(self, collision):
        """Thread'den gelen çarpışmayı OYUN LOGİĞİNE uygula"""
        try:
            collision_type = collision['type']
            
            if collision_type == 'bullet_wall':
                bullet = collision['bullet']
                if bullet and bullet.origin:
                    bullet.origin.kill_bullet()
                    
            elif collision_type == 'bullet_player':
                bullet = collision['bullet']
                player = collision['player']
                
                # Oyuncu vurulma işlemi
                if bullet.origin != player:
                    # Puan ver (eğer oyuncu başka oyuncuyu vurduysa)
                    if hasattr(bullet.origin, 'increase_score'):
                        bullet.origin.increase_score(1000)
                    
                    self.kill_player(player)
                    bullet.origin.kill_bullet()
                    
            elif collision_type == 'bullet_enemy':
                bullet = collision['bullet']
                enemy = collision['enemy']
                
                # Düşman vurulma işlemi
                if hasattr(bullet.origin, 'increase_score'):
                    score = enemy.score_points * self.score_modifier
                    bullet.origin.increase_score(score)
                
                self.kill_enemy(enemy)
                bullet.origin.kill_bullet()
                
                # Ölüm animasyonu ekle
                self.deaths.append(Death(
                    self.enemy_death_sheet,
                    enemy.pixel_position_x,
                    enemy.pixel_position_y,
                    enemy.color,
                    0,
                    pygame.Vector2(1, 1)
                ))
                
                self.kill_count += 1
                self.update_enemies_spawn()
                    
        except Exception as e:
            print(f"❌ Thread collision işleme hatası: {e}")
    
    def _update_bullets_classic(self, delta_time):
        """Klasik yöntemle mermi güncelleme (fallback - thread yok)"""
        # Mevcut update_bullets kodlarını buraya koy
        for bullet in self.bullets[:]:
            bullet.update(delta_time)
            
            # Duvar çarpışma kontrolü
            if (not self.current_level.is_inside_walls(bullet.pixel_position_x, bullet.pixel_position_y) or
                self.current_level.has_pixel(bullet.pixel_position_x, bullet.pixel_position_y)):
                bullet.origin.kill_bullet()
                continue
            
            # Düşman çarpışma kontrolü
            if bullet.target_type == BulletTargetTypes.ANY:
                for enemy in self.enemies[:]:
                    if bullet.test_hit(enemy):
                        if isinstance(bullet.origin, Player):
                            bullet.origin.increase_score(enemy.score_points * self.score_modifier)
                            bullet.origin.kill_bullet()
                        
                        self.kill_enemy(enemy)
                        
                        # Ölüm animasyonu ekle
                        self.deaths.append(Death(
                            self.enemy_death_sheet, 
                            enemy.pixel_position_x, 
                            enemy.pixel_position_y, 
                            enemy.color, 
                            0, 
                            pygame.Vector2(1, 1)
                        ))
                        
                        self.kill_count += 1
                        self.update_enemies_spawn()
                        break
            
            # Oyuncu çarpışma kontrolü
            if isinstance(bullet.origin, Player):
                if self.test_bullet_kills_player(bullet, self.player1):
                    continue
                if self.test_bullet_kills_player(bullet, self.player2):
                    continue
            
            # Düşman mermileri (3+ seviyede)
            if isinstance(bullet.origin, Enemy):
                self.test_bullet_kills_player(bullet, self.player1)
                self.test_bullet_kills_player(bullet, self.player2)

    def _update_performance_monitoring(self, current_time, delta_time):
        """Performance monitoring güncelle"""
        self.frame_count += 1
        self.performance_timer += delta_time
        
        # 5 saniyede bir kontrol et
        if current_time - self.last_performance_check > 5000:
            avg_fps = self.frame_count / self.performance_timer if self.performance_timer > 0 else 0
            
            if self.performance_logging_enabled:
                print(f"📊 Performance: {avg_fps:.1f} FPS")
            
            # Düşük FPS uyarısı
            if avg_fps < 50:
                print(f"⚠️ Düşük FPS tespit edildi: {avg_fps:.1f}")
                if self.thread_communication_enabled:
                    self.debug_thread_performance()
            
            # Reset counters
            self.frame_count = 0
            self.performance_timer = 0.0
            self.last_performance_check = current_time

    def toggle_performance_logging(self):
        """Performance logging'i aç/kapat"""
        self.performance_logging_enabled = not self.performance_logging_enabled
        status = "AÇIK" if self.performance_logging_enabled else "KAPALI"
        print(f"📊 Performance logging: {status}")


    def debug_thread_performance(self):
        """Thread performansını detaylı görüntüle"""
        print("\n" + "="*60)
        print("🔍 THREAD PERFORMANCE MONITOR")
        print("="*60)
        
        # System bilgileri
        try:
            process = psutil.Process()
            print(f"💻 System Status:")
            print(f"  CPU Usage: {process.cpu_percent():.1f}%")
            print(f"  Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
            print(f"  Threads: {process.num_threads()}")
        except:
            print("💻 System info not available")
        
        # Thread durumları
        if self.thread_manager:
            print(f"\n📊 GameThread Status:")
            threads = {
                'Physics': self.thread_manager.physics_thread,
                'Audio': self.thread_manager.audio_thread
            }
            
            for name, thread in threads.items():
                if thread:
                    status = "✅ ALIVE" if thread.is_alive() else "💀 DEAD"
                    print(f"  {name:8}: {status}")
                else:
                    print(f"  {name:8}: ❌ NOT_CREATED")
            
            # Queue durumları
            if hasattr(self.thread_manager, 'render_queue'):
                print(f"\n📦 Queue Status:")
                queues = {
                    'Physics': self.thread_manager.physics_queue.qsize(),
                    'Audio': self.thread_manager.audio_queue.qsize()
                }
                
                for name, size in queues.items():
                    status = "⚠️ HIGH" if size > 10 else "✅ OK"
                    print(f"  {name:8}: {size:3d} items {status}")

        # AI Thread durumları
        if hasattr(self, 'ai_controller'):
            print(f"\n🤖 AI Thread Status:")
            ai_threads = {
                'AI Player 1': self.ai_controller.ai_player1,
                'AI Player 2': self.ai_controller.ai_player2
            }
            
            for name, ai_thread in ai_threads.items():
                if ai_thread:
                    status = "✅ ALIVE" if ai_thread.is_alive() else "💀 DEAD"
                    print(f"  {name}: {status}")
                else:
                    print(f"  {name}: ❌ NOT_ACTIVE")
            
            # AI Queue durumları
            print(f"\n🎮 AI Queue Status:")
            ai_queues = {
                'P1 GameState': self.ai_controller.p1_game_state_queue.qsize(),
                'P1 Actions': self.ai_controller.p1_action_queue.qsize(),
                'P2 GameState': self.ai_controller.p2_game_state_queue.qsize(),
                'P2 Actions': self.ai_controller.p2_action_queue.qsize()
            }
            
            for name, size in ai_queues.items():
                status = "⚠️ HIGH" if size > 5 else "✅ OK"
                print(f"  {name}: {size:2d} items {status}")
        
        print("="*60 + "\n")

    def _shutdown_threads(self):
        """Tüm thread'leri güvenli şekilde kapat"""
        print("🛑 Thread'ler kapatılıyor...")
        
        try:
            # AI thread'leri kapat
            if hasattr(self, 'ai_controller'):
                self.ai_controller.stop_all()
                print("  ✅ AI thread'leri kapatıldı")
            
            # GameThreadManager thread'leri kapat
            if self.thread_manager:
                self.thread_manager.stop_threads()
                print("  ✅ GameThreadManager thread'leri kapatıldı")
            
            # Message Bus kapat (varsa)
            if self.message_bus:
                self.message_bus.shutdown_all()
                print("  ✅ Message Bus kapatıldı")
                
        except Exception as e:
            print(f"  ❌ Thread kapatma hatası: {e}")
        
        print("🏁 Tüm thread'ler güvenli şekilde kapatıldı")


            ############
    
    def run(self):
        """Ana oyun döngüsü - Thread entegrasyonu ile"""
        
        self.load_assets()
        
         # MainGameLoop'u başlat
        self.main_loop = MainGameLoop(self)
        
        pygame.key.set_repeat(0)
        
        # Oyun başlangıç durumları
        self.player_selection_mode = True
        self.player_selection_timer = 0
        self.game_mode_selection = False
        self.game_mode_selection_timer = 0
        self.selected_player_mode = 0
        self.is_cooperative = True
        self.game_over = False
        
        # 🔥 YENİ: Performance monitoring değişkenleri
        self.frame_count = 0
        self.performance_timer = 0.0
        self.last_performance_check = pygame.time.get_ticks()
        
        running = True
        
        try:
            print("🎮 Oyun döngüsü başlatıldı")
            
            while running:
                # Delta time hesapla
                current_time = pygame.time.get_ticks()
                delta_time = (current_time - self.last_time) / 1000.0
                self.last_time = current_time
                
                # 🔥 YENİ: Thread durumunu kontrol et
                if self.thread_communication_enabled:
                    if not self._check_thread_health():
                        print("⚠️ Thread sağlık kontrolü başarısız!")
                        # Critical thread failure - işaretlenebilir
                
                # Olayları işle
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    elif event.type == pygame.KEYUP:
                        if event.key in SimpleControls._key_down_processed:
                            SimpleControls._key_down_processed[event.key] = False

                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            self.handle_mouse_event(event.pos, event.button)
                    
                    # 🔥 YENİ: Debug tuşları
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F10:
                            self.debug_thread_performance()
                        elif event.key == pygame.K_F11:
                            self.toggle_performance_logging()
                        
                        # Game Over ekranından çıkış
                        if self.game_over:
                            self.game_over = False
                            self.player_selection_mode = True
                            self.player_selection_timer = 0
                
                # Kontrolleri güncelle
                SimpleControls.get_states()
                
                # 🔥 YENİ: Thread verilerini işle
                if self.thread_communication_enabled:
                    self._process_thread_communications(delta_time)
                
                # Oyun güncelleme
                self.update(delta_time)
                
                # 🔥 YENİ: Thread'lere veri gönder
                if self.thread_communication_enabled:
                    self._send_data_to_threads()
                
                # Çizim işlemleri
                self.draw()
                
                # 🔥 YENİ: Performance monitoring
                self._update_performance_monitoring(current_time, delta_time)
                
                # FPS sınırlaması
                self.clock.tick(60)
                
        except KeyboardInterrupt:
            print("🛑 Kullanıcı tarafından durduruldu")
        except Exception as e:
            print(f"❌ Oyun döngüsü hatası: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 🔥 YENİ: Thread'leri güvenli şekilde kapat
            self._shutdown_threads()
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    print("🎮 Wizard of Wor - Thread Edition başlatılıyor...")
    
    try:
        game = WizardOfWor()
        game.run()
    except Exception as e:
        print(f"❌ Kritik hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 Oyun sonlandırıldı")