# ⚽ Football Match Data API

Bu API, **Nowgoal25.com** futbol sitesinden canlı maç verilerini çekmek ve analiz etmek için geliştirilmiş profesyonel bir sistemdir. Yüksek performans, güvenlik ve ölçeklenebilirlik odaklı tasarlanmıştır.

## 🎯 Proje Amacı

Bu proje, futbol maçlarıyla ilgili kapsamlı verileri toplamak ve kullanıcıların ihtiyaçlarına göre sunmak amacıyla geliştirilmiştir. API aşağıdaki temel işlevleri gerçekleştirir:

- **Maç Detayları**: Belirli bir maçın tüm istatistiklerini çekme
- **Tarih Bazlı Maç Listeleri**: Belirli tarihlerdeki tüm maçları listeleme
- **Oran Verileri**: Bahis oranları, köşe vuruşları, gol sayısı tahminleri
- **Takım Bilgileri**: Lig pozisyonları, oyuncu kadroları, sakatlıklar
- **Canlı Veri Takibi**: Gerçek zamanlı maç skorları ve istatistikleri

## 🛠️ Teknoloji Stack

### Backend Framework
- **Flask** - Python web framework
- **aiohttp** - Asenkron HTTP istemcisi
- **Flask-CORS** - Cross-origin resource sharing
- **Flask-Caching** - Önbellekleme sistemi

### Güvenlik ve Performans
- **JWT (PyJWT)** - JSON Web Token authentication
- **Flask-Limiter** - Rate limiting
- **bcrypt** - Password hashing
- **aiofiles** - Asenkron dosya işlemleri

### Veri İşleme
- **BeautifulSoup4** - HTML parsing
- **lxml** - XML/HTML parser
- **marshmallow** - Veri validasyonu
- **requests** - HTTP istemcisi

### Sistem
- **python-dotenv** - Environment variables
- **asyncio** - Asenkron programlama
- **logging** - Sistem loglaması

## 🚀 Özellikler

### ✅ Temel Özellikler

1. **🔐 Güvenlik Sistemi**
   - JWT token authentication
   - API key authentication
   - Rate limiting (dakika/saat bazlı)
   - Request validation

2. **⚡ Yüksek Performans**
   - Asenkron HTTP istekleri (7 API'yi eş zamanlı)
   - Connection pooling (20 eş zamanlı bağlantı)
   - In-memory cache sistemi (5 dakika TTL)
   - Gzip sıkıştırma

3. **📊 Veri Çekme Kapasitesi**
   - Maç detayları ve istatistikleri
   - Bahis oranları (European, Asian Handicap, Over/Under)
   - Takım pozisyonları ve lig bilgileri
   - Oyuncu kadroları ve sakatlıklar
   - Head-to-head karşılaştırmaları

4. **📈 Monitoring ve Logging**
   - Detaylı performans takibi
   - Request/response loglaması
   - Error tracking
   - Cache istatistikleri

5. **🛡️ Güvenlik Özellikleri**
   - Input validation (Marshmallow)
   - CORS protection
   - Security headers
   - Real IP detection

6. **📅 Tarih Bazlı İşlemler**
   - Belirli tarih için maç listesi
   - Bugünkü maçlar endpoint'i
   - Zaman dilimi desteği

## 📦 Kurulum

```bash
# 1. Depoyu klonla
git clone <repo-url>
cd apiyeni

# 2. Virtual environment oluştur
python3 -m venv instance
source instance/bin/activate

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Environment variables ayarla (opsiyonel)
cp .env.example .env
```

## 🔧 Çevre Değişkenleri (.env)

```bash
# Güvenlik
SECRET_KEY=your-super-secret-key-here
API_SECRET_KEY=your-api-key-here

# Rate Limiting
API_RATE_LIMIT=100 per hour

# CORS
ALLOWED_ORIGINS=*

# Cache
CACHE_DEFAULT_TIMEOUT=300
```

## 🚀 Kullanım

### Sunucuyu Başlat

```bash
source instance/bin/activate
python3 app.py
```

Sunucu `http://localhost:5001` adresinde çalışacak.

## 📚 API Endpoints

### 🏠 Sağlık Kontrolü

```bash
# Basit sağlık kontrolü
GET /health

# Detaylı sistem durumu
GET /health/detailed
```

### ⚽ Maç Detayları

```bash
# Belirli bir maçın detayları
GET /api/v1/match/{match_id}
GET /match/{match_id}  # Geriye uyumluluk

# Örnek
curl "http://localhost:5001/api/v1/match/2789144"
```

### 📅 Tarih Bazlı Maçlar

```bash
# Belirli bir tarihteki tüm maçlar
GET /api/v1/matches/date/{YYYY-MM-DD}

# Bugünkü maçlar
GET /api/v1/matches/today

# Örnekler
curl "http://localhost:5001/api/v1/matches/date/2024-08-24"
curl "http://localhost:5001/api/v1/matches/today"
```

**Response Format:**
```json
{
    "date": "2024-08-24",
    "match_count": 15,
    "matches": [
        {
            "match_id": 2789144,
            "home_team": "Everton",
            "away_team": "Brighton Hove Albion",
            "match_time": "2024-08-24T13:00:00",
            "league": {
                "id": 1,
                "name": "English Premier League",
                "code": "ENG PR"
            }
        }
    ],
    "cached_at": "2024-08-24T14:30:00.123456"
}
```

### 🔍 Debug Endpoints (Development)

```bash
# Tablo yapısı analizi
GET /api/v1/debug/table/{match_id}

# Ham tarih verisi
GET /api/v1/debug/date/{YYYY-MM-DD}
```

### 🔐 Güvenli Endpoints (Authentication Required)

```bash
# JWT ile güvenli maç detayı
GET /api/v1/secure/match/{match_id}

# API Key ile güvenli tarih sorgusu
GET /api/v1/secure/matches/date/{YYYY-MM-DD}

# Admin istatistikleri
GET /api/v1/admin/stats
```

## 🏗️ Sistem Mimarisi

### Veri Akışı

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client        │────│   Flask API      │────│  Nowgoal25.com  │
│                 │    │                  │    │                 │
│ - Web/Mobile    │    │ - Request        │    │ - HTML Pages    │
│ - REST API      │    │   Validation     │    │ - JSON APIs     │
│ - Admin Panel   │    │                  │    │ - Live Data     │
└─────────────────┘    │ - Authentication │    └─────────────────┘
                       │ - Rate Limiting  │
                       │ - Caching        │
                       │ - Data Parsing   │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Response       │
                       │                  │
                       │ - JSON Format    │
                       │ - Error Handling │
                       │ - Cache Headers  │
                       └──────────────────┘
```

### Çekilen Veri Türleri

1. **Maç Bilgileri**
   - Takım isimleri ve logoları
   - Lig bilgileri
   - Stadyum ve hava durumu
   - Maç saati ve durumu

2. **İstatistikler**
   - Puan durumu
   - İlk yarı/ikinci yarı skorları
   - Köşe vuruşları
   - Sarı/kırmızı kartlar

3. **Bahis Oranları**
   - European odds (1X2)
   - Asian Handicap
   - Over/Under (gol sayısı)
   - Double chance
   - Correct score

4. **Takım Verileri**
   - Lig pozisyonları
   - Önceki maç sonuçları
   - Head-to-head karşılaştırmaları
   - Oyuncu kadroları
   - Sakatlık bilgileri

### 🗄️ Cache Yönetimi

```bash
# Cache'i temizle
DELETE /api/v1/cache/clear

# Cache istatistikleri
GET /api/v1/cache/stats
```

## 🔐 Güvenlik

### API Key Authentication (Önerilen)

```bash
# Header ile API key gönder
curl -H "X-API-Key: your-api-key-here" \
     "http://localhost:5001/api/v1/match/2789144"
```

### JWT Token Authentication

```python
import jwt
import requests

# Token oluştur
token = jwt.encode(
    {'user_id': 'user123', 'exp': datetime.utcnow() + timedelta(hours=1)},
    'your-secret-key',
    algorithm='HS256'
)

# İstek gönder
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:5001/api/v1/match/2789144', headers=headers)
```

## 📊 Performans Özellikleri

### ⚡ Hız İyileştirmeleri

- **Asenkron HTTP İstekleri**: 7 API'yi eş zamanlı çağırır
- **Connection Pooling**: 20 eş zamanlı bağlantı
- **In-Memory Cache**: 5 dakika cache süresi
- **Gzip Compression**: Otomatik sıkıştırma

### 📈 Performans Sonuçları

```
ÖNCESİ: 7-14 saniye (sequential)
SONRASI: 
  - İlk istek: ~1.7 saniye
  - Cache'li istek: ~0.01 saniye
  
🚀 170x performans artışı!
```

### 🛡️ Güvenlik Özellikleri

- **Rate Limiting**: Dakika/saat bazlı limit
- **Input Validation**: Marshmallow ile veri doğrulama
- **Error Handling**: Güvenli hata mesajları
- **Request Logging**: Detaylı istek takibi
- **CORS Protection**: Origin kontrolü

## 🧪 Test

```bash
# Unit testleri çalıştır
python3 -m pytest test_app.py -v

# Belirli bir test
python3 -m pytest test_app.py::TestApp::test_health_endpoint -v

# Coverage raporu
python3 -m pytest test_app.py --cov=app --cov-report=html
```

## 📋 API Rate Limits

| Endpoint | Limit | Açıklama |
|----------|-------|----------|
| `/health` | Sınırsız | Sağlık kontrolü |
| `/api/v1/match/*` | 10/dk | Ana maç endpoint'i |
| `/match/*` | 5/dk | Legacy endpoint |
| `/api/v1/matches/date/*` | 20/dk | Tarih bazlı |
| `/api/v1/matches/today` | 30/dk | Bugünkü maçlar |
| `/api/v1/cache/clear` | 1/dk | Cache temizleme |
| **Genel Limit** | **100/saat** | Tüm endpoint'ler |

## 🔍 Monitoring

### Log Takibi

```bash
# Real-time log takibi
tail -f app.log

# Error'ları filtrele
grep "ERROR" app.log

# Performans analizi
grep "completed.*in.*s" app.log
```

### Cache İstatistikleri

```bash
# Cache durumu
curl "http://localhost:5001/api/v1/cache/stats"

# Cache'i temizle
curl -X DELETE "http://localhost:5001/api/v1/cache/clear"
```

## 🚦 Kullanım Örnekleri

### Python ile Kullanım

```python
import requests
import json

# 1. Bugünkü maçları çek
response = requests.get('http://localhost:5001/api/v1/matches/today')
matches = response.json()

print(f"Bugün {matches['match_count']} maç var:")
for match in matches['matches']:
    print(f"⚽ {match['home_team']} vs {match['away_team']}")
    print(f"   🏆 {match['league']['name']}")
    print(f"   ⏰ {match['match_time']}")
    print()

# 2. Belirli bir maçın detaylarını çek
match_id = 2789144
match_response = requests.get(f'http://localhost:5001/api/v1/match/{match_id}')
match_data = match_response.json()

print("Maç Detayları:")
print(f"Takımlar: {match_data.get('match_info', {}).get('home_team_name', '')} vs {match_data.get('match_info', {}).get('away_team_name', '')}")
print(f"Lig: {match_data.get('match_info', {}).get('league', '')}")
print(f"Stadyum: {match_data.get('match_info', {}).get('stadium', '')}")
```

### JavaScript ile Kullanım

```javascript
// Fetch API ile
async function getTodaysMatches() {
    try {
        const response = await fetch('/api/v1/matches/today');
        const data = await response.json();

        console.log(`Bugün ${data.match_count} maç var:`);
        data.matches.forEach(match => {
            console.log(`⚽ ${match.home_team} vs ${match.away_team}`);
            console.log(`🏆 ${match.league.name}`);
        });
    } catch (error) {
        console.error('Maç verileri alınamadı:', error);
    }
}

// Belirli maç detaylarını çek
async function getMatchDetails(matchId) {
    try {
        const response = await fetch(`/api/v1/match/${matchId}`);
        const data = await response.json();

        if (data.match_info) {
            console.log("Maç Bilgileri:");
            console.log(`Takımlar: ${data.match_info.home_team_name} vs ${data.match_info.away_team_name}`);
            console.log(`Skor: ${data.match_info.score_info.home_score} - ${data.match_info.score_info.away_score}`);
            console.log(`Durum: ${data.match_info.score_info.status}`);
        }
    } catch (error) {
        console.error('Maç detayları alınamadı:', error);
    }
}

getTodaysMatches();
getMatchDetails(2789144);
```

### cURL Örnekleri

```bash
# Bugünkü Premier League maçları
curl -s "http://localhost:5001/api/v1/matches/today" | \
jq '.matches[] | select(.league.code == "ENG PR")'

# Belirli tarihteki maç sayısı
curl -s "http://localhost:5001/api/v1/matches/date/2025-07-24" | \
jq '.match_count'

# Sağlık kontrolü
curl -s "http://localhost:5001/health" | jq '.'
```

## 🛠️ Geliştirme

### Yeni Endpoint Ekleme

```python
@app.route('/api/v1/new-endpoint')
@limiter.limit("20 per minute")
@log_requests
@validate_json
def new_endpoint():
    """Yeni endpoint örneği"""
    try:
        # İş mantığı
        result = {"status": "success"}
        return jsonify(result)
    except Exception as e:
        logger.error(f"New endpoint error: {e}")
        raise APIError("Internal error", 500)
```

### Cache Stratejisi

```python
# Önbellek anahtarı oluştur
cache_key = f"endpoint_{param1}_{param2}"

# Cache kontrolü
cached_data = cache.get(cache_key)
if cached_data:
    return jsonify(cached_data)

# Veri işle
result = process_data()

# Cache'e kaydet (1 saat)
cache.set(cache_key, result, timeout=3600)
```

## 📈 Production Deployment

### Environment Setup

```bash
# Production ortamı
export FLASK_ENV=production
export SECRET_KEY=production-secret-key
export API_RATE_LIMIT=1000 per hour
```

### Nginx Configuration

```nginx
upstream football_api {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://football_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Docker Support

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
```

## 🤝 Katkıda Bulunma

1. Fork'layın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit'leyin (`git commit -m 'Add some amazing feature'`)
4. Push'layın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🔗 Faydalı Linkler

- [API Güvenlik Rehberi](./API_GUVENLIK_REHBERI.md)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [Flask-Caching](https://flask-caching.readthedocs.io/)

## 📁 Proje Dosyaları

### Ana Dosyalar

| Dosya | Açıklama |
|-------|----------|
| **`app.py`** | Ana Flask uygulaması - tüm endpoint'ler ve iş mantığı |
| **`config.py`** | Uygulama yapılandırması (güvenlik, cache, rate limiting) |
| **`models.py`** | Veri modelleri, validation şemaları ve özel exception'lar |
| **`parsers.py`** | HTML/JSON parsing fonksiyonları - veri çekme işlemleri |
| **`security.py`** | Güvenlik modülleri (JWT, API key, rate limiting) |
| **`http_client.py`** | HTTP istemcisi - asenkron veri çekme işlemleri |

### Sistem Dosyaları

| Dosya | Açıklama |
|-------|----------|
| **`requirements.txt`** | Python bağımlılıkları |
| **`README.md`** | Bu dokümantasyon dosyası |
| **`app.log`** | Uygulama logları |
| **`.env`** | Environment variables (gizli anahtarlar) |
| **`instance/`** | Python virtual environment |

### Veri Akışı

1. **Client Request** → `app.py` (Flask routes)
2. **Authentication** → `security.py` (JWT/API Key validation)
3. **Rate Limiting** → `flask_limiter` (Request throttling)
4. **Cache Check** → `flask_caching` (Önbellek kontrolü)
5. **Data Fetching** → `http_client.py` (Nowgoal25.com'dan veri çekme)
6. **Data Parsing** → `parsers.py` (HTML/JSON parsing)
7. **Response Building** → `models.py` (JSON response format)
8. **Logging** → `app.log` (İstek/yanıt loglaması)

### Önemli Noktalar

- **Asenkron İşlemler**: `http_client.py` ve `asyncio` kullanarak yüksek performans
- **Güvenlik**: Çok katmanlı güvenlik sistemi (JWT, API Key, Rate Limiting)
- **Önbellekleme**: 5 dakikalık TTL ile in-memory cache
- **Error Handling**: Kapsamlı hata yakalama ve logging
- **Data Validation**: Marshmallow ile input validation
- **CORS Support**: Cross-origin resource sharing desteği

## 🔧 Yapılandırma Parametreleri

### Environment Variables (.env)

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-production-secret-key

# Security
API_SECRET_KEY=your-api-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Rate Limiting
API_RATE_LIMIT=1000 per hour
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Cache
CACHE_TYPE=filesystem
CACHE_DIR=/tmp/flask_cache
CACHE_DEFAULT_TIMEOUT=300

# API
API_VERSION=1.0.0
MAX_CONNECTIONS=20
CONNECTION_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
```

### Production Deployment Checklist

- [ ] Environment variables ayarlandı
- [ ] SECRET_KEY değiştirildi
- [ ] API_SECRET_KEY ayarlandı
- [ ] CORS origins yapılandırıldı
- [ ] Rate limiting limitleri ayarlandı
- [ ] Logging seviyesi ayarlandı
- [ ] HTTPS etkinleştirildi
- [ ] Database backup aktif
- [ ] Monitoring araçları kuruldu

---

🎉 **API'niz artık production-ready!** Herhangi bir sorunla karşılaştığınızda loglara bakın ve health endpoint'lerini kontrol edin.

**Geliştirici**: Bu API, futbol verilerini gerçek zamanlı olarak çekmek ve analiz etmek için profesyonel bir çözümdür. Herhangi bir sorun veya iyileştirme önerisi için lütfen issue açın.