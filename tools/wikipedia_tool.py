"""
Wikipedia özet tool'u - MediaWiki REST API, ücretsiz, API key gerektirmiyor.
'wikipedia' kütüphanesi Python 3.12+ ile uyumsuz olduğundan requests kullanıyoruz.
"""
import requests
from langchain_core.tools import tool


def _search_wikipedia(query: str, lang: str = "en") -> list[str]:
    """Wikipedia'da arama yapar, sayfa başlıklarını döner."""
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 5,
        "format": "json",
    }
    resp = requests.get(url, params=params, timeout=8, headers={"User-Agent": "PersonalAgent/1.0"})
    resp.raise_for_status()
    results = resp.json()
    return results[1] if len(results) > 1 else []


def _get_summary(title: str, lang: str = "en", sentences: int = 5) -> dict | None:
    """Wikipedia REST API ile sayfa özeti getirir."""
    encoded_title = title.replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
    resp = requests.get(url, timeout=8, headers={"User-Agent": "PersonalAgent/1.0"})
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


@tool
def fetch_wikipedia_summary(topic: str, sentences: str = "5") -> str:
    """Wikipedia'dan bir konu hakkında özet bilgi getirir.

    Args:
        topic: Aranacak konu (örn: "Albert Einstein", "Python programlama dili", "İstanbul")
        sentences: Kaç cümle özet getirileceği (varsayılan 5, max 10, REST API'de yaklaşık)
    """
    try:
        # Önce İngilizce dene
        titles = _search_wikipedia(topic, lang="en")
        
        if titles:
            data = _get_summary(titles[0], lang="en")
            if data:
                extract = data.get("extract", "")
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                page_title = data.get("title", titles[0])
                return f"**{page_title}**\n\n{extract}\n\nKaynak: {page_url}"

        # İngilizce bulunamazsa Türkçe dene
        titles_tr = _search_wikipedia(topic, lang="tr")
        if titles_tr:
            data = _get_summary(titles_tr[0], lang="tr")
            if data:
                extract = data.get("extract", "")
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                page_title = data.get("title", titles_tr[0])
                return f"**{page_title}**\n\n{extract}\n\nKaynak: {page_url}"

        return f"'{topic}' için Wikipedia'da sayfa bulunamadı. Farklı bir terim dene."

    except requests.Timeout:
        return "Wikipedia'ya ulaşılamadı: zaman aşımı."
    except Exception as e:
        return f"Wikipedia'ya ulaşılamadı: {e}"