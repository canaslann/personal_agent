"""
Basit to-do listesi - SQLite tabanlı, tamamen local.
Program kapansa bile görevler kalıcı olarak saklanır.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

_DB_PATH = Path(__file__).parent.parent / "todo.db"


def _get_conn():
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            done_at TEXT
        )
    """)
    conn.commit()
    return conn


def add_task(task: str) -> str:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO todos (task, created_at) VALUES (?, ?)",
            (task, datetime.now().isoformat())
        )
    return f"Görev eklendi: '{task}'"


def list_tasks(show_done: bool = False) -> str:
    with _get_conn() as conn:
        if show_done:
            rows = conn.execute(
                "SELECT id, task, done FROM todos ORDER BY done, id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, task, done FROM todos WHERE done = 0 ORDER BY id"
            ).fetchall()

    if not rows:
        return "Görev listesi boş." if not show_done else "Hiç görev yok."

    lines = []
    for sira, (row_id, task, done) in enumerate(rows, start=1):
        status = "✓" if done else "○"
        lines.append(f"[{sira}] {status} {task}  (ID:{row_id})")
    return "\n".join(lines)


def complete_task(task_id: int) -> str:
    with _get_conn() as conn:
        cur = conn.execute(
            "UPDATE todos SET done = 1, done_at = ? WHERE id = ? AND done = 0",
            (datetime.now().isoformat(), task_id)
        )
        if cur.rowcount == 0:
            return f"ID {task_id} bulunamadı veya zaten tamamlanmış."
    return f"Görev tamamlandı: ID {task_id}"


def delete_task(task_id: int) -> str:
    with _get_conn() as conn:
        cur = conn.execute("DELETE FROM todos WHERE id = ?", (task_id,))
        if cur.rowcount == 0:
            return f"ID {task_id} bulunamadı."
    return f"Görev silindi: ID {task_id}"


def get_pending_count() -> int:
    """Gün sonu özeti için bekleyen görev sayısı."""
    with _get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM todos WHERE done = 0").fetchone()[0]


def get_completed_today() -> list[str]:
    """Gün sonu özeti için bugün tamamlanan görevler."""
    today = datetime.now().strftime("%Y-%m-%d")
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT task FROM todos WHERE done = 1 AND done_at LIKE ?",
            (f"{today}%",)
        ).fetchall()
    return [r[0] for r in rows]