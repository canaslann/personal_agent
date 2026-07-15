# Kişisel Asistan Agent

Ücretsiz, local çalışan, tool-calling kişisel asistan.
LangGraph + Groq + Google Calendar/Gmail + RAG memory.

## Özellikler

- **Google Calendar** — etkinlik oluştur, listele, güncelle, sil
- **Gmail** — taslak oluştur, listele, sil, gelen kutusu oku, arama yap
- **To-do listesi** — görev ekle, listele, tamamla, sil (SQLite, kalıcı)
- **Hava durumu** — güncel durum ve 3 günlük tahmin (OpenWeatherMap)
- **RAG memory** — geçmiş konuşmaları hatırlar (ChromaDB, session'lar arası)
- **Doğal dil tarih/saat** — "yarın saat 3", "gelecek pazartesi" gibi ifadeleri anlar

## Mimari

```
Kullanıcı
    ↓
Agent (LangGraph — ReAct loop)
    ↓
LLM (Llama 3.3 70B / Groq, ücretsiz)
    ↓ tool seçer
┌───────────────────────────────────────────┐
│  Calendar  │  Gmail  │  Todo  │  Weather  │
│  (Google   │ (Google │(SQLite)│  (OWM     │
│   API)     │  API)   │        │   API)    │
└───────────────────────────────────────────┘
    ↓
RAG Memory (ChromaDB — geçmiş konuşmalar)
```

## Kurulum

### 1. Repoyu klonla

```powershell
git clone https://github.com/kullanici/personal-agent.git
cd personal-agent
```

### 2. Bağımlılıkları kur

```powershell
pip install -r requirements.txt
```

### 3. API key'leri ayarla

Proje kök dizininde `.env` dosyası oluştur:

```
GROQ_API_KEY=gsk_xxxxxxxxxxxx
OPENWEATHER_API_KEY=xxxxxxxxxxxx
```

**Groq API key** (ücretsiz, kredi kartsız):
1. https://console.groq.com → ücretsiz hesap aç
2. API Keys → yeni key oluştur

**OpenWeatherMap API key** (ücretsiz, kredi kartsız):
1. https://openweathermap.org/api → ücretsiz hesap aç
2. API Keys sekmesinden key'ini kopyala

### 4. Google Calendar + Gmail kurulumu

1. https://console.cloud.google.com → yeni proje oluştur
2. **APIs & Services > Library** → şunları etkinleştir:
   - Google Calendar API
   - Gmail API
3. **APIs & Services > OAuth consent screen**:
   - User type: External
   - Test users kısmına kendi Gmail adresini ekle
4. **APIs & Services > Credentials** → Create Credentials → OAuth client ID
   - Application type: **Desktop app**
   - JSON olarak indir, adını `credentials.json` yap, proje kök dizinine koy

İlk çalıştırmada tarayıcı otomatik açılır, Google hesabınla giriş yapıp
izin verirsin. Sonrasında `token.json` oluşur, bir daha login istemez.

### 5. Çalıştır

```powershell
python main.py
```

## Kullanım Örnekleri

```
Sen: yarın saat 15'te proje toplantısı ekle
Asistan: Etkinlik oluşturuldu: 'proje toplantısı' - 2026-07-04 15:00

Sen: gelen kutumda ne var?
Asistan: [Son 10 email listelenir]

Sen: yapılacaklara raporu bitir ekle
Asistan: Görev eklendi: 'raporu bitir'

Sen: görev listemi göster
Asistan: [1] ○ raporu bitir  (ID:1)

Sen: İstanbul'da hava nasıl?
Asistan: İstanbul, TR
         Durum: parçalı bulutlu
         Sıcaklık: 28°C (hissedilen: 30°C)
         Nem: %65

Sen: ahmet@gmail.com'a toplantı hatırlatması maili taslağı hazırla
Asistan: Taslak oluşturuldu: 'Toplantı Hatırlatması' -> ahmet@gmail.com
```

## Tool Listesi (13 tool)

| Tool | Açıklama |
|------|----------|
| `create_calendar_event` | Takvime etkinlik ekle |
| `list_calendar_events` | Yaklaşan etkinlikleri listele |
| `update_calendar_event` | Etkinlik güncelle |
| `delete_calendar_event` | Etkinlik sil |
| `draft_email` | Gmail taslağı oluştur |
| `list_drafts` | Taslakları listele |
| `delete_draft` | Taslak sil |
| `list_inbox` | Gelen kutusu listele |
| `search_emails` | Gmail'de arama yap |
| `todo_add` | Görev ekle |
| `todo_list` | Görev listesi |
| `todo_complete` | Görevi tamamla |
| `todo_delete` | Görev sil |
| `weather` | Güncel hava durumu |
| `weather_forecast` | 3 günlük hava tahmini |

## Proje Yapısı

```
personal-agent/
├── main.py              # CLI — giriş noktası
├── agent.py             # LangGraph graph, ReAct loop
├── auth.py              # Google OAuth 2.0
├── requirements.txt
├── .env                 # API key'ler (repoya gitmiyor)
├── credentials.json     # Google OAuth client (repoya gitmiyor)
├── token.json           # Google OAuth token (repoya gitmiyor)
├── todo.db              # SQLite veritabanı (repoya gitmiyor)
├── tools/
│   ├── agent_tools.py   # Tüm tool tanımları
│   ├── todo.py          # To-do SQLite yönetimi
│   └── weather.py       # Hava durumu API
└── memory/
    ├── store.py         # ChromaDB RAG memory
    └── chroma_store/    # Vector DB dosyaları (repoya gitmiyor)
```

## Teknik Detaylar

- **LLM:** Llama 3.3 70B (Groq ücretsiz tier — dakikalık/günlük token limiti var)
- **Agent framework:** LangGraph (ReAct-style tool-calling loop)
- **Memory:** ChromaDB embedded (local, sunucu gerektirmez)
- **Calendar/Gmail:** Google API v3, OAuth 2.0 (gmail.compose + gmail.readonly scope)
- **Email:** Sadece taslak oluşturma — gönderme YOK (OAuth scope seviyesinde garanti)

## Bilinen Sınırlamalar

- Groq ücretsiz tier: günlük 100k token limiti — yoğun kullanımda limit aşılabilir
- Email gönderme yok, sadece taslak (bilinçli tasarım kararı)
- Hava durumu: OpenWeatherMap ücretsiz tier günlük 1000 istek