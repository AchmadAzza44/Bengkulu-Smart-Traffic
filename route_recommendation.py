import osmnx as ox
import networkx as nx
import folium
import logging
import pickle
import os
import numpy as np
import requests
from datetime import datetime, timedelta
import heapq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RouteRecommendationEngine:
    def __init__(self, bengkulu_locations, weather_api_key=None):
        self.road_network = None
        self.walking_network = None
        self.current_traffic = None
        self.bengkulu_locations = bengkulu_locations
        self.location_nodes = {}
        self.walking_nodes = {}
        self.weather_api_key = weather_api_key
        self._initialize_networks()
        self._map_locations_to_nodes()

    def _initialize_networks(self):
        logging.info("🌍 Mulai mengambil data OSM untuk Kota Bengkulu...")
        try:
            ox.settings.timeout = 60
            ox.settings.log_console = True
            ox.settings.use_cache = True
            ox.settings.cache_folder = "./osm_cache"
            os.makedirs("./osm_cache", exist_ok=True)

            # Cache for driving network (cars and motorcycles)
            drive_cache_file = "bengkulu_drive_graph.pkl"
            if os.path.exists(drive_cache_file):
                try:
                    with open(drive_cache_file, 'rb') as f:
                        G_drive = pickle.load(f)
                    logging.info("✅ Loaded driving network graph from cache")
                except Exception as e:
                    logging.warning(f"⚠ Drive cache file corrupted: {e}, downloading fresh data...")
                    G_drive = self._download_osm_graph('drive')
                    with open(drive_cache_file, 'wb') as f:
                        pickle.dump(G_drive, f)
            else:
                G_drive = self._download_osm_graph('drive')
                with open(drive_cache_file, 'wb') as f:
                    pickle.dump(G_drive, f)
                logging.info("✅ Saved driving network graph to cache")

            # Cache for walking network (pedestrians)
            walk_cache_file = "bengkulu_walk_graph.pkl"
            if os.path.exists(walk_cache_file):
                try:
                    with open(walk_cache_file, 'rb') as f:
                        G_walk = pickle.load(f)
                    logging.info("✅ Loaded walking network graph from cache")
                except Exception as e:
                    logging.warning(f"⚠ Walk cache file corrupted: {e}, downloading fresh data...")
                    G_walk = self._download_osm_graph('walk')
                    with open(walk_cache_file, 'wb') as f:
                        pickle.dump(G_walk, f)
            else:
                G_walk = self._download_osm_graph('walk')
                with open(walk_cache_file, 'wb') as f:
                    pickle.dump(G_walk, f)
                logging.info("✅ Saved walking network graph to cache")

            # Convert to directed graphs and validate nodes
            self.road_network = nx.DiGraph(G_drive)
            self.walking_network = nx.DiGraph(G_walk)

            # Remove nodes without coordinates from driving network
            invalid_nodes = [n for n, d in self.road_network.nodes(data=True) if 'x' not in d or 'y' not in d]
            self.road_network.remove_nodes_from(invalid_nodes)
            logging.info(f"🧹 Removed {len(invalid_nodes)} invalid nodes from driving network")

            # Process driving network (for cars and motorcycles)
            for u, v, data in self.road_network.edges(data=True):
                length = data.get('length', 1000)
                if not isinstance(length, (int, float)) or length <= 0:
                    logging.warning(f"⚠ Invalid length for edge ({u}, {v}): {length}, using default 1000m")
                    length = 1000
                data['weight'] = length / 1000
                speed = data.get('maxspeed', 40)
                try:
                    data['speed_limit'] = float(speed[0] if isinstance(speed, list) else speed.split()[0] if isinstance(speed, str) else speed)
                except:
                    data['speed_limit'] = 40
                data['preference'] = 1.0 if data.get('highway') in ['primary', 'secondary', 'tertiary'] else 1.5

            # Remove nodes without coordinates from walking network
            invalid_nodes = [n for n, d in self.walking_network.nodes(data=True) if 'x' not in d or 'y' not in d]
            self.walking_network.remove_nodes_from(invalid_nodes)
            logging.info(f"🧹 Removed {len(invalid_nodes)} invalid nodes from walking network")

            # Process walking network
            for u, v, data in self.walking_network.edges(data=True):
                length = data.get('length', 1000)
                if not isinstance(length, (int, float)) or length <= 0:
                    logging.warning(f"⚠ Invalid length for edge ({u}, {v}): {length}, using default 1000m")
                    length = 1000
                data['weight'] = length / 1000
                data['preference'] = 1.0 if data.get('highway') in ['path', 'footway', 'steps', 'residential'] else 1.2

            logging.info(f"✅ Driving graph: {len(self.road_network.nodes)} nodes, {len(self.road_network.edges)} edges")
            logging.info(f"✅ Walking graph: {len(self.walking_network.nodes)} nodes, {len(self.walking_network.edges)} edges")
        except Exception as e:
            logging.error(f"❌ Gagal mengambil data OSM: {str(e)}")
            raise

    def _download_osm_graph(self, network_type):
        try:
            G_city = ox.graph_from_place("Bengkulu, Indonesia", network_type=network_type, simplify=True)
            logging.info(f"✅ Downloaded OSM {network_type} data for Bengkulu City")
            G_detail = ox.graph_from_point((-3.8000, 102.2667), dist=15000, network_type=network_type, simplify=True)
            G = nx.compose(G_city, G_detail)
            return G
        except Exception as e:
            logging.warning(f"⚠ Failed to download {network_type} with graph_from_place: {e}, falling back to point-based...")
            G = ox.graph_from_point((-3.8000, 102.2667), dist=15000, network_type=network_type, simplify=True)
            logging.info(f"✅ Downloaded OSM {network_type} data using center point with 15 km radius")
            return G

    def _map_locations_to_nodes(self):
        for location, coords in self.bengkulu_locations.items():
            try:
                # Map to driving network (for cars and motorcycles)
                node = ox.distance.nearest_nodes(self.road_network, coords[1], coords[0])
                if not self.road_network.has_node(node):
                    logging.error(f"❌ Node {node} for {location} not in driving graph")
                    continue
                if 'x' not in self.road_network.nodes[node] or 'y' not in self.road_network.nodes[node]:
                    logging.error(f"❌ Node {node} for {location} missing coordinates in driving graph")
                    continue
                if len(list(self.road_network.edges(node))) == 0:
                    logging.warning(f"⚠ Node {node} for {location} has no edges in driving graph, finding nearest connected node...")
                    neighbors = [n for n in self.road_network.neighbors(node) if self.road_network.degree(n) > 0]
                    node = node if neighbors else ox.distance.nearest_nodes(self.road_network, coords[1], coords[0], return_dist=False)
                self.location_nodes[location] = node

                # Map to walking network
                walk_node = ox.distance.nearest_nodes(self.walking_network, coords[1], coords[0])
                if not self.walking_network.has_node(walk_node):
                    logging.error(f"❌ Node {walk_node} for {location} not in walking graph")
                    continue
                if 'x' not in self.walking_network.nodes[walk_node] or 'y' not in self.walking_network.nodes[walk_node]:
                    logging.error(f"❌ Node {walk_node} for {location} missing coordinates in walking graph")
                    continue
                if len(list(self.walking_network.edges(walk_node))) == 0:
                    logging.warning(f"⚠ Node {walk_node} for {location} has no edges in walking graph, finding nearest connected node...")
                    neighbors = [n for n in self.walking_network.neighbors(walk_node) if self.walking_network.degree(n) > 0]
                    walk_node = walk_node if neighbors else ox.distance.nearest_nodes(self.walking_network, coords[1], coords[0], return_dist=False)
                self.walking_nodes[location] = walk_node

                logging.info(f"✅ Mapped {location} to driving node {node} and walking node {walk_node} at coordinates {coords}")
            except Exception as e:
                logging.warning(f"⚠ Could not map {location}: {e}")

    def update_traffic_conditions(self, traffic_data, location_nodes_cache=None):
        self.current_traffic = traffic_data
        if self.current_traffic is not None:
            location_nodes = location_nodes_cache if location_nodes_cache is not None else self.location_nodes
            new_weights = {}
            relevant_nodes = set(location_nodes.values())
            for _, row in self.current_traffic.iterrows():
                location = row['location']
                congestion = row['congestion_ratio']
                avg_speed = row['avg_speed']
                weather_intensity = row.get('weather_intensity', 0.0)
                node = location_nodes.get(location)
                if node:
                    for u, v, data in self.road_network.edges(data=True):
                        if u in relevant_nodes or v in relevant_nodes:
                            base_weight = data.get('weight', 1.0)
                            speed_factor = max(0.5, data.get('speed_limit', 50) / max(avg_speed, 5))
                            weather_factor = 1 + (weather_intensity * 0.1)
                            preference_factor = data.get('preference', 1.0)
                            new_weights[(u, v)] = base_weight * (1 + congestion) * speed_factor * weather_factor * preference_factor
            nx.set_edge_attributes(self.road_network, new_weights, 'weight')
            logging.info("✅ Kondisi traffic di jaringan jalan diperbarui dengan faktor cuaca")

    def get_weather_data(self, lat=-3.80044, lon=102.26554):
        if not self.weather_api_key:
            logging.warning("⚠ No weather API key provided, using default weather intensity")
            return 0.0
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={-3.80044}&lon={102.26554}&appid=721ec4e5c0e36f2349bc8bbcd4025b60&units=metric"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            weather_desc = data['weather'][0]['main'].lower()
            intensity = 1.0 if 'rain' in weather_desc else 0.5 if 'clouds' in weather_desc else 0.0
            logging.info(f"✅ Weather data: {weather_desc}, intensity: {intensity}")
            return intensity
        except Exception as e:
            logging.error(f"❌ Failed to fetch weather data: {str(e)}")
            return 0.0

    def get_alternative_routes(self, start, end, departure_time=None, max_alternatives=5, min_alternatives=3, mode='car'):
        logging.info(f"🔍 Menghitung rute fleksibel dari {start} ke {end} at {departure_time or 'now'} for mode {mode}...")
        if start not in self.location_nodes or end not in self.location_nodes:
            logging.error(f"❌ Lokasi start atau end tidak valid: {start} → {end}")
            return []

        # Select network and nodes based on mode
        if mode == 'walking':
            network = self.walking_network
            start_node = self.walking_nodes[start]
            end_node = self.walking_nodes[end]
        else:  # car or motorcycle
            network = self.road_network
            start_node = self.location_nodes[start]
            end_node = self.location_nodes[end]

        alternative_routes = []
        temp_graph = network.copy()

        cache_key = f"{start}_{end}_{max_alternatives}_{mode}"
        cache_file = f"cache/routes_{cache_key}.pkl"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_routes = pickle.load(f)
                logging.info(f"✅ Memuat rute dari cache untuk {start} ke {end} mode {mode}")
                return cached_routes
            except:
                logging.warning(f"⚠ Cache rusak, menghitung ulang rute")

        try:
            # Gunakan A* untuk rute utama
            shortest_path = nx.astar_path(temp_graph, start_node, end_node, heuristic=self._heuristic, weight='weight')
            paths = [(shortest_path, 0)]  # (path, penalty)

            # Generate rute alternatif dengan penalti edge
            for i in range(max_alternatives - 1):
                new_path = self._generate_alternative_path(temp_graph, shortest_path, end_node, penalty_factor=1.2 + i * 0.2)
                if new_path and tuple(new_path) not in [tuple(p) for p, _ in paths]:
                    paths.append((new_path, 1.2 + i * 0.2))

            for path, _ in paths[:max_alternatives]:
                coordinates = []
                for node in path:
                    try:
                        node_data = temp_graph.nodes[node]
                        if 'y' in node_data and 'x' in node_data:
                            coordinates.append((node_data['y'], node_data['x']))
                        else:
                            logging.warning(f"⚠ Node {node} in path missing coordinates, skipping...")
                            continue
                    except Exception as e:
                        logging.warning(f"⚠ Error accessing coordinates for node {node}: {e}")
                        continue
                if len(coordinates) < 2:
                    logging.error(f"❌ Route path for {start} to {end} via {mode} has insufficient valid coordinates")
                    continue

                total_distance = self.calculate_distance(path, mode)
                estimated_time = self.estimate_time(path, departure_time, mode)
                congestion_level = self.analyze_congestion(path) if mode in ['car', 'motorcycle'] else "Low"
                route_quality = self.assess_route_quality(path, mode)

                route = {
                    'path': path,
                    'coordinates': coordinates,
                    'total_distance': total_distance,
                    'estimated_time': estimated_time,
                    'congestion_level': congestion_level,
                    'route_quality': route_quality,
                    'start_location': start,
                    'end_location': end,
                    'mode': mode
                }
                alternative_routes.append(route)

            alternative_routes.sort(key=lambda x: (x['total_distance'], x['estimated_time'], -1 if x['route_quality'] == "Good" else 0))
            alternative_routes = alternative_routes[:max_alternatives]

            os.makedirs("cache", exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(alternative_routes, f)
            logging.info(f"✅ Menyimpan rute ke cache untuk {start} ke {end} mode {mode}")

            return alternative_routes
        except Exception as e:
            logging.error(f"❌ Error menghitung rute: {str(e)}")
            return []

    def _heuristic(self, node1, node2, network=None):
        """Heuristic untuk algoritma A* berdasarkan jarak Euclidean"""
        try:
            network = network or self.road_network
            if node1 not in network.nodes or node2 not in network.nodes:
                raise ValueError(f"Node not found in network: node1={node1}, node2={node2}")
            data1, data2 = network.nodes[node1], network.nodes[node2]
            if 'x' not in data1 or 'y' not in data1 or 'x' not in data2 or 'y' not in data2:
                raise KeyError(f"Missing coordinates: node1={node1} ({data1}), node2={node2} ({data2})")
            x1, y1 = float(data1['x']), float(data1['y'])
            x2, y2 = float(data2['x']), float(data2['y'])
            distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) / 1000  # Konversi ke kilometer
            return distance
        except Exception as e:
            logging.warning(f"⚠ Error in heuristic calculation: node1={node1}, node2={node2}, error={str(e)}")
            return 0  # Fallback, tapi sebaiknya diperbaiki di masa depan

    def _generate_alternative_path(self, G, base_path, end_node, penalty_factor=1.2):
        try:
            if not base_path or len(base_path) < 2:
                return None
            temp_graph = G.copy()
            for i in range(len(base_path) - 1):
                u, v = base_path[i], base_path[i + 1]
                if temp_graph.has_edge(u, v):
                    temp_graph[u][v]['weight'] = temp_graph[u][v].get('weight', 1.0) * penalty_factor
            alt_path = nx.astar_path(temp_graph, base_path[0], end_node, heuristic=self._heuristic, weight='weight')
            return alt_path if alt_path != base_path else None
        except Exception as e:
            logging.error(f"❌ Error generating alternative path: {str(e)}")
            return None

    def estimate_time_for_edge(self, u, v, historical_factor=1.0, mode='car', network=None):
        network = network or self.road_network
        weight = network[u][v].get('weight', 1.0)
        if mode == 'walking':
            speed = 5  # Average walking speed: 5 km/h
        elif mode == 'motorcycle':
            speed = network[u][v].get('speed_limit', 40) * 0.9  # Motorcycles slightly slower than cars
        else:  # car
            speed = network[u][v].get('speed_limit', 40)
        return (weight / speed) * 60 * historical_factor

    def calculate_distance(self, path, mode='car'):
        network = self.walking_network if mode == 'walking' else self.road_network
        distance = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if not network.has_edge(u, v):
                logging.warning(f"⚠ Edge ({u}, {v}) not found in {mode} network, skipping...")
                continue
            distance += network[u][v].get('weight', 1.0)
        return distance

    def estimate_time(self, path, departure_time=None, mode='car'):
        network = self.walking_network if mode == 'walking' else self.road_network
        total_time = 0
        historical_factor = self.get_historical_factor(departure_time) if departure_time else 1.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if not network.has_edge(u, v):
                logging.warning(f"⚠ Edge ({u}, {v}) not found in {mode} network, skipping...")
                continue
            total_time += self.estimate_time_for_edge(u, v, historical_factor, mode, network)
        return total_time

    def get_historical_factor(self, departure_time):
        if not departure_time:
            return 1.0
        try:
            dt = datetime.strptime(str(departure_time), "%Y-%m-%d %H:%M:%S.%f")
            hour = dt.hour
            if (7 <= hour < 9) or (17 <= hour < 19):
                return 1.5
            return 1.0
        except:
            return 1.0

    def analyze_congestion(self, path):
        if self.current_traffic is not None and not self.current_traffic.empty:
            avg_congestion = self.current_traffic['congestion_ratio'].mean()
            return "High" if avg_congestion > 0.7 else "Moderate" if avg_congestion > 0.4 else "Low"
        return "Unknown"

    def assess_route_quality(self, path, mode='car'):
        congestion = self.analyze_congestion(path) if mode in ['car', 'motorcycle'] else "Low"
        return "Good" if congestion == "Low" else "Moderate" if congestion == "Moderate" else "Poor"

    def create_route_map(self, route, filename, idx=1):
        try:
            logging.info(f"Creating route map for {route['start_location']} to {route['end_location']} via {route['mode']} with index {idx}")
            if not route.get('coordinates') or len(route.get('coordinates', [])) < 2:
                logging.error("❌ Route coordinates are empty or invalid")
                return None

            full_path = os.path.abspath(os.path.join(os.getcwd(), "maps", filename))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Tentukan warna berdasarkan congestion_level
            congestion_level = route['congestion_level']
            if congestion_level == "Low":
                line_color = '#4CAF50'  # Hijau untuk Lancar
            elif congestion_level == "Moderate":
                line_color = '#FFCA28'  # Kuning untuk Sedang
            else:  # High
                line_color = '#FF5722'  # Merah untuk Macet

            # Tambahkan warna biru untuk rute alternatif (selain rute utama)
            is_alternative = idx > 1
            if is_alternative:
                line_color = '#2196F3'  # Biru untuk alternatif

            m = folium.Map(location=route['coordinates'][0], zoom_start=13, tiles='OpenStreetMap')
            folium.PolyLine(
                locations=route['coordinates'],
                color=line_color,
                weight=5,
                opacity=0.8,
                popup=f"Rute dari {route['start_location']} ke {route['end_location']} ({route['mode']})<br>Jarak: {route['total_distance']:.2f} km<br>Waktu: {route['estimated_time']:.2f} menit<br>Kemacetan: {congestion_level}"
            ).add_to(m)
            folium.Marker(
                location=route['coordinates'][0],
                popup=f"Start: {route['start_location']} ({route['mode']})",
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)
            folium.Marker(
                location=route['coordinates'][-1],
                popup=f"End: {route['end_location']} ({route['mode']})",
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)

            m.save(full_path)
            logging.info(f"✅ Route map saved to: {full_path}")
            if os.path.exists(full_path):
                logging.info(f"✅ File {full_path} confirmed to exist")
                return full_path
            else:
                logging.error(f"❌ File {full_path} not found after saving")
                return None
        except Exception as e:
            logging.error(f"❌ Failed to create route map: {str(e)}")
            return None
        finally:
            logging.info("🎉 Completed route map creation process")

class OptimizedRouteRecommendationEngine(RouteRecommendationEngine):
    def __init__(self, bengkulu_locations, weather_api_key=None):
        logging.info("🔍 Initializing OptimizedRouteRecommendationEngine...")
        super().__init__(bengkulu_locations, weather_api_key)

    def get_alternative_routes(self, start, end, departure_time=None, max_alternatives=5, min_alternatives=3, mode='car'):
        logging.info(f"🔍 Optimized route calculation for {start} to {end} with mode {mode}...")
        if start not in self.location_nodes or end not in self.location_nodes:
            logging.error(f"❌ Lokasi start atau end tidak valid: {start} → {end}")
            return []

        # Select network and nodes based on mode
        if mode == 'walking':
            network = self.walking_network
            start_node = self.walking_nodes[start]
            end_node = self.walking_nodes[end]
        else:  # car or motorcycle
            network = self.road_network
            start_node = self.location_nodes[start]
            end_node = self.location_nodes[end]

        alternative_routes = []
        temp_graph = network.copy()

        cache_key = f"{start}_{end}_{max_alternatives}_{mode}"
        cache_file = f"cache/routes_{cache_key}.pkl"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_routes = pickle.load(f)
                logging.info(f"✅ Memuat rute dari cache untuk {start} ke {end} mode {mode}")
                return cached_routes
            except:
                logging.warning(f"⚠ Cache rusak, menghitung ulang rute")

        try:
            # Gunakan A* untuk rute utama
            shortest_path = nx.astar_path(temp_graph, start_node, end_node, heuristic=self._heuristic, weight='weight')
            paths = [(shortest_path, 0)]  # (path, penalty)

            # Generate rute alternatif dengan penalti edge
            for i in range(max_alternatives - 1):
                new_path = self._generate_alternative_path(temp_graph, shortest_path, end_node, penalty_factor=1.2 + i * 0.2)
                if new_path and tuple(new_path) not in [tuple(p) for p, _ in paths]:
                    paths.append((new_path, 1.2 + i * 0.2))

            for i, (path, _) in enumerate(paths[:max_alternatives], 1):
                coordinates = []
                for node in path:
                    try:
                        node_data = temp_graph.nodes[node]
                        if 'y' in node_data and 'x' in node_data:
                            coordinates.append((node_data['y'], node_data['x']))
                        else:
                            logging.warning(f"⚠ Node {node} in path missing coordinates, skipping...")
                            continue
                    except Exception as e:
                        logging.warning(f"⚠ Error accessing coordinates for node {node}: {e}")
                        continue
                if len(coordinates) < 2:
                    logging.error(f"❌ Route path for {start} to {end} via {mode} has insufficient valid coordinates")
                    continue

                total_distance = self.calculate_distance(path, mode)
                estimated_time = self.estimate_time(path, departure_time, mode)
                congestion_level = self.analyze_congestion(path) if mode in ['car', 'motorcycle'] else "Low"
                route_quality = self.assess_route_quality(path, mode)

                route = {
                    'path': path,
                    'coordinates': coordinates,
                    'total_distance': total_distance,
                    'estimated_time': estimated_time,
                    'congestion_level': congestion_level,
                    'route_quality': route_quality,
                    'start_location': start,
                    'end_location': end,
                    'mode': mode,
                    'route_index': i  # Menambahkan indeks rute
                }
                alternative_routes.append(route)

            alternative_routes.sort(key=lambda x: (x['total_distance'], x['estimated_time'], -1 if x['route_quality'] == "Good" else 0))
            alternative_routes = alternative_routes[:max_alternatives]

            os.makedirs("cache", exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(alternative_routes, f)
            logging.info(f"✅ Menyimpan rute ke cache untuk {start} ke {end} mode {mode}")

            return alternative_routes
        except Exception as e:
            logging.error(f"❌ Error menghitung rute: {str(e)}")
            return []
