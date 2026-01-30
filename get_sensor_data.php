<?php
$servername = "34.50.79.244"; // default XAMPP
$username = "root";        // default XAMPP
$password = "Rez@090503";            // default XAMPP
$dbname = "db_kualitas_udara"; // ganti sesuai nama database kamu

// buat koneksi
$conn = new mysqli($servername, $username, $password, $dbname);

// cek koneksi
if ($conn->connect_error) {
    die(json_encode(['error' => 'koneksi gagal: ' . $conn->connect_error]));
}

// query untuk ambil data terakhir
$query_konsentrasi = "SELECT PM25_ugm3, PM10_ugm3, CO_ugm3, NO2_ugm3, O3_ugm3, temperature, humidity FROM tb_konsentrasi_gas ORDER BY id DESC LIMIT 1";
$query_prediksi = "SELECT hasil_prediksi FROM tb_prediksi_kualitas_udara ORDER BY timestamp DESC LIMIT 1";

$result_konsentrasi = $conn->query($query_konsentrasi);
$result_prediksi = $conn->query($query_prediksi);

if ($result_konsentrasi && $result_prediksi && $result_konsentrasi->num_rows > 0 && $result_prediksi->num_rows > 0) {
    $data_konsentrasi = $result_konsentrasi->fetch_assoc();
    $data_prediksi = $result_prediksi->fetch_assoc();

    // gabungkan hasilnya
    $output = array_merge($data_konsentrasi, $data_prediksi);
    echo json_encode($output);
} else {
    echo json_encode(['error' => 'data tidak ditemukan']);
}

$conn->close();
?>
