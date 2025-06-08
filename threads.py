from PyQt5.QtCore import QThread, pyqtSignal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RouteCalculationThread(QThread):
    routes_calculated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, route_engine, start_location, end_location, mode='car', max_alternatives=3, min_alternatives=1):
        super().__init__()
        self.route_engine = route_engine
        self.start_location = start_location
        self.end_location = end_location
        self.mode = mode
        self.max_alternatives = max_alternatives
        self.min_alternatives = min_alternatives
        logging.info(f"Inisialisasi RouteCalculationThread untuk {start_location} ke {end_location} dengan mode {mode}")
    
    def run(self):
        try:
            logging.info(f"Menjalankan perhitungan rute dari {self.start_location} ke {self.end_location}")
            
            # Validasi lokasi
            start_node = self.route_engine.location_nodes.get(self.start_location)
            end_node = self.route_engine.location_nodes.get(self.end_location)
            
            if start_node is None or end_node is None:
                invalid_locations = []
                if start_node is None:
                    invalid_locations.append(self.start_location)
                if end_node is None:
                    invalid_locations.append(self.end_location)
                error_msg = f"❌ Lokasi tidak valid: {', '.join(invalid_locations)}"
                logging.error(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            logging.info(f"✅ Lokasi divalidasi: {self.start_location} dan {self.end_location}")
            
            # Panggil get_alternative_routes dengan mode yang sesuai
            routes = self.route_engine.get_alternative_routes(
                self.start_location,
                self.end_location,
                mode=self.mode,
                max_alternatives=self.max_alternatives,
                min_alternatives=self.min_alternatives
            )
            logging.info(f"Berhasil menghitung {len(routes)} rute")
            self.routes_calculated.emit(routes)
        except Exception as e:
            error_msg = f"❌ Error dalam perhitungan rute: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
