from datetime import datetime

class EarlyWarningSystem:
    """🚨 Early Warning System for Traffic Congestion"""
    
    def __init__(self):
        self.alert_thresholds = {
            'CRITICAL': {'congestion_ratio': 0.8, 'avg_speed': 15},
            'HIGH': {'congestion_ratio': 0.6, 'avg_speed': 25},
            'MEDIUM': {'congestion_ratio': 0.4, 'avg_speed': 35},
            'LOW': {'congestion_ratio': 0.2, 'avg_speed': 45}
        }
        self.active_alerts = []
        
    def analyze_traffic_conditions(self, traffic_data):
        """Analyze current traffic and generate alerts"""
        alerts = []
        
        for _, row in traffic_data.iterrows():
            alert_level = self.determine_alert_level(row)
            
            if alert_level in ['CRITICAL', 'HIGH']:
                alert = {
                    'timestamp': datetime.now(),
                    'location': row['location'],
                    'alert_level': alert_level,
                    'congestion_ratio': row['congestion_ratio'],
                    'avg_speed': row['avg_speed'],
                    'vehicle_count': row['vehicle_count'],
                    'estimated_delay': self.calculate_delay(row),
                    'affected_routes': self.get_affected_routes(row['location'])
                }
                alerts.append(alert)
        
        self.active_alerts = alerts
        return alerts
    
    def determine_alert_level(self, traffic_row):
        """Determine alert level based on traffic conditions"""
        congestion = traffic_row['congestion_ratio']
        speed = traffic_row['avg_speed']
        
        if congestion >= 0.8 or speed <= 15:
            return 'CRITICAL'
        elif congestion >= 0.6 or speed <= 25:
            return 'HIGH'
        elif congestion >= 0.4 or speed <= 35:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def calculate_delay(self, traffic_row):
        """Calculate estimated delay in minutes"""
        normal_speed = 45
        current_speed = max(5, traffic_row['avg_speed'])
        distance = 5
        normal_time = (distance / normal_speed) * 60
        current_time = (distance / current_speed) * 60
        delay = max(0, current_time - normal_time)
        return round(delay, 1)
    
    def get_affected_routes(self, location):
        """Get routes affected by congestion"""
        route_map = {
            'Pasar Minggu': ['Jl. Ahmad Yani', 'Jl. Sudirman', 'Jl. Pariwisata'],
            'Unib': ['Jl. WR Supratman', 'Jl. Kandang Limun', 'Jl. Raya Unib'],
            'Mall Bengkulu': ['Jl. Ahmad Yani', 'Jl. Panorama', 'Jl. Zainul Arifin'],
            'Simpang Lima': ['Jl. Ahmad Yani', 'Jl. Sudirman', 'Jl. Suprapto', 'Jl. RE Martadinata'],
            'Terminal Panorama': ['Jl. Panorama', 'Jl. Veteran', 'Jl. Khadijah']
        }
        return route_map.get(location, ['Main Road'])
    
    def broadcast_alerts(self):
        """Broadcast active alerts"""
        print(f"\n🚨 EARLY WARNING SYSTEM - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        if not self.active_alerts:
            print("✅ No traffic alerts at this time")
            return
        
        for alert in self.active_alerts:
            icon = "🔴" if alert['alert_level'] == 'CRITICAL' else "🟡"
            print(f"\n{icon} {alert['alert_level']} ALERT - {alert['location']}")
            print(f"   🚗 Vehicle Count: {alert['vehicle_count']}")
            print(f"   🐌 Average Speed: {alert['avg_speed']} km/h")
            print(f"   📊 Congestion Ratio: {alert['congestion_ratio']:.2f}")
            print(f"   ⏱ Estimated Delay: {alert['estimated_delay']} minutes")
            print(f"   🛣 Affected Routes: {', '.join(alert['affected_routes'])}")
            if alert['alert_level'] == 'CRITICAL':
                print(f"   💡 RECOMMENDATION: Avoid this area, use alternative routes")
            else:
                print(f"   💡 RECOMMENDATION: Expect moderate delays")
