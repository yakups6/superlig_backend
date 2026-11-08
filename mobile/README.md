# 📱 Trendyol Süper Lig Analiz & Scout - React Native (Expo SDK 58)

Bu klasör, projenin **React Native / Expo SDK 58** tabanlı mobil istemci uygulamasını içerir. Backend servisi olarak ana dizindeki **Django REST Framework** API'sini kullanır (`2026/2027 Adnan Süvari Sezonu`, Maçkolik tarzı canlı skor/dakika akışı, 1959'dan günümüze tüm sezonlar ve JWT üyelik).

---

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler
- **Node.js** (v20 LTS veya üzeri)
- **Expo Go** uygulaması (Google Play Store veya App Store'dan telefona ücretsiz yükleyebilirsiniz)
- Bilgisayar ve telefonun **aynı Wi-Fi ağına** bağlı olması

### 2. Backend Sunucusunu Yerel Ağa Açma (Ana Klasörde)
Telefonun bilgisayardaki Django API'sine erişebilmesi için sunucuyu `0.0.0.0:8000` üzerinde çalıştırın:
```bash
.\env\Scripts\python.exe manage.py runserver 0.0.0.0:8000 --noreload
```

### 3. Mobil Uygulamayı Başlatma (`mobile/` Klasöründe)
```bash
cd mobile
npm install
npx expo start --lan
```
Terminalde çıkan QR kodu telefonunuzdaki **Expo Go** uygulaması ile taratın veya Expo Go içinde **"Enter URL manually"** kısmına `exp://<BILGISAYAR_IP>:8081` yazarak açın.

---

## 🌐 Otomatik API Bağlantısı (`src/services/api.js` & `AuthScreen`)
- **Fiziksel Cihaz (Expo Go):** Expo `hostUri` üzerinden bilgisayarın LAN IP adresini (`http://<LAN_IP>:8000/api`) otomatik algılar.
- **Android Emülatör:** `http://10.0.2.2:8000/api`
- **iOS Simülatör / Web:** `http://127.0.0.1:8000/api`
- İsterseniz uygulama içindeki **Üyelik / Profil (`Auth`)** ekranının en altından özel bir sunucu URL'si kaydedebilirsiniz.

---

## 📂 Mimari & Dosya Yapısı

```text
mobile/
├── index.js                            # Expo registerRootComponent('main') giriş dosyası
├── App.js                              # Root AuthProvider + SafeAreaProvider + NavigationContainer
├── app.json                            # Expo SDK 58 yapılandırması
├── package.json                        # Expo 58, React 19, RN 0.88 bağımlılıkları
└── src/
    ├── components/
    │   ├── PlayerDetailModal.js        # Oyuncu detay, sezon istatistikleri, karşılaştır ve favori modalı
    │   └── SeasonPickerBar.js          # 1959-2026/27 kompakt sezon seçici + hızlı zıplama butonları
    ├── context/
    │   └── AuthContext.js              # JWT oturum yönetimi, misafir favori senkronu ve sezon durumu
    ├── navigation/
    │   └── AppNavigator.js             # 6'lı Bottom Tab + Stack ekranları (Players, Legends, Standings, Auth)
    ├── screens/
    │   ├── HomeScreen.js               # Ana Sayfa (Dinamik sayaçlar, Maçkolik canlı ticker, modül gridi)
    │   ├── FixturesScreen.js           # Canlı Skor & 1-34. Hafta Fikstürü (1 sn saat, 8 sn polling, İY/MS)
    │   ├── PlayersScreen.js            # Tüm Süper Lig Oyuncuları (Mevki, kulüp ve sezon filtresi)
    │   ├── TeamAnalysisScreen.js       # Takım Analizi (18 Süper Lig + 13 Tarihi Kulüp, sezon seçici)
    │   ├── TransfersScreen.js          # Transfer Takip (Gelen/Giden, sezonlar, API güncelleme)
    │   ├── CompareScreen.js            # Oyuncu Karşılaştırma (Sezonlu, Swap, 6-eksen SVG Radar, Analiz)
    │   ├── StandingsScreen.js          # Puan Durumu & Gol/Asist Krallığı (1959-2026/27)
    │   ├── LegendsScreen.js            # Eski Oyuncular & Efsaneler
    │   ├── ScoutScreen.js              # Favoriler / Scout Takip Listesi
    │   └── AuthScreen.js               # JWT Giriş, Kayıt, Profil, Şifre Değiştir ve API URL ayarları
    ├── services/
    │   └── api.js                      # Axios + JWT Refresh Interceptor + Tüm API metodları
    ├── theme/
    │   └── colors.js                   # Koyu stadyum tema paleti
    └── utils/
        ├── format.js                   # Piyasa değeri ve görsel yardımcıları
        └── liveClock.js                # Maçkolik 1H / İY / 2H / +uzatma / MS canlı saat motoru
```
