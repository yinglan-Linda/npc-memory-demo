# NPC Memory Demo

一个使用 Ollama 本地模型、Markdown 角色设定和 JSON 持久记忆的命令行 NPC 对话原型。从 AI Orchestrator 项目提取，运行时无需原项目、OpenRouter 或 API Key。

当前示例角色为原创的「林舟」：雾港酒馆的守夜人，外冷内热、谨慎守信。默认模型为 `qwen2.5:3b`。

## 当前状态

- 支持本地角色文档、最近 6 轮对话上下文、重启后续聊。
- 玩家 ID 与角色文档内容共同确定存档，不同玩家或角色隔离。
- 使用 UTF-8 JSON 和同目录临时文件替换保存历史；模型失败或返回空文本时不保存该轮。
- 原项目已验证 Ollama 实际调用成功；用户试用 3B 后反馈约第 4 轮仍可能重复介绍或偏离问题。此问题尚未修复，不能宣称稳定角色扮演。
- 独立版延续单条提示词方案，尚未改为独立的 system/user/assistant 消息，也未实现长期事实摘要、语义检索、流式输出或并发存档写锁。

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
├── npc_demo.py              # 命令行与 NPCSession
├── npc_agent.py             # 角色加载与提示词
├── ollama_client.py         # 本地模型请求与错误处理
├── memory.py               # JSON 持久记忆
├── config.json
├── characters/linzhou.md
├── tests/
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
├── README.md
└── GITHUB_UPLOAD.md
```

复制整个目录，包括隐藏文件 `.gitignore`。不要把原项目的 `.venv`、`.git`、`.env`、日志或整个 memory/agents/config 目录复制进来。新目录中 `memory.py` 是文件，不需要原项目的同名目录。

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
.\.venv\Scripts\python.exe -m pytest -q
```

测试覆盖跨会话恢复、上一轮进入上下文、玩家与角色隔离、失败不保存、损坏存档保护及上下文窗口。原项目的 101 项测试结果不等于独立版测试数量。

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

## 来源与许可

本项目由 AI Orchestrator 的 NPC Demo 拆分，保留原有提示词与存档机制。附带原创角色资料，不包含游戏官方角色资料。

默认模型 `qwen2.5:3b` 约 1.9GB，采用 Qwen Research License，模型许可与项目代码许可分开处理。参见 [Ollama 模型页](https://ollama.com/library/qwen2.5:3b) 和 [模型许可证](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE)。

此目录尚未添加代码 LICENSE；发布者应在确认所含代码的授权后选择许可证。仓库公开不自动代表授予开源使用许可。

上传步骤见 [GITHUB_UPLOAD.md](GITHUB_UPLOAD.md)。
