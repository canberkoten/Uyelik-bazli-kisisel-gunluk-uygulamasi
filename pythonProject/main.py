import streamlit as st
import sqlite3
import hashlib
import os
import matplotlib.pyplot as plt

# Şifreyi hash'leme fonksiyonu
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Veritabanı bağlantısı oluşturma
def create_connection():
    conn = sqlite3.connect('users.db')
    return conn

# Kullanıcı tablosu oluşturma
def create_user_table():
    conn = create_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
    conn.commit()

# Günlük tablosu oluşturma (file_path sütunu ile)
def create_journal_table():
    conn = create_connection()
    # Günlük tablosunu oluşturuyoruz (file_path sütunu ile)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS journals (
        username TEXT, 
        entry TEXT, 
        file_path TEXT
    )''')
    conn.commit()

# Kullanıcı ekleme
def add_user(username, password):
    conn = create_connection()
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()

# Kullanıcı girişi
def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    data = cursor.fetchone()
    return data

# Günlük kaydetme
def add_journal_entry(username, entry, file_path=None):
    conn = create_connection()
    conn.execute('INSERT INTO journals (username, entry, file_path) VALUES (?, ?, ?)', (username, entry, file_path))
    conn.commit()

# Günlükleri alma
def get_journal_entries(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT rowid, entry, file_path FROM journals WHERE username = ?', (username,))
    data = cursor.fetchall()
    return data

# Günlüğü güncelleme
def update_journal_entry(entry_id, new_entry):
    conn = create_connection()
    conn.execute('UPDATE journals SET entry = ? WHERE rowid = ?', (new_entry, entry_id))
    conn.commit()

# Günlüğü silme
def delete_journal_entry(entry_id):
    conn = create_connection()
    conn.execute('DELETE FROM journals WHERE rowid = ?', (entry_id,))
    conn.commit()

# Günlükleri arama
def search_journal_entries(username, search_term):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT rowid, entry, file_path FROM journals WHERE username = ? AND entry LIKE ?', (username, f'%{search_term}%'))
    data = cursor.fetchall()
    return data

# Günlük sayısını alma
def get_journal_count(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM journals WHERE username = ?', (username,))
    count = cursor.fetchone()[0]
    return count

# Streamlit uygulaması
def main():
    # Oturum bilgilerini kontrol et
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ''

    st.title("Kişisel Günlük Uygulaması")

    # Kullanıcı çıkış yapma
    if st.session_state.logged_in:
        st.sidebar.write(f"Hoşgeldin, {st.session_state.username}")
        if st.sidebar.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.session_state.username = ''
            st.success("Başarıyla çıkış yaptınız!")
        else:
            # Günlükleri gösterme ve yeni günlük ekleme
            st.subheader("Günlüklerin")
            entries = get_journal_entries(st.session_state.username)
            if entries:
                for entry in entries:
                    st.write(entry[1])
                    if entry[2]:
                        st.image(entry[2])
                    if st.button(f"Düzenle {entry[0]}"):
                        new_entry = st.text_area("Günlüğü Düzenle", entry[1])
                        if st.button(f"Güncelle {entry[0]}"):
                            update_journal_entry(entry[0], new_entry)
                            st.success("Günlük başarıyla güncellendi!")
                    if st.button(f"Sil {entry[0]}"):
                        delete_journal_entry(entry[0])
                        st.success("Günlük başarıyla silindi!")
            else:
                st.write("Henüz bir günlük eklemediniz.")

            st.subheader("Yeni Günlük Ekle")
            daily_entry = st.text_area("Bugünkü düşüncelerinizi yazın")
            uploaded_file = st.file_uploader("Bir dosya yükleyin (opsiyonel)", type=["jpg", "png", "pdf"])
            file_path = None
            if uploaded_file is not None:
                file_path = f"uploads/{uploaded_file.name}"
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Dosya yüklendi: {uploaded_file.name}")

            if st.button("Günlüğü Kaydet"):
                add_journal_entry(st.session_state.username, daily_entry, file_path)
                st.success("Günlüğünüz başarıyla kaydedildi!")

            # Günlüklerde arama
            st.subheader("Günlüklerde Ara")
            search_term = st.text_input("Anahtar kelime girin")
            if st.button("Ara"):
                search_results = search_journal_entries(st.session_state.username, search_term)
                if search_results:
                    for result in search_results:
                        st.write(result[1])
                        if result[2]:
                            st.image(result[2])
                else:
                    st.write("Hiçbir sonuç bulunamadı.")

            # Analitik veriler (günlük sayısı)
            st.subheader("Günlük Yazma İstatistikleri")
            journal_count = get_journal_count(st.session_state.username)
            st.write(f"Toplam Günlük Sayısı: {journal_count}")

            # Basit bir grafik oluşturma
            fig, ax = plt.subplots()
            ax.bar(['Toplam Günlük'], [journal_count])
            st.pyplot(fig)
    else:
        # Giriş ve kayıt sayfası
        menu = ["Giriş Yap", "Kayıt Ol"]
        choice = st.sidebar.selectbox("Menü", menu)

        if choice == "Kayıt Ol":
            st.subheader("Kullanıcı Kayıt")
            new_user = st.text_input("Kullanıcı Adı")
            new_password = st.text_input("Parola", type='password')

            if st.button("Kayıt Ol"):
                create_user_table()
                hashed_password = hash_password(new_password)
                add_user(new_user, hashed_password)
                st.success("Başarıyla kayıt oldunuz!")
                st.info("Giriş yapmak için menüden 'Giriş Yap' seçeneğini kullanın.")

        elif choice == "Giriş Yap":
            st.subheader("Kullanıcı Girişi")
            username = st.text_input("Kullanıcı Adı")
            password = st.text_input("Parola", type='password')

            if st.button("Giriş Yap"):
                hashed_password = hash_password(password)
                result = login_user(username, hashed_password)

                if result:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    create_journal_table()  # Günlük tablosunu oluştur
                    st.success(f"Hoşgeldin {username}")
                else:
                    st.warning("Kullanıcı adı veya parola hatalı")

if __name__ == '__main__':
    main()
