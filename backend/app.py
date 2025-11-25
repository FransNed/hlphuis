import os
from flask import Flask, request, jsonify, send_from_directory, Response
import csv
import io
from datetime import datetime
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from backend.models import db, User, Lesson


def create_app():
    app = Flask(__name__, static_folder=None)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    # ensure instance folder exists
    instance_dir = os.path.join(base_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    db_path = os.path.join(instance_dir, 'hlphuis.sqlite')
    app.config['SECRET_KEY'] = os.environ.get('HLPHUIS_SECRET', 'dev-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    def admin_required(fn):
        from functools import wraps

        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'ok': False, 'error': 'authentication required'}), 401
            if not getattr(current_user, 'is_admin', False):
                return jsonify({'ok': False, 'error': 'admin required'}), 403
            return fn(*args, **kwargs)

        return wrapper

    @app.route('/api/login', methods=['POST'])
    def api_login():
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({'ok': False, 'error': 'email and password required'}), 400
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'ok': True, 'email': user.email, 'id': user.id})
        return jsonify({'ok': False, 'error': 'invalid credentials'}), 401

    @app.route('/api/logout', methods=['POST'])
    @login_required
    def api_logout():
        logout_user()
        return jsonify({'ok': True})

    @app.route('/api/lessons', methods=['GET'])
    def list_lessons():
        user_id = request.args.get('user_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        q = Lesson.query
        if user_id:
            try:
                uid = int(user_id)
                q = q.filter(Lesson.user_id == uid)
            except Exception:
                pass
        # filter by date range (date stored as YYYY-MM-DD string)
        if from_date:
            try:
                datetime.strptime(from_date, '%Y-%m-%d')
                q = q.filter(Lesson.date >= from_date)
            except Exception:
                pass
        if to_date:
            try:
                datetime.strptime(to_date, '%Y-%m-%d')
                q = q.filter(Lesson.date <= to_date)
            except Exception:
                pass
        lessons = q.order_by(Lesson.created_at.desc()).all()
        out = [
            {
                'id': l.id,
                'date': l.date,
                'customer_name': l.customer_name,
                'amount': str(l.amount),
                'created_at': l.created_at.isoformat(),
                'user_id': l.user_id,
                'user_name': l.user.name if l.user else None,
            }
            for l in lessons
        ]
        return jsonify({'ok': True, 'lessons': out})

    @app.route('/api/lessons', methods=['POST'])
    @login_required
    def create_lesson():
        data = request.get_json() or {}
        date = data.get('date')
        customer = data.get('customer_name')
        amount = data.get('amount')
        # Basic validation: require all fields
        if not date or not customer or amount is None:
            return jsonify({'ok': False, 'error': 'missing fields (required: date, customer_name, amount)'}), 400
        # Validate date format (ISO YYYY-MM-DD)
        try:
            parsed = datetime.strptime(date, '%Y-%m-%d')
            date = parsed.strftime('%Y-%m-%d')
        except Exception:
            return jsonify({'ok': False, 'error': 'invalid date format. Use YYYY-MM-DD (e.g. 2025-01-12)'}), 400
        # Validate amount is numeric
        try:
            amount = float(amount)
        except Exception:
            return jsonify({'ok': False, 'error': 'invalid amount format. Use a number, e.g. 12.50'}), 400

        # attach to user: either passed user_id (admin) or current_user
        user_id = data.get('user_id')
        if user_id is None:
            user_id = current_user.id
        else:
            try:
                user_id = int(user_id)
            except Exception:
                user_id = current_user.id

        lesson = Lesson(date=date, customer_name=customer, amount=amount, user_id=user_id)
        db.session.add(lesson)
        db.session.commit()
        return jsonify({'ok': True, 'id': lesson.id})

    @app.route('/api/users_simple', methods=['GET'])
    @login_required
    def users_simple():
        users = User.query.order_by(User.name).all()
        out = [{'id': u.id, 'username': u.username, 'name': u.name} for u in users]
        return jsonify({'ok': True, 'users': out})

    @app.route('/api/users', methods=['GET'])
    @admin_required
    def list_users():
        users = User.query.order_by(User.created_at.desc()).all()
        out = [
            {'id': u.id, 'email': u.email, 'username': u.username, 'name': u.name, 'description': u.description, 'is_admin': bool(u.is_admin)}
            for u in users
        ]
        return jsonify({'ok': True, 'users': out})

    @app.route('/api/users', methods=['POST'])
    @admin_required
    def create_user():
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        description = data.get('description')
        is_admin = bool(data.get('is_admin', False))
        if not email or not password:
            return jsonify({'ok': False, 'error': 'email and password required'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'ok': False, 'error': 'email exists'}), 400
        # keep username for backward compatibility; set to email localpart if empty
        username = data.get('username') or email.split('@')[0]
        u = User(username=username, email=email, name=name, description=description, is_admin=is_admin)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return jsonify({'ok': True, 'id': u.id})

    @app.route('/api/users/<int:user_id>', methods=['PUT'])
    @login_required
    def update_user(user_id):
        data = request.get_json() or {}
        u = User.query.get(user_id)
        if not u:
            return jsonify({'ok': False, 'error': 'user not found'}), 404
        # only admin or the user themself can update
        if not (current_user.is_admin or current_user.id == u.id):
            return jsonify({'ok': False, 'error': 'forbidden'}), 403
        u.name = data.get('name', u.name)
        u.description = data.get('description', u.description)
        # allow updating email (admin or owner)
        new_email = data.get('email')
        if new_email:
            # ensure uniqueness
            exists = User.query.filter(User.email == new_email, User.id != u.id).first()
            if exists:
                return jsonify({'ok': False, 'error': 'email already in use'}), 400
            u.email = new_email
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/users/<int:user_id>/password', methods=['POST'])
    @login_required
    def change_password(user_id):
        data = request.get_json() or {}
        new_password = data.get('new_password')
        old_password = data.get('old_password')
        if not new_password:
            return jsonify({'ok': False, 'error': 'new_password required'}), 400
        u = User.query.get(user_id)
        if not u:
            return jsonify({'ok': False, 'error': 'user not found'}), 404
        # if current user updating own password, verify old_password
        if current_user.id == u.id and not current_user.is_admin:
            if not old_password or not u.check_password(old_password):
                return jsonify({'ok': False, 'error': 'old password incorrect'}), 403
        # admin can reset without old_password
        u.set_password(new_password)
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/lessons/export', methods=['GET'])
    @login_required
    def export_lessons():
        user_id = request.args.get('user_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        q = Lesson.query
        if user_id:
            try:
                q = q.filter(Lesson.user_id == int(user_id))
            except Exception:
                pass
        if from_date:
            try:
                datetime.strptime(from_date, '%Y-%m-%d')
                q = q.filter(Lesson.date >= from_date)
            except Exception:
                pass
        if to_date:
            try:
                datetime.strptime(to_date, '%Y-%m-%d')
                q = q.filter(Lesson.date <= to_date)
            except Exception:
                pass
        lessons = q.order_by(Lesson.created_at.desc()).all()

        # create CSV
        out_io = io.StringIO()
        writer = csv.writer(out_io)
        writer.writerow(['user_id', 'user_name', 'date', 'customer_name', 'amount', 'created_at'])
        for l in lessons:
            writer.writerow([l.user_id or '', (l.user.name if l.user else ''), l.date, l.customer_name, str(l.amount), l.created_at.isoformat()])
        csv_data = out_io.getvalue()
        return Response(csv_data, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename="lessons.csv"'})

    # Serve frontend files from ../frontend when available (for easy local testing)
    @app.route('/', defaults={'path': 'index.html'})
    @app.route('/<path:path>')
    def frontend(path):
        frontend_dir = os.path.abspath(os.path.join(base_dir, '..', 'frontend'))
        if os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        return jsonify({'ok': False, 'error': 'not found'}), 404

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
