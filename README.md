# NPC Memory Demo

一个使用 Ollama 本地模型、Markdown 角色设定和 JSON 持久记忆的命令行 NPC 对话原型。

当前示例角色为原创的「林舟」：雾港酒馆的守夜人，外冷内热、谨慎守信。默认模型为 `qwen2.5:3b`。

## 当前状态

- 支持本地角色文档、最近 6 轮对话上下文、重启后续聊。
- 玩家 ID 与角色文档内容共同确定存档，不同玩家或角色隔离。
- 使用 UTF-8 JSON 和同目录临时文件替换保存历史；模型失败或返回空文本时不保存该轮。
- 已完成真实模型多轮评测，仍存在计划召回不完整、重复推荐饮品和无依据补充等问题。
- 使用 Ollama `/api/chat`，分别传入角色设定、历史消息与当前玩家输入。尚未实现长期事实摘要、语义检索、流式输出和并发存档写锁。

## 环境与安装（Windows PowerShell）

需要 Python 3.10+、Ollama。GitHub 上传另需 Git。

进入本文件所在的项目目录后执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull qwen2.5:3b
ollama list
```

如果 Ollama 没有运行，在另一个终端启动，并保持窗口打开：

```powershell
ollama serve
```

如果提示 11434 端口已占用，先检查现有 Ollama 服务，无需重复启动。

运行 Demo：

```powershell
.\.venv\Scripts\python.exe npc_demo.py --player xiaoyu
```

`--provider ollama` 仍可使用，但现在默认就是 Ollama。独立版不支持 `--provider router`。

## 文件结构

```text
npc-memory-demo/
├── .github/workflows/tests.yml
├── npc_demo.py              # 命令行与 NPCSession
├── npc_agent.py             # 角色加载与提示词
├── ollama_client.py         # 本地模型请求与错误处理
├── memory.py               # JSON 持久记忆
├── config.json
├── characters/linzhou.md
├── docs/                   # 评测说明与原始对话记录
├── tests/
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── README.md
```

## 模型配置

编辑根目录的 `config.json`，保存后重新启动：

```json
{
  "base_url": "http://localhost:11434",
  "model": "qwen2.5:3b",
  "timeout": 180,
  "num_predict": 512
}
```

`model` 必须与 `ollama list` 中的名字一致。`timeout` 为请求超时秒数，`num_predict` 是生成 token 上限。可用环境变量 `OLLAMA_BASE_URL` 覆盖请求地址；无需配置 `.env`。

本地推理不收取云端 API 调用费，仍使用本机硬件和电力。模型权重由用户通过 Ollama 下载，不放入代码仓库。

## 角色与记忆

替换角色资料：

```powershell
.\.venv\Scripts\python.exe npc_demo.py --character characters/linzhou.md --player xiaoyu
```

角色文档应为 UTF-8，包含身份、背景、性格、语气和知识边界，最多 24000 字符；单条输入最多 4000 字符。

输入 `/history` 查看最近 6 轮，输入 `/exit` 退出。再次用同一玩家 ID 与相同角色文档启动，会恢复历史。存档写入 `npc_saves/`，默认不提交 Git。

JSON 保存全部轮次，但每次只把最近 6 轮提供给模型，较早信息不保证召回。JSON 持久化不代表训练或无限长期记忆。更换模型不会创建新存档，旧模型的错误回复也可能影响后续对话；比较模型时建议使用新的玩家 ID。修改角色文档会创建新的记忆空间。

## 验证与排查

自动化测试不调用真实模型：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q --basetemp .test_tmp
```

测试覆盖跨会话恢复、上一轮进入上下文、玩家与角色隔离、失败不保存、损坏存档保护及上下文窗口。5 项单元测试通过。真实模型的测试场景、原始对话、评分及已知限制见 [评测记录](docs/evaluation.md)。

拆分验证记录（2026-10-24）：独立版 5 项测试通过，命令行帮助可运行；验证使用现有 Python 环境中的依赖。独立版尚未在全新安装依赖的环境中执行真实模型多轮验收。

人工检查可使用新玩家 ID，依次输入「我叫小雨，不喝酒，明天去旧灯塔」「我刚才说去哪？给我推荐喝的」，退出重启后再问名字。检查是否记得小雨、旧灯塔和饮品偏好，同时观察是否重复介绍或跑题。

| 现象 | 检查方法 |
| --- | --- |
| 连接失败 | 确认 Ollama 服务运行及地址正确 |
| HTTP 404 | 执行 `ollama list`，核对并下载配置的模型；检查服务地址 |
| ReadTimeout | 检查服务负载，必要时提高 timeout；180 秒不保证所有机器均能完成 |
| 暂时没有文字 | 当前等待完整回复后才显示，不是逐字流式输出 |
| 重复介绍、偏题 | 已知回答质量问题，不能仅靠重启或延长超时解决 |
| JSON 损坏 | 保留原文件检查；不要直接覆盖唯一存档 |

同一个玩家与角色的存档只支持单进程使用。

## 模型与角色资料

本项目通过 Ollama 在本地运行 `qwen2.5:3b`，
无需云端 API Key。模型权重由用户自行下载，不包含在本仓库中。

模型采用 Qwen Research License：
[模型页面](https://ollama.com/library/qwen2.5:3b) ·
[模型许可证](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE)

示例 NPC「林舟」及背景设定为原创，不包含游戏官方角色资料。

