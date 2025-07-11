# app.py

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from extensions import db, migrate

# ======================================================================
#  ส่วนสร้าง Flask App และตั้งค่า
# ======================================================================
def create_app():
    app = Flask(__name__)

    # --- START: ส่วนที่แก้ไขเพื่อรองรับการ Deployment ---
    # ตั้งค่าฐานข้อมูล: ใช้ DATABASE_URL จาก Environment Variable ถ้ามี,
    # ถ้าไม่มี (ตอนรันบนเครื่องตัวเอง) ให้ใช้ sqlite:///site.db เป็นค่าเริ่มต้น
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')

    # สำหรับ Render Disk ที่เราจะใช้กับ SQLite หรือการรันบนเครื่อง
    # เราจะปรับ path ให้เก็บไฟล์ db ไว้ในโฟลเดอร์ instance
    if database_url.startswith('sqlite:///'):
        # สร้างโฟลเดอร์ instance ถ้ายังไม่มีอยู่
        # os.path.dirname(os.path.abspath(__file__)) คือ path ของไดเรกทอรีที่ไฟล์ app.py อยู่
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        # สร้าง path เต็มไปยังไฟล์ database ในโฟลเดอร์ instance
        db_name = database_url.split('///')[1] # ดึงชื่อไฟล์ db ออกมา (เช่น site.db)
        database_url = f"sqlite:///{os.path.join(instance_path, db_name)}"

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ตั้งค่า Secret Key จาก Environment Variable เพื่อความปลอดภัย
    # หากไม่พบค่าใน Environment Variable จะใช้ค่า default (เหมาะสำหรับตอนพัฒนา)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_development')
    # --- END: ส่วนที่แก้ไข ---

    db.init_app(app)
    migrate.init_app(app, db)

    from models import Chanda, syllabify_and_analyze, analyze_prosody, identify_chanda_logic

    # ======================================================================
    #  ส่วนของ Web Server (Routes)
    # ======================================================================
    @app.route('/')
    def index():
        chandas_from_db = Chanda.query.order_by(Chanda.syllable_count).all()
        chandas_dict = {c.chanda_id: {"name": c.name, "pattern": c.pattern, "syllable_count": c.syllable_count, "type": c.chanda_type, "description_short": c.description_short, "pariyat_url": c.pariyat_url} for c in chandas_from_db}
        return render_template('index.html', chandas=chandas_dict)

    @app.route('/analyzer/<chanda_id>')
    def analyzer_page(chanda_id):
        chanda_info = Chanda.query.filter_by(chanda_id=chanda_id).first()
        if not chanda_info: return "ไม่พบฉันท์ที่ระบุ", 404
        chanda_data = {"name": chanda_info.name, "pattern": chanda_info.pattern, "syllable_count": chanda_info.syllable_count, "type": chanda_info.chanda_type, "description_short": chanda_info.description_short, "pariyat_url": chanda_info.pariyat_url}
        return render_template('analyzer.html', chanda=chanda_data, chanda_id=chanda_id)

    @app.route('/identify_chanda')
    def identify_chanda_page():
        return render_template('identify_chanda.html')

    # ======================================================================
    #  API สำหรับวิเคราะห์ (ใช้ทั้งการแบ่งพยางค์เริ่มต้น และวิเคราะห์ซ้ำ)
    # ======================================================================
    @app.route('/api/analyze', methods=['POST'])
    def analyze_api():
        data = request.get_json()
        if not data or 'verses' not in data or not isinstance(data['verses'], list):
            return jsonify({'error': 'Invalid input, expected a list of verses.'}), 400

        results_by_verse = []
        if all(isinstance(v, str) for v in data['verses']):
            for verse_text in data['verses']:
                syllables = syllabify_and_analyze(verse_text)
                results_by_verse.append(syllables)
        elif all(isinstance(v, list) and all(isinstance(s, str) for s in v) for v in data['verses']):
            for verse_syllables_list in data['verses']:
                analyzed_syllables = analyze_prosody(verse_syllables_list)
                results_by_verse.append(analyzed_syllables)
        else:
            return jsonify({'error': 'Invalid input format.'}), 400

        return jsonify(results_by_verse)

    @app.route('/api/identify_chanda', methods=['POST'])
    def identify_chanda_api():
        data = request.get_json()
        if not data or 'verses' not in data or not isinstance(data['verses'], list):
            return jsonify({'error': 'Invalid input, expected a list of verses.'}), 400

        if not all(isinstance(v, list) and all(isinstance(s, str) for s in v) for v in data['verses']):
             return jsonify({'error': 'Invalid input format. Expected a list of lists of syllables.'}), 400

        prosody_results_by_verse = []
        for verse_syllables_list in data['verses']:
            analyzed_syllables = analyze_prosody(verse_syllables_list)
            prosody_results_by_verse.append(analyzed_syllables)

        identification_results = identify_chanda_logic(prosody_results_by_verse, db, Chanda)

        return jsonify({
            "identification": identification_results,
            "prosody_results": prosody_results_by_verse
        })

    # ======================================================================
    #  Admin Panel Routes
    # ======================================================================
    @app.route('/admin')
    def admin_home():
        chandas = Chanda.query.order_by(Chanda.syllable_count).all()
        return render_template('admin/index.html', chandas=chandas)

    @app.route('/admin/add', methods=['GET', 'POST'])
    def admin_add_chanda():
        if request.method == 'POST':
            chanda_id = request.form['chanda_id']
            name = request.form['name']
            pattern = request.form['pattern']
            syllable_count = int(request.form['syllable_count'])
            chanda_type = request.form['chanda_type']
            description_short = request.form['description_short']
            pariyat_url = request.form['pariyat_url']

            existing_chanda = Chanda.query.filter_by(chanda_id=chanda_id).first()
            if existing_chanda:
                flash(f"ข้อผิดพลาด: Chanda ID '{chanda_id}' นี้มีอยู่แล้ว กรุณาใช้ ID อื่น หรือไปแก้ไขข้อมูลเดิม", 'danger')
                return render_template('admin/add.html',
                                       chanda_id=chanda_id, name=name, pattern=pattern,
                                       syllable_count=syllable_count, chanda_type=chanda_type,
                                       description_short=description_short, pariyat_url=pariyat_url)

            new_chanda = Chanda(chanda_id=chanda_id, name=name, pattern=pattern,
                                syllable_count=syllable_count, chanda_type=chanda_type,
                                description_short=description_short, pariyat_url=pariyat_url)
            db.session.add(new_chanda)
            db.session.commit()
            flash(f"เพิ่มฉันท์ '{name}' สำเร็จแล้ว!", 'success')
            return redirect(url_for('admin_home'))
        return render_template('admin/add.html', chanda_id='', name='', pattern='', syllable_count='', chanda_type='vutta', description_short='', pariyat_url='')

    @app.route('/admin/edit/<string:chanda_id>', methods=['GET', 'POST'])
    def admin_edit_chanda(chanda_id):
        chanda_to_edit = Chanda.query.filter_by(chanda_id=chanda_id).first_or_404()
        if request.method == 'POST':
            chanda_to_edit.name = request.form['name']
            chanda_to_edit.pattern = request.form['pattern']
            chanda_to_edit.syllable_count = int(request.form['syllable_count'])
            chanda_to_edit.chanda_type = request.form['chanda_type']
            chanda_to_edit.description_short = request.form['description_short']
            chanda_to_edit.pariyat_url = request.form['pariyat_url']
            db.session.commit()
            flash(f"แก้ไขฉันท์ '{chanda_to_edit.name}' สำเร็จแล้ว!", 'success')
            return redirect(url_for('admin_home'))
        return render_template('admin/edit.html', chanda=chanda_to_edit)

    @app.route('/admin/delete/<string:chanda_id>', methods=['POST'])
    def admin_delete_chanda(chanda_id):
        chanda_to_delete = Chanda.query.filter_by(chanda_id=chanda_id).first_or_404()
        db.session.delete(chanda_to_delete)
        db.session.commit()
        flash(f"ลบฉันท์ '{chanda_to_delete.name}' สำเร็จแล้ว!", 'success')
        return redirect(url_for('admin_home'))

    return app

# เพิ่มส่วนนี้เพื่อให้สามารถรันไฟล์ app.py โดยตรงได้ (สำหรับการทดสอบบนเครื่อง)
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)