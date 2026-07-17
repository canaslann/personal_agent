# Kişisel Asistan Agent

Ücretsiz, local çalışan, tool-calling kişisel asistan. LangGraph + Groq.

## Mimari

```
Sen -> Agent (Llama 3.3 70B / Groq, ücretsiz) -> Tool seçer
                                                    |
        +----------+----------+----------+----------+----------+----------+
        |          |          |          |          |          |          |
  Takvim (4)  Gmail (5)  Görev (4)  Wikipedia  Hava Durumu (2)  Finans (3)
  create      draft      add        summary    weather        exchange_rate
  list        list       list                  weather_forecast gold_price
  update      delete     complete                              crypto_price
  delete      inbox      delete
              search
```

`agent.py` ReAct-style bir loop: kullanıcı mesajı → LLM tool seçer →
tool çalışır → sonuç LLM'e döner → LLM final cevabı üretir.

## Mevcut Tool'lar (19)

### Google Calendar (4)
- `create_calendar_event` — yeni etkinlik oluşturur
- `list_calendar_events` — yaklaşan 10 etkinliği listeler
- `update_calendar_event` — mevcut etkinliği günceller
- `delete_calendar_event` — etkinliği siler

### Gmail (5)
- `draft_email` — taslak oluşturur (gönderme YOK, OAuth scope seviyesinde garanti)
- `list_drafts` — taslakları listeler
- `delete_draft` — taslağı siler
- `list_inbox` — gelen kutusunu listeler
- `search_emails` — Gmail'de arama yapar

### Yapılacaklar Listesi / SQLite (4)
- `todo_add` — görev ekler
- `todo_list` — görevleri listeler
- `todo_complete` — görevi tamamlandı işaretler
- `todo_delete` — görevi siler

### Hava Durumu / OpenWeatherMap (2)
- `weather` — herhangi bir şehir için güncel hava durumu getirir
- `weather_forecast` — 3 günlük hava tahmini getirir

### Wikipedia (1)
- `fetch_wikipedia_summary` — MediaWiki REST API üzerinden özet getirir (TR + EN)

### Finans / Yahoo Finance (3)
- `get_exchange_rate` — döviz kuru getirir (USD/TRY, EUR/TRY, GBP/TRY vb.)
- `get_gold_price` — gram altın fiyatını TL ve USD cinsinden getirir
- `get_crypto_price` — kripto para fiyatı getirir (BTC, ETH, SOL vb.)

## Google Calendar + Gmail Kurulumu

1. https://console.cloud.google.com → yeni proje oluştur
2. **APIs & Services > Library** → etkinleştir:
   - Google Calendar API
   - Gmail API
3. **APIs & Services > OAuth consent screen**:
   - User type: External
   - Test users kısmına kendi Gmail adresini ekle
4. **APIs & Services > Credentials** → Create Credentials → OAuth client ID
   - Application type: **Desktop app**
   - JSON olarak indir, adını `credentials.json` yap, proje kök dizinine koy

İlk çalıştırmada tarayıcı açılır, Google hesabınla giriş yapıp izin verirsin.
Sonrasında `token.json` oluşur, bir daha login istemez.

> **ÖNEMLİ:** OAuth scope'ları değiştiğinde `token.json` silinmeli ve
> OAuth akışı yeniden çalıştırılmalı, yoksa eski izinler sessizce devam eder.

## Kurulum

```powershell
cd personal-agent
pip install -r requirements.txt
```

## API Key'ler

### Groq (ücretsiz, kredi kartsız)
1. https://console.groq.com → ücretsiz hesap aç
2. API Keys → yeni key oluştur

### OpenWeatherMap (ücretsiz, kredi kartsız)
1. https://openweathermap.org/api → ücretsiz hesap aç
2. API Keys sekmesinden key'ini kopyala

`.env` dosyası oluştur:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxx
OPENWEATHER_API_KEY=xxxxxxxxxxxx
```

> **NOT:** Finans tool'ları (döviz, altın, kripto) Yahoo Finance üzerinden
> çalışır — `yfinance` kütüphanesi, API key gerektirmez.

### Groq Ücretsiz Tier Limitleri (llama-3.3-70b-versatile)
- Dakikada: 30 istek, 6.000 token
- Günlük: 100.000 token
- Sıfırlanma: UTC 00:00 (Türkiye: 03:00)

## Çalıştırma

```powershell
python main.py
```

## Örnek Kullanım

```
Sen: yarın saat 15:00'te proje toplantısı ekle
Asistan: Etkinlik oluşturuldu: 'proje toplantısı' - 2026-07-17 15:00.

Sen: İstanbul'da hava nasıl?
Asistan: İstanbul, TR — parçalı bulutlu, 28°C (hissedilen: 30°C)

Sen: Ankara için 3 günlük hava tahmini ver
Asistan: Ankara, TR — 3 Günlük Tahmin: ...

Sen: Atatürk hakkında bilgi ver
Asistan: **Mustafa Kemal Atatürk** — Türkiye Cumhuriyeti'nin kurucusu...

Sen: matematik ödevini yapılacaklara ekle
Asistan: Görev eklendi: 'matematik ödevini yap'

Sen: ahmet@example.com'a toplantı hatırlatması taslağı hazırla
Asistan: Taslak oluşturuldu: 'Toplantı Hatırlatması' -> ahmet@example.com

Sen: dolar kaç TL?
Asistan: 1 USD = 38.4500 TRY

Sen: 1 gram altın ne kadar?
Asistan: Gram Altın: 4.021,30 TL / 104,52 USD

Sen: bitcoin kaç dolar?
Asistan: BTC = 118,432.50 USD
```

## Memory (RAG) Sistemi

ChromaDB ile local vector store. Her konuşma otomatik kaydedilir,
ilgili geçmiş bilgiler bir sonraki konuşmada prompt'a eklenir.
`memory/chroma_store/` dizininde saklanır (`.gitignore`'da).

## Bilinen Sınırlamalar

- Groq ücretsiz tier günlük 100K token limiti var — limitine ulaşırsan UTC 00:00'da sıfırlanır
- Email gönderme YOK, sadece taslak (OAuth `gmail.compose` scope'u gönderimi API seviyesinde engelliyor)
- Wikipedia, hava durumu ve finans tool'ları ağ bağlantısı gerektirir
- OpenWeatherMap ücretsiz tier: günlük 1.000 istek
- `yfinance` fiyatları Yahoo Finance'ten çeker, anlık borsa fiyatlarında ~15 dk gecikme olabilir

## Planlanan Özellikler

- Gün sonu özeti

## Dosya Yapısı

```
personal-agent/
├── agent.py              # LangGraph agent, ReAct loop
├── main.py               # CLI giriş noktası
├── auth.py               # Google OAuth yönetimi
├── requirements.txt
├── .env                  # (gitignore) API key'ler
├── credentials.json      # (gitignore) Google OAuth client
├── token.json            # (gitignore) OAuth token
├── todo.db               # (gitignore) SQLite görev listesi
├── tools/
│   ├── agent_tools.py    # Tüm tool tanımları + ALL_TOOLS listesi
│   ├── todo.py           # SQLite to-do implementasyonu
│   ├── weather.py        # OpenWeatherMap hava durumu
│   ├── wikipedia_tool.py # Wikipedia MediaWiki REST API tool
│   └── finance_tool.py   # Yahoo Finance döviz/altın/kripto tool'ları
└── memory/
    ├── store.py           # ChromaDB AgentMemory sınıfı
    └── chroma_store/      # (gitignore) Vector store verisi
```