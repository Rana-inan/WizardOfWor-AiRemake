# src/config_manager.py
class ConfigManager:
    _config = {}
    
    @staticmethod
    def load_config(path):
        ConfigManager._config.clear()
        
        try:
            with open(path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line.startswith('--'):  # Yorum satırı
                        split = line.split('=')
                        if len(split) == 2:
                            key, value = split[0].strip(), split[1].strip()
                            ConfigManager._config[key] = value
        except FileNotFoundError:
            print(f"Yapılandırma dosyası bulunamadı: {path}")
    
    @staticmethod
    def get_config(key, default_value):
        if key in ConfigManager._config:
            try:
                if isinstance(default_value, int):
                    return int(ConfigManager._config[key])
                elif isinstance(default_value, float):
                    return float(ConfigManager._config[key])
                elif isinstance(default_value, bool):
                    return ConfigManager._config[key].lower() == 'true'
                else:
                    return ConfigManager._config[key]
            except:
                return default_value
        
        return default_value