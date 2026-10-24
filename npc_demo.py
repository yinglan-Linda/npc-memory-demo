"""Run: python npc_demo.py --player demo --provider ollama"""
import argparse
import json
import sys
from pathlib import Path

from npc_agent import NPCAgent
from memory import NPCMemory

ROOT = Path(__file__).resolve().parent


class NPCSession:
    def __init__(self, character_file, player_id="demo", memory_dir=None,
                 provider="ollama", responder=None):
        self.agent = NPCAgent(character_file)
        self.memory = NPCMemory(player_id, self.agent.character,
                                memory_dir if memory_dir is not None else ROOT / "npc_saves")
        if responder is not None:
            self.respond = responder
        elif provider == "ollama":
            from ollama_client import fallback_to_ollama
            self.respond = fallback_to_ollama
        else:
            raise ValueError("未知模型提供方")

    def chat(self, message):
        message = message.strip()
        if not message:
            raise ValueError("消息不能为空")
        if len(message) > 4000:
            raise ValueError("单条消息最多支持 4000 字符")
        # Always include the immediately preceding turn, even without keyword overlap.
        context = json.dumps(self.memory.get_recent_history(6), ensure_ascii=False)
        result = self.respond(self.agent.build_prompt(message, context))
        content = result.get("content")
        if result.get("source") == "error" or not isinstance(content, str) or not content.strip():
            raise RuntimeError(result.get("error") or "模型没有返回有效文本，本轮未保存")
        self.memory.save_conversation(message, content)
        return content


def main():
    # Windows redirected streams can default to cp1252, which cannot print Chinese.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="带 JSON 持久记忆的 NPC 对话 Demo")
    parser.add_argument("--character", type=Path, default=ROOT / "characters/linzhou.md")
    parser.add_argument("--player", default="demo", help="同一玩家 ID 自动续聊")
    parser.add_argument("--memory-dir", type=Path, default=ROOT / "npc_saves")
    parser.add_argument("--provider", choices=["ollama"], default="ollama")
    args = parser.parse_args()
    try:
        session = NPCSession(args.character, args.player, args.memory_dir, args.provider)
    except (OSError, ValueError) as error:
        parser.exit(1, f"初始化失败：{error}\n")
    print(f"角色文档：{session.agent.character_file}\n存档：{session.memory.memory_file}")
    if args.provider == "ollama":
        from ollama_client import config
        print(f"Ollama：{config.get('ollama.base_url')} | "
              f"模型：{config.get('ollama.model')} | "
              f"超时：{config.get('ollama.timeout')} 秒")
    print("输入 /exit 退出；/history 查看最近对话。相同玩家和角色设定会恢复记忆。")
    while True:
        try:
            message = input("你：").strip()
            if message == "/exit":
                break
            if message == "/history":
                print(json.dumps(session.memory.get_recent_history(6), ensure_ascii=False, indent=2))
            elif message:
                print("NPC：" + session.chat(message))
        except (EOFError, KeyboardInterrupt):
            print("\n对话结束。")
            break
        except (OSError, ValueError, RuntimeError) as error:
            print(f"本轮失败：{error}")


if __name__ == "__main__":
    main()
