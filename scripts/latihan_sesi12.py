
# LANGKAH 0 - Menyiapkan alat (import) dan alamat berkas

from datetime import datetime
from getpass import getpass
from pathlib import Path
import pandas as pd
from sqlalchemy import URL, Date, create_engine, text

# Alamat folder dan berkas
FOLDER_REPO = Path(__file__).resolve().parent.parent
BERKAS_MENTAH = FOLDER_REPO / "data" / "daftar_arsip_fakultas.csv"
FOLDER_OUTPUT = FOLDER_REPO / "output"
FOLDER_OUTPUT.mkdir(exist_ok=True)

# Tanggal acuan penilaian retensi
BERKAS_MENTAH = Path("data/daftar_arsip_fakultas.csv")
BERKAS_HASIL  = Path("output/salinan_arsip_bersih.csv") 
TANGGAL_ACUAN = pd.Timestamp("2026-12-31")

# LANGKAH 1 - Membaca CSV dan mengenali isinya

df = pd.read_csv(BERKAS_MENTAH, dtype=str, keep_default_na=False)

print("=== LANGKAH 1 - Kenali data ===")
print("Jumlah baris, kolom :", df.shape)
print("Nama kolom          :", list(df.columns))
print(df.head())

# LANGKAH 2 - Merapikan teks: buang spasi berlebih
for kolom in df.columns:
    df[kolom] = df[kolom].str.strip()

# Ganti spasi ganda di tengah judul menjadi satu spasi
df["judul"] = df["judul"].str.replace(r"\s+", " ", regex=True)
# LANGKAH 3 - Kosakata terkendali

KAMUS_UNIT = {
    "kepegawaian": "Kepegawaian",
    "kpg": "Kepegawaian",
    "kepeg.": "Kepegawaian",
    "keuangan": "Keuangan",
    "keu": "Keuangan",
    "keu.": "Keuangan",
    "akademik": "Akademik",
    "akd": "Akademik",
    "akadem.": "Akademik",
    "kemahasiswaan": "Kemahasiswaan",
    "umum dan perlengkapan": "Umum dan Perlengkapan",
    "ump": "Umum dan Perlengkapan",
    "umum & perlengkapan": "Umum dan Perlengkapan",
    "akad.": "Akademik",
    "kmh": "Kemahasiswaan",
}

KAMUS_MEDIA = {
    "kertas": "Kertas",
    "fisik": "Kertas",
    "elektronik": "Elektronik",
    "digital": "Elektronik",
    "e-arsip": "Elektronik",
}

KAMUS_AKSES = {
    "biasa": "Biasa",
    "terbatas": "Terbatas",
    "rahasia": "Rahasia",
}

# Menyeragamkan penulisan data
df["unit_pencipta"] = df["unit_pencipta"].str.lower().map(KAMUS_UNIT)
df["media"] = df["media"].str.lower().map(KAMUS_MEDIA)
df["tingkat_akses"] = df["tingkat_akses"].str.lower().map(KAMUS_AKSES)

print("\n=== LANGKAH 3 - Nilai unit setelah dibakukan ===")
print(df["unit_pencipta"].value_counts(dropna=False))
# LANGKAH 4 - Memeriksa data yang belum terbakukan

print("\n=== LANGKAH 4 - Pemeriksaan data ===")

print("Unit pencipta yang kosong:")
print(df[df["unit_pencipta"].isna()]["unit_pencipta"])

print("Media:")
print(df["media"].value_counts(dropna=False))

print("Tingkat akses:")
print(df["tingkat_akses"].value_counts(dropna=False))
# Menampilkan jumlah data kosong
print("\n=== CEK DATA KOSONG ===")
print(df.isna().sum())

# Menampilkan baris yang unit penciptanya kosong
print("\n=== DATA UNIT PENCIPTA KOSONG ===")
print(df[df["unit_pencipta"].isna()])
# Memeriksa variasi unit pencipta asli
df_cek = pd.read_csv(BERKAS_MENTAH, dtype=str, keep_default_na=False)

print("\n=== VARIASI UNIT PENCIPTA ASLI ===")
print(df_cek["unit_pencipta"].value_counts(dropna=False).to_string())
# Memeriksa nama unit yang belum masuk kamus
nilai_asli = df_cek["unit_pencipta"].str.strip().str.lower()

belum_terdaftar = sorted(set(nilai_asli) - set(KAMUS_UNIT.keys()))

print("\n=== UNIT BELUM TERDAFTAR DI KAMUS ===")
print(belum_terdaftar)
# LANGKAH 5 · Membuang baris duplikat (ekspor ganda)
jumlah_awal = len(df)
df = df.drop_duplicates()  # hapus baris kembar persis
print("\n=== LANGKAH 5 · Duplikat ===")
print("Duplikat dibuat :", jumlah_awal - len(df))
print("Sisa baris :", len(df))
# LANGKAH 6 · Menghubungkan dengan Jadwal Retensi Arsip (JRA)
JRA = pd.DataFrame([
    ("KP.01", "Formasi Pegawai",              2, 3, "Musnah"),
    ("KP.02", "Cuti Pegawai",                 1, 2, "Musnah"),
    ("KP.03", "Penilaian Kinerja",            2, 3, "Musnah"),
    ("KP.04", "Pengangkatan Pegawai",         2, 8, "Permanen"),
    ("KU.01", "Pertanggungjawaban Keuangan",  2, 8, "Musnah"),
    ("KU.02", "Laporan Keuangan Tahunan",     2, 8, "Permanen"),
    ("AK.01", "Jadwal Perkuliahan",           1, 1, "Musnah"),
    ("AK.02", "Daftar Nilai",                 2, 5, "Musnah"),
    ("AK.03", "Kurikulum dan RPS",            3, 5, "Permanen"),
    ("KM.01", "Beasiswa",                     2, 3, "Musnah"),
    ("KM.02", "Kegiatan Kemahasiswaan",       2, 3, "Musnah"),
    ("UM.01", "Pengadaan Barang",             2, 5, "Musnah"),
    ("UM.02", "Surat Edaran Pimpinan",        2, 3, "Permanen"),
], columns=["kode_klasifikasi", "nama_klasifikasi", 
            "retensi_aktif", "retensi_inaktif", "keterangan_jra"])

df = df.merge(JRA, on="kode_klasifikasi", how="left")

for kolom in ["retensi_aktif", "retensi_inaktif"]:
    df[kolom] = df[kolom].astype("Int64")

print("\n=== LANGKAH 6 · Cek 5 baris hasil gabungan JRA ===")
print(df[["no_arsip", "kode_klasifikasi", "nama_klasifikasi", "retensi_aktif"]].head())
# Memastikan kolom tanggal_arsip bertipe datetime (bukan teks)
df["tanggal_arsip"] = pd.to_datetime(df["tanggal_arsip"], dayfirst=True, errors="coerce")
# LANGKAH 7 · Menghitung akhir retensi dan status arsip
def tambah_tahun(tanggal, tahun):
    if pd.isna(tanggal) or pd.isna(tahun):
        return pd.NaT
    return tanggal + pd.DateOffset(years=int(tahun))

df["akhir_aktif"] = [
    tambah_tahun(t, n) 
    for t, n in zip(df["tanggal_arsip"], df["retensi_aktif"])
]
df["akhir_inaktif"] = [
    tambah_tahun(t, n) 
    for t, n in zip(df["akhir_aktif"], df["retensi_inaktif"])
]

def tentukan_status(baris):
    if pd.isna(baris["akhir_inaktif"]):
        return "Perlu Dicek"
    if TANGGAL_ACUAN < baris["akhir_aktif"]:
        return "Aktif"
    if TANGGAL_ACUAN < baris["akhir_inaktif"]:
        return "Inaktif"
    if baris["keterangan_jra"] == "Musnah":
        return "Usul Musnah"
    return "Serah ke Arsip Statis"

df["status_retensi"] = df.apply(tentukan_status, axis=1)

print("\n=== LANGKAH 7 · Hasil Penentuan Status ===")
print(df["status_retensi"].value_counts(dropna=False))
# LANGKAH 8 · Menandai masalah kualitas metadata
def catatan_kualitas(baris):
    masalah = []
    if baris["judul"] == "":
        masalah.append("judul kosong")
    if pd.isna(baris["tanggal_arsip"]):
        masalah.append("tanggal kosong")
    if pd.isna(baris["nama_klasifikasi"]):
        masalah.append("kode tidak ada di JRA")
    return "; ".join(masalah)

df["catatan_kualitas"] = df.apply(catatan_kualitas, axis=1)
df["perlu_dicek"] = df["catatan_kualitas"] != ""

# LANGKAH 9 · Ringkasan
print("\n=== LANGKAH 9 · Ringkasan status retensi ===")
print(df["status_retensi"].value_counts(dropna=False))
print("\nPerlu dicek manual :", int(df["perlu_dicek"].sum()), "arsip")

# LANGKAH 10 · Simpan salinan CSV
BERKAS_HASIL.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(BERKAS_HASIL, index=False)
print("\nSalinan disimpan ke :", BERKAS_HASIL)
# LANGKAH 11 · Simpan ke PostgreSQL
print("\n=== LANGKAH 11 · Menyimpan ke PostgreSQL ===")
user = "postgres" # Username bawaan PostgreSQL
sandi = getpass("Masukkan Password PostgreSQL Anda: ")

try:
    # Membuat koneksi ke database lokal
    engine = create_engine(f"postgresql+psycopg2://{user}:{sandi}@localhost:5432/postgres")
    
    # Menyimpan tabel (replace = timpa jika tabel sudah ada)
    df.to_sql("arsip_bersih_sesi12", engine, if_exists="replace", index=False)
    print("✅ Berhasil! Data tersimpan di tabel 'arsip_bersih_sesi12'")
except Exception as e:
    print("❌ Gagal menyimpan ke database. Error:", e)