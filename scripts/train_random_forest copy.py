# scripts/train_random_forest.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib # Untuk menyimpan/memuat model
import os     # Untuk operasi file/direktori
import matplotlib.pyplot as plt # Untuk visualisasi
import seaborn as sns # Untuk visualisasi

print("--- Memulai Proses Pelatihan Model Random Forest ---")

# --- 1. Memuat Data dari File CSV ---
# Path relatif dari skrip ini ke file CSV
# Asumsikan 'data' folder berada satu level di atas 'scripts'
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.abspath(os.path.join(current_script_dir, os.pardir))
data_csv_path = os.path.join(project_root_dir, 'data', 'kualitas_udara_fixed.csv')

print(f"\nMencoba memuat data dari: {data_csv_path}")
try:
    df = pd.read_csv(data_csv_path)
    print("Data berhasil dimuat!")
    print("\nPratinjau Data (5 baris pertama):")
    print(df.head())
    print(f"\nDistribusi Kelas Target:\n{df['Kualitas_Udara'].value_counts()}")
except FileNotFoundError:
    print(f"ERROR: File CSV tidak ditemukan di '{data_csv_path}'. Pastikan file ada dan path benar.")
    exit() # Keluar dari skrip jika file tidak ditemukan

# --- 2. Memisahkan Fitur (X) dan Target (y) ---
# 'suhu' dan 'kelembapan' adalah fitur, 'Kualitas_Udara' adalah target
X = df[['PM2_5_ISPU', 'PM10_ISPU', 'CO_ISPU', 'NO2_ISPU', 'O3_ISPU']]
y = df['Kualitas_Udara']

print(f"\nFitur yang digunakan: {X.columns.tolist()}")
print(f"Nama Kolom Target: '{y.name}'")
print(f"Kelas Target Unik: {y.unique().tolist()}")

# --- 3. Memisahkan Data Training dan Testing ---
# 25% data untuk pengujian, 75% untuk pelatihan
# stratify=y penting untuk menjaga proporsi kelas di train/test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

print(f"\nUkuran Data Pelatihan (X_train, y_train): {X_train.shape}, {y_train.shape}")
print(f"Ukuran Data Pengujian (X_test, y_test): {X_test.shape}, {y_test.shape}")

# --- 4. Membuat dan Melatih Model Random Forest ---
# n_estimators: Jumlah pohon dalam hutan (coba 100 sebagai awal yang baik)
# random_state: Untuk reproduktifitas hasil (agar hasilnya sama setiap kali dijalankan)
print("\nMelatih Model Random Forest...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
print("Model Random Forest berhasil dilatih!")

# --- 5. Membuat Prediksi dan Mengevaluasi Model ---
print("\nMengevaluasi kinerja model pada data pengujian...")
y_pred = model.predict(X_test)

# a. Akurasi
accuracy = accuracy_score(y_test, y_pred)
print(f"\n---> Akurasi Model: {accuracy:.4f}")

# b. Laporan Klasifikasi (Precision, Recall, F1-Score per kelas)
print("\n---> Laporan Klasifikasi:")
print(classification_report(y_test, y_pred, target_names=model.classes_))

# c. Confusion Matrix
cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
print("\n---> Confusion Matrix:")
print(cm)

# d. Visualisasi Confusion Matrix
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=model.classes_, yticklabels=model.classes_)
plt.title('Confusion Matrix untuk Klasifikasi Kualitas_Udara Ruangan')
plt.xlabel('Prediksi Label')
plt.ylabel('Label Sebenarnya')
plt.show()

# --- 6. Menyimpan Model yang Sudah Dilatih ---
# Buat folder 'models' di root proyek jika belum ada
models_dir = os.path.join(project_root_dir, 'models')
if not os.path.exists(models_dir):
    os.makedirs(models_dir)

model_filename = 'kualitas_udara_rf_model.joblib'
model_path = os.path.join(models_dir, model_filename)
joblib.dump(model, model_path)
print(f"\nModel telah disimpan di: {model_path}")

# --- 7. Menyimpan Label Kelas (Penting untuk PHP) ---
# Menyimpan urutan label kelas yang dipelajari model.
# Ini memastikan PHP dapat menginterpretasikan hasil prediksi dengan benar.
class_labels = list(model.classes_)
labels_filename = 'class_labels.txt'
labels_path = os.path.join(models_dir, labels_filename)
with open(labels_path, 'w') as f:
    for label in class_labels:
        f.write(label + '\n')
print(f"Label kelas disimpan di: {labels_path}")


from sklearn.tree import plot_tree

# --- 8. Visualisasi Salah Satu Pohon Menggunakan Matplotlib ---
print("\nMenampilkan salah satu pohon dalam Random Forest dengan matplotlib...")

estimator = model.estimators_[0]  # ambil pohon ke-1
plt.figure(figsize=(20, 10))
plot_tree(
    estimator,
    feature_names=X.columns,
    class_names=model.classes_,
    filled=True,
    rounded=True,
    max_depth=3  # opsional: batasi kedalaman agar tidak terlalu besar
)
plt.title("Visualisasi Salah Satu Pohon Keputusan (Random Forest)")
plt.tight_layout()
plt.show()
print("\n--- Proses Pelatihan Model Selesai ---")

