"""
Wikipedia özet tool'u - ücretsiz, API key gerektirmiyor.
'wikipedia' kütüphanesi kullanır (MediaWiki API üzerinden).
"""
from langchain_core.tools import tool


@tool
def fetch_wikipedia_summary(topic: str, sentences: str = "5") -> str:
    """Wikipedia'dan bir konu hakkında özet bilgi getirir.

    Args:
        topic: Aranacak konu (örn: "Albert Einstein", "Python programlama dili", "İstanbul")
        sentences: Kaç cümle özet getirileceği (varsayılan 5, max 10)
    """
    try:
        import wikipedia
    except ImportError:
        return "wikipedia kütüphanesi yüklü değil. 'pip install wikipedia' ile yükle."

    # Türkçe arama için dil ayarı - konuya göre otomatik
    # Önce İngilizce dene, Türkçe sonuç için kullanıcı "Türkçe" diyebilir
    n = min(int(sentences), 10)

    try:
        # Önce tam eşleşme dene
        summary = wikipedia.summary(topic, sentences=n, auto_suggest=True)
        page = wikipedia.page(topic, auto_suggest=True)
        return f"**{page.title}**\n\n{summary}\n\nKaynak: {page.url}"

    except wikipedia.exceptions.DisambiguationError as e:
        # Belirsizlik durumu - seçenekleri sun
        options = e.options[:5]
        options_str = "\n".join(f"  - {opt}" for opt in options)
        return (
            f"'{topic}' için birden fazla sonuç var. Daha spesifik bir terim dene:\n"
            f"{options_str}"
        )

    except wikipedia.exceptions.PageError:
        # Sayfa bulunamadı - Türkçe dene
        try:
            wikipedia.set_lang("tr")
            summary = wikipedia.summary(topic, sentences=n, auto_suggest=True)
            page = wikipedia.page(topic, auto_suggest=True)
            wikipedia.set_lang("en")  # reset
            return f"**{page.title}**\n\n{summary}\n\nKaynak: {page.url}"
        except Exception:
            wikipedia.set_lang("en")  # reset
            return f"'{topic}' için Wikipedia'da sayfa bulunamadı. Farklı bir terim dene."

    except Exception as e:
        return f"Wikipedia'ya ulaşılamadı: {e}"