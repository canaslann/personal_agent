"""
Hava durumu sorgulama - OpenWeatherMap API (ücretsiz tier).
OPENWEATHER_API_KEY ortam değişkeni gerekli (.env dosyasında).
"""
import os
import requests


def _get_api_key() -> str:
    key = os.environ.get("OPENWEATHER_API_KEY")
    if not key:
        raise ValueError(
            "OPENWEATHER_API_KEY bulunamadı. .env dosyasına ekle."
        )
    return key


def get_weather(city: str) -> str:
    """Belirtilen şehir için güncel hava durumunu getirir."""
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": _get_api_key(),
            "units": "metric",
            "lang": "tr",
        }
        resp = requests.get(url, params=params, timeout=5)

        if resp.status_code == 404:
            return f"'{city}' şehri bulunamadı. Şehir adını kontrol et."
        if resp.status_code == 401:
            return "API key geçersiz. .env dosyasındaki OPENWEATHER_API_KEY'i kontrol et."
        resp.raise_for_status()

        data = resp.json()
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        city_name = data["name"]
        country = data["sys"]["country"]

        return (
            f"{city_name}, {country}\n"
            f"Durum: {desc}\n"
            f"Sıcaklık: {temp}°C (hissedilen: {feels}°C)\n"
            f"Nem: %{humidity}\n"
            f"Rüzgar: {wind} m/s"
        )
    except requests.Timeout:
        return "Hava durumu servisi zaman aşımına uğradı, tekrar dene."
    except Exception as e:
        return f"Hava durumu alınamadı: {e}"


def get_forecast(city: str) -> str:
    """Belirtilen şehir için 3 günlük hava tahminini getirir."""
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": city,
            "appid": _get_api_key(),
            "units": "metric",
            "lang": "tr",
            "cnt": 24,  # 3 günlük (8 ölçüm/gün × 3)
        }
        resp = requests.get(url, params=params, timeout=5)

        if resp.status_code == 404:
            return f"'{city}' şehri bulunamadı."
        resp.raise_for_status()

        data = resp.json()
        city_name = data["city"]["name"]
        country = data["city"]["country"]

        # Günlük özet — her gün için öğlen ölçümünü al
        seen_dates = {}
        for item in data["list"]:
            date = item["dt_txt"].split(" ")[0]
            hour = item["dt_txt"].split(" ")[1]
            if date not in seen_dates and hour == "12:00:00":
                seen_dates[date] = item

        lines = [f"{city_name}, {country} — 3 Günlük Tahmin:"]
        for date, item in list(seen_dates.items())[:3]:
            desc = item["weather"][0]["description"]
            temp_min = item["main"]["temp_min"]
            temp_max = item["main"]["temp_max"]
            lines.append(f"{date}: {desc}, {temp_min}°C - {temp_max}°C")

        return "\n".join(lines)
    except requests.Timeout:
        return "Hava durumu servisi zaman aşımına uğradı."
    except Exception as e:
        return f"Tahmin alınamadı: {e}"