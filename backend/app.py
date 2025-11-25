import os
from flask import Flask, request, jsonify, send_from_directory
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

    @app.route('/api/login', methods=['POST'])
    def api_login():
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({'ok': False, 'error': 'username and password required'}), 400
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'ok': True, 'username': user.username})
        return jsonify({'ok': False, 'error': 'invalid credentials'}), 401

    @app.route('/api/logout', methods=['POST'])
    @login_required
    def api_logout():
        logout_user()
        return jsonify({'ok': True})

    @app.route('/api/lessons', methods=['GET'])
    def list_lessons():
        lessons = Lesson.query.order_by(Lesson.created_at.desc()).all()
        out = [
            {'id': l.id, 'date': l.date, 'customer_name': l.customer_name, 'amount': str(l.amount), 'created_at': l.created_at.isoformat()}
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
        if not date or not customer or amount is None:
            return jsonify({'ok': False, 'error': 'missing fields'}), 400
        lesson = Lesson(date=date, customer_name=customer, amount=amount)
        db.session.add(lesson)
        db.session.commit()
        return jsonify({'ok': True, 'id': lesson.id})

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
