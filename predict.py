import sys
import pandas as pd
import joblib
import os
import requests
import time 
# Import library Supabase
from supabase import create_client, Client 

# --- KONFIGURASI TELEGRAM & SUPABASE ---
TELEGRAM_BOT_TOKEN = "8059645974:AAGWoj6l9eQgeJtS09O6p7ReDTIU9rlg3rU"
# TELEGRAM_CHAT_ID dihilangkan karena akan diambil dari DB

SUPABASE_URL = "https://qnvthdiylfpuumcancxo.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFudnRoZGl5bGZwdXVtY2FuY3hvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDkxMzI4OCwiZXhwIjoyMDc2NDg5Mjg4fQ.lgU9j959hUw8sKtIqV_bJVy8c6OZBiJtRCwFWGX7Wss" 
TABLE_NAME = 'tb_prediksi_kualitas_udara'
TELEGRAM_ID_TABLE = 'tb_telegram_id' # <--- BARU: Nama tabel ID Telegram

# --- KONFIGURASI JADWAL ---
JUMLAH_SIKLUS = 26
INTERVAL_JEDA_DETIK = 30 #detik
TELEGRAM_RATE_LIMIT_DELAY = 1.5 # Jeda 1 detik antar pengiriman pesan ke user berbeda

# --- KAMUS SARAN KUALITAS UDARA (BARU) ---
AIR_QUALITY_ADVICE = {
    "Baik": (
        "<b>✅ Saran: Baik</b>\n"
        "Tingkat kualitas udara yang sangat baik, tidak memberikan efek negatif terhadap manusia, hewan, dan tumbuhan. "
        "<b>Sangat baik untuk melakukan aktivitas di luar ruangan.</b>"
    ),
    "Sedang": (
        "<b>🟡 Saran: Sedang</b>\n"
        "Tingkat kualitas udara masih dapat diterima pada kesehatan manusia, hewan, dan tumbuhan. "
        "<b>Semua Orang:</b> Masih dapat beraktivitas di luar.\n"
        "<b>Kelompok Sensitif:</b> Kurangi aktivitas fisik yang terlalu lama atau berat di luar ruangan."
    ),
    "Tidak_Sehat": (
        "<b>🟠 Saran: Tidak Sehat</b>\n"
        "Tingkat kualitas udara yang bersifat merugikan pada manusia, hewan, dan tumbuhan.\n"
        "<b>Setiap Orang:</b> Mengurangi aktivitas fisik yang terlalu lama di luar ruangan.\n"
        "<b>Penderita Asma:</b> Harus mengikuti petunjuk kesehatan untuk asma dan menyimpan obat asma.\n"
        "<b>Penderita Penyakit Jantung:</b> Gejala seperti palpitasi/jantung berdetak lebih cepat, sesak nafas, atau kelelahan yang tidak biasa mungkin mengindikasikan masalah serius."
    ),
    "Sangat_Tidak_Sehat": (
        "<b>🔴 Saran: Sangat Tidak Sehat</b>\n"
        "Tingkat kualitas udara dapat meningkatkan resiko kesehatan pada sejumlah segmen populasi yang terpapar.\n"
        "<b>Semua Orang:</b> Hindari semua aktivitas fisik yang terlalu lama di luar ruangan. Pertimbangkan untuk melakukan aktivitas di dalam ruangan.\n"
        "<b>Kelompok Sensitif:</b> Hindari semua aktivitas di luar."
    ),
    "Berbahaya": (
        "<b>⚫ Saran: Berbahaya</b>\n"
        "Tingkat kualitas udara yang dapat merugikan kesehatan serius pada populasi dan perlu penanganan cepat.\n"
        "<b>Semua Orang:</b> Hindari semua aktvitas di luar.\n"
        "<b>Kelompok Sensitif:</b> Tetap di dalam ruangan dan hanya melakukan sedikit aktivitas."
    )
}

# --- FUNGSI BARU: MENGAMBIL DAFTAR CHAT ID DARI SUPABASE ---
def get_telegram_chat_ids(supabase_client: Client):
    """Mengambil semua 'teleid' dari tabel tb_telegram_id."""
    try:
        response = supabase_client.table(TELEGRAM_ID_TABLE).select("teleid").execute()
        # Mengembalikan list dari semua teleid yang ditemukan
        return [row['teleid'] for row in response.data]
    except Exception as e:
        print(f"Gagal mengambil daftar Telegram ID dari database: {e}", file=sys.stderr)
        return []

# --- FUNGSI MODIFIKASI: MENGIRIM PESAN KE SEMUA ID ---
def send_telegram_notification(message, chat_ids: list):
    """Mengirim notifikasi ke semua Chat ID dalam daftar."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    if not chat_ids:
        print("Daftar Chat ID kosong. Tidak ada pesan yang dikirim.")
        return

    for chat_id in chat_ids:
        payload = {
            "chat_id" : chat_id, # Menggunakan ID dari loop
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            print(f"Notifikasi berhasil dikirim ke ID: {chat_id}")
            # PENTING: Jeda antar pesan untuk menghindari batasan API Telegram (1 pesan/detik per user)
            time.sleep(TELEGRAM_RATE_LIMIT_DELAY) 
        except requests.exceptions.RequestException as e:
            print(f"Gagal mengirim notifikasi Telegram ke ID {chat_id}: {e}", file=sys.stderr)

        
try:
    # --- INISIALISASI (DILAKUKAN SEKALI) ---
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(current_script_dir, 'models')
    model_path = os.path.join(models_dir, 'kualitas_udara_rf_model.joblib')
    labels_path = os.path.join(models_dir, 'class_labels.txt')

    model = joblib.load(model_path)
    
    try:
        with open(labels_path, 'r') as f:
            class_labels = [line.strip() for line in f]
    except FileNotFoundError:
        class_labels = []
    
    # 1. Koneksi ke Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) 

    # 2. AMBIL DAFTAR CHAT ID SEBELUM MEMULAI LOOP UTAMA
    telegram_ids = get_telegram_chat_ids(supabase) # <--- PANGGIL FUNGSI BARU
    
    if not telegram_ids:
        # Kirim notifikasi ke console/log jika tidak ada ID
        print("PERINGATAN: Tidak ada Telegram ID yang terdaftar. Notifikasi tidak akan dikirim.")


    # --- LOOP PREDIKSI (DILAKUKAN 7 KALI DENGAN INTERVAL 2 MENIT) ---
    for i in range(JUMLAH_SIKLUS): 
        print(f"\n=======================================================")
        print(f"--- MULAI SIKLUS PREDIKSI KE-{i + 1} DARI {JUMLAH_SIKLUS} ---")
        print(f"=======================================================")
        
        # 3. MENCARI ID TERTINGGI (Data Terbaru)
        response_data = supabase.table(TABLE_NAME).select(
            "id, hasil_prediksi, pm2_5_ispu, pm10_ispu, co_ispu, no2_ispu, o3_ispu"
        ).order(
            "id", desc=True
        ).limit(
            1 
        ).execute()

        row_data = response_data.data

        if not row_data:
            print("Tabel kosong atau tidak ada data untuk diprediksi.")
            break 

        row = row_data[0]
        data_id = row['id']
        hasil_prediksi_status = row['hasil_prediksi']
            
        print(f"Mengecek ID tertinggi: {data_id} dari tabel {TABLE_NAME}")

        # 4. Memproses Prediksi dan Update Database
        if hasil_prediksi_status is not None:
            # Mengirim notifikasi lewati hanya pada siklus ke-30 (indeks 29)
            if i == 29:
                message_to_send = (
                    f"<b>❕ PREDIKSI DENGAN ID(<code>{data_id}</code>) DILEWATI KARENA SUDAH DIPREDIKSI (<code>{hasil_prediksi_status}</code>)</b>\n\n"
                    f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Siklus: {i + 1}/{JUMLAH_SIKLUS}"
                )
                
                send_telegram_notification(message_to_send, telegram_ids) # <--- PANGGIL DENGAN DAFTAR ID
                print(f"Kualitas Udara untuk ID: {data_id} sudah diprediksi. Proses prediksi dilewati.")
            else:
                print(f"Kualitas Udara untuk ID: {data_id} sudah diprediksi. Proses prediksi dilewati.")
        else:
            print(f"Data ID {data_id} belum diprediksi. Memulai proses prediksi...")
            
            # ... (Logika Prediksi) ...
            input_dict= {
                'PM2_5_ISPU': float(row['pm2_5_ispu']),
                'PM10_ISPU': float(row['pm10_ispu']),
                'CO_ISPU': float(row['co_ispu']),
                'NO2_ISPU': float(row['no2_ispu']),
                'O3_ISPU': float(row['o3_ispu'])
            }
            input_data = pd.DataFrame([input_dict])
            predicted_label = model.predict(input_data)[0]
            
            # 5. Menyimpan hasil prediksi kembali ke Supabase
            update_response = supabase.table(TABLE_NAME).update(
                {"hasil_prediksi": predicted_label}
            ).eq(
                "id", data_id
            ).execute()
            
            # Periksa apakah update berhasil
            if update_response.data: 
                # --- AMBIL SARAN BERDASARKAN HASIL PREDIKSI ---
                saran_kesehatan = AIR_QUALITY_ADVICE.get(predicted_label, "Tidak ada saran spesifik untuk kategori ini.")
                
                success_message = (
                    f"<b>✨ PREDIKSI BARU BERHASIL (Siklus {i + 1}/{JUMLAH_SIKLUS})✨</b>\n"
                    f"ID: <code>{data_id}</code>\n"
                    f"Hasil: <b>{predicted_label}</b>\n"
                    f"--- Status Kualitas Udara ---\n"
                    f"{saran_kesehatan}\n" # <--- SARAN DITAMBAHKAN DI SINI
                    f"Waktu Update: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                send_telegram_notification(success_message, telegram_ids) # <--- PANGGIL DENGAN DAFTAR ID
                print(f"Prediksi berhasil disimpan untuk ID {data_id}: {predicted_label}")
            else:
                failure_message = (
                    f"<b>❌ PREDIKSI GAGAL DISIMPAN (Siklus {i + 1}/{JUMLAH_SIKLUS})</b>\n"
                    f"Data ID: <code>{data_id}</code>\n"
                    f"Status: Gagal menyimpan hasil prediksi ke database.\n"
                    f"Waktu Gagal: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                send_telegram_notification(failure_message, telegram_ids) # <--- PANGGIL DENGAN DAFTAR ID
                raise Exception(f"Gagal menyimpan hasil prediksi ke database untuk ID {data_id}.")

        # --- JEDA WAKTU ---
        if i < JUMLAH_SIKLUS - 1: 
            print(f"Siklus {i + 1} selesai. Menunggu {INTERVAL_JEDA_DETIK} Detik untuk siklus berikutnya...")
            time.sleep(INTERVAL_JEDA_DETIK)
            
    print("\n=======================================================")
    print(f"{JUMLAH_SIKLUS} Siklus Prediksi telah selesai dieksekusi.")
    print("=======================================================")


except Exception as e:
    # Mengirim notifikasi error umum (jika list ID sudah didapat)
    error_message = (
        f"<b>🚨 ERROR KRITIS!</b>\n"
        f"Deskripsi: Terjadi kesalahan saat menjalankan prediksi.\n"
        f"Detail: <code>{str(e)}</code>\n"
        f"Waktu: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    # Gunakan telegram_ids jika sudah terdefinsi, jika belum, hanya print error
    try:
        send_telegram_notification(error_message, telegram_ids)
    except NameError:
        # Jika 'telegram_ids' belum terdefinisi (misalnya error saat koneksi awal), hanya print.
        pass
    
    print(f"Error dalam prediksi atau koneksi database: {e}", file=sys.stderr)
    sys.exit(1)