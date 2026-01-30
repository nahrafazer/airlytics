<?php
// Set header untuk memberitahu browser bahwa ini adalah file CSV yang akan diunduh
header('Content-Type: text/csv');
header('Content-Disposition: attachment; filename="data_kualitas_udara.csv"'); // Nama file CSV saat diunduh

// Konfigurasi Database
$servername = "34.50.79.244"; // Sesuaikan dengan server database Anda
$username = "root";       // Sesuaikan dengan username database Anda (berdasarkan diskusi sebelumnya)
$password = "Rez@090503";           // Sesuaikan dengan password database Anda (berdasarkan diskusi sebelumnya)
$dbname = "db_kualitas_udara"; // Nama database Anda
$table_name = "tb_konsentrasi_gas"; // Nama tabel Anda

// Membuat koneksi ke database
$conn = new mysqli($servername, $username, $password, $dbname);

// Periksa koneksi
if ($conn->connect_error) {
    // Jika koneksi gagal, hentikan eksekusi dan tampilkan pesan error
    // Pastikan tidak ada output lain sebelum header jika ini akan di-download
    die("Koneksi database gagal: " . $conn->connect_error);
}

// Ambil parameter kolom yang dipilih dari request GET
// Default: jika tidak ada 'columns' di URL, atau kosong, maka array kosong
$selectedColumns = isset($_GET['columns']) ? explode(',', $_GET['columns']) : [];
$selectedColumns = array_map('trim', $selectedColumns); // Hapus spasi di awal/akhir setiap nama kolom

// Peta antara nama kolom di URL/JS dan nama kolom di database
// Ini penting karena nama kolom di database Anda menggunakan underscore dan 'ugm3'
$columnMap = [
    "timestamp"   => "timestamp",
    "temperature" => "temperature",
    "humidity"    => "humidity",
    "pm25"        => "PM25_ugm3",
    "pm10"        => "PM10_ugm3",
    "co"          => "CO_ugm3",
    "no2"         => "NO2_ugm3",
    "o3"          => "O3_ugm3"
];

$columnsToSelect = []; // Kolom yang akan diambil dari database
$csvHeaders = [];      // Header yang akan ditampilkan di file CSV (sesuai request user)

// Iterasi melalui kolom yang diminta oleh user
foreach ($selectedColumns as $col) {
    if (isset($columnMap[$col])) {
        // Jika kolom valid, tambahkan ke daftar kolom yang akan diambil dari DB
        // Format: 'nama_kolom_DB AS nama_alias_di_CSV'
        $columnsToSelect[] = $columnMap[$col] . " AS " . $col;
        $csvHeaders[] = $col; // Gunakan nama alias sebagai header CSV
    }
}

// Wajib menyertakan timestamp di CSV jika belum ada
if (!in_array("timestamp", $csvHeaders)) {
    // Tambahkan di awal jika belum ada
    array_unshift($columnsToSelect, $columnMap["timestamp"] . " AS timestamp");
    array_unshift($csvHeaders, "timestamp");
}

// Jika tidak ada kolom yang valid setelah proses, hentikan
if (empty($columnsToSelect)) {
    die("Tidak ada kolom yang valid untuk diunduh.");
}

// Buat query SQL
$query = "SELECT " . implode(", ", $columnsToSelect) . " FROM " . $table_name . " ORDER BY timestamp DESC"; // Mengambil semua data yang relevan

$result = $conn->query($query);

// Jika tidak ada data yang ditemukan
if ($result->num_rows === 0) {
    die("Tidak ada data yang tersedia dalam tabel.");
}

// Buka output stream untuk menulis ke file CSV
$output = fopen('php://output', 'w');

// Tulis baris header CSV
fputcsv($output, $csvHeaders);

// Tulis setiap baris data ke file CSV
while ($row = $result->fetch_assoc()) {
    // Urutkan kolom sesuai dengan $csvHeaders
    $orderedRow = [];
    foreach ($csvHeaders as $header) {
        $orderedRow[] = $row[$header];
    }
    fputcsv($output, $orderedRow);
}

// Tutup output stream
fclose($output);

// Tutup koneksi database
$conn->close();
?>