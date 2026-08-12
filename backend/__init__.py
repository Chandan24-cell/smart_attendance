import os
from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

from backend.models import db
from config import DB_PATH, SECRET_KEY


def create_app():
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
    )
    template_dirs = [
        os.path.abspath(
            os.path.join(app.root_path, "..", "frontend", "templates")
        ),
        os.path.abspath(os.path.join(app.root_path, "..", "templates")),
    ]
    app.jinja_loader = ChoiceLoader(
        [FileSystemLoader(path) for path in template_dirs]
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = SECRET_KEY

    db.init_app(app)

    from backend.routes.auth import auth_bp
    from backend.routes.dashboard import dashboard_bp
    from backend.routes.students import students_bp
    from backend.routes.attendance import attendance_bp
    from backend.routes.records import records_bp
    from backend.routes.reports import reports_bp
    from backend.routes.datasource import datasource_bp
    from backend.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(datasource_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

        from backend.models import AdminUser, Setting
        from werkzeug.security import generate_password_hash

        if AdminUser.query.count() == 0:
            db.session.add(
                AdminUser(
                    name="System Admin",
                    username="admin",
                    password_hash=generate_password_hash("admin123"),
                    role="Admin",
                )
            )

        if Setting.query.count() == 0:
            db.session.add_all([
                Setting(
                    setting_key="default_grace_minutes",
                    setting_value="15",
                ),
                Setting(
                    setting_key="allow_admin_override",
                    setting_value="Yes",
                ),
                Setting(
                    setting_key="auto_mark_absent_after_period",
                    setting_value="Yes",
                ),
                Setting(
                    setting_key="sync_interval_minutes",
                    setting_value="5",
                ),
            ])
        default_settings = {
            "default_grace_minutes": "15",
            "allow_admin_override": "Yes",
            "auto_mark_absent_after_period": "Yes",
            "sync_interval_minutes": "5",
            "student_sheet_link": (
                "https://docs.google.com/spreadsheets/d/"
                "1oZpLnlg3hPvyvi0UNeJRyXKVbnQMngkVVaAJyJjflZY/edit"
            ),
            "timetable_sheet_link": (
                "https://docs.google.com/spreadsheets/d/"
                "107R1Q4578ujcrsFWI4sAYJwKC85ExA14hZVVVCYrNRI/edit"
            ),
        }
        for key, value in default_settings.items():
            if not Setting.query.filter_by(setting_key=key).first():
                db.session.add(Setting(setting_key=key, setting_value=value))
        db.session.commit()

    return app
