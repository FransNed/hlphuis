import os
import argparse
from backend.models import db, User
from backend.app import create_app


def create_database(create_admin: bool = False, admin_user: str = 'admin', admin_pass: str = 'admin'):
    app = create_app()
    with app.app_context():
        # ensure instance folder exists
        try:
            os.makedirs(app.instance_path, exist_ok=True)
        except Exception:
            pass
        db.init_app(app)
        db.create_all()
        if create_admin:
            if not User.query.filter_by(username=admin_user).first():
                u = User(username=admin_user)
                u.set_password(admin_pass)
                db.session.add(u)
                db.session.commit()
                print(f"Created admin user: {admin_user}")
            else:
                print("Admin user already exists")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--create-admin', action='store_true')
    parser.add_argument('--admin-user', default='admin')
    parser.add_argument('--admin-pass', default='admin')
    args = parser.parse_args()
    create_database(args.create_admin, args.admin_user, args.admin_pass)
