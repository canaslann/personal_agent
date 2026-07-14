# Kişisel Asistan Agent

Ücretsiz, local çalışan, tool-calling kişisel asistan. LangGraph + Groq.

## Mimari

```
Sen -> Agent (Llama 3.3 70B / Groq, ücretsiz) -> Tool seçer
                                                    |
                                    +---------------+---------------+
                                    |               |                |
                              create_calendar_  draft_email      list_*
                                  event
                                    |               |
                              (şu an mock)     (şu an mock, hiç
                                                 gerçek mail gitmez)
```

`agent.py` ReAct-style bir loop: kullanıcı mesajı -> LLM tool seçer ->
tool çalışır -> sonuç LLM'e döner -> LLM final cevabı üretir.

## Google Calendar + Gmail kurulumu (GERÇEK API, mock değil artık)

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
   (Bu dosya `.gitignore`'da, asla GitHub'a gitmeyecek - kişisel anahtarın.)

İlk `python main.py` çalıştırmasında ve bir calendar/email tool'u
tetiklendiğinde tarayıcı otomatik açılır, Google hesabınla giriş
yapıp izin verirsin. Sonrasında `token.json` oluşur, bir daha login
istemez (token süresi dolunca otomatik yenilenir).

## Kurulum (senin bilgisayarında, Windows/PowerShell)

```powershell
cd personal-agent
pip install -r requirements.txt


## Groq API key alma (ücretsiz, kredi kartsız)

1. https://console.groq.com adresine git, ücretsiz hesap aç
2. API Keys bölümünden yeni key oluştur
3. PowerShell'de ortam değişkeni olarak ayarla:

```powershell
$env:GROQ_API_KEY = "gsk_xxxxxxxxxxxx"
```

(Kalıcı olması için sistem ortam değişkenlerine de ekleyebilirsin.)

## Çalıştırma

```powershell
python main.py
```

Örnek kullanım:
```
Sen: yarın saat 15:00'te proje toplantısı ekle
Asistan: Etkinlik oluşturuldu: 'proje toplantısı' - 2026-06-29 15:00. ID: 1

Sen: ahmet@example.com'a toplantı hatırlatması maili taslağı hazırla
Asistan: Taslak oluşturuldu (ID: 1): 'Toplantı Hatırlatması' -> ahmet@example.com
```

## Artık gerçek API'ye bağlı (mock kaldırıldı)

`tools/agent_tools.py` artık gerçek Google Calendar ve Gmail API'sini
çağırıyor. `auth.py` OAuth kimlik doğrulamayı yönetiyor (token.json'da
saklanır, otomatik yenilenir).

- Calendar: gerçekten Google Calendar'ına etkinlik ekler/listeler
- Gmail: gerçekten Gmail taslak klasörüne taslak ekler/listeler -
  **gönderme YOK**. Bu sadece bir tercih değil, OAuth scope'u
  (`gmail.compose`) zaten API seviyesinde göndermeye izin vermiyor.

Bir sonraki adım: memory (RAG) sistemini `agent.py`'a bağlamak,
böylece asistan geçmiş konuşmaları hatırlayabilsin.

## Memory (RAG/hafıza) sistemi

`memory/store.py` ChromaDB ile local vector store kuruyor. İlk
çalıştırmada embedding modelini internetten indirir (~30MB, tek seferlik,
ücretsiz). Henüz `agent.py` içine bağlanmadı - bu bir sonraki adım:
her konuşmadan önemli bilgileri `remember()` ile kaydetmek, ilgili
geçmişi `recall()` ile agent'ın prompt'una eklemek.

## Bilinen sınırlamalar

- Groq ücretsiz tier'ında rate limit var (dakikalık istek sınırı) -
  çok hızlı art arda istek atarsan kısa süreli hata alabilirsin.
- Email gönderme YOK, sadece taslak. Gerçek gönderim için Gmail API
  `send` scope'u ve ek bir onay adımı gerekir (bilinçli olarak koymadım,
  yanlışlıkla mail gitmesin diye).
