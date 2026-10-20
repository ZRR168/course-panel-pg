# 蜗牛AI 课程安排系统面板（PostgreSQL / Supabase 版）

与现有 `course-panel.onrender.com`（SQLite）**功能相同、网址不同**的新面板。
后端改用 **Supabase 上的 PostgreSQL**，并接入 **Supabase Realtime** 实现登录后全员实时同步。

## 功能模块
1. 登录 / 鉴权（角色：admin / ta）
2. 总览看板：总席位、已/未认领、各模块进度、最近动态
3. 课程安排表（按周）：40 个席位色块看板，助教点选认领/释放
4. 助教认领：TA 选席位认领；可认领模块范围由管理员设定
5. 助教与权限管理（admin）：建/停用账号、限定可认领模块、重置密码
6. 同步信息：基于 Supabase Realtime，任何人认领/释放，其他人实时可见

## 课程数据（来自 PDF 第25-27页）
- 6 大模块：思维入口 / 技能库 / 项目实战 / 商业化 / 工作流 / 财富+毕业
- 8 周 × 每周 5 席位（周一 1-A/1-B/1-C + 周四 2-A/2-B）= 40 席位
- 助教：Grace、ZRR、Mandy、Jason、Sean、Michael；管理员：Amanda

## 本地运行
```bash
pip install -r requirements.txt
cp .env.example .env   # 填入 DATABASE_URL / SUPABASE_* / SECRET_KEY
python seed.py         # 建表 + 写入 40 席位 + 账号（Supabase 连接串）
python app.py          # 本地 http://localhost:5050
```

## 部署
见 `SUPABASE_SETUP.md`（建库取密钥）与 `RENDER_DEPLOY.md`（新建 Render 服务拿新网址）。
