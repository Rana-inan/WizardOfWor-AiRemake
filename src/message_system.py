
import threading
import queue
import time
import uuid
from enum import Enum
from typing import Dict, Any, List

class MessageType(Enum):
    PHYSICS_UPDATE = 1
    AI_DECISION = 2
    RENDER_REQUEST = 3
    SOUND_PLAY = 4
    LEVEL_LOAD = 5
    INPUT_EVENT = 6
    GAME_EVENT = 7
    SHUTDOWN = 99

class Message:
    def __init__(self, msg_type, sender_id, data=None, priority=0):
        self.id = uuid.uuid4()
        self.type = msg_type
        self.sender_id = sender_id
        self.data = data
        self.timestamp = time.time()
        self.priority = priority  # 0 (normal) - 10 (en yüksek)

class MessageBus:
    def __init__(self):
        self.actors = {}
        self.lock = threading.Lock()
        self.stats = {
            'routed_messages': 0,
            'broadcast_messages': 0,
            'dropped_messages': 0
        }
    
    def register_actor(self, actor):
        """Aktörü mesaj sistemine kaydeder"""
        with self.lock:
            self.actors[actor.actor_id] = actor
    
    def unregister_actor(self, actor_id):
        """Aktörü mesaj sisteminden çıkarır"""
        with self.lock:
            if actor_id in self.actors:
                del self.actors[actor_id]
    
    def route_message(self, target_id, message):
        """Mesajı hedef aktöre yönlendirir"""
        with self.lock:
            if target_id in self.actors:
                self.actors[target_id].receive(message)
                self.stats['routed_messages'] += 1
            else:
                self.stats['dropped_messages'] += 1
    
    def broadcast_message(self, message):
        """Mesajı tüm aktörlere yayınlar"""
        with self.lock:
            for actor_id, actor in self.actors.items():
                if actor_id != message.sender_id:  # Gönderene geri gönderme
                    actor.receive(message)
            self.stats['broadcast_messages'] += 1
    
    def shutdown_all(self):
        """Tüm aktörlere kapatma mesajı gönderir"""
        shutdown_msg = Message(MessageType.SHUTDOWN, "SYSTEM")
        with self.lock:
            for actor in self.actors.values():
                actor.receive(shutdown_msg)

    # message_system.py içinde devam eder

class Actor(threading.Thread):
    def __init__(self, actor_id, message_bus):
        super().__init__()
        self.actor_id = actor_id
        self.message_bus = message_bus
        self.inbox = queue.PriorityQueue()
        self.running = True
        self.handlers = {}  # Mesaj işleyicileri
        self.state = {}  # Aktörün durumu
        self.daemon = True
        self.last_activity = time.time()
        self.sleeping = False
        self.lock = threading.RLock()  # Yeniden girişli kilit
    
    def register_handler(self, msg_type, handler_func):
        """Mesaj türü için bir işleyici fonksiyon kaydeder"""
        self.handlers[msg_type] = handler_func
    
    def send(self, target_id, msg_type, data=None, priority=0):
        """Başka bir aktöre mesaj gönderir"""
        message = Message(msg_type, self.actor_id, data, priority)
        self.message_bus.route_message(target_id, message)
        
    def broadcast(self, msg_type, data=None, priority=0):
        """Tüm aktörlere mesaj yayınlar"""
        message = Message(msg_type, self.actor_id, data, priority)
        self.message_bus.broadcast_message(message)
    
    def receive(self, message):
        """Mesajı gelen kutusuna ekler"""
        self.inbox.put((10-message.priority, message))  # Öncelik tersine çevrilir
        
        # Uyku modundaysa uyandır
        if self.sleeping:
            with self.lock:
                self.sleeping = False
    
    def process_messages(self, max_messages=10):
        """Belirli sayıda mesajı işler"""
        processed = 0
        
        while processed < max_messages and not self.inbox.empty():
            try:
                _, message = self.inbox.get(block=False)
                self._handle_message(message)
                self.inbox.task_done()
                processed += 1
                self.last_activity = time.time()
            except queue.Empty:
                break
        
        return processed
    
    def _handle_message(self, message):
        """Mesajı uygun işleyiciye yönlendirir"""
        if message.type == MessageType.SHUTDOWN:
            self.running = False
            return
            
        if message.type in self.handlers:
            with self.lock:
                self.handlers[message.type](message)
        else:
            print(f"Aktör {self.actor_id}: İşlenemeyen mesaj türü: {message.type}")
    
    def run(self):
        """Aktör ana döngüsü"""
        while self.running:
            processed = self.process_messages()
            
            # Hiç mesaj işlenmediyse uyku moduna geç
            if processed == 0:
                if time.time() - self.last_activity > 0.1:  # 100ms aktivite olmazsa
                    with self.lock:
                        self.sleeping = True
                time.sleep(0.001)  # CPU kullanımını azalt