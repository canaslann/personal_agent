"""
Finans tool'ları - Yahoo Finance üzerinden döviz, altın ve kripto fiyatları.
yfinance kütüphanesi kullanır - ücretsiz, API key gerektirmez.
"""
import yfinance as yf
from langchain_core.tools import tool

# 1 troy ons = 31.1035 gram
_TROY_OZ_TO_GRAM = 31.1035


def _fetch_price(ticker: str) -> float | None:
    """Verilen ticker sembolünün güncel fiyatını döner."""
    try:
        return yf.Ticker(ticker).fast_info.last_price
    except Exception:
        return None


@tool
def get_exchange_rate(currency_pair: str = "USD/TRY") -> str:
    """Döviz kuru getirir. Desteklenen çiftler: USD/TRY, EUR/TRY, GBP/TRY, JPY/TRY vb.

    Args:
        currency_pair: Döviz çifti (örn: "USD/TRY", "EUR/TRY", "GBP/TRY")
    """
    # "USD/TRY" -> "USDTRY=X" formatına çevir
    pair = currency_pair.upper().replace("/", "").replace(" ", "")
    if not pair.endswith("=X"):
        ticker = f"{pair}=X"
    else:
        ticker = pair

    price = _fetch_price(ticker)
    if price is None:
        return f"HATA: '{currency_pair}' kuru alınamadı. Döviz çiftini kontrol et (örn: USD/TRY)."

    base = currency_pair.upper().split("/")[0] if "/" in currency_pair else pair[:3]
    quote = currency_pair.upper().split("/")[1] if "/" in currency_pair else pair[3:6]
    return f"1 {base} = {price:.4f} {quote}"


@tool
def get_gold_price() -> str:
    """Güncel gram altın fiyatını Türk Lirası cinsinden getirir.
    Uluslararası altın fiyatı (XAU/USD) ve USD/TRY kuru kullanılarak hesaplanır.
    """
    gold_usd_oz = _fetch_price("GC=F")   # vadeli altın, ons başına USD
    usdtry = _fetch_price("USDTRY=X")    # USD/TRY kuru

    if gold_usd_oz is None:
        return "HATA: Altın fiyatı alınamadı."
    if usdtry is None:
        return "HATA: USD/TRY kuru alınamadı."

    gold_try_gram = (gold_usd_oz / _TROY_OZ_TO_GRAM) * usdtry
    gold_usd_gram = gold_usd_oz / _TROY_OZ_TO_GRAM

    return (
        f"Gram Altın: {gold_try_gram:.2f} TL\n"
        f"Gram Altın: {gold_usd_gram:.2f} USD\n"
        f"Ons Altın:  {gold_usd_oz:.2f} USD\n"
        f"USD/TRY:    {usdtry:.4f}"
    )


@tool
def get_crypto_price(symbol: str = "BTC") -> str:
    """Kripto para biriminin güncel USD fiyatını getirir.

    Args:
        symbol: Kripto sembolü (örn: "BTC", "ETH", "SOL", "DOGE", "BNB")
    """
    ticker = f"{symbol.upper()}-USD"
    price = _fetch_price(ticker)

    if price is None:
        return f"HATA: '{symbol}' fiyatı alınamadı. Sembolü kontrol et (örn: BTC, ETH, SOL)."

    # Küçük değerler için daha fazla ondalık göster
    if price < 0.01:
        formatted = f"{price:.6f}"
    elif price < 1:
        formatted = f"{price:.4f}"
    else:
        formatted = f"{price:,.2f}"

    return f"{symbol.upper()} = {formatted} USD"