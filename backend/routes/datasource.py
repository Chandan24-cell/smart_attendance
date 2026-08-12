from flask import Blueprint, flash, redirect, render_template, request, url_for

from backend.models import Setting, SyncLog, db
from backend.routes.utils import require_login, save_setting
from backend.services.sync_service import sync_students, sync_timetable

datasource_bp = Blueprint("datasource", __name__)


@datasource_bp.route("/datasource", methods=["GET", "POST"])
def datasource_page():
    if not require_login():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        for key in ["student_sheet_link", "timetable_sheet_link"]:
            value = request.form.get(key, "").strip()
            if value:
                save_setting(key, value)
        db.session.commit()
        flash("✅ Sheet links saved! Now click the Sync buttons.", "success")
        return redirect(url_for("datasource.datasource_page"))

    st = Setting.query.filter_by(setting_key="student_sheet_link").first()
    tt = Setting.query.filter_by(setting_key="timetable_sheet_link").first()
    logs = SyncLog.query.order_by(SyncLog.sync_id.desc()).limit(10).all()

    return render_template("datasource.html", student_link=st.setting_value if st else "",
                           timetable_link=tt.setting_value if tt else "", logs=logs)


@datasource_bp.route("/sync_data")
def sync_data():
    if not require_login():
        return redirect(url_for("auth.login"))
    s_res = sync_students()
    t_res = sync_timetable()
    flash(f"Sync Complete! Students: {s_res['added']} added, {s_res['updated']} updated. | Periods: {t_res['added']} added, {t_res['updated']} updated.", "success")
    return redirect(url_for("dashboard.dashboard"))


@datasource_bp.route("/sync_students_only")
def sync_students_route():
    if not require_login():
        return redirect(url_for("auth.login"))
    r = sync_students()
    flash(f"Students synced → added: {r['added']}, updated: {r['updated']}, errors: {r['errors']}", "success")
    return redirect(url_for("datasource.datasource_page"))


@datasource_bp.route("/sync_timetable_only")
def sync_timetable_route():
    if not require_login():
        return redirect(url_for("auth.login"))
    r = sync_timetable()
    flash(f"Timetable synced → added: {r['added']}, updated: {r['updated']}, errors: {r['errors']}", "success")
    return redirect(url_for("datasource.datasource_page"))
