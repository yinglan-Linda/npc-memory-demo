"""UTF-8, atomic JSON saves isolated by player and character content."""
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path



class NPCMemory:
    def __init__(self, player_id, character, directory):
        # Isolate history by player and character contents.
        identity = json.dumps([player_id, character], ensure_ascii=False)
        key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        self.user_id = player_id
        self.memory_file = Path(directory) / f"memory_npc_{key}.json"
        self.preferences = {}
        self.conversations = []
        if self.memory_file.exists():
            records = json.loads(self.memory_file.read_text(encoding="utf-8"))
            if not isinstance(records, list) or any(
                not isinstance(row, dict)
                or not isinstance(row.get("user"), str)
                or not isinstance(row.get("agent"), str)
                for row in records
            ):
                raise ValueError(f"存档格式无效，请检查：{self.memory_file}")
            self.conversations = records

    def save_conversation(self, user_input, agent_response):
        records = self.conversations + [{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user_input,
            "agent": agent_response,
        }]
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            dir=self.memory_file.parent, suffix=".tmp"
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(records, handle, ensure_ascii=False, indent=2)
            os.replace(temporary, self.memory_file)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        self.conversations = records

    def get_recent_history(self, n=6):
        return self.conversations[-n:] if n > 0 else []
