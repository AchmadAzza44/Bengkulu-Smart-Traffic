from PyQt5.QtCore import QThread, pyqtSignal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RouteCalculationThread(QThread):
    routes_calculated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, route_engine, start_location, end_location, max_alternatives=3, min_alternatives=1):
        super().__init__()
        self.route_engine = route_engine
        self.start_location = start_location
        self.end_location = end_location
        self.max_alternatives = max_alternatives
        self.min_alternatives = min_alternatives
        logging.info(f"Inisialisasi RouteCalculationThread untuk {start_location} ke {end_location}")
    
    def run(self):
        try:
            logging.info(f"Menjalankan perhitungan rute dari {self.start_location} ke {self.end_location}")
            routes = self.route_engine.get_alternative_routes(
                self.start_location, 
                self.end_location, 
                None,
                self.max_alternatives, 
                self.min_alternatives
            )
            logging.info(f"Berhasil menghitung {len(routes)} rute")
            self.routes_calculated.emit(routes)
        except Exception as e:
            logging.error(f"Error dalam perhitungan rute: {str(e)}", exc_info=True)
            self.error_occurred.emit(str(e))