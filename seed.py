"""一次性种子脚本：建表 + 写入 40 个课程席位 + 管理员/助教账号。
数据来源：PDF《教学指导·助教教师版》第25-27页「助教分配总表（填写用）」。

用法：
    pip install -r requirements.txt
    python seed.py
可重复运行（已存在的数据会跳过）。
"""
import os
import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

from db import engine, SessionLocal
from models import Base, User, CourseSession, MODULES

load_dotenv()

# 周 -> 模块 code
WEEK_MODULE = {
    1: "M1", 2: "M2", 3: "M3", 4: "M3",
    5: "M4", 6: "M4", 7: "M5", 8: "M6",
}
# 周 -> (周一日期, 周四日期)
WEEK_DATES = {
    1: ("2026-10-26", "2026-10-29"),
    2: ("2026-11-02", "2026-11-05"),
    3: ("2026-11-09", "2026-11-12"),
    4: ("2026-11-16", "2026-11-19"),
    5: ("2026-11-23", "2026-11-26"),
    6: ("2026-11-30", "2026-12-03"),
    7: ("2026-12-07", "2026-12-10"),
    8: ("2026-12-14", "2026-12-17"),
}

# (week, slot, topic, claimer_username_or_None)
# 已按 PDF 第25-27页预填的认领关系录入 claimer；其余为待认领(None)
SESSIONS = [
    (1, "1-A", "认知导入", "zrr"),
    (1, "1-B", "唯一入口与三模式", "sean"),
    (1, "1-C", "技能创建与全量设置", None),
    (1, "2-A", "验收展示", "mandy"),
    (1, "2-B", "排障与作业评价", None),

    (2, "1-A", "版本底座", "sean"),
    (2, "1-B", "技能生态与官制", "michael"),
    (2, "1-C", "发布实操", None),
    (2, "2-A", "验收展示", None),
    (2, "2-B", "排障与作业评价", None),

    (3, "1-A", "需求澄清", None),
    (3, "1-B", "策划书", None),
    (3, "1-C", "对标拆解", None),
    (3, "2-A", "验收展示", None),
    (3, "2-B", "排障与作业评价", None),

    (4, "1-A", "MVP与口令", None),
    (4, "1-B", "部署实操", None),
    (4, "1-C", "协作纪律", None),
    (4, "2-A", "验收展示", None),
    (4, "2-B", "排障与作业评价", None),

    (5, "1-A", "收款闭环", "mandy"),
    (5, "1-B", "获客引擎 I", None),
    (5, "1-C", "获客引擎 II · GEO", None),
    (5, "2-A", "验收展示", None),
    (5, "2-B", "排障与作业评价", None),

    (6, "1-A", "AI客服", None),
    (6, "1-B", "CRM与账单", None),
    (6, "1-C", "通知三档", "michael"),
    (6, "2-A", "验收展示", None),
    (6, "2-B", "排障与作业评价", None),

    (7, "1-A", "第二大脑与日记", "michael"),
    (7, "1-B", "数字人与远程", None),
    (7, "1-C", "记忆体系", None),
    (7, "2-A", "验收展示", None),
    (7, "2-B", "排障与作业评价", None),

    (8, "1-A", "投资框架", None),
    (8, "1-B", "财富系统与服务器", None),
    (8, "1-C", "毕业路演", None),
    (8, "2-A", "毕业路演展示", None),
    (8, "2-B", "结算与作业评价", None),
]

# 助教账号（PDF 五位助教 + Michael）：username, 显示名
TAS = [
    ("grace", "Grace"),
    ("zrr", "ZRR"),
    ("mandy", "Mandy"),
    ("jason", "Jason"),
    ("sean", "Sean"),
    ("michael", "Michael"),
]


def seed(db=None):
    """幂等种子：缺用户补用户、缺席位补席位。可被 app 启动时自动调用。"""
    own = db is None
    if own:
        Base.metadata.create_all(engine)
        db = SessionLocal()

    admin_pw = os.environ.get("ADMIN_DEFAULT_PASSWORD", "Admin@2026snail")
    ta_pw = os.environ.get("TA_DEFAULT_PASSWORD", "Ta@2026snail")

    if not db.query(User).filter_by(username="amanda").first():
        db.add(User(
            username="amanda", display_name="Amanda（管理员）", role="admin",
            password_hash=generate_password_hash(admin_pw), claim_scope=[],
            must_change_pw=True,
        ))
        print("[seed] 创建管理员 amanda")

    for uname, dname in TAS:
        if not db.query(User).filter_by(username=uname).first():
            db.add(User(
                username=uname, display_name=dname, role="ta",
                password_hash=generate_password_hash(ta_pw), claim_scope=[],
                must_change_pw=True,
            ))
            print(f"[seed] 创建助教 {uname}")

    # ---- 课程席位 ----
    existing = db.query(CourseSession).count()
    if existing == 0:
        claimer_map = {u.username: u.id for u in db.query(User).all()}
        for week, slot, topic, claimer in SESSIONS:
            mon, thu = WEEK_DATES[week]
            date_str = mon if slot.startswith("1") else thu
            dt = datetime.datetime.strptime(date_str + " 20:00", "%Y-%m-%d %H:%M")
            cid = claimer_map.get(claimer) if claimer else None
            db.add(CourseSession(
                week=week, module=WEEK_MODULE[week], topic=topic, slot=slot,
                class_time=dt, claimed_by=cid,
                status="claimed" if cid else "open", note="",
            ))
        db.commit()
        print(f"[seed] 写入 {len(SESSIONS)} 个课程席位")
    else:
        print(f"[seed] 席位已存在（{existing} 条），跳过")

    if own:
        db.close()
    print("[seed] 完成。")


if __name__ == "__main__":
    seed()
