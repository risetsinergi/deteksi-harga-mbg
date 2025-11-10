import streamlit as st
from PIL import Image
import pandas as pd
from ultralytics import YOLO

# --- PENGATURAN DASAR & DATA ---

hide_st_style = """
            <style>
            .stToolbarActions {visibility: hidden;}
            #GithubIcon {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
            .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
            .viewerBadge_text__1JaDK {display: none;}
            ._terminalButton_rix23_138 {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
"""

st.markdown(hide_st_style, unsafe_allow_html=True)

st.set_page_config(
    page_title="Analisis Harga Porsi MBG",
    page_icon="🍱",
    layout="wide"
)

st.title('🍱 Analisis Estimasi Harga Porsi MBG')
st.write(
    "Unggah gambar nampan makanan Anda. Aplikasi ini akan menganalisis estimasi harga porsinya "
    "dan membandingkannya dengan target harga **Rp 10.000**."
)
st.info("Catatan: Harga di bawah ini adalah **estimasi kasar (kira-kira)** per porsi untuk wilayah Banjarbaru dan dapat bervariasi.")

data_harga = {
    'nama_makanan': [
        'nasi_putih', 'ayam', 'nasi_kuning', 'nasi_liwet', 'buah_jeruk',
        'buah_melon', 'buah_pisang', 'buah_duku', 'sayur_capcay',
        'sayur_wortel_kacang', 'sayur', 'wortel', 'susu', 'tahu', 'tempe',
        'tempe_bacem', 'ayam_kecap', 'buah_semangka',
        'buah_kelengkeng', 'mie_goreng', 'daging_slice', 'burger',
        'lontong_labu', 'sayur_gori', 'buah_rambutan'
    ],
    'estimasi_harga_rp': [
        2500,  # nasi_putih (1 porsi)
        4000,  # ayam (1 potong lauk)
        3000,  # nasi_kuning (1 porsi)
        3000,  # nasi_liwet (1 porsi)
        1500,  # buah_jeruk (1 buah)
        1000,  # buah_melon (1 potong)
        1000,  # buah_pisang (1 buah)
        1500,  # buah_duku (1 porsi kecil)
        2000,  # sayur_capcay (1 porsi sayur)
        1500,  # sayur_wortel_kacang (1 porsi sayur)
        1500,  # sayur (umum, 1 porsi)
        500,   # wortel (sebagai bagian dari sayur/lalapan)
        2500,  # susu (1 kotak/gelas kecil)
        1000,  # tahu (1 potong)
        1000,  # tempe (1 potong)
        1500,  # tempe_bacem (1 potong)
        4000,  # ayam_kecap (1 potong lauk)
        1000,  # buah_semangka (1 potong)
        1500,  # buah_kelengkeng (~3 biji)
        2000,  # mie_goreng (porsi pendamping)
        4500,  # daging_slice (1 potong lauk)
        5000,  # burger (1 mini burger sbg lauk)
        3500,  # lontong_labu (porsi)
        1500,  # sayur_gori (1 porsi sayur)
        1000   # buah_rambutan (~2 biji)
    ]
}
df_harga = pd.DataFrame(data_harga)

# Buat daftar semua makanan yang diketahui untuk dropdown
all_known_foods = list(data_harga['nama_makanan'])

# Target harga untuk perbandingan
TARGET_HARGA = 10000

# --- FUNGSI & MODEL ---
@st.cache_resource
def load_model(model_path):
    model = YOLO(model_path)
    return model

try:
    model = load_model('best.pt')
except Exception as e:
    st.error(f"Error memuat model: {e}. Pastikan file 'best.pt' ada di folder yang sama dengan app.py")
    st.stop()

# --- TAMPILAN UTAMA APLIKASI ---

st.subheader("Unggah Gambar Makananmu")
uploaded_file = st.file_uploader("Unggah gambar di sini...", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    col_img, col_res = st.columns(2)

    with col_img:
        st.image(image, caption='Gambar yang diunggah.', use_container_width=True)

    with col_res:
        st.subheader("🔍 Hasil Analisis")
        with st.spinner('Model sedang menganalisis gambar...'):
            results = model(image)
            
            detected_objects = set()
            for r in results:
                for box in r.boxes:
                    class_name = model.names[int(box.cls)]
                    detected_objects.add(class_name)
            
            # Tampilkan apa yang terdeteksi
            if detected_objects:
                st.success(f"**Otomatis terdeteksi:** {', '.join(list(detected_objects))}")
            else:
                st.info("Model tidak mendeteksi item apapun. Silakan tambahkan secara manual.")

            st.write("---")
            st.subheader("Koreksi & Konfirmasi Manual")
            
            # Konversi set ke list agar bisa jadi nilai default
            detected_list = list(detected_objects) 
            
            final_food_list = st.multiselect(
                "Periksa hasil deteksi. Tambah/hapus item untuk konfirmasi manual:",
                options=all_known_foods,
                default=detected_list
            )
    
            # Cek apakah ada makanan untuk dihitung
            if final_food_list:
                
                # Ubah ke set untuk perhitungan (menghindari duplikat jika ada)
                final_food_set = set(final_food_list)

                estimasi = df_harga[df_harga['nama_makanan'].isin(final_food_set)]
                
                # Hanya ambil kolom harga dan jumlahkan
                total_harga = estimasi['estimasi_harga_rp'].sum()
                
                st.write("---")
                st.subheader("📊 Estimasi Total Harga Porsi")
                
                # Menampilkan daftar item dan harganya
                st.dataframe(estimasi.set_index('nama_makanan'))
                
                # Menampilkan total harga menggunakan st.metric
                st.metric(
                    label="Total Estimasi Harga",
                    value=f"Rp {total_harga:,.0f}"
                )
                
                st.write("---")
                st.subheader(f"📈 Perbandingan dengan Target Harga (Rp {TARGET_HARGA:,.0f})")

                selisih = total_harga - TARGET_HARGA
                
                if total_harga > TARGET_HARGA:
                    st.error(
                        f"**Lebih Mahal.** Estimasi harga (Rp {total_harga:,.0f}) "
                        f"lebih mahal Rp {selisih:,.0f} dari target."
                    )
                elif total_harga == TARGET_HARGA:
                     st.success(
                        f"**Sesuai Target.** Estimasi harga (Rp {total_harga:,.0f}) "
                        f"tepat sama dengan target harga."
                    )
                else:
                    # total_harga < TARGET_HARGA
                    st.success(
                        f"**Lebih Murah.** Estimasi harga (Rp {total_harga:,.0f}) "
                        f"lebih murah Rp {abs(selisih):,.0f} dari target."
                    )
                
            else:
                # Ini hanya muncul jika model tidak mendeteksi DAN pengguna menghapus semuanya
                st.warning("Tidak ada makanan yang dipilih untuk dianalisis.")
