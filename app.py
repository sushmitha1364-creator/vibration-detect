import streamlit as st
import time
import threading
import queue
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from vibration_detector import VibrationDetector
from signal_processor import SignalProcessor
from data_logger import DataLogger

# Initialize session state
if 'detector' not in st.session_state:
    st.session_state.detector = VibrationDetector()
    st.session_state.processor = SignalProcessor()
    st.session_state.logger = DataLogger()
    st.session_state.monitoring = False
    st.session_state.data_queue = queue.Queue()
    st.session_state.alert_history = []

def main():
    st.set_page_config(
        page_title="Vibration Detection System",
        page_icon="📳",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📳 Vibration Detection System")
    st.markdown("Real-time vibration monitoring with signal processing and alert notifications")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Threshold settings
        st.subheader("Threshold Settings")
        threshold = st.slider(
            "Vibration Threshold", 
            min_value=0.1, 
            max_value=5.0, 
            value=2.0, 
            step=0.1,
            help="Set the vibration level that triggers an alert"
        )
        
        # Sensitivity settings
        sensitivity = st.select_slider(
            "Sensitivity Level",
            options=["Low", "Medium", "High"],
            value="Medium",
            help="Adjust the sensitivity of vibration detection"
        )
        
        # Signal processing settings
        st.subheader("Signal Processing")
        filter_enabled = st.checkbox("Enable Noise Filtering", value=True)
        smoothing_window = st.slider("Smoothing Window", 1, 20, 5)
        
        # Update detector settings
        st.session_state.detector.set_threshold(threshold)
        st.session_state.detector.set_sensitivity(sensitivity)
        st.session_state.processor.set_filter_enabled(filter_enabled)
        st.session_state.processor.set_smoothing_window(smoothing_window)
        
        st.divider()
        
        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 Start Monitoring", disabled=st.session_state.monitoring):
                start_monitoring()
        
        with col2:
            if st.button("🔴 Stop Monitoring", disabled=not st.session_state.monitoring):
                stop_monitoring()
        
        # Clear data button
        if st.button("🗑️ Clear History"):
            st.session_state.logger.clear_data()
            st.session_state.alert_history = []
            st.rerun()
    
    # Main dashboard
    create_dashboard()

def start_monitoring():
    """Start the vibration monitoring system"""
    st.session_state.monitoring = True
    
    def monitoring_loop():
        while st.session_state.monitoring:
            # Generate vibration data
            raw_data = st.session_state.detector.get_vibration_reading()
            
            # Process signal
            processed_data = st.session_state.processor.process_signal(raw_data)
            
            # Check for alerts
            alert_triggered = st.session_state.detector.check_threshold(processed_data['magnitude'])
            
            # Log data
            log_entry = {
                'timestamp': datetime.now(),
                'raw_magnitude': raw_data['magnitude'],
                'processed_magnitude': processed_data['magnitude'],
                'x_axis': processed_data['x'],
                'y_axis': processed_data['y'], 
                'z_axis': processed_data['z'],
                'alert': alert_triggered,
                'threshold_used': st.session_state.detector.threshold,
                'sensitivity_level': st.session_state.detector.sensitivity,
                'filter_enabled': st.session_state.processor.filter_enabled
            }
            
            st.session_state.logger.add_entry(log_entry)
            
            # Handle alerts
            if alert_triggered:
                alert_message = f"⚠️ Vibration Alert: {processed_data['magnitude']:.2f} exceeds threshold {st.session_state.detector.threshold:.2f}"
                st.session_state.alert_history.append({
                    'timestamp': datetime.now(),
                    'message': alert_message,
                    'magnitude': processed_data['magnitude']
                })
            
            time.sleep(0.5)  # Update every 500ms
    
    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitor_thread.start()
    st.rerun()

def stop_monitoring():
    """Stop the vibration monitoring system"""
    st.session_state.monitoring = False
    st.rerun()

def create_dashboard():
    """Create the main monitoring dashboard"""
    
    # Status indicator
    status_col, metrics_col = st.columns([1, 3])
    
    with status_col:
        if st.session_state.monitoring:
            st.success("🟢 System Active")
        else:
            st.error("🔴 System Inactive")
    
    with metrics_col:
        # Get latest data for metrics
        latest_data = st.session_state.logger.get_latest_data()
        if latest_data:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Magnitude", f"{latest_data['processed_magnitude']:.2f}")
            with col2:
                st.metric("Threshold", f"{st.session_state.detector.threshold:.2f}")
            with col3:
                alert_count = len([a for a in st.session_state.alert_history if a['timestamp'] > datetime.now() - timedelta(hours=1)])
                st.metric("Alerts (1h)", alert_count)
            with col4:
                st.metric("Data Points", len(st.session_state.logger.data))
    
    # Real-time charts
    if st.session_state.monitoring or st.session_state.logger.data:
        create_real_time_charts()
    
    # Alert notifications
    create_alert_section()
    
    # Historical data analysis
    create_historical_analysis()

def create_real_time_charts():
    """Create real-time visualization charts"""
    
    st.subheader("📊 Real-time Monitoring")
    
    data = st.session_state.logger.get_recent_data(100)  # Last 100 points
    
    if data:
        df = pd.DataFrame(data)
        
        # Create subplot with multiple y-axes
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Vibration Magnitude', 'X-Y-Z Components', 'Signal Comparison', 'Alert Timeline'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": True}, {"secondary_y": False}]]
        )
        
        # Magnitude chart with threshold line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], 
                y=df['processed_magnitude'],
                mode='lines',
                name='Processed Magnitude',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=[st.session_state.detector.threshold] * len(df),
                mode='lines',
                name='Threshold',
                line=dict(color='red', dash='dash', width=2)
            ),
            row=1, col=1
        )
        
        # X-Y-Z components
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['x_axis'], name='X-axis', line=dict(color='red')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['y_axis'], name='Y-axis', line=dict(color='green')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['z_axis'], name='Z-axis', line=dict(color='blue')),
            row=1, col=2
        )
        
        # Raw vs Processed comparison
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['raw_magnitude'], name='Raw Signal', line=dict(color='orange')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['processed_magnitude'], name='Filtered Signal', line=dict(color='blue')),
            row=2, col=1
        )
        
        # Alert timeline
        alert_df = df[df['alert'] == True]
        if not alert_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=alert_df['timestamp'], 
                    y=alert_df['processed_magnitude'],
                    mode='markers',
                    name='Alerts',
                    marker=dict(color='red', size=10, symbol='diamond')
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            height=600,
            showlegend=True,
            title_text="Vibration Monitoring Dashboard"
        )
        
        # Update chart every second if monitoring
        chart_placeholder = st.empty()
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        
        if st.session_state.monitoring:
            time.sleep(1)
            st.rerun()

def create_alert_section():
    """Create alert notifications section"""
    
    st.subheader("🚨 Alert Notifications")
    
    if st.session_state.alert_history:
        # Show recent alerts
        recent_alerts = sorted(st.session_state.alert_history, key=lambda x: x['timestamp'], reverse=True)[:5]
        
        for alert in recent_alerts:
            alert_time = alert['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            if datetime.now() - alert['timestamp'] < timedelta(minutes=5):
                st.error(f"🔴 **{alert_time}** - {alert['message']}")
            else:
                st.warning(f"🟡 **{alert_time}** - {alert['message']}")
    else:
        st.info("No alerts recorded yet.")

def create_historical_analysis():
    """Create historical data analysis section"""
    
    st.subheader("📈 Historical Analysis")
    
    data = st.session_state.logger.data
    
    if data:
        df = pd.DataFrame(data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Statistics
            st.write("**System Statistics**")
            stats = {
                'Total Data Points': len(df),
                'Average Magnitude': f"{df['processed_magnitude'].mean():.2f}",
                'Max Magnitude': f"{df['processed_magnitude'].max():.2f}",
                'Min Magnitude': f"{df['processed_magnitude'].min():.2f}",
                'Total Alerts': len([a for a in st.session_state.alert_history]),
                'Alert Rate': f"{(df['alert'].sum() / len(df) * 100):.1f}%" if len(df) > 0 else "0%"
            }
            
            for key, value in stats.items():
                st.metric(key, value)
        
        with col2:
            # Trend analysis
            st.write("**Trend Analysis**")
            if len(df) > 10:
                # Calculate moving average
                df['moving_avg'] = df['processed_magnitude'].rolling(window=10).mean()
                
                trend_fig = go.Figure()
                trend_fig.add_trace(go.Scatter(
                    x=df['timestamp'], 
                    y=df['processed_magnitude'],
                    mode='lines',
                    name='Magnitude',
                    opacity=0.7
                ))
                trend_fig.add_trace(go.Scatter(
                    x=df['timestamp'], 
                    y=df['moving_avg'],
                    mode='lines',
                    name='Moving Average',
                    line=dict(color='red', width=3)
                ))
                
                trend_fig.update_layout(
                    title="Vibration Trend Analysis",
                    height=300
                )
                
                st.plotly_chart(trend_fig, use_container_width=True)
    else:
        st.info("No historical data available yet. Start monitoring to collect data.")

if __name__ == "__main__":
    main()
