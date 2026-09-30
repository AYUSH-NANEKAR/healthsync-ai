from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSION_FILE = PROJECT_ROOT / ".healthsync_session"


def save_session(session_token: str):
    """
    Save the current session token locally.
    """

    SESSION_FILE.write_text(
        session_token,
        encoding="utf-8",
    )


def load_session():
    """
    Load the saved session token.

    Returns:
        Session token if one exists.
        None otherwise.
    """

    if not SESSION_FILE.exists():
        return None

    session_token = SESSION_FILE.read_text(
        encoding="utf-8"
    ).strip()

    return session_token or None


def clear_session():
    """
    Remove the locally stored session token.
    """

    if SESSION_FILE.exists():
        SESSION_FILE.unlink()