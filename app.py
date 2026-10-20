"""课程安排系统面板（PostgreSQL / Supabase 后端）。
功能模块：登录鉴权、总览看板、按周课程安排表、助教认领/释放、管理员账号与权限、实时同步。
"""
import os
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g, abort,
)
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from db import engine, SessionLocal
from models import Base, User, CourseSession, ClaimHistory, ActivityLog, MODULES
from seed import seed

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

MODULE_ORDER = ["M1", "M2", "M3", "M4", "M5", "M6"]


@app.before_request
def _ensure_db():
    # 首次请求时确保表存在并自动灌入种子数据（幂等）；DB 暂不可达则跳过
    if not getattr(app, "_db_ready", False):
        try:
            Base.metadata.create_all(engine)
            seed()
            app._db_ready = True
        except Exception as e:  # noqa: BLE001
            app.logger.warning("init_db 暂跳过：%s", e)


# ---------------- 工具 ----------------
def db() -> Session:
    return SessionLocal()


def get_user(uid):
    if not uid:
        return None
    return db().get(User, uid)


def login_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*a, **k)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        u = get_user(session.get("user_id"))
        if not u or u.role != "admin":
            abort(403)
        return f(*a, **k)
    return wrapper


@app.before_request
def load_g():
    g.user = get_user(session.get("user_id"))
    g.modules = MODULES
    g.module_order = MODULE_ORDER


def serialize_session(s: CourseSession, claimer_name=None):
    return {
        "id": s.id, "week": s.week, "module": s.module,
        "module_name": MODULES.get(s.module, s.module),
        "topic": s.topic, "slot": s.slot,
        "class_time": s.class_time.strftime("%Y-%m-%d %H:%M") if s.class_time else "",
        "claimed_by": s.claimed_by, "claimer_name": claimer_name or "",
        "status": s.status, "note": s.note or "",
    }


def build_sessions_payload():
    d = db()
    rows = d.query(CourseSession).order_by(CourseSession.week, CourseSession.slot).all()
    users = {u.id: u.display_name for u in d.query(User).all()}
    return [serialize_session(s, users.get(s.claimed_by)) for s in rows]


# ---------------- 鉴权 ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""
        d = db()
        u = d.query(User).filter_by(username=username).first()
        if u and u.active and check_password_hash(u.password_hash, password):
            session["user_id"] = u.id
            session["must_change_pw"] = u.must_change_pw
            flash("登录成功，欢迎 " + u.display_name, "success")
            return redirect(url_for("dashboard"))
        flash("用户名或密码错误，或账号已停用", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/change-password", methods=["POST"])
@login_required
def change_password():
    u = g.user
    old = request.form.get("old_password", "")
    new = request.form.get("new_password", "")
    if not check_password_hash(u.password_hash, old):
        flash("原密码不正确", "danger")
        return redirect(request.referrer or url_for("dashboard"))
    if len(new) < 6:
        flash("新密码至少 6 位", "danger")
        return redirect(request.referrer or url_for("dashboard"))
    d = db()
    u2 = d.get(User, u.id)
    u2.password_hash = generate_password_hash(new)
    u2.must_change_pw = False
    d.commit()
    session["must_change_pw"] = False
    flash("密码已修改", "success")
    return redirect(url_for("dashboard"))


# ---------------- 页面 ----------------
@app.route("/")
@login_required
def dashboard():
    d = db()
    total = d.query(func.count(CourseSession.id)).scalar()
    claimed = d.query(func.count(CourseSession.id)).filter(
        CourseSession.status == "claimed").scalar()
    by_module = {}
    for code in MODULE_ORDER:
        t = d.query(func.count(CourseSession.id)).filter(
            CourseSession.module == code).scalar()
        c = d.query(func.count(CourseSession.id)).filter(
            CourseSession.module == code,
            CourseSession.status == "claimed").scalar()
        by_module[code] = {"name": MODULES[code], "total": t, "claimed": c}
    recent = d.query(ActivityLog).order_by(
        ActivityLog.created_at.desc()).limit(12).all()
    users = {u.id: u.display_name for u in d.query(User).all()}
    return render_template(
        "dashboard.html", total=total, claimed=claimed, by_module=by_module,
        recent=recent, users=users,
    )


@app.route("/schedule")
@login_required
def schedule():
    return render_template(
        "schedule.html", supabase_url=SUPABASE_URL,
        supabase_anon_key=SUPABASE_ANON_KEY,
    )


@app.route("/admin")
@login_required
@admin_required
def admin():
    d = db()
    users = d.query(User).order_by(User.role, User.id).all()
    return render_template("admin.html", users=users)


# ---------------- API ----------------
@app.route("/api/sessions")
@login_required
def api_sessions():
    return jsonify(build_sessions_payload())


@app.route("/api/activity")
@login_required
def api_activity():
    d = db()
    rows = d.query(ActivityLog).order_by(
        ActivityLog.created_at.desc()).limit(30).all()
    users = {u.id: u.display_name for u in d.query(User).all()}
    out = [{
        "id": r.id, "message": r.message,
        "user": users.get(r.user_id, "系统"),
        "created_at": r.created_at.strftime("%m-%d %H:%M"),
    } for r in rows]
    return jsonify(out)


@app.route("/api/claim", methods=["POST"])
@login_required
def api_claim():
    data = request.get_json(silent=True) or {}
    sid = data.get("session_id")
    action = data.get("action")
    u = g.user
    d = db()
    s = d.get(CourseSession, sid)
    if not s:
        return jsonify({"ok": False, "msg": "席位不存在"}), 404

    if action == "claim":
        if s.status == "claimed" and s.claimed_by != u.id:
            return jsonify({"ok": False, "msg": "该席位已被其他人认领"}), 409
        if s.status == "locked" and u.role != "admin":
            return jsonify({"ok": False, "msg": "该席位已锁定，需管理员改派"}), 403
        if u.role == "ta" and u.claim_scope and s.module not in u.claim_scope:
            return jsonify({"ok": False, "msg": f"你无权认领「{MODULES.get(s.module)}」模块"}), 403
        s.claimed_by = u.id
        s.status = "claimed"
        d.add(ClaimHistory(session_id=s.id, user_id=u.id, action="claim"))
        d.add(ActivityLog(
            user_id=u.id,
            message=f"{u.display_name} 认领了 第{s.week}周 {s.slot}《{s.topic}》"))
    elif action == "release":
        if s.claimed_by != u.id and u.role != "admin":
            return jsonify({"ok": False, "msg": "只能释放自己认领的席位"}), 403
        s.claimed_by = None
        s.status = "open"
        d.add(ClaimHistory(session_id=s.id, user_id=u.id, action="release"))
        d.add(ActivityLog(
            user_id=u.id,
            message=f"{u.display_name} 释放了 第{s.week}周 {s.slot}《{s.topic}》"))
    else:
        return jsonify({"ok": False, "msg": "未知操作"}), 400

    d.commit()
    return jsonify({"ok": True, "session": serialize_session(
        s, u.display_name if s.claimed_by == u.id else "")})


# ---- 管理员：账号与权限 ----
@app.route("/api/admin/user", methods=["POST"])
@login_required
@admin_required
def admin_create_user():
    data = request.get_json(silent=True) or {}
    uname = (data.get("username") or "").strip().lower()
    dname = data.get("display_name") or uname
    pw = data.get("password") or "Ta@2026snail"
    d = db()
    if d.query(User).filter_by(username=uname).first():
        return jsonify({"ok": False, "msg": "用户名已存在"}), 409
    d.add(User(
        username=uname, display_name=dname, role="ta",
        password_hash=generate_password_hash(pw), claim_scope=[],
        must_change_pw=True))
    d.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/user/<int:uid>/scope", methods=["POST"])
@login_required
@admin_required
def admin_set_scope(uid):
    data = request.get_json(silent=True) or {}
    scope = data.get("scope", [])
    d = db()
    u = d.get(User, uid)
    if not u:
        return jsonify({"ok": False, "msg": "用户不存在"}), 404
    u.claim_scope = list(scope)
    d.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/user/<int:uid>/reset", methods=["POST"])
@login_required
@admin_required
def admin_reset_pw(uid):
    data = request.get_json(silent=True) or {}
    pw = data.get("password") or "Ta@2026snail"
    d = db()
    u = d.get(User, uid)
    if not u:
        return jsonify({"ok": False, "msg": "用户不存在"}), 404
    u.password_hash = generate_password_hash(pw)
    u.must_change_pw = True
    d.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/user/<int:uid>/toggle", methods=["POST"])
@login_required
@admin_required
def admin_toggle(uid):
    d = db()
    u = d.get(User, uid)
    if not u:
        return jsonify({"ok": False, "msg": "用户不存在"}), 404
    if u.role == "admin":
        return jsonify({"ok": False, "msg": "不能停用管理员"}), 403
    u.active = not u.active
    d.commit()
    return jsonify({"ok": True, "active": u.active})


@app.route("/healthz")
def healthz():
    """诊断接口：数据库连通性 + 账号/席位数（不含敏感信息）"""
    info = {"ok": True, "db": False, "users": None, "sessions": None}
    try:
        d = db()
        info["db"] = True
        info["users"] = d.query(User).count()
        info["sessions"] = d.query(CourseSession).count()
        d.close()
    except Exception as e:  # noqa: BLE001
        info["error"] = str(e)[:200]
    return jsonify(info)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)))
