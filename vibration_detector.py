import numpy as np
import random
import time
from datetime import datetime

class VibrationDetector:
    """
    Vibration detection class that simulates sensor readings and monitors thresholds
    """
    
    def __init__(self):
        self.threshold = 2.0
        self.sensitivity = "Medium"
        self.base_frequency = 0.5  # Base vibration frequency
        self.noise_level = 0.1
        self.last_reading_time = time.time()
        
        # Sensitivity multipliers
        self.sensitivity_multipliers = {
            "Low": 0.7,
            "Medium": 1.0,
            "High": 1.3
        }
    
    def set_threshold(self, threshold):
        """Set the vibration threshold for alerts"""
        self.threshold = threshold
    
    def set_sensitivity(self, sensitivity):
        """Set the sensitivity level (Low, Medium, High)"""
        self.sensitivity = sensitivity
    
    def get_vibration_reading(self):
        """
        Simulate vibration sensor reading with realistic patterns
        Returns a dictionary with x, y, z components and magnitude
        """
        current_time = time.time()
        dt = current_time - self.last_reading_time
        self.last_reading_time = current_time
        
        # Generate base vibration with some realistic patterns
        t = current_time
        
        # Simulate different vibration sources
        # Normal ambient vibration
        ambient_x = 0.1 * np.sin(2 * np.pi * 0.5 * t) + random.gauss(0, 0.05)
        ambient_y = 0.1 * np.cos(2 * np.pi * 0.3 * t) + random.gauss(0, 0.05)
        ambient_z = 0.05 * np.sin(2 * np.pi * 0.7 * t) + random.gauss(0, 0.03)
        
        # Occasional spikes to simulate actual vibrations
        spike_probability = 0.05  # 5% chance of spike
        if random.random() < spike_probability:
            spike_magnitude = random.uniform(1.5, 4.0)
            spike_duration = random.uniform(0.5, 2.0)
            
            spike_x = spike_magnitude * np.sin(2 * np.pi * 10 * t) * np.exp(-t % spike_duration)
            spike_y = spike_magnitude * np.cos(2 * np.pi * 8 * t) * np.exp(-t % spike_duration)
            spike_z = spike_magnitude * np.sin(2 * np.pi * 12 * t) * np.exp(-t % spike_duration)
        else:
            spike_x = spike_y = spike_z = 0
        
        # Combine ambient and spike vibrations
        x = ambient_x + spike_x
        y = ambient_y + spike_y
        z = ambient_z + spike_z
        
        # Add sensitivity adjustment
        sensitivity_factor = self.sensitivity_multipliers[self.sensitivity]
        x *= sensitivity_factor
        y *= sensitivity_factor
        z *= sensitivity_factor
        
        # Calculate magnitude
        magnitude = np.sqrt(x**2 + y**2 + z**2)
        
        return {
            'timestamp': datetime.now(),
            'x': x,
            'y': y,
            'z': z,
            'magnitude': magnitude
        }
    
    def check_threshold(self, magnitude):
        """
        Check if the vibration magnitude exceeds the threshold
        Returns True if alert should be triggered
        """
        return magnitude > self.threshold
    
    def get_status(self):
        """Get current detector status"""
        return {
            'threshold': self.threshold,
            'sensitivity': self.sensitivity,
            'active': True
        }
