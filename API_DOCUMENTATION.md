# ⚽ Trendyol Süper Lig Analiz & Scout REST API Dokümantasyonu
> **Ders:** Web Tabanlı Teknolojiler – Dönem Sonu Projesi  
> **Teknoloji Yığını:** Python (Django 6), Django REST Framework, PostgreSQL, SimpleJWT, React Native  

---

## 📋 1. Proje Şartnamesi Karşılama Tablosu
*(Kaynak: `Web Tabanlı Teknolojiler Dönem Sonu Projesi.docx`)*

| Şartname Maddesi | Projedeki Karşılığı | Durum |
|---|---|---|
| **En az 5 farklı veri modeli / entity** | **9 Farklı Model:** `Season`, `Team`, `Player`, `PlayerAttribute`, `PlayerSeasonStats`, `LeagueStanding`, `Transfer`, `ScoutList`, `Fixture` | ✅ **Tam Karşılandı (9/5)** |

| **Kalıcı bir veritabanı kullanımı** | **PostgreSQL** (`psycopg2-binary`, `.env` üzerinden dinamik yapılandırma, SQLite fallback) | ✅ **Tam Karşılandı** |
| **RESTful API Mimarisi & HTTP Metotları** | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` metotlarının tamamı desteklenir | ✅ **Tam Karşılandı** |
| **Tam CRUD İşlemleri** | Oyuncular, Takımlar, Transferler, Sezonlar, Puan Durumu ve Scout Notları üzerinde tam CRUD | ✅ **Tam Karşılandı** |
| **Kullanıcı Kayıt & Giriş Sistemi** | `POST /api/auth/register/`, `POST /api/auth/login/`, `POST /api/auth/refresh/` | ✅ **Tam Karşılandı** |
| **Kimlik Doğrulama & Yetkilendirme** | **JWT (JSON Web Token - SimpleJWT):** `Bearer <access_token>` | ✅ **Tam Karşılandı** |
| **Uygun HTTP Durum Kodları** | `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error` | ✅ **Tam Karşılandı** |
| **Anlamlı Hata Mesajları** | `api/exceptions.py` üzerinden standart yapılandırılmış JSON hata yanıtları | ✅ **Tam Karşılandı** |
| **API Dokümantasyonu & Swagger** | **Swagger UI & ReDoc** entegrasyonu (`drf-spectacular`, OpenAPI 3.0, `/swagger/`) | ✅ **Tam Karşılandı** |

---

## 🌐 2. Canlı Sunum & Swagger UI Dokümantasyonu

Projenize **OpenAPI 3.0 & Swagger UI** (`drf-spectacular`) tam entegre edilmiştir. Sunumunuzu doğrudan tarayıcı üzerinden interaktif olarak gerçekleştirebilirsiniz.

### 2.1. Swagger Arayüzü Bağlantıları
Sunucuyu başlattıktan sonra (`python manage.py runserver`) tarayıcınızda açabileceğiniz adresler:
* **Swagger UI (Canlı Sunum Adresi):** [http://localhost:8000/swagger/](http://localhost:8000/swagger/) *(Alternatif: `http://localhost:8000/api/docs/`)*
* **ReDoc Alternatif Görünümü:** [http://localhost:8000/redoc/](http://localhost:8000/redoc/)
* **OpenAPI 3.0 Şema İndirme:** [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

### 2.2. Swagger Üzerinden Sunum Adımları
1. **Endpoint'leri İnceleme:**
   - Swagger arayüzünde tüm uç noktalar 11 ayrı kategoriye bölünmüştür:
     * `1. Kimlik Doğrulama (Auth)` -> Kayıt, Giriş, Token Yenileme, Profil
     * `2. Sezonlar` -> Sezon CRUD ve Otomatik Sezon Geçişi
     * `3. Takım Analizi` -> Takımlar, Puan, Sıra, Kadro Değeri ve Oyuncu Kadrosu
     * `4. Oyuncular & Efsaneler` -> Güncel ve efsane oyuncular (Alex, Sneijder, Hagi vb.)
     * `5. Oyuncu Sezon İstatistikleri` -> Sezon sezon maç, gol, asist, reyting
     * `6. Transfer Takip` -> Süper Lig'e gelenler, gidenler ve lig içi
     * `7. Puan Durumu` -> Sıra, O, G, B, M, AG, YG, AV, P
     * `8. Scout / Favoriler` -> Kullanıcıya özel favori oyuncu listesi (CRUD)
     * `9. Lig İstatistikleri & Liderler` -> Gol krallığı, asist krallığı, kilit pas
     * `10. Oyuncu Karşılaştırma & Algoritmik Analiz` -> Birebir istatistik barları, radar özellikleri ve algoritmik analiz cümlesi
     * `11. Ana Sayfa Gösterge Paneli` -> 1. fotoğraftaki sayaçlar ve lig lideri
2. **Canlı Test Etme (Try it out):**
   - Herhangi bir endpoint'e tıklayın, **"Try it out"** butonuna basın ve **"Execute"** ile anında çalışan canlı yanıtı hocanıza gösterin.
3. **Yetkilendirme (Authorize):**
   - `POST /api/auth/login/` ile giriş yapıp dönen `access` token'ı kopyalayın.
   - Sayfanın sağ üstündeki **"Authorize"** butonuna tıklayıp `Bearer <access_token>` formatında yapıştırın. Yetki gerektiren işlemleri (Scout ekleme, profil vb.) canlı test edin.

---

## 🗄️ 3. PostgreSQL Kurulum & Çalıştırma

### 2.1. PostgreSQL Veritabanı Oluşturma
PostgreSQL terminalinde (`psql`) veya pgAdmin'de:
```sql
CREATE DATABASE superlig_db;
```

### 2.2. `.env` Dosyası Ayarları
Proje kök dizinindeki `.env` dosyasını düzenleyin:
```env
DEBUG=True
SECRET_KEY=django-insecure-superlig-secret-key

# PostgreSQL'i aktif etmek için:
USE_SQLITE=false

# PostgreSQL Bağlantı Bilgileri
DB_ENGINE=postgresql
DB_NAME=superlig_db
DB_USER=postgres
DB_PASSWORD=sizin_postgres_sifreniz
DB_HOST=localhost
DB_PORT=5432
```

### 2.3. Migrasyonları Çalıştırma ve Tohum Verileri Yükleme
```bash
# Tabloları oluştur
.\env\Scripts\python manage.py migrate

# Fotoğraflardaki gerçekçi verileri yükle
.\env\Scripts\python manage.py seed_data

# Sunucuyu React Native için tüm IP'lerden dinleyecek şekilde başlat
.\env\Scripts\python manage.py runserver 0.0.0.0:8000
```

---

## 🔐 3. Kimlik Doğrulama (Auth) Endpoint'leri

### 3.1. Kullanıcı Kaydı (`POST /api/auth/register/`)
Yeni kullanıcı hesabı oluşturur, otomatik JWT token'ları üretir.
- **URL:** `http://localhost:8000/api/auth/register/`
- **Metot:** `POST`
- **İstek Gövdesi:**
```json
{
  "username": "scout_furkan",
  "email": "furkan@example.com",
  "first_name": "Furkan",
  "last_name": "Kaya",
  "password": "Password123!",
  "password2": "Password123!"
}
```
- **Yanıt (201 Created):**
```json
{
  "message": "Kullanıcı başarıyla kaydedildi.",
  "user": {
    "id": 2,
    "username": "scout_furkan",
    "email": "furkan@example.com",
    "first_name": "Furkan",
    "last_name": "Kaya"
  },
  "tokens": {
    "refresh": "eyJhbGciOi...",
    "access": "eyJhbGciOi..."
  }
}
```

### 3.2. Kullanıcı Girişi (`POST /api/auth/login/`)
- **URL:** `http://localhost:8000/api/auth/login/`
- **Metot:** `POST`
- **İstek Gövdesi:**
```json
{
  "username": "scout_furkan",
  "password": "Password123!"
}
```
- **Yanıt (200 OK):**
```json
{
  "message": "Giriş başarılı.",
  "user": {
    "id": 2,
    "username": "scout_furkan",
    "email": "furkan@example.com"
  },
  "tokens": {
    "refresh": "eyJhbGciOi...",
    "access": "eyJhbGciOi..."
  }
}
```

### 3.3. Token Yenileme (`POST /api/auth/refresh/`)
- **URL:** `http://localhost:8000/api/auth/refresh/`
- **İstek Gövdesi:** `{"refresh": "<refresh_token>"}`
- **Yanıt (200 OK):** `{"access": "<new_access_token>"}`

### 3.4. Profil Bilgisi (`GET`, `PUT` `/api/auth/me/`)
- **Header:** `Authorization: Bearer <access_token>`
- **Metot:** `GET` veya `PUT`
- **Yanıt (200 OK):** Giriş yapan kullanıcının profil bilgileri.

---

## 📡 4. REST API CRUD ve Analiz Endpoint'leri

### 4.1. Sezon Yönetimi & Otomatik Sezon Geçişi
| Metot | Endpoint | Açıklama | HTTP Kodu |
|---|---|---|---|
| `GET` | `/api/seasons/` | Sezon listesi | 200 OK |
| `GET` | `/api/seasons/current/` | **Aktif Sezon (Tarihe göre otomatik güncellenir)** | 200 OK |
| `POST` | `/api/seasons/` | Yeni sezon ekleme (CRUD - Create) | 201 Created |
| `PUT/PATCH` | `/api/seasons/<id>/` | Sezon güncelleme (CRUD - Update) | 200 OK |
| `DELETE` | `/api/seasons/<id>/` | Sezon silme (CRUD - Delete) | 204 No Content |
| `POST` | `/api/seasons/auto-switch/` | Tarihe göre otomatik geçişi tetikle | 200 OK |

---

### 4.2. Takımlar (2. Fotoğraf - Takım Analizi)
| Metot | Endpoint | Açıklama | HTTP Kodu |
|---|---|---|---|
| `GET` | `/api/teams/` | Süper Lig takımlarını listeler | 200 OK |
| `GET` | `/api/teams/<id>/` | **Puan, Lig Sırası, Kadro Değeri ve Oyuncu Listesi** | 200 OK |
| `POST` | `/api/teams/` | Yeni takım ekle (CRUD - Create) | 201 Created |
| `PUT/PATCH` | `/api/teams/<id>/` | Takım güncelle (CRUD - Update) | 200 OK |
| `DELETE` | `/api/teams/<id>/` | Takım sil (CRUD - Delete) | 204 No Content |

#### `GET /api/teams/1/` Örnek Yanıtı (Galatasaray):
```json
{
  "id": 1,
  "name": "Galatasaray",
  "short_name": "GS",
  "city": "İstanbul",
  "stadium": "RAMS Park",
  "manager": "Okan Buruk",
  "market_value": "261000000.00",
  "logo_url": "https://.../Galatasaray_Sports_Club_Logo.png",
  "standing": {
    "rank": 1,
    "played": 18,
    "won": 15,
    "drawn": 2,
    "lost": 1,
    "goals_for": 44,
    "goals_against": 15,
    "goal_difference": 29,
    "points": 47
  },
  "players": [
    {
      "id": 1,
      "name": "Victor Osimhen",
      "position": "Santrafor",
      "market_value": "100000000.00",
      "image_url": "https://.../864389.png"
    },
    {
      "id": 2,
      "name": "Rafael Leão",
      "position": "Sol Kanat",
      "market_value": "40000000.00",
      "image_url": "https://.../leao.png"
    },
    {
      "id": 4,
      "name": "Barış Alper Yılmaz",
      "position": "Kanat",
      "market_value": "20000000.00",
      "image_url": "https://.../1188448.png"
    }
  ]
}
```

---

### 4.3. Transfer Takip (2. Fotoğraf - Transfer Hareketleri)
| Metot | Endpoint | Açıklama |
|---|---|---|
| `GET` | `/api/transfers/` | Tüm transferler |
| `GET` | `/api/transfers/?type=INCOMING` | **Süper Lig'e Gelenler** |
| `GET` | `/api/transfers/?type=OUTGOING` | **Süper Lig'den Gidenler** (Örn: Gabriel Sara Betis'e 18M €) |
| `GET` | `/api/transfers/?type=DOMESTIC` | **Süper Lig İçi** (Örn: Rafa Silva Başakşehir'e Kiralık) |
| `POST` | `/api/transfers/` | Yeni transfer kaydet (CRUD - Create) |
| `PUT/PATCH` | `/api/transfers/<id>/` | Transfer güncelle (CRUD - Update) |
| `DELETE` | `/api/transfers/<id>/` | Transfer sil (CRUD - Delete) |

---

### 4.4. Oyuncu Karşılaştırma & Algoritmik Analiz (2. Fotoğraf - Sağ Ekran)
- **URL:** `GET /api/compare/?player1=<id>&player2=<id>`
- **Örnek:** `/api/compare/?player1=1&player2=2` (Victor Osimhen vs Youssef En-Nesyri)
- **Dönen Veriler:**
  - `bars`: Gol (12 vs 8), Asist (4 vs 3), Şut/Maç (3.5 vs 2.1), Pas İsabeti (%78 vs %74), Kilit Pas / Maç (2.2 vs 1.1) ve her iki oyuncunun bar doluluk yüzdeleri (`pct1`, `pct2`).
  - `radar`: Hız, Şut, Pas, Teknik, Defans, Fizik değerleri.
  - `algorithmic_analysis`:
    ```json
    {
      "headline": "Algoritmik Analiz: Victor Osimhen ceza sahası etkinliğinde ve gol üretkenliğinde %60 daha verimli.",
      "insights": [
        "Victor Osimhen, maç başına 0.80 gol ortalamasıyla Youssef En-Nesyri (0.50) karşısında hücum sonlandırmada önde.",
        "Victor Osimhen, maç başına 2.2 kilit pas ile rakip savunma arkasına sarkmada daha yaratıcı.",
        "Victor Osimhen, maç başına şut denemelerinde (%67 farkla) kaleyi daha sık yokluyor.",
        "Victor Osimhen, açık alanda ve kontra atak geçişlerinde sprint süratiyle fark yaratıyor."
      ]
    }
    ```

---

### 4.5. Lig İstatistikleri (Liderler)
- **URL:** `GET /api/leaderboards/`
- İçinde bulunulan sezonda:
  - `top_scorers` (Gol krallığı)
  - `top_assists` (Asist krallığı)
  - `top_key_passes` (Kilit pas sıralaması)
  - `top_shots` (Şut / Maç)
  - `top_pass_accuracy` (Pas isabet yüzdesi)
  - `top_ratings` (En yüksek maç puanı)

---

### 4.6. Eski Oyuncular (Efsaneler - Sezon Sezon Geçmiş)
- **URL:** `GET /api/players/?is_legend=true` (Alex de Souza, Sneijder, Mario Gomez, Hagi vb.)
- **URL:** `GET /api/players/<id>/` (Oyuncunun detayları ve `season_stats` dizisi altında sezon sezon maç, dakika, gol, asist, kilit pas, reyting verileri).

---

### 4.7. Kullanıcı Scout / Favori Takip Listesi (Özel CRUD)
Giriş yapmış her kullanıcı kendi scout listesini yönetir (`Authorization: Bearer <token>`):
| Metot | Endpoint | Açıklama |
|---|---|---|
| `GET` | `/api/scout-notes/` | Kullanıcının eklediği scout/favori oyuncular |
| `POST` | `/api/scout-notes/` | Oyuncuyu scout listesine ekle ve not/puan ver |
| `PUT/PATCH` | `/api/scout-notes/<id>/` | Notu veya puanı güncelle |
| `DELETE` | `/api/scout-notes/<id>/` | Oyuncuyu scout listesinden sil |

---

## 📱 5. React Native Entegrasyonu

```javascript
// services/api.js
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

const API_URL = Platform.select({
  android: 'http://10.0.2.2:8000/api',
  ios: 'http://localhost:8000/api',
  default: 'http://localhost:8000/api',
});

const api = axios.create({ baseURL: API_URL });

// Otomatik JWT Token ekleyici
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth Servisleri
export const registerUser = (userData) => api.post('/auth/register/', userData);
export const loginUser = (credentials) => api.post('/auth/login/', credentials);
export const getMyProfile = () => api.get('/auth/me/');

// Uygulama Servisleri
export const getHomeSummary = () => api.get('/home-summary/');
export const getCurrentSeason = () => api.get('/seasons/current/');
export const getTeamDetail = (teamId) => api.get(`/teams/${teamId}/`);
export const getTransfers = (type = '') => api.get(`/transfers/${type ? `?type=${type}` : ''}`);
export const comparePlayers = (p1, p2) => api.get(`/compare/?player1=${p1}&player2=${p2}`);
export const getLeaderboards = () => api.get('/leaderboards/');
export const getStandings = () => api.get('/standings/');
export const getLegendPlayers = () => api.get('/players/?is_legend=true');
export const getPlayerDetail = (id) => api.get(`/players/${id}/`);

// Scout / Favori CRUD
export const getScoutNotes = () => api.get('/scout-notes/');
export const addScoutNote = (data) => api.post('/scout-notes/', data);
export const updateScoutNote = (id, data) => api.patch(`/scout-notes/${id}/`, data);
export const deleteScoutNote = (id) => api.delete(`/scout-notes/${id}/`);

// Fikstür & Canlı Skor Servisleri (API-Football)
export const getFixtures = (round = '') => api.get(`/fixtures/${round ? `?round_number=${round}` : ''}`);
export const getLiveMatches = () => api.get('/fixtures/live/');
export const getCurrentRoundFixtures = () => api.get('/fixtures/current-round/');

// Veri Senkronizasyonu & Otomasyon ("🔄 API ile Güncelle" Butonları)
export const syncTransfers = () => api.post('/sync/transfers/');
export const syncSquads = (teamId = '') => api.post(`/sync/squads/${teamId ? `?team_id=${teamId}` : ''}`);
export const syncAttributes = () => api.post('/sync/attributes/');
export const syncFixtures = () => api.post('/sync/fixtures/');
export const syncAllData = () => api.post('/sync/all/');

export default api;
```

---

## 🌐 6. Canlı Veri Entegrasyonları ve Otomasyon

Projede 3 farklı profesyonel futbol veri kaynağı mimariye entegre edilmiştir:

### 6.1. Transfermarkt (Web Scraping)
* **Kullanım Amacı:** Süper Lig kulüpleri, güncel oyuncu kadroları, forma numaraları, yaş, uyruk, piyasa değerleri ve transferler.
* **Nasıl Çalışır:** `api/integrations/transfermarkt_scraper.py` modülü `BeautifulSoup` ve modern `User-Agent` başlıklarıyla Transfermarkt Süper Lig ve kulüp sayfalarını tarar; gelen/giden transferleri ve kadro değerlerini günceller.
* **Uç Noktalar:**
  - `POST /api/sync/transfers/`: Mobil Transfer Takip ekranındaki **"🔄 API ile Güncelle"** butonuna basıldığında tetiklenir.
  - `POST /api/sync/squads/`: Kulüplerin resmi kadrolarını Transfermarkt'tan çeker.
* **Komut Satırı:**
  ```powershell
  python manage.py sync_transfermarkt --transfers
  python manage.py sync_transfermarkt --teams
  python manage.py sync_transfermarkt --squads
  ```

### 6.2. SofaScore & WhoScored (Oyuncu Analitiği & Radar Grafikleri)
* **Kullanım Amacı:** Oyuncu güçlü/zayıf yönleri ve 6 eksenli radar grafiği metrikleri (`Hız`, `Şut`, `Pas`, `Teknik`, `Defans`, `Fizik`).
* **Nasıl Çalışır:** `api/integrations/player_analytics.py` modülü WhoScored ve SofaScore'un analitik modelini temel alır. Osimhen, Icardi, En-Nesyri, Sara, Rafa Silva gibi yıldızların onaylı niteliklerini eşleştirir; yeni taranan oyuncular için de mevkilerine ve istatistiklerine göre dinamik algoritmik radar profili üretir.
* **Uç Noktalar:**
  - `POST /api/sync/attributes/`: Tüm futbolcuların radar değerlerini ve karakteristiklerini günceller.
  - `GET /api/compare/?player1=1&player2=2`: İki oyuncunun radar ve karşılaştırma grafiğini döndürür.
* **Komut Satırı:**
  ```powershell
  python manage.py sync_player_attributes
  ```

### 6.3. API-Football (RapidAPI) – Fikstür, Canlı Skor ve Otomasyon
* **Kullanım Amacı:** Süper Lig maç fikstürü, maç sonuçları, oynanmakta olan maçların canlı dakikası/skoru ve puan durumu otomasyonu.
* **Nasıl Çalışır:** `api/integrations/api_football.py` modülü API-Football RapidAPI servisini (`League ID: 203`) kullanır. `.env` içerisindeki `RAPIDAPI_KEY` ile çalışır; anahtar girilmediğinde veya kota aşıldığında sistem kesintiye uğramadan entegre Süper Lig fikstür motorunu devreye sokar.
* **Uç Noktalar:**
  - `GET /api/fixtures/`: Tüm maç fikstürü (haftaya, takıma veya duruma göre filtrelenebilir).
  - `GET /api/fixtures/live/`: Şu anda canlı oynanan Süper Lig maçları ve anlık skorlar.
  - `GET /api/fixtures/current_round/`: Güncel haftanın tüm maçları.
  - `POST /api/sync/fixtures/`: Fikstür ve canlı skorları API-Football ile senkronize eder.
* **Komut Satırı:**
  ```powershell
  python manage.py sync_fixtures
  python manage.py sync_fixtures --live
  python manage.py sync_fixtures --standings
  ```

### 6.4. Tek Tıkla Tam Otomasyon
Tüm veri kaynaklarını sırayla çalıştırmak için:
* **API:** `POST /api/sync/all/`
* **CLI:** `python manage.py sync_all`

