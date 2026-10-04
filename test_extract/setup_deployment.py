"""
完全部署脚本 - 自动部署到 GitHub + Streamlit Cloud

运行此脚本前需要：
1. GitHub 账号 (https://github.com)
2. GitHub Personal Access Token (https://github.com/settings/tokens)
   - 需要 repo 权限
3. Streamlit Cloud 账号 (https://share.streamlit.io)
   - 用 GitHub 登录即可

Usage:
    python setup_deployment.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def run_cmd(cmd, shell=True):
    """Run command and return output"""
    print(f"  Running: {cmd}")
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  {RED}Error: {result.stderr}{RESET}")
        return False, result
    return True, result

def check_prerequisites():
    """Check if prerequisites are installed"""
    print("\n📋 检查前提条件...")

    checks = [
        ("git", ["git", "--version"]),
        ("python", ["python", "--version"]),
    ]

    for name, cmd in checks:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ {name}: {result.stdout.strip()}")
            else:
                print(f"  ❌ {name}: 未安装")
                return False
        except FileNotFoundError:
            print(f"  ❌ {name}: 未安装")
            return False

    return True

def get_github_token():
    """Get GitHub token from user"""
    print("\n🔑 请提供 GitHub Personal Access Token")
    print("   获取地址: https://github.com/settings/tokens")
    print("   需要勾选: repo (全部)")
    print()
    token = input("Token: ").strip()
    return token if token else None

def get_repo_name():
    """Get repository name from user"""
    print("\n📁 请输入 GitHub 仓库名称")
    print("   (留空则使用: reliability-annotation)")
    name = input("仓库名称: ").strip()
    return name if name else "reliability-annotation"

def main():
    print("=" * 60)
    print("🚀 可靠性标注系统 - 自动部署脚本")
    print("=" * 60)

    # Check prerequisites
    if not check_prerequisites():
        print(f"\n{RED}❌ 前提条件检查失败，请安装缺失的工具{RESET}")
        return

    # Get user inputs
    github_token = get_github_token()
    if not github_token:
        print(f"{RED}❌ 需要 GitHub Token 才能继续{RESET}")
        return

    repo_name = get_repo_name()

    # Working directory
    repo_path = Path(__file__).parent
    os.chdir(repo_path)

    print(f"\n📂 工作目录: {repo_path}")

    # Step 1: Initialize git
    print("\n📦 Step 1: 初始化 Git...")

    git_dir = repo_path / ".git"
    if git_dir.exists():
        print("  Git 已初始化")
    else:
        success, _ = run_cmd("git init")
        if not success:
            print(f"{RED}❌ Git 初始化失败{RESET}")
            return
        print("  ✅ Git 初始化完成")

    # Step 2: Configure git
    print("\n⚙️ Step 2: 配置 Git...")

    # Get git config or use defaults
    success, result = run_cmd('git config --global user.email')
    email = result.stdout.strip() if result.stdout.strip() else "annotation@example.com"

    success, result = run_cmd('git config --global user.name')
    name = result.stdout.strip() if result.stdout.strip() else "Annotator"

    print(f"  User: {name}")
    print(f"  Email: {email}")

    # Step 3: Create .gitignore
    print("\n📄 Step 3: 创建 .gitignore...")

    gitignore_content = """# Byte-compiled files
__pycache__/
*.py[cod]

# Data files
data/external/
data/raw/
calibration/
results/
data/annotation_db/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
"""

    gitignore_path = repo_path / ".gitignore"
    if not gitignore_path.exists():
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("  ✅ .gitignore 创建完成")

    # Step 4: Create GitHub repo
    print("\n🌐 Step 4: 创建 GitHub 仓库...")

    import urllib.request
    import urllib.parse
    import json

    # Create repo via GitHub API
    api_url = "https://api.github.com/user/repos"
    data = json.dumps({
        "name": repo_name,
        "description": "长程 Computer-Use Agent 执行可靠性测量 - 人类标注系统",
        "private": False,
        "auto_init": False
    }).encode('utf-8')

    req = urllib.request.Request(api_url, data=data)
    req.add_header('Authorization', f'token {github_token}')
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            repo_data = json.loads(response.read())
            repo_url = repo_data['html_url']
            print(f"  ✅ 仓库创建成功: {repo_url}")
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read())
        if 'name already exists' in str(error_body):
            repo_url = f"https://github.com/{email.split('@')[0] if '@' in email else 'user'}/{repo_name}"
            print(f"  ⚠️ 仓库已存在: {repo_url}")
        else:
            print(f"  ❌ GitHub API 错误: {error_body}")
            return

    # Step 5: Add files and commit
    print("\n📝 Step 5: 提交代码...")

    # Determine git remote URL
    # Extract username from token API call or use placeholder
    try:
        req = urllib.request.Request("https://api.github.com/user")
        req.add_header('Authorization', f'token {github_token}')
        with urllib.request.urlopen(req) as response:
            user_data = json.loads(response.read())
            username = user_data['login']
            remote_url = f"https://{username}@{repo_name.replace('_', '-')}:443/{username}/{repo_name}.git"
            # Simpler format
            remote_url = f"https://github.com/{username}/{repo_name}.git"
    except:
        remote_url = f"https://github.com/YOUR_USERNAME/{repo_name}.git"

    # Add remote
    run_cmd("git remote remove origin 2>/dev/null || true")
    success, _ = run_cmd(f'git remote add origin {remote_url}')

    # Add files
    run_cmd("git add -A")

    # Check if there are files to commit
    success, result = run_cmd("git status --porcelain")
    if not result.stdout.strip():
        print("  ⚠️ 没有新文件需要提交")
    else:
        success, _ = run_cmd('git commit -m "Initial: Human Gold annotation system with Schema v3"')
        if success:
            print("  ✅ 提交完成")

    # Step 6: Push to GitHub
    print("\n⬆️ Step 6: 推送到 GitHub...")

    # Set up credential helper
    run_cmd('git config credential.helper store')

    # Push with token
    env = os.environ.copy()
    success, result = run_cmd(f'echo "https://{github_token}@github.com" | git push -u origin master --force')

    if not success:
        print(f"\n{YELLOW}⚠️ 自动推送失败，请手动执行:{RESET}")
        print(f"\n  git push -u origin master")
        print(f"\n  或者手动复制仓库地址并添加 remote:")
        print(f"  git remote add origin {remote_url}")
        print(f"  git push -u origin master")

    # Final instructions
    print("\n" + "=" * 60)
    print("✅ 部署准备完成！")
    print("=" * 60)

    print(f"""
📋 下一步操作:

1. 🌐 打开 Streamlit Cloud:
   https://share.streamlit.io

2. 用 GitHub 账号登录

3. 点击 "New app"

4. 配置应用:
   - Repository: 找到你的仓库 ({repo_name})
   - Branch: master
   - Main file path: annotation_tool/app_chinese.py

5. 点击 "Deploy!"

6. 部署完成后，复制 URL 发给标注伙伴：
   例如: https://your-app.streamlit.app

   标注伙伴打开 URL 后，输入标注员编号（如 A001）即可开始标注！
""")

if __name__ == "__main__":
    main()
