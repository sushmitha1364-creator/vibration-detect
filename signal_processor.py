import numpy as np
from collections import deque
import scipy.signal as signal

class SignalProcessor:
    """
    Signal processing class for noise filtering and smoothing
    """
    
    def __init__(self):
        self.filter_enabled = True
        self.smoothing_window = 5
        self.history_buffer = deque(maxlen=100)  # Keep last 100 readings for processing
        
        # Filter parameters
        self.filter_order = 4
        self.cutoff_frequency = 0.3  # Normalized frequency (0-1)
        
        # Create butterworth low-pass filter
        self.b, self.a = signal.butter(self.filter_order, self.cutoff_frequency, btype='low')
        
        # Smoothing buffer for each axis
        self.x_buffer = deque(maxlen=self.smoothing_window)
        self.y_buffer = deque(maxlen=self.smoothing_window)
        self.z_buffer = deque(maxlen=self.smoothing_window)
        self.magnitude_buffer = deque(maxlen=self.smoothing_window)
    
    def set_filter_enabled(self, enabled):
        """Enable or disable noise filtering"""
        self.filter_enabled = enabled
    
    def set_smoothing_window(self, window_size):
        """Set the smoothing window size"""
        self.smoothing_window = window_size
        # Update buffer sizes
        self.x_buffer = deque(list(self.x_buffer), maxlen=window_size)
        self.y_buffer = deque(list(self.y_buffer), maxlen=window_size)
        self.z_buffer = deque(list(self.z_buffer), maxlen=window_size)
        self.magnitude_buffer = deque(list(self.magnitude_buffer), maxlen=window_size)
    
    def apply_noise_filter(self, data):
        """
        Apply butterworth low-pass filter to remove high-frequency noise
        """
        if not self.filter_enabled:
            return data
        
        # Add current data to history
        self.history_buffer.append(data)
        
        # Need at least filter_order + 1 points for filtering
        if len(self.history_buffer) < self.filter_order + 1:
            return data
        
        # Extract recent data for filtering
        recent_data = list(self.history_buffer)
        
        try:
            # Apply filter to each axis
            x_values = [d['x'] for d in recent_data]
            y_values = [d['y'] for d in recent_data]
            z_values = [d['z'] for d in recent_data]
            
            # Apply butterworth filter
            x_filtered = signal.filtfilt(self.b, self.a, x_values)
            y_filtered = signal.filtfilt(self.b, self.a, y_values)
            z_filtered = signal.filtfilt(self.b, self.a, z_values)
            
            # Return the last (most recent) filtered values
            filtered_data = {
                'timestamp': data['timestamp'],
                'x': x_filtered[-1],
                'y': y_filtered[-1],
                'z': z_filtered[-1],
                'magnitude': np.sqrt(x_filtered[-1]**2 + y_filtered[-1]**2 + z_filtered[-1]**2)
            }
            
            return filtered_data
            
        except Exception as e:
            # If filtering fails, return original data
            return data
    
    def apply_smoothing(self, data):
        """
        Apply moving average smoothing to the signal
        """
        # Add to buffers
        self.x_buffer.append(data['x'])
        self.y_buffer.append(data['y'])
        self.z_buffer.append(data['z'])
        
        # Calculate smoothed values
        smoothed_x = np.mean(list(self.x_buffer))
        smoothed_y = np.mean(list(self.y_buffer))
        smoothed_z = np.mean(list(self.z_buffer))
        
        # Calculate smoothed magnitude
        smoothed_magnitude = np.sqrt(smoothed_x**2 + smoothed_y**2 + smoothed_z**2)
        
        return {
            'timestamp': data['timestamp'],
            'x': smoothed_x,
            'y': smoothed_y,
            'z': smoothed_z,
            'magnitude': smoothed_magnitude
        }
    
    def process_signal(self, raw_data):
        """
        Complete signal processing pipeline:
        1. Apply noise filtering
        2. Apply smoothing
        """
        # Step 1: Apply noise filtering
        filtered_data = self.apply_noise_filter(raw_data)
        
        # Step 2: Apply smoothing
        processed_data = self.apply_smoothing(filtered_data)
        
        return processed_data
    
    def get_filter_status(self):
        """Get current filter configuration"""
        return {
            'filter_enabled': self.filter_enabled,
            'smoothing_window': self.smoothing_window,
            'cutoff_frequency': self.cutoff_frequency,
            'filter_order': self.filter_order
        }
    
    def reset_buffers(self):
        """Clear all processing buffers"""
        self.history_buffer.clear()
        self.x_buffer.clear()
        self.y_buffer.clear()
        self.z_buffer.clear()
        self.magnitude_buffer.clear()
