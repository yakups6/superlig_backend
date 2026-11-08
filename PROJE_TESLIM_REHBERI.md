# 🎓 Trendyol Süper Lig Analiz & Scout Projesi — Teslim ve Sunum Rehberi

Bu rehber, projenizi hocanıza eksiksiz bir şekilde sunmanız, canlı çalışan mobil arayüzü göstermeniz ve sorulabilecek tüm teknik/verisel soruları yanıtlamanız için hazırlanmıştır.

---

## 🌟 1. Projeye Genel Bakış ve Mimarisi

Bu proje, **Trendyol Süper Lig 2026/2027 Sezonu** için geliştirilmiş **Full-Stack Analiz, İstatistik, Transfer Takip ve Scout** platformudur.

### Teknoloji Yığını:
- **Backend Servisi:** Python 3.14 + Django 5.x + Django REST Framework (DRF)
- **Veritabanı:** İlişkisel Veritabanı (SQLite / PostgreSQL uyumlu ORM, 8 ana tablo)
- **API Dokümantasyonu:** OpenAPI 3.0 & Swagger UI (drf-spectacular)
- **Canlı Mobil Web Uygulaması:** HTML5 / CSS3 / Vanilla JS SPA (Mobil Cihaz Çerçevesi + Masaüstü Tam Ekran Modu, Sıfır Bağımlılıkla Tarayıcıda Anında Çalışır)
- **Mobil Uygulama Kaynak Kodları:** `mobile/` klasöründe React Native (Expo) tabanlı modüler mobil istemci.
- **Dış Entegrasyonlar:** Transfermarkt + SofaScore/WhoScored + API-Football (RapidAPI) senkronizasyon motoru.

---

## 🚀 2. Projeyi Canlı Çalıştırma ve Hocaya Gösterme Adımları

### A. Sunucuyu Başlatma (Şu an Zaten Arka Planda Çalışıyor)
Eğer sunucu kapalıysa, terminalden şu komutla başlatılır:
```powershell
.\env\Scripts\python.exe manage.py runserver
```

### B. Canlı Mobil Uygulamayı Açma
Tarayıcınızda (Chrome, Edge vb.) şu adrese gidin:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** (veya `http://localhost:8000/app/`)

**Sunumda Göstereceğiniz 6 Ana Ekran:**
1. **📱 Ana Sayfa (Home):**
   - 2026/2027 Sezonu canlı rozeti, güncel saat, lig özet şeridi (18 Takım, 149 Oyuncu, 93 Transfer, Lider Galatasaray).
   - 6 modüllü görsel menü: *Oyuncular, Eski Oyuncular, Transferler, Karşılaştırma, Takımlar, Lig İstatistikleri*.
   - Canlı maç skoru kartı (Galatasaray 2 - 1 Amed SK).
2. **🛡️ Takım Analizi (1. Ekran):**
   - 18 Süper Lig kulübünü içeren dinamik açılır kutu.
   - 3 Metrik Rozeti: **Puan**, **Ligdeki Sıra**, **Kadro Değeri**.
   - Kadro arama çubuğu ve tüm futbolcuların fotoğraflı, mevki, forma numaralı ve piyasa değerli kartları.
3. **🔄 Transfer Takip (2. Ekran):**
   - **"API ile Güncelle"** butonu (canlı veri senkronizasyonu tetikler).
   - Arama kutusu ve filtre sekmeleri (*Tümü, Gelenler, Gidenler, Galatasaray, Fenerbahçe, Beşiktaş, Trabzonspor*).
   - Transfer hareket kartları (Ayrıldığı kulüp ➔ Yeni kulüp, Bonservis/Kira bedeli, Tarih ve Transfer Tipi).
4. **⚖️ Oyuncu Karşılaştırma & Scout (3. Ekran):**
   - İki futbolcuyu seçerek kafa kafaya karşılaştırma.
   - Canlı **Yetenek Radarı (Canvas Radar Chart)**: *Hız, Şut, Pas, Dribbling, Defans, Fizik*.
   - Oran çubukları: *Gol, Asist, Şut / Maç, Pas İsabeti* ve *Piyasa Değeri*.
   - **Algoritmik Analiz Konuşma Balonu**: İki oyuncunun güçlü yönlerini kıyaslayan yapay zeka analiz metni.
5. **🏆 Lig İstatistikleri & Puan Durumu:**
   - 18 takımlı güncel puan cetveli (Galatasaray 19P, Amed SK 16P, Fenerbahçe 15P...).
   - **Gol Krallığı Zirvesi** (Osimhen 6, Muriqi 7...).
   - **Asist Krallığı Zirvesi** (Barış Alper Yılmaz, Rafa Silva...).
6. **⭐ Süper Lig Efsaneleri:**
   - 23 efsane oyuncu (Gheorghe Hagi, Alex de Souza, Sergen Yalçın, Fernando Muslera, Wesley Sneijder, Ricardo Quaresma...).

---

## 📑 3. Swagger API Dokümantasyonu

Hoca backend API mimarisini görmek isterse:
👉 **[http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)**

- **Auth:** `/api/auth/register/`, `/api/auth/login/`, `/api/auth/profile/`
- **Takımlar:** `/api/teams/`, `/api/teams/{id}/`
- **Oyuncular:** `/api/players/`, `/api/players/{id}/`
- **Transferler:** `/api/transfers/`
- **Puan Durumu:** `/api/standings/`
- **Liderler:** `/api/leaderboards/`
- **İkili Karşılaştırma:** `/api/compare/?player1={id}&player2={id}`
- **Ana Sayfa Özeti:** `/api/home-summary/`
- **Senkronizasyon:** `/api/sync/`
- **Efsaneler:** `/api/legends/`

---

## 🧪 4. Otomasyon ve Birim Testleri (Unit Tests)

Projeyi savunurken testlerin eksiksiz geçtiğini göstermek için:
```powershell
.\env\Scripts\python.exe manage.py test api
```
**Sonuç:** `Ran 10 tests in ~9s — OK` (Tüm 10 test başarıyla geçmektedir).

---

## 📊 5. Veri Doğruluğu ve Güncellik Tablosu (Hocanın Sorabileceği Sorular)

| Soru / Konu | Cevabınız ve Projedeki Gerçek Durum |
| :--- | :--- |
| **Victor Nelsson nerede?** | Galatasaray'dan Danimarka kulübü **FC Nordsjaelland**'a bedelsiz transfer olmuştur. Transfer hareketlerinde ve kadroda günceldir. |
| **Youssef En-Nesyri nerede?** | Fenerbahçe'den Suudi Arabistan kulübü **Al-Ittihad**'a 15.00M € bedelle gitmiştir. Fenerbahçe aktif kadrosundan çıkarılmıştır. |
| **Dominik Livakovic nerede?** | Fenerbahçe'den **FC Barcelona**'ya 10.00M € bedelle transfer olmuştur. |
| **Mert Günok nerede?** | Beşiktaş'tan **Fenerbahçe**'ye geçmiştir. |
| **Ciro Immobile nerede?** | Beşiktaş'tan İtalya Serie A ekibi **Bologna FC**'ye transfer olmuştur. |
| **Mauro Icardi ve Masuaku?** | Sözleşmeleri sona ermiş olup **Serbest Oyuncu** (Free Agent) statüsündedir. |
| **Galatasaray'ın puanı ve durumu?** | 8 maçta 6 Galibiyet, 1 Beraberlik, 1 Mağlubiyet ile **19 Puan** ile 1. sıradadır. |
| **Ligde 2. sırada kim var?** | 8 maçta 5G, 1B, 2M ve 18 atılan golle **Amed SK (16 Puan)** 2. sıradadır. |
| **Galatasaray'ın Kadro Değeri?** | Güncel Transfermarkt verilerine göre **381.5M €** (381.500.000 €) olarak doğrulanmıştır ve kadrodaki oyuncuların toplam piyasa değeriyle %100 birebir uyuşmaktadır. |
| **Takım Gol Eşitliği (Parity)?** | Oyuncuların ligde attığı gollerin toplamı, puan cetvelindeki takım gol sayıları ile %100 birebir uyuşmaktadır (GS: 17, AMD: 18, FB: 22, TS: 18, BJK: 16, İBFK: 12). |

---

## 📱 6. React Native Mobil Projesi (`mobile/`)

Hocanız projenin kaynak kodlarını incelerken `mobile/` klasöründeki React Native projesini de gösterebilirsiniz:
- `mobile/App.js` ➔ Giriş ve Dark Tema yöneticisi
- `mobile/src/navigation/AppNavigator.js` ➔ Tab Navigator
- `mobile/src/screens/` ➔ 7 ekran (Home, Teams, Transfers, Compare, Standings, Legends, Scout)
- `mobile/src/services/api.js` ➔ Axios REST API bağlantısı
- `mobile/src/theme/colors.js` ➔ Ortak tema paleti
