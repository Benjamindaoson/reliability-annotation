# 🚀 快速部署指南

## 方案一：本地部署 + ngrok（最简单，5分钟搞定）

### 步骤 1: 启动标注工具

```bash
cd D:\01_work\Reliability-Bottleneck-Shift
streamlit run annotation_tool/app_chinese.py
```

浏览器会自动打开标注界面。

### 步骤 2: 下载 ngrok

1. 打开 https://ngrok.com/download
2. 下载 Windows 版本
3. 解压得到 `ngrok.exe`

### 步骤 3: 注册 ngrok（免费）

1. 打开 https://ngrok.com
2. 注册账号
3. 登录后复制你的 Authtoken（个人主页 → Getting Started → Your Authtoken）

### 步骤 4: 配置 ngrok

打开命令提示符（cmd），运行：

```bash
ngrok config add-authtoken 你的Authtoken
```

### 步骤 5: 启动内网穿透

在另一个命令提示符窗口运行：

```bash
ngrok http 8501
```

会看到类似输出：

```
Session Status                online
Account                      your@email.com
Forwarding                   https://abc123.ngrok-free.app -> http://localhost:8501
```

### 步骤 6: 把链接发给标注伙伴

标注伙伴打开 `https://abc123.ngrok-free.app`

输入标注员编号（如 A001）即可开始标注！

---

## 方案二：Streamlit Cloud（公网永久部署）

### 步骤 1: 把代码上传到 GitHub

**方法 A: 命令行（需要 GitHub Token）**

```bash
cd D:\01_work\Reliability-Bottleneck-Shift

# 初始化
git init
git add -A
git commit -m "Initial commit"

# 创建 GitHub 仓库（需要 token）
# 打开 https://github.com/settings/tokens 创建 Personal Access Token
# 需要勾选 repo 权限

git remote add origin https://github.com/YOUR_USERNAME/reliability-annotation.git
git push -u origin master
```

**方法 B: GitHub Desktop（图形界面）**

1. 下载 GitHub Desktop: https://desktop.github.com
2. File → Add Local Repository → 选择项目文件夹
3. Publish repository → 选择 Public
4. 上传到 GitHub

### 步骤 2: 部署到 Streamlit Cloud

1. 打开 https://share.streamlit.io
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 配置：
   - Repository: 选择你刚上传的仓库
   - Branch: master
   - Main file path: `annotation_tool/app_chinese.py`
5. 点击 "Deploy!"

### 步骤 3: 获取 URL

部署完成后，你会获得一个 URL：
`https://your-app-name.streamlit.app`

把这个 URL 发给标注伙伴即可！

---

## 标注伙伴如何使用

1. 打开你发的 URL
2. 输入标注员编号（如 A001）
3. 开始标注！

---

## 常见问题

### Q: ngrok 免费版有限制吗？
A: 免费版有连接数限制，但 2-3 个人标注完全够用。

### Q: ngrok 链接会过期吗？
A: 免费版重启后链接会变，需要重新告诉伙伴新链接。

### Q: Streamlit Cloud 部署失败？
A: 检查 requirements.txt 是否包含 streamlit，或者查看错误日志。

### Q: 标注数据存在哪里？
A: 当前版本存在本地文件 `data/annotation_db/`。部署到云端后需要配置数据库。

### Q: 多个标注员数据会冲突吗？
A: 当前文件版本不支持多人并发写入。云部署需要升级到 PostgreSQL。

---

## 需要帮助？

查看详细文档：
- [CODEX_DELIVERY_REPORT.md](results/CODEX_DELIVERY_REPORT.md)
- [annotation_tool/README_CHINESE.md](annotation_tool/README_CHINESE.md)
