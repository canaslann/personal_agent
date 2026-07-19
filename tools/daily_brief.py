"""
Günlük özet tool'u - takvim etkinlikleri + bekleyen görevler.
Kullanıcı "günlük özetimi göster", "bugünkü planım nedir" gibi bir şey
söylediğinde agent bu tool'u çağırır.
"""
from datetime import datetime, timezone, timedelta
from langchain_core.tools import tool
from auth import get_calendar_service
from tools.todo import list_tasks as _list_tasks

ISTANBUL = timezone(timedelta(hours=3))


def _get_todays_events() -> list[str]:
    """Bugüne ait takvim etkinliklerini getirir."""
    service = get_calendar_service()

    now = datetime.now(ISTANBUL)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end   = now.replace(hour=23, minute=59, second=59, microsecond=0)

    try:
        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=day_start.isoformat(),
                timeMax=day_end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = result.get("items", [])
        lines = []
        for e in events:
            start_raw = e["start"].get("dateTime", e["start"].get("date"))
            # dateTime → saat göster, date (tüm gün) → "Tüm gün"
            if "T" in start_raw:
                dt = datetime.fromisoformat(start_raw)
                time_str = dt.strftime("%H:%M")
            else:
                time_str = "Tüm gün"
            lines.append(f"  • {time_str} — {e.get('summary', '(başlıksız)')}")
        return lines
    except Exception as e:
        return [f"  (Takvim alınamadı: {e})"]


@tool
def daily_brief() -> str:
    """Günün planını özetler: bugünkü takvim etkinlikleri ve bekleyen görevler.
    Kullanıcı 'günlük özet', 'bugünkü planım', 'güne başla' gibi bir şey
    söylediğinde bu tool çağrılmalıdır.
    """
    now = datetime.now(ISTANBUL)
    date_str = now.strftime("%d %B %Y, %A")

    # Takvim
    events = _get_todays_events()
    if events:
        calendar_section = "📅 Bugünkü Etkinlikler:\n" + "\n".join(events)
    else:
        calendar_section = "📅 Bugün için takvimde etkinlik yok."

    # Görevler
    tasks_raw = _list_tasks(show_done=False)
    if tasks_raw.strip() == "Görev listesi boş.":
        tasks_section = "✅ Bekleyen görev yok."
    else:
        tasks_section = "📋 Bekleyen Görevler:\n" + "\n".join(
            f"  {line}" for line in tasks_raw.splitlines()
        )

    return f"— {date_str} —\n\n{calendar_section}\n\n{tasks_section}"
