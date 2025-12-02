"""
Configuration persistence manager.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages saving and loading of user configuration."""
    
    def __init__(self, config_file: str = "user_config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                print(f"✓ Configuration loaded from {self.config_file}")
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
                self.config = {}
        else:
            self.config = {}
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✓ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports nested keys with dots, e.g., 'analysis.prominence')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports nested keys with dots)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to nested dict, creating if necessary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set final value
        config[keys[-1]] = value
    
    def get_analysis_params(self) -> Dict[str, float]:
        """
        Get saved analysis parameters.
        
        Returns:
            Dictionary of analysis parameters
        """
        return {
            'prominence_pct': self.get('analysis.prominence_pct', 2.0),
            'width_time': self.get('analysis.width_time', 0.2e-6),
            'min_dist_time': self.get('analysis.min_dist_time', 0.05e-6),
            'baseline_pct': self.get('analysis.baseline_pct', 85.0),
            'max_dist_pct': self.get('analysis.max_dist_pct', 99.0),
            'afterpulse_pct': self.get('analysis.afterpulse_pct', 80.0)
        }
    
    def save_analysis_params(self, params: Dict[str, float]):
        """
        Save analysis parameters.
        
        Args:
            params: Dictionary of analysis parameters
        """
        for key, value in params.items():
            self.set(f'analysis.{key}', value)
        self.save()
    
    def get_sipm_thresholds(self) -> Dict[str, float]:
        """
        Get saved SiPM threshold values.
        
        Returns:
            Dictionary with amplitude and time thresholds
        """
        return {
            'amplitude_threshold_mV': self.get('sipm.amplitude_threshold_mV', 60.0),
            'time_threshold_us': self.get('sipm.time_threshold_us', 100.0)
        }
    
    def save_sipm_thresholds(self, amplitude_mV: float, time_us: float):
        """
        Save SiPM threshold values.
        
        Args:
            amplitude_mV: Amplitude threshold in mV
            time_us: Time threshold in microseconds
        """
        self.set('sipm.amplitude_threshold_mV', amplitude_mV)
        self.set('sipm.time_threshold_us', time_us)
        self.save()
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config = {}
        self.save()
        print("✓ Configuration reset to defaults")


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Get global configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
