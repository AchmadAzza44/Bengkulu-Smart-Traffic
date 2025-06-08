import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytz
import logging

logging.basicConfig(level=logging.INFO)

class TrafficDataGenerator:
    def __init__(self):
        self.weather_conditions = ['Cerah', 'Hujan Ringan', 'Hujan Lebat']
        self.traffic_levels = ['Lancar', 'Sedang', 'Padat', 'Macet']
        self.road_types = ['arterial', 'collector', 'highway', 'local']
        self.bengkulu_locations = {
            'Pasar Minggu': [-3.795212421885914, 102.26642346750113],
            'Unib': [-3.7586595451193867, 102.27251927605995],
            'Mega Mall Bengkulu': [-3.7934621203876135, 102.26682606750101],
            'Bandara Fatmawati': [-3.8604219973135545, 102.33940522517231],
            'Pantai Panjang': [-3.8059338665369626, 102.26266711178698],
            'RSUD Dr. M. Yunus': [-3.834000341829357, 102.31399499448848],
            'RSUD Ummi Bengkulu': [-3.8278284638525935, 102.31254938469135],
            'RSUD DKT Bengkulu': [-3.8173470055947836, 102.30952021167856],
            'RSUD Bhayangkara Bengkulu': [-3.7928922663183555, 102.2551855553066],
            'RSUD Raflessia Bengkulu': [-3.796551453369947, 102.27033395215926],
            'RSUD Gading Medika ': [-3.8385010055682525, 102.29988944051404],
            'Masjid Jamik': [-3.7921047732575657, 102.26230389448831],
            'Fort Marlborough': [-3.787108888055518, 102.25187954421024],
            'Simpang Lima': [-3.7972108852675914, 102.2659721656528],
            'Kampus IAIN': [-3.8345755950087703, 102.32677828469133],
            'Bencoolen Mall': [-3.811403145104594, 102.26823998284303],
            'Stadion Semarak': [-3.79302403217433, 102.27290824051377],
            'Pasar Panorama': [-3.8156627496656457, 102.29987162332382],
            'Pelabuhan Pulau Baai': [-3.907446983141679, 102.30551696750155],
            'Kantor Gubernur Bengkulu': [-3.8207211863982824, 102.2839554098303],
            'Taman Pantai Berkas': [-3.7991473910261364, 102.25514278284298],
            'SMAN 1 Bengkulu': [-3.8224166116949023, 102.28022002332396],
            'SMAN 4 Bengkulu': [-3.81795962582216, 102.30838168284306],
            'Pasar Barukoto': [-3.7882637398269368, 102.25061048284293],
            'Rumah Pengasingan Bung Karno': [-3.7987119383101406, 102.26126433866563],
            'Polresta Bengkulu': [-3.7891853971341356, 102.252076625172],
            'Museum Bengkulu': [-3.815511625397444, 102.28759528284307],
            'Taman Remaja': [-3.821902131480549, 102.30241234051401],
            'Pasar Tradisional Bawah': [-3.815511625397444, 102.28759528284307],
            'Simpang Baru': [-3.8000, 102.2700],
            'Persimpangan Utama': [-3.7950, 102.2650],
            'Gang Mawar': [-3.7945, 102.2585],
            'Jalan Sudirman': [-3.7970, 102.2605],
            'Gang Melati': [-3.7985, 102.2625],
            'Simpang Tiga Baru': [-3.7995, 102.2675],
            'Jalan Kapten Tendean': [-3.8025, 102.2695],
            'Gang Flamboyan': [-3.8030, 102.2660],
            'Jalan Letjen Suprapto': [-3.7915, 102.2545],
            'Simpang Empat Veteran': [-3.7895, 102.2555],
            'Gang Kamboja': [-3.7875, 102.2535],
            'Jalan Ahmad Yani': [-3.7855, 102.2525],
        }
        self.holidays = [
            datetime(2025, 1, 1),
            datetime(2025, 4, 18),
            datetime(2025, 12, 25),
        ]

    def _generate_base_traffic(self, num_records):
        np.random.seed(42)
        data = []
        start_time = datetime.now()
        wib = pytz.timezone('Asia/Jakarta')

        for i in range(num_records):
            location = np.random.choice(list(self.bengkulu_locations.keys()))
            timestamp = start_time + timedelta(minutes=i * 5)
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            month = timestamp.month
            is_weekend = 1 if day_of_week >= 5 else 0
            is_holiday = 1 if any((timestamp.date() == holiday.date() for holiday in self.holidays)) else 0

            base_vehicle_count = np.random.normal(100, 30)
            if 6 <= hour <= 9 or 16 <= hour <= 19:
                base_vehicle_count *= np.random.uniform(1.5, 2.0)
            elif 22 <= hour <= 3:
                base_vehicle_count *= np.random.uniform(0.3, 0.6)
            if is_weekend or is_holiday:
                base_vehicle_count *= np.random.uniform(0.7, 0.9)

            event_factor = 1.0
            if np.random.random() < 0.05:
                event_factor = np.random.uniform(1.5, 3.0)
                logging.info(f"🚨 Random event (e.g., accident) at {location}, time: {timestamp}")

            weather = np.random.choice(self.weather_conditions, p=[0.6, 0.3, 0.1])
            weather_intensity = {'Cerah': 0, 'Hujan Ringan': 0.5, 'Hujan Lebat': 1.0}[weather]
            if weather != 'Cerah':
                base_vehicle_count *= (1 + weather_intensity * 0.4)

            vehicle_count = max(10, int(base_vehicle_count * event_factor))

            road_type = np.random.choice(self.road_types, p=[0.4, 0.3, 0.2, 0.1])
            road_capacity = {
                'arterial': np.random.normal(300, 50),
                'collector': np.random.normal(200, 30),
                'highway': np.random.normal(400, 60),
                'local': np.random.normal(100, 20)
            }[road_type]
            congestion_ratio = min(1.0, vehicle_count / max(road_capacity, 1))

            base_speed = np.random.normal(40, 10)
            avg_speed = max(5, base_speed * (1 - congestion_ratio * 0.8) / event_factor)

            if congestion_ratio < 0.3:
                traffic_level = 'Lancar'
            elif congestion_ratio < 0.5:
                traffic_level = 'Sedang'
            elif congestion_ratio < 0.7:
                traffic_level = 'Padat'
            else:
                traffic_level = 'Macet'

            data.append({
                'location': location,
                'timestamp': timestamp,
                'hour': hour,
                'day_of_week': day_of_week,
                'month': month,
                'is_weekend': is_weekend,
                'is_holiday': is_holiday,
                'weather': weather,
                'weather_intensity': weather_intensity,
                'vehicle_count': vehicle_count,
                'road_capacity': road_capacity,
                'congestion_ratio': congestion_ratio,
                'avg_speed': avg_speed,
                'traffic_level': traffic_level,
                'road_type': road_type,
                'event_factor': event_factor
            })

        df = pd.DataFrame(data)
        if df.empty:
            logging.warning(f"⚠ Generated empty traffic data at {datetime.now(wib).strftime('%H:%M:%S')}")
        else:
            logging.info(f"✅ Generated {len(df)} traffic records at {datetime.now(wib).strftime('%H:%M:%S')}")
        return df

    def generate_enhanced_bengkulu_data(self, num_records):
        num_records = min(num_records, 30)
        df = self._generate_base_traffic(num_records)
        if df.empty:
            logging.warning("⚠ No data to enhance, returning empty DataFrame")
            return df
        df['day_of_week'] = df['timestamp'].dt.weekday
        df['month'] = df['timestamp'].dt.month
        df['is_central'] = df['location'].apply(
            lambda x: 1 if x in ['Simpang Lima', 'Mall Bengkulu', 'Masjid Jamik', 'Simpang Baru', 'Persimpangan Utama'] else 0
        )
        df['hour_weather_interaction'] = df['hour'] * df['weather_intensity']
        return df