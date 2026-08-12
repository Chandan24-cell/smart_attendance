import smtplib
import csv
import io
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from models import db, Student, AttendanceRecord, AttendanceSession, Setting

def get_setting(key, default=""):
    s = Setting.query.filter_by(setting_key=key).first()
    return s.setting_value if s and s.setting_value else default

def build_30day_report():
    since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    rows = db.session.query(AttendanceRecord, AttendanceSession, Student)\
        .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.session_id)\
        .join(Student, AttendanceRecord.student_id == Student.student_id)\
        .filter(AttendanceSession.session_date >= since)\
        .order_by(AttendanceSession.session_date, AttendanceRecord.attendance_id).all()

    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["date", "period", "roll_no", "student_name", "status", "detected_time", "method"])
    for r, s, st in rows:
        w.writerow([s.session_date, f"P{s.period_number}", st.roll_no,
                    st.student_name, r.status, r.detected_time or "", r.method])
    return output.getvalue(), len(rows)

def send_30day_report():
    smtp_user = get_setting("smtp_email")
    smtp_pass = get_setting("smtp_password")
    to_addr = get_setting("report_email_to")

    if not (smtp_user and smtp_pass and to_addr):
        return False, "❌ Email settings missing. Save them on the Reports page first."

    csv_data, count = build_30day_report()

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_addr
    msg["Subject"] = f"Smart Attendance — 30-Day Report ({datetime.now().strftime('%d %b %Y')})"
    msg.attach(MIMEText(
        f"Hello,\n\nPlease find attached the complete attendance report for the last 30 days.\n"
        f"Total records: {count}\n\n— Smart Attendance System (AI Automated)"))

    part = MIMEBase("application", "octet-stream")
    part.set_payload(csv_data.encode())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename=attendance_30days.csv")
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_addr, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        return False, "❌ Login failed! Gmail requires an **App Password** (not your normal password). Please generate one from Google Account settings and update it below."
    except Exception as e:
        return False, f"❌ Email sending failed: {str(e)}"

    return True, f"✅ 30-day report sent to {to_addr} ({count} records)."


def check_auto_report():
    """Automatically sends the report once every 30 days."""
    today = datetime.now()
    last = get_setting("last_report_date")
    if last:
        if (today - datetime.strptime(last, "%Y-%m-%d")).days < 30:
            return
    ok, msg = send_30day_report()
    print(msg)
    if ok:
        s = Setting.query.filter_by(setting_key="last_report_date").first()
        if s:
            s.setting_value = today.strftime("%Y-%m-%d")
        else:
            db.session.add(Setting(setting_key="last_report_date",
                                   setting_value=today.strftime("%Y-%m-%d")))
        db.session.commit()
