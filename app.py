from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Pipeline, Defect
from analytics import DefectAnalyzer
import pandas as pd
import os
from werkzeug.utils import secure_filename
from werkzeug.utils import redirect

# Импорт для админ-панели
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)

# Конфигурация
app.config['SECRET_KEY'] = 'gazprom-super-secret-key-2024'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ISPr25-24_LinkovNI:ISPr25-24_LinkovNI@cfif31.ru:3306/ISPr25-24_LinkovNI_pipeline_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========== АДМИН-ПАНЕЛЬ ==========
class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect('/login')

# Убрал template_mode - он не поддерживается в вашей версии
admin = Admin(app, name='ВТД Админ')
admin.add_view(AdminModelView(Pipeline, db.session))
admin.add_view(AdminModelView(Defect, db.session))
admin.add_view(AdminModelView(User, db.session))
# ==================================

# Настройки загрузки
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Создание таблиц и тестовых данных
with app.app_context():
    db.create_all()
    
    if User.query.count() == 0:
        admin_user = User(username='admin', email='admin@gazprom.ru', role='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        normal_user = User(username='user', email='user@gazprom.ru', role='user')
        normal_user.set_password('user123')
        db.session.add(normal_user)
        
        db.session.commit()
        print("✅ Созданы тестовые пользователи:")
        print("   Админ: admin / admin123")
        print("   Пользователь: user / user123")
    
    if Pipeline.query.count() == 0:
        pipeline1 = Pipeline(name="Газопровод 'Уренгой-Помары-Ужгород'", length_km=4451)
        pipeline2 = Pipeline(name="Газопровод 'Ямал-Европа'", length_km=2000)
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.commit()
        print("✅ Созданы тестовые трубопроводы")

# ==================== АВТОРИЗАЦИЯ ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

# ==================== ОСНОВНЫЕ МАРШРУТЫ ====================
@app.route('/')
@login_required
def index():
    pipelines = Pipeline.query.all()
    defects_count = Defect.query.count()
    risk_stats = {
        'critical': Defect.query.filter_by(risk_level='КРИТИЧЕСКИЙ').count(),
        'high': Defect.query.filter_by(risk_level='ВЫСОКИЙ').count(),
        'medium': Defect.query.filter_by(risk_level='СРЕДНИЙ').count(),
        'low': Defect.query.filter_by(risk_level='НИЗКИЙ').count()
    }
    return render_template('index.html', 
                         pipelines=pipelines,
                         defects_count=defects_count,
                         risk_stats=risk_stats,
                         is_admin=current_user.is_admin())

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_data():
    if not current_user.is_admin():
        flash('Доступ запрещен. Только администраторы могут загружать данные.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Нет файла', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Файл не выбран', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            df = pd.read_csv(filepath, encoding='utf-8')
            pipeline_id = request.form.get('pipeline_id', 1)
            
            count = 0
            for _, row in df.iterrows():
                defect_type = row.get('defect_type', 'коррозия')
                depth_mm = float(row.get('depth_mm', 0))
                length_mm = float(row.get('length_mm', 0))
                width_mm = float(row.get('width_mm', 0)) if 'width_mm' in row else None
                km = float(row.get('km', 0))
                
                risk_level, risk_score, recommendation = DefectAnalyzer.analyze_defect(
                    defect_type, depth_mm, length_mm, width_mm
                )
                
                defect = Defect(
                    pipeline_id=pipeline_id,
                    km=km,
                    defect_type=defect_type,
                    depth_mm=depth_mm,
                    length_mm=length_mm,
                    width_mm=width_mm,
                    risk_level=risk_level,
                    risk_score=risk_score,
                    recommendation=recommendation
                )
                db.session.add(defect)
                count += 1
            
            db.session.commit()
            flash(f'Успешно загружено {count} дефектов!', 'success')
            return redirect(url_for('defects_list'))
    
    pipelines = Pipeline.query.all()
    return render_template('upload.html', pipelines=pipelines, is_admin=current_user.is_admin())

@app.route('/defects')
@login_required
def defects_list():
    defects = Defect.query.order_by(Defect.risk_score.desc()).all()
    return render_template('defects.html', defects=defects, is_admin=current_user.is_admin())

@app.route('/defects/delete/<int:defect_id>')
@login_required
def delete_defect(defect_id):
    if not current_user.is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('defects_list'))
    
    defect = Defect.query.get_or_404(defect_id)
    db.session.delete(defect)
    db.session.commit()
    flash('Дефект удален', 'success')
    return redirect(url_for('defects_list'))

@app.route('/defects/edit/<int:defect_id>', methods=['GET', 'POST'])
@login_required
def edit_defect(defect_id):
    if not current_user.is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('defects_list'))
    
    defect = Defect.query.get_or_404(defect_id)
    
    if request.method == 'POST':
        defect.km = float(request.form.get('km'))
        defect.defect_type = request.form.get('defect_type')
        defect.depth_mm = float(request.form.get('depth_mm'))
        defect.length_mm = float(request.form.get('length_mm'))
        defect.risk_level = request.form.get('risk_level')
        defect.recommendation = request.form.get('recommendation')
        
        db.session.commit()
        flash('Дефект обновлен', 'success')
        return redirect(url_for('defects_list'))
    
    return render_template('edit_defect.html', defect=defect, is_admin=current_user.is_admin())

@app.route('/pipelines')
@login_required
def pipelines_list():
    if not current_user.is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    pipelines = Pipeline.query.all()
    return render_template('pipelines.html', pipelines=pipelines, is_admin=current_user.is_admin())

@app.route('/pipelines/add', methods=['GET', 'POST'])
@login_required
def add_pipeline():
    if not current_user.is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        length_km = float(request.form.get('length_km'))
        
        pipeline = Pipeline(name=name, length_km=length_km)
        db.session.add(pipeline)
        db.session.commit()
        flash('Трубопровод добавлен', 'success')
        return redirect(url_for('pipelines_list'))
    
    return render_template('add_pipeline.html', is_admin=current_user.is_admin())

@app.route('/pipelines/delete/<int:pipeline_id>')
@login_required
def delete_pipeline(pipeline_id):
    if not current_user.is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    db.session.delete(pipeline)
    db.session.commit()
    flash('Трубопровод удален', 'success')
    return redirect(url_for('pipelines_list'))

@app.route('/report')
@login_required
def report():
    defects = Defect.query.order_by(Defect.risk_score.desc()).all()
    pipeline = Pipeline.query.first()
    return render_template('report.html', defects=defects, pipeline=pipeline, is_admin=current_user.is_admin())

@app.route('/api/defects')
@login_required
def api_defects():
    defects = Defect.query.all()
    return jsonify([defect.to_dict() for defect in defects])

if __name__ == '__main__':
    app.run(debug=True)
    import plotly.graph_objs as go
import plotly.utils
import json

@app.route('/charts_data')
@login_required
def charts_data():
    defects = Defect.query.all()
    
    # Данные для графика
    risk_counts = {
        'КРИТИЧЕСКИЙ': 0,
        'ВЫСОКИЙ': 0,
        'СРЕДНИЙ': 0,
        'НИЗКИЙ': 0
    }
    type_counts = {}
    km_data = []
    
    for d in defects:
        risk_counts[d.risk_level] = risk_counts.get(d.risk_level, 0) + 1
        type_counts[d.defect_type] = type_counts.get(d.defect_type, 0) + 1
        km_data.append({'km': d.km, 'risk': d.risk_level, 'type': d.defect_type})
    
    return jsonify({
        'risk_counts': risk_counts,
        'type_counts': type_counts,
        'km_data': km_data
    })
