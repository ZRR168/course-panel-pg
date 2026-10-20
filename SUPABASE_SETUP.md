# Supabase 新建项目指引（给 Amanda）

目标：新建一个 **PostgreSQL 数据库**（托管在 Supabase），拿到 3 个关键值发给我，我就能连库建表、写种子数据并部署。

## 第 1 步：注册 / 登录 Supabase
1. 打开 https://supabase.com ，点右上角 **Start your project** / **Sign in**。
2. 用邮箱注册或直接登录（免费层 Free tier 足够，无需绑卡）。

## 第 2 步：新建项目
1. 登录后点 **New project**。
2. 填写：
   - **Name**：`snail-course-pg`（随意）
   - **Database Password**：**设一个你能记住的强密码**（一定要记下来！后面要用）
   - **Region**：选 **Singapore (ap-southeast-1)**（离你最近，速度快）
   - **Pricing Plan**：Free
3. 点 **Create new project**，等待 1–2 分钟就绪。

## 第 3 步：复制数据库连接串（DATABASE_URL）
1. 左侧菜单最下面点 **Settings → Database**。
2. 找到 **Connection string**，选 **URI** 标签。
3. 复制 **Transaction pooler**（端口 `6543`）那一条，例如：
   ```
   postgresql://postgres:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```
4. 把里面的 `[YOUR-PASSWORD]` 替换成第 2 步你设的数据库密码。
   → 这就是 **DATABASE_URL**。

## 第 4 步：复制 API 信息（前端实时同步用）
1. 左侧 **Settings → API**。
2. 复制：
   - **Project URL**（形如 `https://xxxxxxxx.supabase.co`）→ **SUPABASE_URL**
   - **anon public key**（很长一串 `eyJ...`）→ **SUPABASE_ANON_KEY**

## 第 5 步：把 3 个值发给我
请把下面 3 项发我（可直接粘贴，我不会外传）：
- `DATABASE_URL=...`
- `SUPABASE_URL=...`
- `SUPABASE_ANON_KEY=...`

拿到后我会：
1. 在本地连你的 Supabase，**自动建表**并**写入 40 个课程席位 + 6 名助教 + 管理员**；
2. 把同样 3 项 + 一个随机 `SECRET_KEY`、`ADMIN_DEFAULT_PASSWORD` 配到 Render；
3. 部署后给你新网址和账号清单。

> 备注：Supabase 免费层在长时间无访问后会自动暂停，首次打开会花几秒唤醒，属正常现象。
