import sys
import time
import pandas as pd
import os
import pickle
from PyQt5.QtCore import QUrl
import osmnx as ox
import networkx as nx
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal
from data_generator import TrafficDataGenerator
from ml_models import TrafficMLModels
from early_warning import EarlyWarningSystem
from route_recommendation import RouteRecommendationEngine, OptimizedRouteRecommendationEngine
from visualization import TrafficVisualizer, RealTimeMonitoringDashboard
from gui import TrafficMonitoringGUI
from threads import RouteCalculationThread
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_console_mode():
    logging.info("🚀 Starting Traffic Monitoring System in Console Mode...")
    
    traffic_system = TrafficDataGenerator()
    logging.info("✅ TrafficDataGenerator initialized")
    if not hasattr(traffic_system, 'bengkulu_locations'):
        logging.error("❌ TrafficDataGenerator has no bengkulu_locations attribute")
        return
    ml_models = TrafficMLModels()
    logging.info("✅ TrafficMLModels initialized")
    early_warning = EarlyWarningSystem()
    logging.info("✅ EarlyWarningSystem initialized")
    try:
        weather_api_key = "721ec4e5c0e36f2349bc8bbcd4025b60"
        route_engine = OptimizedRouteRecommendationEngine(traffic_system.bengkulu_locations, weather_api_key)
        logging.info("✅ RouteRecommendationEngine initialized")
    except Exception as e:
        logging.error(f"❌ Failed to initialize RouteRecommendationEngine: {str(e)}")
        return
    visualizer = TrafficVisualizer(traffic_system)
    logging.info("✅ TrafficVisualizer initialized")
    dashboard = RealTimeMonitoringDashboard(traffic_system, route_engine)
    logging.info("✅ RealTimeMonitoringDashboard initialized")
    
    logging.info("📊 Generating sample traffic data...")
    traffic_data = traffic_system.generate_enhanced_bengkulu_data(100)
    
    logging.info("\n🧠 Training ML model...")
    accuracy = ml_models.train_models(traffic_data)['accuracy']
    logging.info(f"✅ Model trained with accuracy: {accuracy:.1%}")
    
    logging.info("\n🚨 Analyzing traffic conditions...")
    alerts = early_warning.analyze_traffic_conditions(traffic_data)
    early_warning.broadcast_alerts()
    
    logging.info("\n📈 Creating visualizations...")
    visualizer.create_visualizations(traffic_data)
    
    logging.info("\n🛣 Generating sample route recommendations...")
    route_engine.update_traffic_conditions(traffic_data)
    route_engine.display_route_recommendations("Pasar Minggu", "Gang Mawar", max_alternatives=3, min_alternatives=1)
    
    logging.info("\n📡 Starting real-time monitoring (press Ctrl+C to stop)...")
    dashboard.start_monitoring(interval_seconds=30)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        dashboard.stop_monitoring()

if __name__ == '__main__':
    logging.info("📍 File main.py starting...")
    logging.info("Starting main.py...")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--console':
        logging.info("Running in console mode...")
        run_console_mode()
    else:
        logging.info("Running in GUI...")
        try:
            app = QApplication(sys.argv)
            logging.info("✅ QApplication initialized")
            
            traffic_system = TrafficDataGenerator()
            logging.info("✅ TrafficDataGenerator initialized")
            
            if not hasattr(traffic_system, 'bengkulu_locations'):
                logging.error("❌ TrafficDataGenerator has no bengkulu_locations attribute")
                sys.exit(1)
            
            try:
                weather_api_key = "721ec4e5c0e36f2349bc8bbcd4025b60"
                route_engine = OptimizedRouteRecommendationEngine(traffic_system.bengkulu_locations, weather_api_key)
                logging.info("✅ RouteRecommendationEngine initialized")
            except Exception as e:
                logging.error(f"❌ Failed to initialize RouteRecommendationEngine: {str(e)}")
                logging.error("Debug: Check if osmnx is installed and network is available.")
                sys.exit(1)

            gui = TrafficMonitoringGUI(traffic_system, route_engine)
            logging.info("✅ EnhancedTrafficMonitoringGUI initialized")
            gui.show()
            logging.info("🖥️⬣🎉 GUI should be visible now...")
            
            sys.exit(app.exec_())
        except Exception as e:
            logging.error(f"❌ Failed to launch GUI: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            if 'gui' in locals():
                gui.status_bar.showMessage(f"Status: Failed to launch - {str(e)}")
            else:
                sys.exit(1)