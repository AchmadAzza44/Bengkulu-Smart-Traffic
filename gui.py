# File: gui.py
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QComboBox, QTextEdit, QTabWidget, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QProgressDialog)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import webbrowser
import os
import logging
from threads import RouteCalculationThread

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataUpdateThread(QThread):
    data_updated = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, traffic_system, route_engine):
        super().__init__()
        self.traffic_system = traffic_system
        self.route_engine = route_engine
    
    def run(self):
        try:
            data = self.traffic_system.generate_enhanced_bengkulu_data(30)
            self.route_engine.update_traffic_conditions(data)
            self.data_updated.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class MapGenerationThread(QThread):
    map_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, traffic_system, current_data):
        super().__init__()
        self.traffic_system = traffic_system
        self.current_data = current_data
    
    def run(self):
        try:
            import folium
            from folium.plugins import HeatMap
            bengkulu_center = [-3.8000, 102.2667]
            m = folium.Map(location=bengkulu_center, zoom_start=13)
            heat_data = []
            for _, row in self.current_data.iterrows():
                loc = self.traffic_system.bengkulu_locations.get(row['location'])
                if loc:
                    heat_data.append([loc[0], loc[1], row['congestion_ratio']])
            HeatMap(heat_data, name="Tingkat Kemacetan").add_to(m)
            for loc_name, coords in self.traffic_system.bengkulu_locations.items():
                folium.Marker(coords, popup=loc_name, icon=folium.Icon(color='blue')).add_to(m)
            map_file = "peta_kemacetan.html"
            m.save(map_file)
            self.map_generated.emit(map_file)
        except Exception as e:
            self.error_occurred.emit(str(e))

class TrafficMonitoringGUI(QMainWindow):
    def __init__(self, traffic_system, route_engine):
        super().__init__()
        self.traffic_system = traffic_system
        self.route_engine = route_engine
        self.current_data = None
        self.route_thread = None
        self.data_thread = None
        self.map_thread = None
        self.init_ui()
        self.start_data_update()
        
    def init_ui(self):
        self.setWindowTitle('Sistem Pemantauan Lalu Lintas Kota Bengkulu')
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply a global stylesheet for consistent look
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f4f8;
            }
            QLabel {
                color: #2c3e50;
            }
            QPushButton {
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background-color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: #ffffff;
            }
            QTabBar::tab {
                padding: 12px 25px;
                min-width: 150px;
                font-size: 14px;
                color: #2c3e50;
                background-color: #ecf0f1;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                font-weight: bold;
            }
        """)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.create_monitoring_tab()
        self.create_early_warning_tab()
        self.create_route_recommendation_tab()
        self.create_visualization_tab()
        
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #ecf0f1;
                color: #2c3e50;
                font-size: 13px;
                padding: 5px;
            }
        """)
        self.status_bar.showMessage("Sistem siap - Menunggu data...")
        
        refresh_btn = QPushButton("Perbarui Data")
        refresh_btn.setStyleSheet("""
            background-color: #27ae60;
            color: white;
        """)
        refresh_btn.clicked.connect(self.start_data_update)
        main_layout.addWidget(refresh_btn)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.start_data_update)
        self.timer.start(60000)  # Update setiap 60 detik
        
    def create_monitoring_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("Pemantauan Lalu Lintas Real-Time")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        layout.addWidget(title)
        
        self.overview_label = QLabel()
        self.overview_label.setStyleSheet("""
            font-size: 14px;
            padding: 15px;
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
        """)
        layout.addWidget(self.overview_label)
        
        self.traffic_table = QTableWidget()
        self.traffic_table.setColumnCount(5)
        self.traffic_table.setHorizontalHeaderLabels(["Lokasi", "Jumlah Kendaraan", "Kecepatan (km/jam)", "Rasio Kemacetan", "Status"])
        self.traffic_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.traffic_table.setStyleSheet("""
            QTableWidget {
                font-size: 13px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border: 1px solid #bdc3c7;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        layout.addWidget(self.traffic_table)
        
        self.tabs.addTab(tab, "Pemantauan")
        
    def create_early_warning_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("Sistem Peringatan Dini Kemacetan")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        layout.addWidget(title)
        
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        layout.addWidget(self.alerts_text)
        
        check_btn = QPushButton("Periksa Peringatan")
        check_btn.setStyleSheet("""
            background-color: #e67e22;
            color: white;
        """)
        check_btn.clicked.connect(self.check_alerts)
        layout.addWidget(check_btn)
        
        self.tabs.addTab(tab, "Peringatan Dini")
        
    def create_route_recommendation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("Rekomendasi Rute Perjalanan")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        layout.addWidget(title)
        
        route_layout = QHBoxLayout()
        route_layout.setSpacing(10)
        
        route_layout.addWidget(QLabel("Lokasi Awal:"))
        self.start_combo = QComboBox()
        self.start_combo.addItems(self.traffic_system.bengkulu_locations.keys())
        route_layout.addWidget(self.start_combo)
        
        route_layout.addWidget(QLabel("Lokasi Tujuan:"))
        self.end_combo = QComboBox()
        self.end_combo.addItems(self.traffic_system.bengkulu_locations.keys())
        route_layout.addWidget(self.end_combo)
        
        route_layout.addWidget(QLabel("Moda Transportasi:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Jalan Kaki", "Mobil", "Motor"])
        route_layout.addWidget(self.mode_combo)
        
        layout.addLayout(route_layout)
        
        self.get_routes_btn = QPushButton("Dapatkan Rekomendasi Rute")
        self.get_routes_btn.setStyleSheet("""
            background-color: #2980b9;
            color: white;
        """)
        self.get_routes_btn.clicked.connect(self.get_route_recommendations)
        layout.addWidget(self.get_routes_btn)
        
        self.routes_text = QTextEdit()
        self.routes_text.setReadOnly(True)
        layout.addWidget(self.routes_text)
        
        # Tambahkan tombol "Cari Rute Lagi" dan "Selesai"
        self.cari_lagi_btn = QPushButton("Cari Rute Lagi")
        self.cari_lagi_btn.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            margin-top: 10px;
        """)
        self.cari_lagi_btn.clicked.connect(self.get_route_recommendations)
        self.cari_lagi_btn.hide()  # Sembunyikan awalnya
        layout.addWidget(self.cari_lagi_btn)
        
        self.selesai_btn = QPushButton("Selesai")
        self.selesai_btn.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            margin-top: 10px;
        """)
        self.selesai_btn.clicked.connect(self.reset_route_recommendation)
        self.selesai_btn.hide()  # Sembunyikan awalnya
        layout.addWidget(self.selesai_btn)
        
        self.tabs.addTab(tab, "Rekomendasi Rute")
        
    def create_visualization_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("Visualisasi Data Lalu Lintas")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        layout.addWidget(title)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        traffic_btn = QPushButton("Tampilkan Grafik Lalu Lintas")
        traffic_btn.setStyleSheet("""
            background-color: #8e44ad;
            color: white;
        """)
        traffic_btn.clicked.connect(self.show_traffic_visualization)
        btn_layout.addWidget(traffic_btn)
        
        congestion_btn = QPushButton("Tampilkan Peta Kemacetan")
        congestion_btn.setStyleSheet("""
            background-color: #8e44ad;
            color: white;
        """)
        congestion_btn.clicked.connect(self.show_congestion_map)
        btn_layout.addWidget(congestion_btn)
        
        layout.addLayout(btn_layout)
        
        self.vis_info = QLabel("Pilih visualisasi yang ingin ditampilkan")
        self.vis_info.setStyleSheet("""
            font-size: 14px;
            padding: 15px;
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
        """)
        layout.addWidget(self.vis_info)
        
        self.tabs.addTab(tab, "Visualisasi")
        
    def start_data_update(self):
        self.status_bar.showMessage("Memperbarui data...")
        if self.data_thread and self.data_thread.isRunning():
            self.data_thread.terminate()
            
        self.data_thread = DataUpdateThread(self.traffic_system, self.route_engine)
        self.data_thread.data_updated.connect(self.on_data_updated)
        self.data_thread.error_occurred.connect(self.on_data_error)
        self.data_thread.start()
        
    def on_data_updated(self, data):
        self.current_data = data
        self.update_monitoring_tab()
        self.status_bar.showMessage("Data diperbarui - " + self.get_current_time())
        
    def on_data_error(self, error):
        logging.error(f"Gagal memperbarui data: {error}")
        self.status_bar.showMessage("Gagal memperbarui data")
        
    def update_monitoring_tab(self):
        if self.current_data is None:
            return
            
        total_vehicles = self.current_data['vehicle_count'].sum()
        avg_speed = self.current_data['avg_speed'].mean()
        congested = len(self.current_data[self.current_data['traffic_level'] == 'Macet'])
        
        overview_text = (
            f"📊 <b>Ringkasan Kondisi Lalu Lintas:</b><br>"
            f"🚗 Jumlah Kendaraan: {total_vehicles:,}<br>"
            f"🏎 Kecepatan Rata-Rata: {avg_speed:.1f} km/jam<br>"
            f"⚠ Area Macet: {congested}"
        )
        self.overview_label.setText(overview_text)
        
        self.traffic_table.setRowCount(len(self.current_data))
        
        for i, row in self.current_data.iterrows():
            self.traffic_table.setItem(i, 0, QTableWidgetItem(row['location']))
            self.traffic_table.setItem(i, 1, QTableWidgetItem(str(row['vehicle_count'])))
            self.traffic_table.setItem(i, 2, QTableWidgetItem(f"{row['avg_speed']:.1f}"))
            self.traffic_table.setItem(i, 3, QTableWidgetItem(f"{row['congestion_ratio']:.2f}"))
            
            level_item = QTableWidgetItem(row['traffic_level'])
            if row['traffic_level'] == 'Macet':
                level_item.setBackground(Qt.red)
                level_item.setForeground(Qt.white)
            elif row['traffic_level'] == 'Padat':
                level_item.setBackground(Qt.darkYellow)
            elif row['traffic_level'] == 'Sedang':
                level_item.setBackground(Qt.yellow)
            else:
                level_item.setBackground(Qt.green)
                
            self.traffic_table.setItem(i, 4, level_item)
            
    def check_alerts(self):
        if self.current_data is None:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data untuk dianalisis")
            return
            
        critical = self.current_data[
            (self.current_data['congestion_ratio'] > 0.7) | 
            (self.current_data['avg_speed'] < 20)
        ]
        
        if critical.empty:
            self.alerts_text.setHtml("<h3>✅ Tidak ada peringatan kemacetan saat ini</h3>")
        else:
            alert_html = "<h3>🚨 Peringatan Kemacetan</h3><ul>"
            for _, row in critical.iterrows():
                alert_html += (
                    f"<li><b>{row['location']}</b>: "
                    f"Rasio Kemacetan {row['congestion_ratio']:.0%}, "
                    f"Kecepatan {row['avg_speed']:.1f} km/jam</li>"
                )
            alert_html += "</ul>"
            self.alerts_text.setHtml(alert_html)
            
    def get_route_recommendations(self):
        start_location = self.start_combo.currentText()
        end_location = self.end_combo.currentText()
        mode = self.mode_combo.currentText().lower()
        mode_mapping = {'jalan kaki': 'walking', 'mobil': 'car', 'motor': 'motorcycle'}
        mode = mode_mapping.get(mode, 'car')
        
        if start_location == end_location:
            QMessageBox.warning(self, "Peringatan", "Lokasi awal dan tujuan tidak boleh sama")
            return
            
        progress = QProgressDialog("Menghitung rute...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setStyleSheet("""
            QProgressDialog {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QLabel {
                color: #2c3e50;
            }
        """)
        progress.show()
        
        self.get_routes_btn.setEnabled(False)
        
        if self.route_thread is not None and self.route_thread.isRunning():
            self.route_thread.terminate()
            self.route_thread.wait()
            
        try:
            self.route_thread = RouteCalculationThread(self.route_engine, start_location, end_location, max_alternatives=3)
            self.route_thread.routes_calculated.connect(
                lambda routes: self.on_routes_calculated(routes, start_location, end_location, mode, progress))
            self.route_thread.error_occurred.connect(
                lambda error: self.on_route_error(error, progress))
            self.route_thread.finished.connect(self.route_thread.deleteLater)
            self.route_thread.start()
        except Exception as e:
            logging.error(f"Error creating route thread: {str(e)}")
            progress.close()
            self.get_routes_btn.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Gagal membuat thread kalkulasi rute: {str(e)}")
        
    def on_routes_calculated(self, routes, start_loc, end_loc, mode, progress):
        progress.close()
        self.get_routes_btn.setEnabled(True)
        
        if not routes:
            self.routes_text.setHtml(f"<h3>❌ Tidak ditemukan rute dari {start_loc} ke {end_loc} via {mode}</h3>")
            return
            
        route_html = f"<h3>🛣 Rekomendasi Rute dari {start_loc} ke {end_loc} ({mode})</h3>"
        filtered_routes = [r for r in routes if r['mode'] == mode]
        if not filtered_routes:
            route_html += f"<p>Tidak ada rute untuk moda {mode}</p>"
        else:
            for i, route in enumerate(filtered_routes, 1):
                map_filename = f"rute_{start_loc.replace(' ', '_')}_{end_loc.replace(' ', '_')}_{mode}_{i}.html"
                map_path = self.route_engine.create_route_map(route, map_filename)
                route_html += (
                    f"<h4>Rute {i} ({route['mode']}):</h4>"
                    f"<ul>"
                    f"<li>📏 Jarak: {route['total_distance']:.2f} km</li>"
                    f"<li>⏱ Estimasi Waktu: {route['estimated_time']:.2f} menit</li>"
                    f"<li>🚦 Tingkat Kemacetan: {route['congestion_level']}</li>"
                    f"<li>⭐ Kualitas Rute: {route['route_quality']}</li>"
                )
                if map_path:
                    route_html += f'<li><a href="file:///{map_path}">🗺 Buka Peta Rute</a></li>'
                route_html += "</ul>"
        self.routes_text.setHtml(route_html)
        
        # Tampilkan tombol "Cari Rute Lagi" dan "Selesai" setelah hasil ditampilkan
        self.cari_lagi_btn.show()
        self.selesai_btn.show()
        
    def on_route_error(self, error, progress):
        progress.close()
        self.get_routes_btn.setEnabled(True)
        logging.error(f"Gagal mendapatkan rekomendasi rute: {error}")
        QMessageBox.critical(self, "Error", "Gagal mendapatkan rekomendasi rute")
        
    def reset_route_recommendation(self):
        # Reset tampilan dan sembunyikan tombol tambahan
        self.routes_text.clear()
        self.cari_lagi_btn.hide()
        self.selesai_btn.hide()
        self.get_routes_btn.setEnabled(True)
        
    def show_traffic_visualization(self):
        try:
            from visualization import TrafficVisualizer
            visualizer = TrafficVisualizer(self.traffic_system)
            visualizer.create_visualizations(self.current_data)
            self.vis_info.setText("Visualisasi ditampilkan di jendela terpisah")
        except Exception as e:
            logging.error(f"Gagal menampilkan visualisasi: {str(e)}")
            self.vis_info.setText("Gagal menampilkan visualisasi")
            
    def show_congestion_map(self):
        if self.current_data is None:
            self.vis_info.setText("Tidak ada data untuk peta kemacetan")
            return
            
        progress = QProgressDialog("Membuat peta kemacetan...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setStyleSheet("""
            QProgressDialog {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QLabel {
                color: #2c3e50;
            }
        """)
        progress.show()
        
        if self.map_thread and self.map_thread.isRunning():
            self.map_thread.terminate()
            
        self.map_thread = MapGenerationThread(self.traffic_system, self.current_data)
        self.map_thread.map_generated.connect(lambda map_file: self.on_map_generated(map_file, progress))
        self.map_thread.error_occurred.connect(lambda error: self.on_map_error(error, progress))
        self.map_thread.start()
        
    def on_map_generated(self, map_file, progress):
        progress.close()
        webbrowser.open(f"file://{os.path.abspath(map_file)}")
        self.vis_info.setText(f"Peta kemacetan disimpan sebagai {map_file}")
        
    def on_map_error(self, error, progress):
        progress.close()
        logging.error(f"Gagal membuat peta kemacetan: {error}")
        self.vis_info.setText("Gagal membuat peta kemacetan")
        
    def get_current_time(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")