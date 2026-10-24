import json
from pathlib import Path

import pytest

from npc_demo import NPCSession

CHARACTER = Path(__file__).resolve().parents[1] / "characters/linzhou.md"


def test_persist_reload_latest_turn_and_player_isolation(tmp_path):
    prompts = []

    def responder(prompt):
        prompts.append(prompt)
        return {"content": "姜茶给你留着。", "source": "test"}

    first = NPCSession(CHARACTER, "alice", tmp_path, responder=responder)
    first.chat("我叫小雨，不喝酒，明天去旧灯塔。")
    restarted = NPCSession(CHARACTER, "alice", tmp_path, responder=responder)
    restarted.chat("我刚才说要去哪？")
    messages = prompts[-1]
    assert [item["role"] for item in messages] == [
        "system", "user", "assistant", "user"
    ]
    assert "外冷内热" in messages[0]["content"]
    assert messages[1]["content"] == "我叫小雨，不喝酒，明天去旧灯塔。"
    assert messages[2]["content"] == "姜茶给你留着。"
    assert messages[3]["content"] == "我刚才说要去哪？"
    assert len(json.loads(first.memory.memory_file.read_text(encoding="utf-8"))) == 2
    other = NPCSession(CHARACTER, "bob", tmp_path, responder=responder)
    assert other.memory.conversations == []


def test_failed_generation_does_not_save(tmp_path):
    session = NPCSession(CHARACTER, memory_dir=tmp_path, responder=lambda _: {
        "source": "error", "content": "", "error": "provider unavailable"
    })
    with pytest.raises(RuntimeError):
        session.chat("你好")
    assert session.memory.conversations == []
    assert not session.memory.memory_file.exists()


def test_corrupt_memory_is_not_overwritten(tmp_path):
    session = NPCSession(CHARACTER, memory_dir=tmp_path)
    session.memory.memory_file.write_text("broken", encoding="utf-8")
    with pytest.raises(ValueError):
        NPCSession(CHARACTER, memory_dir=tmp_path)
    assert session.memory.memory_file.read_text(encoding="utf-8") == "broken"


def test_changed_character_gets_separate_memory(tmp_path):
    character = tmp_path / "npc.md"
    character.write_text("角色甲", encoding="utf-8")
    session = NPCSession(character, memory_dir=tmp_path, responder=lambda _: {"content": "你好"})
    session.chat("秘密")
    character.write_text("角色乙", encoding="utf-8")
    assert NPCSession(character, memory_dir=tmp_path).memory.conversations == []


def test_context_window_keeps_last_six_turns(tmp_path):
    prompts = []

    def responder(prompt):
        prompts.append(prompt)
        return {"content": "记下了"}

    session = NPCSession(CHARACTER, memory_dir=tmp_path, responder=responder)
    for i in range(8):
        session.chat(f"消息{i}")
    messages = prompts[-1]
    history_messages = messages[1:-1]
    assert len(history_messages) == 12  # 6 轮，每轮两条消息
    assert [item["role"] for item in history_messages] == [
        "user", "assistant"
    ] * 6
    assert history_messages[0]["content"] == "消息1"
    assert history_messages[-2]["content"] == "消息6"
    assert messages[-1] == {"role": "user", "content": "消息7"}
    assert len(session.memory.conversations) == 8
