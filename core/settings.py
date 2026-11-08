"""
Django settings for core project.
Süper Lig Analiz & Scout API
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-9o+w*r7hz9frcu@l)syqpyo1w3&=5i)@aeve)9_mnr5_%$n%#+')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1')

# React Native (Android Emulator 10.0.2.2, iOS Simulator localhost, Gerçek Cihaz Wi-Fi IP) için izin ver
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    
    # Local apps
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.railway.app',
    'https://*.up.railway.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database Configuration
# PostgreSQL / SQLite
# .env dosyasından DB_ENGINE ve veritabanı bilgileri okunur.
# Varsayılan olarak zengin Süper Lig verili db.sqlite3 kullanılır.
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite').lower()
DB_NAME = os.getenv('DB_NAME', 'superlig_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

if os.getenv('USE_SQLITE', 'true').lower() in ('true', '1') or DB_ENGINE == 'sqlite' or not os.getenv('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# CORS Settings (React Native için tüm isteklere izin ver)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

from datetime import timedelta

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'api.authentication.FlexibleJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': None, # Mobil uygulamalarda listeleri rahatça almak için varsayılan None
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Simple JWT Ayarları (Mobil oturum yönetimi)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# RapidAPI Ayarları (API-Football Entegrasyonu İçin)
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')

# Swagger / OpenAPI (drf-spectacular) Dokümantasyon Ayarları
SPECTACULAR_SETTINGS = {
    'TITLE': 'Trendyol Süper Lig Analiz & Scout REST API',
    'DESCRIPTION': (
        'Web Tabanlı Teknolojiler Dönem Sonu Projesi için geliştirilmiş '
        'Süper Lig Analiz, Kadro Takibi, Transfer Takip (Gelen/Giden/Lig İçi), '
        'Algoritmik Oyuncu Karşılaştırma, Radar Grafikleri, Fikstür & Canlı Skor, '
        'Puan Durumu, Sezon Liderleri, Eski Efsaneler ve Scout Listesi RESTful API sistemi.\n\n'
        '**Entegre Edilen Canli Veri Kaynaklari:**\n'
        '- [Transfermarkt Web Scraping]: Super Lig resmi kadrolari, oyuncu piyasa degerleri ve transferler.\n'
        '- [SofaScore / WhoScored Analitigi]: Oyuncu guclu/zayif yonleri ve 6 eksenli radar grafigi metrikleri.\n'
        '- [API-Football RapidAPI]: Haftalik fikstur, mac sonuclari, anlik canli skorlar ve lig otomasyonu.\n\n'
        '**Yetkilendirme:** Sag ustteki **Authorize** butonuna tiklayip `Bearer <access_token>` formatinda token girebilirsiniz.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': '1. Kimlik Doğrulama (Auth)', 'description': 'Kayıt, Giriş, Token Yenileme, Profil ve Şifre'},
        {'name': '2. Sezonlar', 'description': 'Yıllara göre dinamik ve aktif sezon yönetimi'},
        {'name': '3. Takım Analizi', 'description': 'Süper Lig kulüpleri, stadyumlar, piyasa değerleri ve kadro listeleri'},
        {'name': '4. Oyuncular & Efsaneler', 'description': 'Aktif ve efsane futbolcular, mevkiler, fotoğraflar ve piyasa değerleri'},
        {'name': '5. Oyuncu Sezon İstatistikleri', 'description': 'Sezon sezon maç, gol, asist, şut, pas isabeti ve reyting verileri'},
        {'name': '6. Transfer Takip', 'description': 'Süper Lig\'e gelenler, gidenler, lig içi transferler ve bonservis bedelleri'},
        {'name': '7. Puan Durumu', 'description': 'Sezonluk lig tablosu, averaj, puan ve sıralamalar'},
        {'name': '8. Maçlar & Fikstür & Canlı Skor (API-Football)', 'description': 'Haftalık fikstür, maç sonuçları ve canlı skorlar'},
        {'name': '9. Lig İstatistikleri & Liderler', 'description': 'Gol krallığı, asist krallığı ve en yüksek reytingli oyuncular'},
        {'name': '10. Oyuncu Karşılaştırma & Algoritmik Analiz', 'description': 'İki oyuncuyu (güncel veya efsane) algoritmik ve radar olarak kıyaslama'},
        {'name': '11. Ana Sayfa Gösterge Paneli', 'description': 'Mobil uygulama ana sayfası özet sayaçları ve lider takım'},
        {'name': '12. Veri Entegrasyonu & Otomasyon', 'description': 'Transfermarkt, SofaScore/WhoScored ve API-Football RapidAPI senkronizasyonu'},
        {'name': '13. Scout / Favoriler', 'description': 'Giriş yapan kullanıcının özel oyuncu takip listesi ve scout notları'}
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
        'docExpansion': 'list',
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
    },
    'COMPONENT_SPLIT_REQUEST': True,
}