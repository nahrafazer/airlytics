<?php
header('Content-Type: application/json');

// Konfigurasi Database
$servername = "34.50.79.244"; // Ganti jika database Anda di hosting lain
$username = "root";      // Ganti dengan username database Anda
$password = "Rez@090503";          // Ganti dengan password database Anda
$dbname = "db_kualitas_udara"; // Nama database Anda
$table_name = "tb_konsentrasi_gas"; // Nama tabel Anda

// Membuat koneksi
$conn = new mysqli($servername, $username, $password, $dbname);

// Memeriksa koneksi
if ($conn->connect_error) {
    die(json_encode(["error" => "Koneksi database gagal: " . $conn->connect_error]));
}

// Mengambil data dari database
// Sesuaikan nama kolom dengan struktur tabel Anda
$sql = "SELECT 
            timestamp, 
            temperature, 
            humidity, 
            PM25_ugm3 AS pm25, 
            PM10_ugm3 AS pm10, 
            CO_ugm3 AS co, 
            NO2_ugm3 AS no2, 
            O3_ugm3 AS o3 
        FROM $table_name 
        ORDER BY timestamp DESC 
        LIMIT 24"; // Batasi 24 data terakhir

$result = $conn->query($sql);

$data = [];

if ($result->num_rows > 0) {
    // Mengambil setiap baris data
    while($row = $result->fetch_assoc()) {
        // Format timestamp agar lebih mudah dibaca di grafik (misal: HH:MM)
        // Perhatikan bahwa kolom timestamp di database Anda tampaknya sudah berisi tanggal dan waktu.
        // Jika Anda hanya ingin menampilkan jam:menit, format ini sudah benar.
        $row['timestamp'] = date('H:i', strtotime($row['timestamp']));
        $data[] = $row;
    }
}

// Membalikkan urutan array agar data terbaru ada di akhir (untuk grafik yang mengalir dari kiri ke kanan)
$data = array_reverse($data);

// Mengirimkan data dalam format JSON
echo json_encode($data);

$conn->close();
?>