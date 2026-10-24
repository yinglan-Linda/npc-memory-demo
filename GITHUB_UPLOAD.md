# 发布到 GitHub

## 1. 复制与运行

将本目录整体复制到新的位置，例如 `D:\Projects\npc-memory-demo`。保留 `.gitignore`；不要复制原项目 `.git` 或 `.venv`。按 README 在新目录重新创建环境，并完成测试及一次真实模型对话。

在新目录打开 PowerShell。以下 Git 命令仅在新目录执行，不在 AI Orchestrator 原项目中执行。

## 2. 创建本地仓库

```powershell
git init -b main
git status --short
git add .
git diff --cached --stat
git diff --cached
```

检查暂存内容应为代码、配置、角色示例、文档及测试，不能包含真实聊天记录、密钥、虚拟环境或模型权重。本项目已提供忽略规则。`config.json` 没有密钥，可以提交；若修改为私有服务地址，请先检查是否适合公开。

检查后提交：

```powershell
git commit -m "Initial NPC memory demo"
```

如果 Git 提示身份未配置，可仅为这个仓库设置，再重新提交：

```powershell
git config user.name "你的名字"
git config user.email "你的 GitHub 邮箱或 noreply 邮箱"
```

## 3. 创建 GitHub 空仓库

登录 GitHub，点击右上角 `+` → `New repository`：

- Repository name：`npc-memory-demo`，或自定义名称。
- Description：`A local NPC dialogue demo with Ollama and persistent JSON memory.`
- 选择 Public 或 Private。
- 这里不勾选初始化 README、.gitignore、LICENSE，本地已经有文件；代码许可证可以确认后另行添加。
- 点击 `Create repository`。

## 4. 连接并推送

把下面的 `YOUR_USERNAME` 和仓库名替换为自己的：

```powershell
git remote add origin https://github.com/YOUR_USERNAME/npc-memory-demo.git
git push -u origin main
```

按 Git 的凭据管理器提示完成登录。如使用个人访问令牌，不要把令牌写入命令 URL 或项目文件。GitHub HTTPS 验证不能使用账户密码。

刷新 GitHub 仓库页面，确认 README、代码、角色资料和测试显示正常。

## 5. 后续更新

```powershell
git status
git add npc_agent.py README.md
git diff --cached
git commit -m "Improve NPC dialogue behavior"
git push
```

按实际改动替换 `git add` 的文件列表。如果使用网页上传，也要上传整个必要文件集，包括 `.gitignore`，并核对没有运行数据；日常更新更推荐 Git。

官方参考：[将本地代码添加到 GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)。
