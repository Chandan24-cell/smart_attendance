import pandas as pd
from models import db, Student, Subject, PeriodSchedule, SyncLog, Setting

def clean(v):
    """Convert cell to clean string (handles empty/NaN)."""
    if v is None:
        return ""
    if isinstance(v, float) and v != v:   # NaN check
        return ""
    return str(v).strip()

def extract_sheet_id(link):
    """Works with full URL or raw ID."""
    if "/d/" in link:
        return link.split("/d/")[1].split("/")[0]
    return link.strip()

def fetch_df(link):
    sheet_id = extract_sheet_id(link)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

def get_link(key):
    s = Setting.query.filter_by(setting_key=key).first()
    return s.setting_value if s and s.setting_value else None

def sync_students():
    link = get_link("student_sheet_link")
    if not link:
        return {"total": 0, "added": 0, "updated": 0, "skipped": 0, "errors": 0}

    df = fetch_df(link)
    added = updated = skipped = errors = 0

    for _, row in df.iterrows():
        try:
            name = clean(row.get("student_name"))
            roll = clean(row.get("roll_no"))
            reg = clean(row.get("registration_no"))
            if not name or not roll or not reg:
                skipped += 1
                continue

            st = Student.query.filter_by(roll_no=roll).first()
            if st:
                st.student_name = name
                st.registration_no = reg
                st.department = clean(row.get("department")) or st.department
                st.year = clean(row.get("year")) or st.year
                st.section = clean(row.get("section")) or st.section
                st.email = clean(row.get("email")) or st.email
                st.photo_status = clean(row.get("photo_status")) or st.photo_status
                updated += 1
            else:
                db.session.add(Student(
                    student_name=name, roll_no=roll, registration_no=reg,
                    department=clean(row.get("department")), year=clean(row.get("year")),
                    section=clean(row.get("section")), email=clean(row.get("email")),
                    photo_status=clean(row.get("photo_status"))))
                added += 1
        except Exception:
            errors += 1

    db.session.commit()
    db.session.add(SyncLog(source_type="Google Sheet", sync_type="Students",
                           sync_status="Success" if errors == 0 else "Partial",
                           total_rows_read=len(df), new_records_added=added,
                           records_updated=updated, records_skipped=skipped,
                           error_count=errors))
    db.session.commit()
    return {"total": len(df), "added": added, "updated": updated,
            "skipped": skipped, "errors": errors}

def sync_timetable():
    link = get_link("timetable_sheet_link")
    if not link:
        return {"total": 0, "added": 0, "updated": 0, "errors": 0}

    df = fetch_df(link)
    added = updated = errors = 0

    for _, row in df.iterrows():
        try:
            period_no = int(row["Period"])
            subject_name = clean(row["Subject"])
            start = clean(row["Start Time"])
            end = clean(row["End Time"])
            if not subject_name or not start or not end:
                errors += 1
                continue

            is_break = ("lunch" in subject_name.lower()) or ("break" in subject_name.lower())

            subj = Subject.query.filter_by(subject_name=subject_name).first()
            if not subj:
                subj = Subject(subject_name=subject_name)
                db.session.add(subj)
                db.session.flush()

            p = PeriodSchedule.query.filter_by(period_number=period_no).first()
            if p:
                p.subject_id = subj.subject_id
                p.start_time = start
                p.end_time = end
                p.is_break = is_break
                updated += 1
            else:
                db.session.add(PeriodSchedule(
                    period_number=period_no, subject_id=subj.subject_id,
                    start_time=start, end_time=end, is_break=is_break))
                added += 1
        except Exception:
            errors += 1

    db.session.commit()
    db.session.add(SyncLog(source_type="Google Sheet", sync_type="Timetable",
                           sync_status="Success" if errors == 0 else "Partial",
                           total_rows_read=len(df), new_records_added=added,
                           records_updated=updated, error_count=errors))
    db.session.commit()
    return {"total": len(df), "added": added, "updated": updated, "errors": errors}