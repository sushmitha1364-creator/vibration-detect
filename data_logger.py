import pandas as pd
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc, and_
from database import VibrationData, AlertHistory, get_db_session, init_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLogger:
    """
    Data logging class for storing and retrieving vibration data with database persistence
    """
    
    def __init__(self):
        # Initialize database
        try:
            init_database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Fallback to in-memory storage
            self._data = []
            self.use_database = False
            return
        
        self.use_database = True
        self.max_data_points = 50000  # Increased limit for database storage
    
    def add_entry(self, entry):
        """
        Add a new data entry to the log
        Entry should contain: timestamp, raw_magnitude, processed_magnitude, x_axis, y_axis, z_axis, alert
        """
        if not self.use_database:
            # Fallback to in-memory storage
            self._data.append(entry)
            if len(self._data) > self.max_data_points:
                self._data = self._data[-self.max_data_points:]
            return
        
        session = None
        try:
            session = get_db_session()
            
            # Create database entry
            db_entry = VibrationData(
                timestamp=entry['timestamp'],
                sensor_id=entry.get('sensor_id', 'sensor_1'),
                raw_magnitude=entry['raw_magnitude'],
                processed_magnitude=entry['processed_magnitude'],
                x_axis=entry['x_axis'],
                y_axis=entry['y_axis'],
                z_axis=entry['z_axis'],
                alert=entry['alert'],
                threshold_used=entry.get('threshold_used', 2.0),
                sensitivity_level=entry.get('sensitivity_level', 'Medium'),
                filter_enabled=entry.get('filter_enabled', True)
            )
            
            session.add(db_entry)
            session.commit()
            
            # Clean up old data if we exceed limit
            count = session.query(VibrationData).count()
            if count > self.max_data_points:
                # Delete oldest records
                oldest_records = session.query(VibrationData).order_by(VibrationData.timestamp).limit(count - self.max_data_points)
                for record in oldest_records:
                    session.delete(record)
                session.commit()
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error adding entry to database: {e}")
            if session:
                try:
                    session.close()
                except:
                    pass
    
    def get_latest_data(self):
        """Get the most recent data entry"""
        if not self.use_database:
            # Fallback to in-memory storage
            if self._data:
                return self._data[-1]
            return None
        
        try:
            session = get_db_session()
            latest_record = session.query(VibrationData).order_by(desc(VibrationData.timestamp)).first()
            session.close()
            
            if latest_record:
                return {
                    'timestamp': latest_record.timestamp,
                    'raw_magnitude': latest_record.raw_magnitude,
                    'processed_magnitude': latest_record.processed_magnitude,
                    'x_axis': latest_record.x_axis,
                    'y_axis': latest_record.y_axis,
                    'z_axis': latest_record.z_axis,
                    'alert': latest_record.alert,
                    'sensor_id': latest_record.sensor_id
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return None
    
    def get_recent_data(self, count=100):
        """Get the most recent N data entries"""
        if not self.use_database:
            # Fallback to in-memory storage
            if len(self._data) >= count:
                return self._data[-count:]
            return self._data
        
        try:
            session = get_db_session()
            records = session.query(VibrationData).order_by(desc(VibrationData.timestamp)).limit(count).all()
            session.close()
            
            # Convert to list of dictionaries
            data_list = []
            for record in reversed(records):  # Reverse to get chronological order
                data_list.append({
                    'timestamp': record.timestamp,
                    'raw_magnitude': record.raw_magnitude,
                    'processed_magnitude': record.processed_magnitude,
                    'x_axis': record.x_axis,
                    'y_axis': record.y_axis,
                    'z_axis': record.z_axis,
                    'alert': record.alert,
                    'sensor_id': record.sensor_id
                })
            
            return data_list
            
        except Exception as e:
            logger.error(f"Error getting recent data: {e}")
            return []
    
    def get_data_by_time_range(self, start_time, end_time):
        """Get data within a specific time range"""
        if not self.use_database:
            # Fallback to in-memory storage
            filtered_data = []
            for entry in self._data:
                if start_time <= entry['timestamp'] <= end_time:
                    filtered_data.append(entry)
            return filtered_data
        
        try:
            session = get_db_session()
            records = session.query(VibrationData).filter(
                and_(VibrationData.timestamp >= start_time, VibrationData.timestamp <= end_time)
            ).order_by(VibrationData.timestamp).all()
            session.close()
            
            # Convert to list of dictionaries
            data_list = []
            for record in records:
                data_list.append({
                    'timestamp': record.timestamp,
                    'raw_magnitude': record.raw_magnitude,
                    'processed_magnitude': record.processed_magnitude,
                    'x_axis': record.x_axis,
                    'y_axis': record.y_axis,
                    'z_axis': record.z_axis,
                    'alert': record.alert,
                    'sensor_id': record.sensor_id
                })
            
            return data_list
            
        except Exception as e:
            logger.error(f"Error getting data by time range: {e}")
            return []
    
    def get_data_since(self, since_time):
        """Get all data since a specific time"""
        if not self.use_database:
            # Fallback to in-memory storage
            filtered_data = []
            for entry in self._data:
                if entry['timestamp'] >= since_time:
                    filtered_data.append(entry)
            return filtered_data
        
        try:
            session = get_db_session()
            records = session.query(VibrationData).filter(
                VibrationData.timestamp >= since_time
            ).order_by(VibrationData.timestamp).all()
            session.close()
            
            # Convert to list of dictionaries
            data_list = []
            for record in records:
                data_list.append({
                    'timestamp': record.timestamp,
                    'raw_magnitude': record.raw_magnitude,
                    'processed_magnitude': record.processed_magnitude,
                    'x_axis': record.x_axis,
                    'y_axis': record.y_axis,
                    'z_axis': record.z_axis,
                    'alert': record.alert,
                    'sensor_id': record.sensor_id
                })
            
            return data_list
            
        except Exception as e:
            logger.error(f"Error getting data since time: {e}")
            return []
    
    def get_alert_data(self):
        """Get only entries where alerts were triggered"""
        if not self.use_database:
            # Fallback to in-memory storage
            return [entry for entry in self._data if entry.get('alert', False)]
        
        try:
            session = get_db_session()
            records = session.query(VibrationData).filter(
                VibrationData.alert == True
            ).order_by(VibrationData.timestamp).all()
            session.close()
            
            # Convert to list of dictionaries
            data_list = []
            for record in records:
                data_list.append({
                    'timestamp': record.timestamp,
                    'raw_magnitude': record.raw_magnitude,
                    'processed_magnitude': record.processed_magnitude,
                    'x_axis': record.x_axis,
                    'y_axis': record.y_axis,
                    'z_axis': record.z_axis,
                    'alert': record.alert,
                    'sensor_id': record.sensor_id
                })
            
            return data_list
            
        except Exception as e:
            logger.error(f"Error getting alert data: {e}")
            return []
    
    def clear_data(self):
        """Clear all logged data"""
        if not self.use_database:
            # Fallback to in-memory storage
            self._data = []
            return
        
        try:
            session = get_db_session()
            session.query(VibrationData).delete()
            session.query(AlertHistory).delete()
            session.commit()
            session.close()
            logger.info("All data cleared from database")
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
    
    @property
    def data(self):
        """Get all data for compatibility with existing code"""
        if not self.use_database:
            return getattr(self, '_data', [])
        
        # For database, return recent data to avoid memory issues
        return self.get_recent_data(1000)
    
    def get_statistics(self):
        """Calculate basic statistics for the logged data"""
        data = self.data
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        stats = {
            'total_entries': len(data),
            'time_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max(),
                'duration': df['timestamp'].max() - df['timestamp'].min()
            },
            'magnitude_stats': {
                'mean': df['processed_magnitude'].mean(),
                'std': df['processed_magnitude'].std(),
                'min': df['processed_magnitude'].min(),
                'max': df['processed_magnitude'].max(),
                'median': df['processed_magnitude'].median()
            },
            'alert_stats': {
                'total_alerts': df['alert'].sum(),
                'alert_rate': df['alert'].mean(),
                'time_in_alert': df['alert'].sum() * 0.5  # Assuming 0.5s intervals
            }
        }
        
        return stats
    
    def export_to_csv(self, filename=None):
        """Export data to CSV file"""
        data = self.data
        if not data:
            return None
        
        if filename is None:
            filename = f"vibration_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        return filename
    
    def export_to_json(self, filename=None):
        """Export data to JSON file"""
        data = self.data
        if not data:
            return None
        
        if filename is None:
            filename = f"vibration_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert datetime objects to strings for JSON serialization
        json_data = []
        for entry in data:
            json_entry = entry.copy()
            json_entry['timestamp'] = entry['timestamp'].isoformat()
            json_data.append(json_entry)
        
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        return filename
    
    def get_trend_analysis(self, window_minutes=60):
        """
        Analyze trends in the data over a specified time window
        """
        # Get recent data within the window
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_data = self.get_data_since(cutoff_time)
        
        if len(recent_data) < 2:
            return None
        
        df = pd.DataFrame(recent_data)
        
        # Calculate trend (linear regression slope)
        import numpy as np
        timestamps_numeric = [(entry['timestamp'] - recent_data[0]['timestamp']).total_seconds() 
                             for entry in recent_data]
        
        # Calculate linear trend
        coeffs = np.polyfit(timestamps_numeric, df['processed_magnitude'], 1)
        trend_slope = coeffs[0]
        
        # Determine trend direction
        if abs(trend_slope) < 0.001:
            trend_direction = "stable"
        elif trend_slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
        
        # Calculate volatility (standard deviation)
        volatility = df['processed_magnitude'].std()
        
        trend_analysis = {
            'window_minutes': window_minutes,
            'data_points': len(recent_data),
            'trend_slope': trend_slope,
            'trend_direction': trend_direction,
            'volatility': volatility,
            'current_level': df['processed_magnitude'].iloc[-1],
            'average_level': df['processed_magnitude'].mean(),
            'recent_alerts': df['alert'].sum()
        }
        
        return trend_analysis
