import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import warnings
import os
import threading
import time
import datetime
import folium
import plotly.graph_objects as go
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

warnings.filterwarnings('ignore')

class TrafficVisualizer:
    def __init__(self, traffic_system):
        self.traffic_system = traffic_system
        plt.style.use('ggplot')
        sns.set_palette('husl')
        self.colors = {
            'Lancar': '#4CAF50',  # Hijau
            'Sedang': '#FFCA28',  # Kuning
            'Padat': '#FF5722',   # Oranye
            'Macet': '#D32F2F'    # Merah
        }

    def _validate_data(self, df, required_columns):
        if df is None or df.empty:
            logging.error("❌ DataFrame kosong atau None")
            return False
        if not all(col in df.columns for col in required_columns):
            missing = set(required_columns) - set(df.columns)
            logging.error(f"❌ Kolom yang hilang: {missing}")
            return False
        return True

    def _create_pie_chart(self, ax, data, labels, title):
        try:
            colors = sns.color_palette('Set2', len(data))
            wedges, texts, autotexts = ax.pie(
                data, labels=labels, autopct='%1.0f%%', startangle=90,
                textprops={'fontsize': 12, 'color': 'black'}, colors=colors, 
                shadow=True, explode=[0.05] * len(data)
            )
            for text in texts:
                text.set_fontsize(12)
                text.set_color('black')
                text.set_rotation(0)
            for autotext in autotexts:
                autotext.set_fontsize(10)
                autotext.set_color('black')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color='#333')
            ax.legend(labels, loc="best", bbox_to_anchor=(1, 0.5), fontsize=12)
        except Exception as e:
            logging.error(f"Error membuat diagram lingkaran '{title}': {e}")
            ax.set_title(f"Error: {title}", fontsize=12)

    def _create_bar(self, ax, x, y, labels, title, ylabel, colors=None):
        try:
            bars = ax.bar(range(len(labels)), y, color=colors or '#2196F3', edgecolor='black')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color='#333')
            ax.set_ylabel(ylabel, fontsize=14, color='#333')
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=12, color='#333')
            ax.tick_params(axis='both', labelsize=12, colors='#333')
            ax.grid(True, linestyle='--', alpha=0.5)
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + 0.02 * max(y),
                        f'{height:.1f}', ha='center', va='bottom', fontsize=10, color='#333')
        except Exception as e:
            logging.error(f"Error membuat diagram batang '{title}': {e}")
            ax.set_title(f"Error: {title}", fontsize=12)

    def _create_line_plot(self, ax, x, y, title, xlabel, ylabel, color='#9C27B0'):
        try:
            ax.plot(x, y, marker='o', linewidth=2, color=color)
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color='#333')
            ax.set_xlabel(xlabel, fontsize=14, color='#333')
            ax.set_ylabel(ylabel, fontsize=14, color='#333')
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.tick_params(axis='both', labelsize=12, colors='#333')
        except Exception as e:
            logging.error(f"Error membuat diagram garis '{title}': {e}")
            ax.set_title(f"Error: {title}", fontsize=12)

    def _create_scatter(self, ax, df, x_col, y_col, hue_col, title, xlabel, ylabel):
        try:
            for level in df[hue_col].unique():
                data = df[df[hue_col] == level]
                ax.scatter(data[x_col], data[y_col], c=self.colors.get(level, 'gray'),
                           label=level, alpha=0.6, s=80)
            ax.set_xlabel(xlabel, fontsize=14, color='#333')
            ax.set_ylabel(ylabel, fontsize=14, color='#333')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color='#333')
            ax.legend(fontsize=12, title_fontsize=14, loc='best')
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.tick_params(axis='both', labelsize=12, colors='#333')
        except Exception as e:
            logging.error(f"Error membuat diagram sebar '{title}': {e}")
            ax.set_title(f"Error: {title}", fontsize=12)

    def _create_horizontal_bar(self, ax, y, x, labels, title, xlabel):
        try:
            ax.barh(y=range(len(x)), width=x, color='#2196F3', edgecolor='black')
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels, fontsize=12, color='#333')
            ax.set_xlabel(xlabel, fontsize=14, color='#333')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color='#333')
            ax.tick_params(axis='both', labelsize=12, colors='#333')
            ax.grid(True, linestyle='--', alpha=0.5)
        except Exception as e:
            logging.error(f"Error membuat diagram batang horizontal '{title}': {e}")
            ax.set_title(f"Error: {title}", fontsize=12)

    def _create_heatmap(self, ax, data, title):
        try:
            sns.heatmap(data, annot=True, cmap='coolwarm', center=0, ax=ax,
                        fmt='.2f', annot_kws={'size': 12, 'color': 'black'})
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color='#333')
            ax.tick_params(axis='both', labelsize=12, colors='#333')
        except Exception as e:
            logging.error(f"Error membuat peta panas '{title}': {e}")
            ax.set_title(f"Error: {title}", fontsize=12)

    def create_visualizations(self, df):
        required_cols = ['location', 'hour', 'vehicle_count', 'traffic_level',
                         'congestion_ratio', 'avg_speed', 'weather_intensity',
                         'road_capacity', 'day_of_week', 'month']
        if not self._validate_data(df, required_cols):
            return

        logging.info("\n📊 Membuat Visualisasi Analisis Lalu Lintas (3 Halaman)...")
        logging.info("=" * 50)

        # Halaman 1: 4 Visualisasi
        fig1 = plt.figure(figsize=(22, 16), constrained_layout=True)
        gs1 = fig1.add_gridspec(2, 2, wspace=0.3, hspace=0.5)

        ax1 = fig1.add_subplot(gs1[0, 0])
        location_counts = df['location'].value_counts()
        top_locations = location_counts.head(5)
        self._create_pie_chart(ax1, top_locations.values, top_locations.index,
                              "Distribusi Lalu Lintas Berdasarkan Lokasi (5 Teratas)")

        ax2 = fig1.add_subplot(gs1[0, 1])
        hourly_traffic = df.groupby('hour')['vehicle_count'].mean()
        self._create_line_plot(ax2, hourly_traffic.index, hourly_traffic.values,
                              "Rata-Rata Jumlah Kendaraan per Jam", "Jam dalam Sehari", "Jumlah Kendaraan")

        ax3 = fig1.add_subplot(gs1[1, 0])
        traffic_dist = df['traffic_level'].value_counts()
        colors = [self.colors.get(level, 'gray') for level in traffic_dist.index]
        self._create_bar(ax3, traffic_dist.index, traffic_dist.values, traffic_dist.index,
                        "Distribusi Tingkat Lalu Lintas", "Jumlah", colors=colors)

        ax4 = fig1.add_subplot(gs1[1, 1])
        weekend_data = df.groupby(['is_weekend', 'traffic_level']).size().unstack(fill_value=0)
        weekend_data.plot(kind='bar', stacked=True, ax=ax4, color=[self.colors.get(level, 'gray')
                                                                  for level in weekend_data.columns])
        ax4.set_title("Lalu Lintas: Hari Kerja vs Akhir Pekan", fontsize=16, fontweight='bold', pad=20, color='#333')
        ax4.set_xlabel("Tipe Hari (0=Hari Kerja, 1=Akhir Pekan)", fontsize=14, color='#333')
        ax4.set_ylabel("Jumlah", fontsize=14, color='#333')
        ax4.legend(title="Tingkat Lalu Lintas", fontsize=12, title_fontsize=14, bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.tick_params(axis='both', labelsize=12, colors='#333')
        ax4.grid(True, linestyle='--', alpha=0.5)

        plt.show()
        logging.info("✅ Visualisasi Halaman 1 selesai!")

        # Halaman 2: 4 Visualisasi
        fig2 = plt.figure(figsize=(22, 16), constrained_layout=True)
        gs2 = fig2.add_gridspec(2, 2, wspace=0.3, hspace=0.5)

        ax5 = fig2.add_subplot(gs2[0, 0])
        self._create_scatter(ax5, df, 'congestion_ratio', 'avg_speed', 'traffic_level',
                            "Kecepatan vs Rasio Kemacetan", "Rasio Kemacetan", "Kecepatan Rata-Rata (km/jam)")

        ax6 = fig2.add_subplot(gs2[0, 1])
        monthly_traffic = df.groupby('month')['vehicle_count'].mean()
        self._create_bar(ax6, monthly_traffic.index, monthly_traffic.values, monthly_traffic.index,
                        "Rata-Rata Jumlah Kendaraan per Bulan", "Jumlah Kendaraan")

        ax7 = fig2.add_subplot(gs2[1, 0])
        weather_bins = pd.cut(df['weather_intensity'], bins=5,
                             labels=['Sangat Rendah', 'Rendah', 'Sedang', 'Tinggi', 'Sangat Tinggi'],
                             include_lowest=True)
        weather_traffic = df.groupby(weather_bins, observed=True)['avg_speed'].mean()
        self._create_bar(ax7, weather_traffic.index, weather_traffic.values, weather_traffic.index,
                        "Dampak Cuaca terhadap Kecepatan", "Kecepatan Rata-Rata (km/jam)", colors='#FF5722')
        ax7.tick_params(axis='x', rotation=45, labelsize=12, colors='#333')

        ax8 = fig2.add_subplot(gs2[1, 1])
        top_locations = df.groupby('location')['vehicle_count'].mean().nlargest(10)
        self._create_horizontal_bar(ax8, range(len(top_locations)), top_locations.values,
                                   top_locations.index, "10 Lokasi Tersibuk", "Rata-Rata Jumlah Kendaraan")

        plt.show()
        logging.info("✅ Visualisasi Halaman 2 selesai!")

        # Halaman 3: 4 Visualisasi
        fig3 = plt.figure(figsize=(22, 16), constrained_layout=True)
        gs3 = fig3.add_gridspec(2, 2, wspace=0.3, hspace=0.5)

        ax9 = fig3.add_subplot(gs3[0, 0])
        df = df.copy()
        df['utilization'] = df['vehicle_count'] / df['road_capacity'].replace(0, 1)
        util_by_location = df.groupby('location')['utilization'].mean().sort_values(ascending=False).head(10)
        colors = ['#FFCA28'] * len(util_by_location)
        self._create_bar(ax9, range(len(util_by_location)), util_by_location.values, util_by_location.index,
                        "Pemanfaatan Kapasitas Jalan (10 Teratas)", "Rasio Pemanfaatan", colors=colors)
        ax9.set_xlabel("Lokasi", fontsize=14, color='#333')
        ax9.set_xticks(range(len(util_by_location)))
        ax9.set_xticklabels(util_by_location.index, rotation=45, ha='right', fontsize=12, color='#333')

        ax10 = fig3.add_subplot(gs3[0, 1])
        day_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        daily_pattern = df.groupby('day_of_week')['vehicle_count'].mean()
        self._create_line_plot(ax10, daily_pattern.index, daily_pattern.values,
                              "Lalu Lintas Berdasarkan Hari", "Hari dalam Seminggu", "Jumlah Kendaraan",
                              color='#2196F3')
        ax10.set_xticks(range(7))
        ax10.set_xticklabels(day_names)

        ax11 = fig3.add_subplot(gs3[1, 0])
        rush_hours = df[df['hour'].isin([7, 8, 17, 18, 19])]
        rush_analysis = rush_hours.groupby(['hour', 'traffic_level']).size().unstack(fill_value=0)
        rush_analysis.plot(kind='bar', stacked=True, ax=ax11, color=[self.colors.get(level, 'gray')
                                                                    for level in rush_analysis.columns])
        ax11.set_title("Analisis Lalu Lintas Jam Sibuk", fontsize=16, fontweight='bold', pad=20, color='#333')
        ax11.set_xlabel("Jam", fontsize=14, color='#333')
        ax11.set_ylabel("Jumlah", fontsize=14, color='#333')
        ax11.legend(title="Tingkat Lalu Lintas", fontsize=12, title_fontsize=14, bbox_to_anchor=(1.05, 1), loc='upper left')
        ax11.tick_params(axis='both', labelsize=12, colors='#333')
        ax11.grid(True, linestyle='--', alpha=0.5)

        ax12 = fig3.add_subplot(gs3[1, 1])
        numeric_cols = ['hour', 'day_of_week', 'vehicle_count', 'avg_speed',
                       'congestion_ratio', 'weather_intensity']
        corr_matrix = df[numeric_cols].corr(numeric_only=True)
        self._create_heatmap(ax12, corr_matrix, "Korelasi Fitur Lalu Lintas")

        plt.show()
        logging.info("✅ Visualisasi Halaman 3 selesai!")
        logging.info("✅ Semua visualisasi (3 halaman) selesai!")

    def create_interactive_dashboard(self, df):
        if not self._validate_data(df, ['location', 'vehicle_count', 'avg_speed', 'traffic_level']):
            return

        logging.info("\n🌐 Membuat Dashboard Interaktif...")
        logging.info("=" * 50)

        fig = go.Figure(data=[
            go.Bar(
                x=df['location'].value_counts().index,
                y=df['location'].value_counts().values,
                marker_color=[self.colors.get(level, 'gray') for level in df['traffic_level']],
                text=df['location'].value_counts().values,
                textposition='auto'
            )
        ])
        fig.update_layout(
            title='Jumlah Kendaraan per Lokasi',
            xaxis_title='Lokasi',
            yaxis_title='Jumlah Kendaraan',
            template='plotly_dark',
            font=dict(size=14)
        )

        fig2 = go.Figure(data=[
            go.Scatter(
                x=df['congestion_ratio'],
                y=df['avg_speed'],
                mode='markers',
                marker=dict(color=[self.colors.get(level, 'gray') for level in df['traffic_level']], size=10),
                text=df['location']
            )
        ])
        fig2.update_layout(
            title='Kecepatan vs Rasio Kemacetan',
            xaxis_title='Rasio Kemacetan',
            yaxis_title='Kecepatan Rata-Rata (km/jam)',
            template='plotly_dark',
            font=dict(size=14)
        )

        fig.show()
        fig2.show()
        logging.info("✅ Dashboard interaktif selesai!")

class RealTimeMonitoringDashboard:
    def __init__(self, traffic_system, route_engine):
        self.traffic_system = traffic_system
        self.route_engine = route_engine
        self.monitoring_active = False
        self.monitoring_thread = None
        self.current_data = None
        self.icons = {
            'Lancar': '🟢',
            'Sedang': '🟡',
            'Padat': '🟠',
            'Macet': '🔴',
            'alert': '⚠'
        }
        self.available_locations = list(traffic_system.bengkulu_locations.keys())
        self.custom_route = None
        self.sample_routes = [
            ('Pasar Minggu', 'Unib'),
            ('Mall Bengkulu', 'Pantai Panjang'),
            ('Simpang Lima', 'Kantor Gubernur Bengkulu'),
            ('RSUD Dr. M. Yunus', 'Pasar Barukoto'),
        ]

    def start_monitoring(self, interval_seconds=5):
        try:
            if not hasattr(self.traffic_system, 'generate_enhanced_bengkulu_data'):
                logging.error("❌ Sistem lalu lintas tidak memiliki metode pembuatan data")
                return

            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(interval_seconds,),
                daemon=True
            )
            self.monitoring_thread.start()
            logging.info(f"\n📋 Pemantauan real-time dimulai (update setiap {interval_seconds} detik)")
        except Exception as e:
            logging.error(f"❌ Gagal memulai pemantauan: {e}")

    def stop_monitoring(self):
        try:
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5.0)
                self.monitoring_thread = None
                logging.info("⏹ Pemantauan real-time dihentikan")
        except Exception as e:
            logging.error(f"❌ Gagal menghentikan pemantauan: {e}")

    def _monitoring_loop(self, interval):
        while self.monitoring_active:
            try:
                current_traffic = self.traffic_system.generate_enhanced_bengkulu_data(15)
                if not current_traffic.empty:
                    self.current_data = current_traffic
                    self.route_engine.update_traffic_conditions(current_traffic)
                    self._display_dashboard()
                    logging.info(f"✅ Data lalu lintas diperbarui pada {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    logging.warning("⚠ Data lalu lintas kosong diterima")
                time.sleep(interval)
            except Exception as e:
                logging.error(f"❌ Error pemantauan: {e}")
                self.monitoring_active = False
                break

    def _display_dashboard(self):
        if self.current_data is None or self.current_data.empty:
            logging.error("❌ Tidak ada data untuk dashboard")
            return

        os.system('cls' if os.name == 'nt' else 'clear')
        print("📊 Dashboard Pemantauan Lalu Lintas Real-Time")
        print(f"🕒 Pembaruan Terakhir: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        total_vehicles = self.current_data['vehicle_count'].sum()
        avg_speed = self.current_data['avg_speed'].mean()
        congested_locations = len(self.current_data[self.current_data['traffic_level'] == 'Macet'])
        print("\n📈 Ringkasan Lalu Lintas")
        print(f"{'Jumlah Kendaraan':<25}: {total_vehicles:>8}")
        print(f"{'Kecepatan Rata-Rata':<25}: {avg_speed:>8.1f} km/jam")
        print(f"{'Area Macet':<25}: {congested_locations:>8}")

        print("\n🚦 Kondisi Lalu Lintas Saat Ini (10 Lokasi Teratas)")
        print("-" * 70)
        print(f"{'Lokasi':<25} {'Kendaraan':>12} {'Kecepatan':>12} {'Status':>12}")
        print("-" * 70)
        for _, row in self.current_data.nlargest(10, 'vehicle_count').iterrows():
            icon = self.icons.get(row['traffic_level'], '🔵')
            print(f"{icon} {row['location']:<23} {row['vehicle_count']:>12} {row['avg_speed']:>12.1f} {row['traffic_level']:>12}")

        print("\n🚨 Peringatan Aktif")
        print("-" * 70)
        critical_locations = self.current_data[
            (self.current_data['congestion_ratio'] > 0.7) | (self.current_data['avg_speed'] < 20)
        ]
        if not critical_locations.empty:
            for _, alert in critical_locations.iterrows():
                print(f"{self.icons['alert']} {alert['location']:<25} Kemacetan berat terdeteksi!")
        else:
            print("✅ Tidak ada peringatan kritis saat ini")

        print("\n🛣 Rekomendasi Rute Kustom")
        print("-" * 70)
        if not self.custom_route:
            print("📍 Masukkan lokasi awal dan tujuan untuk rekomendasi rute.")
            print(f"Lokasi tersedia: {', '.join(self.available_locations)}")
            start = input("Masukkan lokasi awal: ").strip()
            end = input("Masukkan lokasi tujuan: ").strip()
            mode = input("Masukkan moda transportasi (Jalan Kaki/Mobil/Motor): ").strip().lower()
            mode_mapping = {'jalan kaki': 'walking', 'mobil': 'car', 'motor': 'motorcycle'}
            mode = mode_mapping.get(mode, 'car')
            if start in self.available_locations and end in self.available_locations:
                self.custom_route = (start, end, mode)
                print(f"✅ Rute kustom diatur: {start} → {end} via {mode}")
            else:
                print("❌ Lokasi tidak valid. Menggunakan rute default.")
                self.custom_route = None

        print("\n🛣 Rekomendasi Rute Real-Time dengan Peta")
        print("-" * 70)
        routes_to_display = []
        if self.custom_route:
            routes_to_display.append(self.custom_route)
        routes_to_display.extend([(s, e, 'car') for s, e in self.sample_routes])

        for start, dest, mode in routes_to_display:
            print(f"\n🚗 Rute dari {start} ke {dest} ({mode}):")
            routes = self.route_engine.get_alternative_routes(start, dest, max_alternatives=3)
            if routes:
                for idx, route in enumerate([r for r in routes if r['mode'] == mode], 1):
                    quality_icon = "🟢" if route['route_quality'] == 'Good' else "🟡" if route['route_quality'] == 'Fair' else "🔴"
                    print(f"\n{quality_icon} Rute {idx}: {start} → {dest} ({mode})")
                    print(f"   📏 Jarak: {route['total_distance']} km")
                    print(f"   ⏱ Estimasi Waktu: {route['estimated_time']} menit")
                    print(f"   🚦 Tingkat Kemacetan: {route['congestion_level']}")
                    print(f"   ⭐ Kualitas Rute: {route['route_quality']}")

                    map_filename = f"peta_rute_{start.lower().replace(' ', '_')}_ke_{dest.lower().replace(' ', '_')}_{mode}_{idx}.html"
                    map_file = self.route_engine.create_route_map(route, map_filename)
                    if map_file and os.path.exists(map_file):
                        print(f"   🗺 Peta Interaktif: Buka '{map_file}' di browser untuk melihat rute.")
                        print(f"   📂 Lokasi file: {os.path.abspath(map_file)}")
                    else:
                        print(f"   ❌ Gagal membuat atau menemukan file peta: {map_file}")
            else:
                print(f"❌ Tidak ditemukan rute: {start} → {dest} via {mode}")

        print("\n" + "=" * 70)
        print("ℹ Tekan Ctrl+C untuk menghentikan pemantauan atau masukkan rute kustom baru pada pembaruan berikutnya")