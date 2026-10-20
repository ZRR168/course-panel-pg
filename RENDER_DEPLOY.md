# Render 手动部署指引（拿到新网址）

> 由于构建环境无法联网，代码由你手动上传到 GitHub，再在 Render 连仓库部署。
> 数据库后端已经是你的 Supabase（PostgreSQL），应用启动时会**自动建表 + 自动灌入 40 个席位和账号**，无需手动跑脚本。

项目文件夹（在你本机）：
```
C:\Users\thinkpad\WorkBuddy\2026-10-20-02-06-40\course-panel-pg
```

---

## 第 1 步：新建 GitHub 仓库
1. 打开 https://github.com ，登录你的 ZRR168 账号。
2. 右上角 **＋ → New repository**。
3. Repository name 填 `course-panel-pg`，其余默认，**Create repository**。

## 第 2 步：把项目文件夹上传到仓库
**最简单（网页拖拽）**：
1. 进到刚建的空仓库，点 **uploading an existing file** 链接。
2. 打开本机文件夹 `course-panel-pg`，把里面**所有文件和文件夹一起拖到网页上传区**（GitHub 网页支持拖文件夹，会保留结构）。
3. 拖进来后点绿色 **Commit changes**。

> 注意：`.env` 文件**不要**上传（我们不用它，密码都走 Render 环境变量）。其余都要传，特别是 `requirements.txt`、`app.py`、`models.py`、`seed.py`、`db.py`、`templates/`、`static/`、`render.yaml`、`Procfile`。

## 第 3 步：在 Render 新建 Web Service
1. 打开 https://render.com ，用 **GitHub 登录**（连 ZRR168 账号）。
2. **New → Web Service** → 选刚才的 `course-panel-pg` 仓库 → Connect。
3. 填写：
   - **Name**：`course-panel-pg`
   - **Environment**：`Python 3`
   - **Region**：`Singapore`（或任意）
   - **Branch**：`main`
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan**：`Free`
4. 展开 **Advanced → Environment Variables**，把下面一组**原样粘贴**为 5 个 Key/Value：

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://postgres.qacfaayziralpntyvhrq:ausrealt168@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres` |
| `SUPABASE_URL` | `https://qacfaayziralpntyvhrq.supabase.co` |
| `SUPABASE_ANON_KEY` | `sb_publishable_MGFnJZEvwjdgxEChmZ5OFQ_L6J_KVnI` |
| `SECRET_KEY` | `EvQuYFePkhAxFk7EHkHxYVy77GK2w6Ix5vMXvrpb7yI` |

> 初始密码已统一为 `123456`（管理员与助教相同），无需再配置密码类环境变量。

> 若顶部实时同步显示「同步未连接」，说明 `SUPABASE_ANON_KEY` 填错了（手打易错）——回到 Supabase **API Keys** 页，点 Publishable key 的 📋 复制，重新粘贴到这一项即可。

5. 点 **Create Web Service**，等约 1–2 分钟构建完成。

## 第 4 步：拿到新网址 + 首次使用
- 部署完成后，Render 给出网址，形如：
  ```
  https://course-panel-pg-xxxx.onrender.com
  ```
  **它和现有 course-panel.onrender.com 不同**，这就是新面板入口。
- 免费层首次访问会"冷启动"几秒，多刷新一次。
- 首次打开会自动建表 + 灌入数据（约 1–2 秒），之后即可登录（**所有人初始密码统一为 `123456`**，登录后按提示先改密码）：
  - **管理员**：`amanda` / `123456`
  - **助教**：`grace` `zrr` `mandy` `jason` `sean` `michael` / `123456`
- 助教登录后到「课程安排表」认领席位；所有人都能看到实时同步动态。

## 排错
- 打开网址报 500：多半是 `DATABASE_URL` 密码错或 Supabase 项目被暂停（免费层长时间无访问会暂停，首次访问会自动唤醒，稍等再试）。
- 顶部「同步未连接」但页面正常：仅实时推送不可用，已靠 20 秒定时刷新兜底，不影响认领；多为 anon key 填错，按上面提示重填。
- 想重灌数据：删掉 Supabase 里 `sessions/users/claim_history/activity_log` 四张表后重新部署即可自动重建。
