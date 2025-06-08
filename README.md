# Bengkulu-Smart-Traffic


Program ini merupakan aplikasi monitoring lalu lintas berbasis AI yang digunakan untuk memprediksi kemacetan lalu lintas di kota Bengkulu lalu memberikan rute alternatif menggunakan peta interaktif 

---

## 👥 Anggota Kelompok 

| Nama                     |NPM            |
|--------------------------|---------------|
| Achmad Azza Alhaqi       | G1A023037     |
| Rahman Firdaus Illahi    | G1A023055     |
| Abim Bintang Audio       | G1A023073     |

---

## 🔍 Fitur Aplikasi

- Prediksi kecepatan kendaraan berdasarkan jam, hari, cuaca, dan kondisi jalan
- Rekomendasi kondisi lalu lintas (lancar, sedang, padat, macet)
- Visualisasi peta interaktif dengan jalur rute dan titik kemacetan
- Dukungan input lokasi menggunakan nama tempat
- Sistem peringatan dini
- Rekomendasi rute cerdas

---

## 🧠 Model AI yang Digunakan

### 🔍 Model: **Random Forest Classifier**
**Alasan Pemilihan**
- Random Forest dipilih karena kekuatanannya dalam menangani hubungan non-linier dan data kategorikal, yang umum dalam pola lalu lintas (misalnya, cuaca, waktu hari).
- Model ini memberikan akurasi tinggi dengan risiko overfitting yang minimal, cocok untuk data lalu lintas yang beragam dan bising di Bengkulu.
- Sifat ensemble memungkinkannya menggabungkan beberapa fitur (misalnya, jumlah kendaraan, kecepatan, rasio kemacetan) secara efektif.

---

## 🗂️ Jenis & Sumber Data

### 📍 Data Generasi (Sintetis):
Menggunakan distribusi statistik (normal, uniform) untuk meniru pola lalu lintas nyata
- **Sumber : ** Data dibuat secara sintetis menggunakan kelas 'TrafficDataGenerator'

### 📍 Data Geospasial:
Data jaringan jalan (graph) Kota Bengkulu.
- **Sumber : ** Diambil dari OpenStreetMap (OSM) menggunakan library 'OSMnx'

### 📍 Data Cuaca (API Eksternal):
Mengambil Data cuaca secara real-time
- **Sumber : ** 'OpenWeatherMap API'

---

## 🗺️ Alur Kerja Sistem

1. **Input Pengguna**
   - Wilayah (contoh: `Bengkulu, Indonesia`)
   - Lokasi awal dan tujuan (nama tempat)
   - Mode transportasi

2. **Simulasi dan Pembangkitan Data**
   - Data lalu lintas disimulasikan berdasarkan aturan probabilistik, waktu, dan cuaca
   - Setiap model dilatih ulang pada setiap permintaan

3. **Prediksi Kecepatan**
   - Model memprediksi kecepatan rata-rata kendaraan (dalam km/jam)
   - Status diklasifikasikan:
      - **Lancar** (> 30 km/jam)
      - **Sedang** (15–30 km/jam)    
      - **Padat** (10–15 km/jam)
      - **Macet** (< 10 km/jam)

4. **Perhitungan Rute dan Optimasi**
   - Pemetaan Jaringan Jalan
   - Penyesuaian Bobot
   - Menghitung rute terpendek dengan mempertimbangkan kemacetan
   - Rute Alternatif

5. **Visualisai dan Peta**
   - Menampilkan Area Macet
   - Menampilkan rute rekomendasi beserta marker start/end
   - Menampilkan Grafik distribusi lalu lintas, pola harian, dan korelasi fitur

6. **Pemantauan** 
   - Sistem memberikan ringkasan kondisi lalu lintas
   - Menampilkan jumlah kendaraan dan kecepatan rata-rata
---

## 🛠️ Teknologi yang Digunakan

1. **Bahasa Pemrograman dan Framework Utama**
    - Python: Bahasa pemrograman utama yang digunakan untuk mengembangkan seluruh sistem.
    - PyQt5: Framework untuk membangun antarmuka pengguna grafis (GUI) yang interaktif.

2. **Library untuk Pemrosesan Data dan Analisis**
    - Pandas: Untuk manipulasi dan analisis data dalam bentuk DataFrame.
    - NumPy: Untuk komputasi numerik dan operasi array.
    - Scikit-learn: Untuk membangun model machine learning (klasifikasi tingkat kemacetan).
    - Matplotlib & Seaborn: Untuk visualisasi data statis (grafik, diagram, dll.).
    - Plotly: Untuk visualisasi interaktif (opsional).

3. **Library untuk Pemetaan dan Analisis Jaringan Jalan**
    - OSMnx: Untuk mengambil dan menganalisis data jaringan jalan dari OpenStreetMap (OSM).
    - NetworkX: Untuk analisis graf dan perhitungan rute.
    - Folium: Untuk membuat peta interaktif berbasis Leaflet.js.
    - GeoPy (implisit): Untuk operasi geospasial seperti menghitung jarak.

4. **Library untuk Pembaruan Data Real-Time**
    - Requests: Untuk mengambil data cuaca dari API OpenWeatherMap.
    - Logging: Untuk mencatat aktivitas sistem dan debugging.
    - Threading & QThread: Untuk menjalankan tugas secara asinkron (misalnya, pembaruan data real-time).

---

## 📦 Cara Menjalankan

1. **Install Dependensi**

```bash
pip install -r rquiremens.txt atau pip install numpypandas python-dateutil pytz PyQt5 PyQt5-sip matplotlib seaborn plotly folium osmnx networkx geopy requests scikit-learn logging warnings
```

2. **Jalankan Aplikasi**

```bash
python main.py
```
---

## 🎯 Pengembangan Lanjutan

- Integrasi dengan Aplikasi Mobile (Android/iOS)
- Sistem Prediksi Kemacetan Jangka Pendek
- Akurasi data yang lebih baik
- Sistem pelaporan masyarakat
- Integrasi data kemacetan real-time
