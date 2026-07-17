"""
Kişisel asistan için tool tanımları - GERÇEK Google Calendar + Gmail API.

Tool isimleri ve imzaları (girdi/çıktı) önceki mock versiyonla aynı,
bu yüzden agent.py'da hiçbir değişiklik gerekmedi.

ÖNEMLİ: Gmail tool'u sadece TASLAK oluşturur. OAuth scope'u
('gmail.compose') zaten teknik olarak gönderim yapmaya izin vermiyor -
yani bu sadece bir tasarım kararı değil, API seviyesinde garanti.
"""
import base64
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from langchain_core.tools import tool
from auth import get_calendar_service, get_gmail_service
from tools.weather import get_weather as _get_weather, get_forecast as _get_forecast
from tools.wikipedia_tool import fetch_wikipedia_summary
from tools.finance_tool import get_exchange_rate, get_gold_price, get_crypto_price

@tool
def create_calendar_event(title: str, date: str, time: str, participants: str = "") -> str:
    """Google Calendar'a yeni bir etkinlik ekler.

    Args:
        title: Etkinlik başlığı (örn: "Proje toplantısı")
        date: Tarih, YYYY-MM-DD formatında (örn: "2026-06-29")
        time: Saat, HH:MM formatında, 24 saat formatı (örn: "15:00")
        participants: Virgülle ayrılmış katılımcı email adresleri (opsiyonel)
    """
    service = get_calendar_service()

    start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(hours=1)  # varsayılan 1 saatlik etkinlik

    event_body = {
        "summary": title,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Europe/Istanbul"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Europe/Istanbul"},
    }

    if participants.strip():
        emails = [e.strip() for e in participants.split(",") if e.strip()]
        event_body["attendees"] = [{"email": e} for e in emails]

    try:
        created = service.events().insert(calendarId="primary", body=event_body).execute()
        return f"Etkinlik oluşturuldu: '{title}' - {date} {time}. Link: {created.get('htmlLink')}"
    except Exception as e:
        return f"Etkinlik oluşturulamadı: {e}"


@tool
def list_calendar_events() -> str:
    """Google Calendar'daki yaklaşan etkinlikleri listeler (önümüzdeki 10 etkinlik)."""
    service = get_calendar_service()
    now = datetime.now(timezone.utc).isoformat()

    try:
        result = (
            service.events()
            .list(calendarId="primary", timeMin=now, maxResults=10, singleEvents=True, orderBy="startTime")
            .execute()
        )
        events = result.get("items", [])
        if not events:
            return "Yaklaşan etkinlik yok."

        lines = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            lines.append(f"- [{e['id']}] {e.get('summary', '(başlıksız)')} | {start}")
        return "\n".join(lines)
    except Exception as e:
        return f"Etkinlikler alınamadı: {e}"


@tool
def update_calendar_event(event_id: str, title: str = "", date: str = "", time: str = "") -> str:
    """Mevcut bir Google Calendar etkinliğini günceller. Sadece değiştirmek
    istediğin alanları doldur, diğerlerini boş bırak (değişmez).

    Args:
        event_id: Güncellenecek etkinliğin ID'si (list_calendar_events ile görebilirsin)
        title: Yeni başlık (opsiyonel, boş bırakılırsa değişmez)
        date: Yeni tarih, YYYY-MM-DD (opsiyonel)
        time: Yeni saat, HH:MM (opsiyonel, date ile birlikte verilmeli)
    """
    service = get_calendar_service()

    try:
        existing = service.events().get(calendarId="primary", eventId=event_id).execute()

        if title:
            existing["summary"] = title

        if date and time:
            if "dateTime" not in existing.get("start", {}):
                return (
                    "Bu tüm-gün bir etkinlik, saat bilgisi içermiyor. "
                    "Sadece saatli (dateTime) etkinlikler için saat güncellemesi yapılabiliyor."
                )
            start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            old_start = datetime.fromisoformat(existing["start"]["dateTime"])
            old_end = datetime.fromisoformat(existing["end"]["dateTime"])
            duration = old_end - old_start
            end_dt = start_dt + duration

            existing["start"]["dateTime"] = start_dt.isoformat()
            existing["end"]["dateTime"] = end_dt.isoformat()

        updated = (
            service.events()
            .update(calendarId="primary", eventId=event_id, body=existing)
            .execute()
        )
        return f"Etkinlik güncellendi: '{updated.get('summary')}'. Link: {updated.get('htmlLink')}"
    except Exception as e:
        return f"Etkinlik güncellenemedi: {e}"


@tool
def delete_calendar_event(event_id: str) -> str:
    """Belirtilen ID'ye sahip Google Calendar etkinliğini siler.

    Args:
        event_id: Silinecek etkinliğin ID'si (list_calendar_events ile görebilirsin)
    """
    service = get_calendar_service()

    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return f"Etkinlik silindi (ID: {event_id})."
    except Exception as e:
        return f"Etkinlik silinemedi: {e}"


@tool
def draft_email(to: str, subject: str, body: str) -> str:
    """Gmail'de email taslağı oluşturur (DİKKAT: gerçekten göndermez, sadece taslak).

    Args:
        to: Alıcı email adresi (virgülle ayrılmış birden fazla olabilir)
        subject: Email konusu
        body: Email içeriği
    """
    service = get_gmail_service()

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )
        return f"Taslak oluşturuldu (Gmail ID: {draft['id']}): '{subject}' -> {to}. Gmail > Taslaklar'dan görebilirsin."
    except Exception as e:
        return f"Taslak oluşturulamadı: {e}"


@tool
def list_drafts() -> str:
    """Gmail'deki tüm email taslaklarını listeler."""
    service = get_gmail_service()

    try:
        result = service.users().drafts().list(userId="me").execute()
        drafts = result.get("drafts", [])
        if not drafts:
            return "Hiç taslak yok."

        lines = []
        for d in drafts:
            detail = service.users().drafts().get(userId="me", id=d["id"], format="metadata").execute()
            headers = detail["message"]["payload"].get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(konusuz)")
            lines.append(f"- [{d['id']}] {subject}")
        return "\n".join(lines)
    except Exception as e:
        return f"Taslaklar alınamadı: {e}"


@tool
def delete_draft(draft_id: str) -> str:
    """Belirtilen ID'ye sahip Gmail taslağını siler.

    Args:
        draft_id: Silinecek taslağın ID'si (list_drafts ile görebilirsin)
    """
    service = get_gmail_service()

    try:
        service.users().drafts().delete(userId="me", id=draft_id).execute()
        return f"Taslak silindi (ID: {draft_id})."
    except Exception as e:
        return f"Taslak silinemedi: {e}"


@tool
def list_inbox(max_results: int = 10) -> str:
    """Gelen kutusundaki son emaillerin özetini listeler (gönderen, konu, tarih).

    Args:
        max_results: Kaç email gösterileceği (varsayılan 10, max 20)
    """
    service = get_gmail_service()
    max_results = min(max_results, 20)

    try:
        result = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
            .execute()
        )
        messages = result.get("messages", [])
        if not messages:
            return "Gelen kutusunda email yok."

        lines = []
        for msg in messages:
            detail = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="metadata",
                     metadataHeaders=["From", "Subject", "Date"])
                .execute()
            )
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            snippet = detail.get("snippet", "")[:80]
            lines.append(
                f"- [{msg['id']}] Kimden: {headers.get('From', '?')} | "
                f"Konu: {headers.get('Subject', '(konusuz)')} | "
                f"Tarih: {headers.get('Date', '?')}\n  Önizleme: {snippet}..."
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Gelen kutusu alınamadı: {e}"


@tool
def search_emails(query: str, max_results: int = 5) -> str:
    """Gmail'de email arar. Kişi, konu, içerik veya tarih bazlı arama yapılabilir.

    Args:
        query: Gmail arama sorgusu. Örnekler:
               'from:ahmet@gmail.com' - kişiden gelenler
               'subject:toplantı' - konuda geçenler
               'is:unread' - okunmamışlar
               'after:2026/06/01' - tarihten sonrakiler
               'ahmet toplantı' - serbest metin araması
        max_results: Kaç sonuç gösterileceği (varsayılan 5, max 10)
    """
    service = get_gmail_service()
    max_results = min(max_results, 10)

    try:
        result = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = result.get("messages", [])
        if not messages:
            return f"'{query}' için sonuç bulunamadı."

        lines = []
        for msg in messages:
            detail = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="metadata",
                     metadataHeaders=["From", "Subject", "Date"])
                .execute()
            )
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            snippet = detail.get("snippet", "")[:100]
            lines.append(
                f"- [{msg['id']}] Kimden: {headers.get('From', '?')} | "
                f"Konu: {headers.get('Subject', '(konusuz)')} | "
                f"Tarih: {headers.get('Date', '?')}\n  Önizleme: {snippet}..."
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Arama yapılamadı: {e}"


from tools.todo import (
    add_task as _add_task,
    list_tasks as _list_tasks,
    complete_task as _complete_task,
    delete_task as _delete_task,
)


@tool
def todo_add(task: str) -> str:
    """Yapılacaklar listesine yeni bir görev ekler.

    Args:
        task: Görev açıklaması (örn: "matematik ödevini bitir")
    """
    return _add_task(task)


@tool
def todo_list(show_done: str = "false") -> str:
    """Yapılacaklar listesini gösterir.

    Args:
        show_done: 'true' ise tamamlananlar da gösterilir, 'false' ise sadece bekleyenler (varsayılan)
    """
    return _list_tasks(show_done=show_done.lower() == "true")


@tool
def todo_complete(task_id: str) -> str:
    """Bir görevi tamamlandı olarak işaretler.

    Args:
        task_id: Tamamlanacak görevin ID'si (todo_list ile görebilirsin)
    """
    return _complete_task(int(task_id))


@tool
def todo_delete(task_id: str) -> str:
    """Yapılacaklar listesinden bir görevi siler.

    Args:
        task_id: Silinecek görevin ID'si (todo_list ile görebilirsin)
    """
    return _delete_task(int(task_id))

@tool
def weather(city: str) -> str:
    """Belirtilen şehir için güncel hava durumunu getirir.

    Args:
        city: Şehir adı (örn: "Istanbul", "Ankara", "London")
    """
    return _get_weather(city)


@tool
def weather_forecast(city: str) -> str:
    """Belirtilen şehir için 3 günlük hava tahminini getirir.

    Args:
        city: Şehir adı (örn: "Istanbul", "Ankara", "London")
    """
    return _get_forecast(city)


ALL_TOOLS = [
    create_calendar_event,
    list_calendar_events,
    update_calendar_event,
    delete_calendar_event,
    draft_email,
    list_drafts,
    delete_draft,
    list_inbox,
    search_emails,
    todo_add,
    todo_list,
    todo_complete,
    todo_delete,
    weather,
    weather_forecast,
    fetch_wikipedia_summary,
    get_exchange_rate,
    get_gold_price,
    get_crypto_price
]