"""
Persistent state: tracks seen message GUIDs and current active project.
Serialized to ~/.claude-imessage-state.json.
"""

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path.home() / ".claude-imessage-state.json"

# Only keep GUIDs from the last N days to prevent unbounded growth
GUID_RETENTION_DAYS = 7


class State:
    def __init__(self):
        self.seen_guids: set[str] = set()
        self.current_project: str | None = None
        # Unix timestamp of the last message we processed
        self.last_message_time: float = time.time()
        self._load()

    def _load(self) -> None:
        if not STATE_FILE.exists():
            return
        try:
            data = json.loads(STATE_FILE.read_text())
            self.seen_guids = set(data.get("seen_guids", []))
            self.current_project = data.get("current_project")
            self.last_message_time = data.get("last_message_time", time.time())
            logger.info(
                "Loaded state: project=%s, %d seen GUIDs",
                self.current_project,
                len(self.seen_guids),
            )
        except Exception as e:
            logger.warning("Failed to load state file: %s", e)

    def save(self) -> None:
        try:
            data = {
                "seen_guids": list(self.seen_guids),
                "current_project": self.current_project,
                "last_message_time": self.last_message_time,
            }
            STATE_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning("Failed to save state file: %s", e)

    def mark_seen(self, guid: str) -> None:
        self.seen_guids.add(guid)

    def is_seen(self, guid: str) -> bool:
        return guid in self.seen_guids

    def set_project(self, project_name: str) -> None:
        self.current_project = project_name
        self.save()

    def update_timestamp(self, unix_ts: float) -> None:
        if unix_ts > self.last_message_time:
            self.last_message_time = unix_ts
