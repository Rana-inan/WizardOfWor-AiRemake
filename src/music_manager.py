# src/music_manager.py
import pygame

class MusicManager:
    def __init__(self):
        self._is_music_playing = False
        self._current_tempo_bps = 0
        self._current_musique_time = 0
        self._music_note_sounds = []
        self._music_note_instances = []
        self._current_music_note = 0
        
        self._tempos = [30.0, 40.0, 60.0, 120.0, 300.0]  # TEMPO_1,2,3,4,5
        
        self._worluk_intro = None
        self._worluk_intro_instance = None
        self._worluk_loop = None
        self._worluk_loop_instance = None
        
        self._is_boss_music = False
        self._is_boss_intro_playing = False
    
    def load_music_sounds(self, sound_paths):
        # sound_paths: Dictionary olarak ses dosyalarının yollarını içermeli
        # Örnek: {'c_long': 'assets/sounds/C-long.wav', 'g_sharp_long': 'assets/sounds/G#-long.wav', ...}
        
        # Ana müzik notalarını yükle
        if 'c_long' in sound_paths and 'g_sharp_long' in sound_paths:
            self._music_note_sounds = [
                pygame.mixer.Sound(sound_paths['c_long']),
                pygame.mixer.Sound(sound_paths['g_sharp_long'])
            ]
            
            # Ses örnekleri oluştur
            self._music_note_instances = [
                self._music_note_sounds[0],
                self._music_note_sounds[1]
            ]
        
        # Boss müziklerini yükle
        if 'worluk_intro' in sound_paths:
            self._worluk_intro = pygame.mixer.Sound(sound_paths['worluk_intro'])
            self._worluk_intro_instance = self._worluk_intro
        
        if 'worluk_loop' in sound_paths:
            self._worluk_loop = pygame.mixer.Sound(sound_paths['worluk_loop'])
            self._worluk_loop_instance = self._worluk_loop
            # Sonsuz döngü ayarı pygame'de direk olarak yok, manuel olarak tekrar çalamak gerekebilir
    
    def _set_tempo(self, tempo_bpm):
        self._current_tempo_bps = tempo_bpm / 60
    
    def start_music(self, tempo):
        self._is_boss_music = False
        self._set_tempo(tempo)
        self._current_musique_time = 0
        self._current_music_note = 0
        
        if self._music_note_instances and len(self._music_note_instances) > 0:
            self._music_note_instances[self._current_music_note].play()
            self._is_music_playing = True
    
    def stop_music(self):
        self._is_music_playing = False
        self._is_boss_music = False
        self._is_boss_intro_playing = False
        
        if self._music_note_instances and len(self._music_note_instances) > self._current_music_note:
            self._music_note_instances[self._current_music_note].stop()
        
        if self._worluk_intro_instance:
            self._worluk_intro_instance.stop()
        
        if self._worluk_loop_instance:
            self._worluk_loop_instance.stop()
    
    def start_boss_music(self):
        self._is_boss_music = True
        self._is_boss_intro_playing = True
        
        if self._worluk_intro_instance:
            self._worluk_intro_instance.play()
            self._is_music_playing = True
            self._current_musique_time = 0
    
    def update(self, delta_time, level_threshold):
        if self._is_music_playing:
            self._current_musique_time += delta_time
            
            if self._is_boss_music:
                if self._is_boss_intro_playing and self._worluk_intro and self._current_musique_time >= self._worluk_intro.get_length():
                    if self._worluk_intro_instance:
                        self._worluk_intro_instance.stop()
                    
                    if self._worluk_loop_instance:
                        self._worluk_loop_instance.play(-1)  # -1: sonsuz döngü
                        self._is_boss_intro_playing = False
            else:
                previous_tempo = self._current_tempo_bps
                self._set_tempo(self._tempos[level_threshold])
                
                if self._current_musique_time > 1 / self._current_tempo_bps:
                    if self._music_note_instances and len(self._music_note_instances) > self._current_music_note:
                        self._music_note_instances[self._current_music_note].stop()
                        self._current_music_note = 1 - self._current_music_note  # 0->1 veya 1->0
                        self._music_note_instances[self._current_music_note].play()
                        
                        if previous_tempo != self._current_tempo_bps:
                            self._current_musique_time = 0
                        else:
                            self._current_musique_time = self._current_musique_time - 1.0 / self._current_tempo_bps