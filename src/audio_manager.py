# src/audio_manager.py
import pygame
import threading
import queue
import time
from enum import Enum

class AudioCommand(Enum):
    PLAY_SOUND = 1
    PLAY_MUSIC = 2
    STOP_MUSIC = 3
    SET_VOLUME = 4
    FADE_IN = 5
    FADE_OUT = 6
    LOAD_SOUND = 7
    PRELOAD_SOUNDS = 8

class AudioManager:
    """Thread-safe audio yöneticisi"""
    
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.audio_thread = None
        self.running = False
        
        # Ses cache'i
        self.sound_cache = {}
        self.music_cache = {}
        
        # Volume kontrolü
        self.master_volume = 1.0
        self.sfx_volume = 1.0
        self.music_volume = 1.0
        
        # Mevcut müzik durumu
        self.current_music = None
        self.music_position = 0
        
        # Thread-safe lock
        self.audio_lock = threading.Lock()
        
    def start(self):
        """Audio thread'i başlat"""
        if not self.running:
            self.running = True
            self.audio_thread = threading.Thread(
                target=self._audio_loop,
                daemon=True
            )
            self.audio_thread.start()
            print("🔊 Audio thread başlatıldı")
    
    def stop(self):
        """Audio thread'i durdur"""
        self.running = False
        if self.audio_thread and self.audio_thread.is_alive():
            # Shutdown komutu gönder
            self.audio_queue.put({
                'command': 'SHUTDOWN',
                'data': None
            })
            self.audio_thread.join(timeout=1.0)
        print("🔇 Audio thread durduruldu")
    
    def play_sound(self, sound_path, volume=1.0, priority=0):
        """Ses efekti çal"""
        command = {
            'command': AudioCommand.PLAY_SOUND,
            'data': {
                'path': sound_path,
                'volume': volume * self.sfx_volume * self.master_volume,
                'priority': priority
            }
        }
        
        try:
            self.audio_queue.put(command, block=False)
        except queue.Full:
            print("⚠️ Audio queue dolu, ses efekti atlandı")
    
    def play_music(self, music_path, loop=True, volume=1.0):
        """Background müzik çal"""
        command = {
            'command': AudioCommand.PLAY_MUSIC,
            'data': {
                'path': music_path,
                'loop': loop,
                'volume': volume * self.music_volume * self.master_volume
            }
        }
        
        try:
            self.audio_queue.put(command, block=False)
        except queue.Full:
            print("⚠️ Audio queue dolu, müzik komutu atlandı")
    
    def stop_music(self, fade_out_time=0):
        """Müziği durdur"""
        command = {
            'command': AudioCommand.STOP_MUSIC,
            'data': {'fade_time': fade_out_time}
        }
        
        self.audio_queue.put(command, block=False)
    
    def set_volume(self, volume_type, volume):
        """Volume ayarla"""
        command = {
            'command': AudioCommand.SET_VOLUME,
            'data': {
                'type': volume_type,  # 'master', 'sfx', 'music'
                'volume': max(0.0, min(1.0, volume))
            }
        }
        
        self.audio_queue.put(command, block=False)
    
    def preload_sounds(self, sound_paths):
        """Ses dosyalarını önceden yükle"""
        command = {
            'command': AudioCommand.PRELOAD_SOUNDS,
            'data': {'paths': sound_paths}
        }
        
        self.audio_queue.put(command, block=False)
    
    def _audio_loop(self):
        """Audio thread ana döngüsü"""
        print("🎵 Audio thread döngüsü başladı")
        
        while self.running:
            try:
                # Komut al
                command_data = self.audio_queue.get(timeout=0.1)
                
                # Shutdown kontrolü
                if command_data.get('command') == 'SHUTDOWN':
                    break
                
                # Komutu işle
                self._process_audio_command(command_data)
                
                # İşlem tamamlandı
                self.audio_queue.task_done()
                
            except queue.Empty:
                # Timeout - normal durum
                self._check_music_status()  # Müzik durumunu kontrol et
                continue
            except Exception as e:
                print(f"❌ Audio thread hatası: {e}")
                time.sleep(0.01)
        
        print("🔇 Audio thread döngüsü sonlandı")
    
    def _process_audio_command(self, command_data):
        """Audio komutunu işle"""
        try:
            command = command_data.get('command')
            data = command_data.get('data', {})
            
            if command == AudioCommand.PLAY_SOUND:
                self._play_sound_effect(data)
            elif command == AudioCommand.PLAY_MUSIC:
                self._play_background_music(data)
            elif command == AudioCommand.STOP_MUSIC:
                self._stop_background_music(data)
            elif command == AudioCommand.SET_VOLUME:
                self._set_volume_levels(data)
            elif command == AudioCommand.PRELOAD_SOUNDS:
                self._preload_sound_files(data)
            else:
                print(f"⚠️ Bilinmeyen audio komutu: {command}")
                
        except Exception as e:
            print(f"❌ Audio komut işleme hatası: {e}")
    
    def _play_sound_effect(self, data):
        """Ses efekti çal"""
        sound_path = data.get('path')
        volume = data.get('volume', 1.0)
        
        try:
            # Cache'den kontrol et
            if sound_path in self.sound_cache:
                sound = self.sound_cache[sound_path]
            else:
                # Yükle ve cache'e ekle
                sound = pygame.mixer.Sound(sound_path)
                self.sound_cache[sound_path] = sound
            
            # Volume ayarla ve çal
            sound.set_volume(volume)
            sound.play()
            
        except Exception as e:
            print(f"❌ Ses efekti çalma hatası ({sound_path}): {e}")
    
    def _play_background_music(self, data):
        """Background müzik çal"""
        music_path = data.get('path')
        loop = data.get('loop', True)
        volume = data.get('volume', 1.0)
        
        try:
            with self.audio_lock:
                # Mevcut müziği durdur
                pygame.mixer.music.stop()
                
                # Yeni müziği yükle
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(volume)
                
                # Çal
                loops = -1 if loop else 0
                pygame.mixer.music.play(loops)
                
                # Durumu kaydet
                self.current_music = music_path
                self.music_position = 0
                
                print(f"🎵 Müzik başlatıldı: {music_path}")
                
        except Exception as e:
            print(f"❌ Müzik çalma hatası ({music_path}): {e}")
    
    def _stop_background_music(self, data):
        """Müziği durdur"""
        fade_time = data.get('fade_time', 0)
        
        try:
            with self.audio_lock:
                if fade_time > 0:
                    pygame.mixer.music.fadeout(int(fade_time * 1000))
                else:
                    pygame.mixer.music.stop()
                
                self.current_music = None
                print("🔇 Müzik durduruldu")
                
        except Exception as e:
            print(f"❌ Müzik durdurma hatası: {e}")
    
    def _set_volume_levels(self, data):
        """Volume seviyelerini ayarla"""
        volume_type = data.get('type')
        volume = data.get('volume')
        
        try:
            if volume_type == 'master':
                self.master_volume = volume
            elif volume_type == 'sfx':
                self.sfx_volume = volume
            elif volume_type == 'music':
                self.music_volume = volume
                # Şu anki müziğin volume'ünü güncelle
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.set_volume(volume * self.master_volume)
            
            print(f"🔊 {volume_type} volume: {volume:.2f}")
            
        except Exception as e:
            print(f"❌ Volume ayarlama hatası: {e}")
    
    def _preload_sound_files(self, data):
        """Ses dosyalarını önceden yükle"""
        paths = data.get('paths', [])
        
        loaded_count = 0
        for path in paths:
            try:
                if path not in self.sound_cache:
                    sound = pygame.mixer.Sound(path)
                    self.sound_cache[path] = sound
                    loaded_count += 1
            except Exception as e:
                print(f"❌ Ses yükleme hatası ({path}): {e}")
        
        print(f"📦 {loaded_count} ses dosyası cache'e yüklendi")
    
    def _check_music_status(self):
        """Müzik durumunu kontrol et (döngüde)"""
        try:
            if self.current_music and not pygame.mixer.music.get_busy():
                # Müzik bitti, bilgiyi temizle
                self.current_music = None
                
        except Exception as e:
            pass  # Sessiz geç