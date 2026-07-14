"""
Google Calendar + Gmail için OAuth kimlik doğrulama.

İlk çalıştırmada tarayıcı açılır, Google hesabınla giriş yapıp izin
verirsin. Token diske kaydedilir (token.json), sonraki çalıştırmalarda
tekrar login istemez (token süresi dolunca otomatik yenilenir).

credentials.json dosyasının proje kök dizininde olması gerekiyor
(Google Cloud Console'dan indirdiğin OAuth client ID dosyası).
"""
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Calendar: okuma/yazma | Gmail: taslak oluşturma + gelen kutusu okuma
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]

_BASE_DIR = Path(__file__).parent
_CREDENTIALS_PATH = _BASE_DIR / "credentials.json"
_TOKEN_PATH = _BASE_DIR / "token.json"


def get_credentials() -> Credentials:
    """Geçerli OAuth credentials döner, gerekirse login akışını başlatır."""
    creds = None

    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not _CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"'{_CREDENTIALS_PATH.name}' bulunamadı. Google Cloud Console'dan "
                    "indirdiğin OAuth client dosyasını proje kök dizinine "
                    "'credentials.json' adıyla koy."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        _TOKEN_PATH.write_text(creds.to_json())

    return creds


def get_calendar_service():
    """Yetkilendirilmiş Google Calendar servis objesi döner."""
    return build("calendar", "v3", credentials=get_credentials())


def get_gmail_service():
    """Yetkilendirilmiş Gmail servis objesi döner."""
    return build("gmail", "v1", credentials=get_credentials())