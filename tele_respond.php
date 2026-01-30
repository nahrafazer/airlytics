<?php
// =======================================================
// KONFIGURASI BOT TELEGRAM
// =======================================================
$BOT_TOKEN = "8059645974:AAGWoj6l9eQgeJtS09O6p7ReDTIU9rlg3rU";
$API_URL = "https://api.telegram.org/bot" . $BOT_TOKEN . "/";
// =======================================================
// KONFIGURASI SUPABASE API (REST)
// =======================================================
// Ganti dengan URL dan Anon Key Proyek Supabase Anda yang sebenarnya!
$SUPABASE_URL = "https://qnvthdiylfpuumcancxo.supabase.co"; // Contoh: https://abcdefghijklmn.supabase.co
$SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFudnRoZGl5bGZwdXVtY2FuY3hvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA5MTMyODgsImV4cCI6MjA3NjQ4OTI4OH0.MnE1KiXh16SelbzOtKFusxgJHAfEtcRrCFvUOlzsCMs"; // Ditemukan di Project Settings -> API
$TABLE_NAME = "tb_konsentrasi_gas";
$TABLE_PREDIKSI = "tb_prediksi_kualitas_udara";
$REGISTER_URL = "https://airlytics.my.id/register_telegram.html"; // URL Registrasi Anda
// =======================================================
// FUNGSI UTAMA BOT
// =======================================================
// Menerima data JSON dari Telegram
$update = file_get_contents("php://input");
$update_array = json_decode($update, TRUE);

if (isset($update_array['message'])) {
    $message = $update_array['message'];
    $chat_id = $message['chat']['id'];
    $first_name = $message['from']['first_name'] ?? 'Pengguna';
    $text = strtolower($message['text']);
    $response_text = "";

    // --- Logika: Perintah /start ---
    if ($text === "/start") {
        $response_text = "👋<b> Halo, " . htmlspecialchars($first_name) . "! Selamat datang di Airlytics Bot.</b>\n\n";
        $response_text .= "Saya adalah bot pemantau kualitas udara yang terhubung langsung dengan data real-time di <code>airlytics.my.id</code>.\n\n";
        $response_text .= "Gunakan perintah berikut:\n";
        $response_text .= "• /ispu : Untuk melihat data konsentrasi gas terbaru.\n";
        $response_text .= "\n";
        $response_text .= "Untuk mulai berlangganan notifikasi kualitas udara harian, silakan daftarkan ID Telegram Anda melalui tautan di bawah:\n";
        $response_text .= "\n";
        $response_text .= "<b><a href=\"{$REGISTER_URL}\">DAFTAR LANGGANAN DI SINI</a></b>";
    }

    // --- Logika: Perintah /ispu ---
    else if ($text === "/ispu") {
        $response_text = getLatestGasData();

    } else if ($text === "/register") {
        $response_text = "Untuk mulai berlangganan notifikasi kualitas udara harian, silakan daftarkan ID Telegram Anda melalui tautan di bawah:\n";
        $response_text .= "<a href=\"{$REGISTER_URL}\">DAFTAR LANGGANAN DI SINI</a>";
    }

    // Kirim Balasan jika ada response_text
    if (!empty($response_text)) {
        sendMessage($chat_id, $response_text);
    }
}


function getLatestPredictionData()
{
    global $SUPABASE_URL, $SUPABASE_ANON_KEY, $TABLE_PREDIKSI;

    $api_endpoint = $SUPABASE_URL . "/rest/v1/" . $TABLE_PREDIKSI .
        "?select=hasil_prediksi" . // Hanya ambil kolom yang dibutuhkan
        "&order=timestamp.desc" .
        "&limit=1";

    $options = [
        'http' => [
            'header' => "apikey: " . $SUPABASE_ANON_KEY . "\r\n" .
                "Authorization: Bearer " . $SUPABASE_ANON_KEY . "\r\n" .
                "Content-Type: application/json\r\n",
            'method' => 'GET'
        ]
    ];

    $context = stream_context_create($options);
    $result = @file_get_contents($api_endpoint, false, $context);

    if ($result === FALSE) {
        return "⚠️ Prediksi: Gagal koneksi.";
    }

    $data_array = json_decode($result, TRUE);

    if (empty($data_array) || !isset($data_array[0]) || !isset($data_array[0]['hasil_prediksi'])) {
        return "⚠️ Prediksi: Data tidak ditemukan.";
    }

    return $data_array[0]['hasil_prediksi'];
}

function getLatestGasData()
{
    global $SUPABASE_URL, $SUPABASE_ANON_KEY, $TABLE_NAME;

    $api_endpoint = $SUPABASE_URL . "/rest/v1/" . $TABLE_NAME .
        "?select=*" .
        "&order=timestamp.desc" .
        "&limit=1";

    $options = [
        'http' => [
            'header' => "apikey: " . $SUPABASE_ANON_KEY . "\r\n" .
                "Authorization: Bearer " . $SUPABASE_ANON_KEY . "\r\n" .
                "Content-Type: application/json\r\n",
            'method' => 'GET'
        ]
    ];

    $context = stream_context_create($options);
    $result = @file_get_contents($api_endpoint, false, $context);

    if ($result === FALSE) {
        return "❌ Gagal terhubung atau mendapatkan data dari Supabase API. Cek API Key/URL.";
    }

    $data_array = json_decode($result, TRUE);

    if (empty($data_array) || !isset($data_array[0])) {
        return "ℹ️ Tabel saat ini kosong atau data tidak ditemukan.";
    }

    $data = $data_array[0];

    $prediksi_text = getLatestPredictionData();
    $rekomendasi = "";

    $prediksi_lower = strtolower($prediksi_text);
    if ($prediksi_lower === "baik") {
        $rekomendasi = "🟢 Tingkat kualitas udara yang sangat baik, tidak memberikan efek negatif terhadap manusia, hewan, dan tumbuhan. Sangat baik melakukan kegiatan di luar.";
    } else if ($prediksi_lower === "sedang") {
        $rekomendasi = "🟡 Tingkat kualitas udara masih dapat diterima pada kesehatan manusia, hewan, dan tumbuhan. Untuk kelompok sensitif kurangi aktivitas fisik yang terlalu lama atau berat.";
    } else if ($prediksi_lower === "tidak sehat") {
        $rekomendasi = "🟠 Tingkat kualitas udara yang bersifat merugikan pada manusia, hewan, dan tumbuhan. Untuk penderita asma harus mengikuti petunjuk kesehatan untuk asma dan menyimpan obat asma. Untuk penderita penyakit jantung, gejala seperti palpitasi/jantung berdetak lebih cepat, sesak nafas, atau kelelahan yang tidak biasa mungkin mengindikasikan masalah serius.";
    } else if ($prediksi_lower === "sangat tidak sehat") {
        $rekomendasi = "🔴 Tingkat kualitas udara dapat meningkatkan resiko kesehatan pada sejumlah segmen populasi yang terpapar. Hindari semua aktivitas di luar.";
    } else if ($prediksi_lower === "berbahaya") {
        $rekomendasi = "🟣 Tingkat kualitas udara yang dapat merugikan kesehatan serius pada populasi dan perlu penanganan cepat. Tetap di dalam ruangan dan hanya melakukan sedikit aktivitas.";
    }

    try {
        // 1. Buat objek DateTime, asumsikan timestamp adalah UTC
        $utc_time = new DateTime($data['timestamp'], new DateTimeZone('UTC'));
        
        // 2. Ubah zona waktu objek ke WIB (Asia/Jakarta)
        $utc_time->setTimezone(new DateTimeZone('Asia/Jakarta'));
        
        // 3. Format waktu yang sudah dikonversi
        $timestamp_wib = $utc_time->format("d F Y, H:i:s");
    } catch (Exception $e) {
        // Fallback jika konversi gagal (misalnya format timestamp Supabase tidak valid)
        $timestamp_wib = date("d F Y, H:i:s", strtotime($data['timestamp'])) . " (Waktu Error)";
    }

    // $timestamp = date("d F Y, H:i:s", strtotime($data['timestamp']));
    $output = "<b>📊 Data Kualitas Udara Terbaru</b>\n";
    $output .= "⏰ Diperbarui: <code>{$timestamp_wib}</code>\n\n";
    $output .= "<b>💨 Konsentrasi Gas:</b>\n";
    $output .= "<b>PM2.5</b> : <code>{$data['pm25_ugm3']}</code> µg/m³\n";
    $output .= "<b>PM10</b>  : <code>{$data['pm10_ugm3']}</code> µg/m³\n";
    $output .= "<b>CO</b>    : <code>{$data['co_ugm3']}</code> µg/m³\n";
    $output .= "<b>NO2</b>   : <code>{$data['no2_ugm3']}</code> µg/m³\n";
    $output .= "<b>O3</b>    : <code>{$data['o3_ugm3']}</code> µg/m³\n";
    $output .= "<b>Suhu</b>  : <code>{$data['temperature']}</code> °C\n";
    $output .= "<b>Kelembaban</b>: <code>{$data['humidity']}</code> %\n";
    $output .= "\n<b>🔮 Prediksi Kualitas Udara: $prediksi_text </b>\n";
    $output .= "------------------------------------------------------";
    $output .= "\n<i>$rekomendasi</i>\n";

    return $output;
}
// =======================================================
// FUNGSI KOMUNIKASI TELEGRAM (TIDAK BERUBAH DARI SEBELUMNYA)
// =======================================================
    function sendMessage($chatId, $text)
    {
        global $API_URL;
        $url = $API_URL . "sendMessage";

        $post_data = [
            'chat_id' => $chatId,
            'text' => $text,
            'parse_mode' => 'HTML'
        ];

        $options = [
            'http' => [
                'header' => "Content-type: application/x-www-form-urlencoded\r\n",
                'method' => 'POST',
                'content' => http_build_query($post_data)
            ]
        ];

        $context = stream_context_create($options);
        @file_get_contents($url, false, $context);
    }
?>