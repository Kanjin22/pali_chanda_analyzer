# app/admin/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Chanda, User, VerseExample, PoeticWord
import functools 

admin = Blueprint('admin', __name__)

# --- Decorator สำหรับตรวจสอบสิทธิ์ผู้ดูแลระบบ ---
def admin_required(f):
    @login_required 
    @functools.wraps(f) 
    def decorated_function(*args, **kwargs):
        if not current_user.is_administrator(): 
            flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้ โปรดเข้าสู่ระบบด้วยบัญชีผู้ดูแลระบบ', 'danger')
            return redirect(url_for('auth.login')) 
        return f(*args, **kwargs)
    return decorated_function


# --- Main admin dashboard ---
@admin.route('/')
@admin.route('/index') 
@admin_required 
def index(): 
    return render_template('admin/index.html', title='หน้าผู้ดูแลระบบ')

# --- Chanda Management ---
@admin.route('/chandas')
@admin_required 
def list_chandas():
    chandas = Chanda.query.order_by(Chanda.syllable_count, Chanda.name).all()
    return render_template('admin/list_chandas.html', chandas=chandas)

@admin.route('/chandas/add', methods=['GET', 'POST'])
@admin_required 
def add_chanda():
    if request.method == 'POST':
        name = request.form.get('name')
        pattern = request.form.get('pattern')
        syllable_count = request.form.get('syllable_count')
        description = request.form.get('description_short')
        pariyat_url = request.form.get('pariyat_url')

        existing_chanda = Chanda.query.filter_by(name=name).first()
        if existing_chanda:
            flash(f"ข้อผิดพลาด: ชื่อฉันท์ '{name}' นี้มีอยู่แล้วในระบบ", 'danger')
            return redirect(url_for('admin.add_chanda'))
        
        is_mixed_chanda = request.form.get('is_mixed_chanda') == 'on'

        if is_mixed_chanda:
            pattern_to_save = None 
        else:
            pattern_to_save = pattern 

        new_chanda = Chanda(
            name=name, 
            pattern=pattern_to_save, 
            syllable_count=int(syllable_count), 
            description_short=description, 
            pariyat_url=pariyat_url,
            is_mixed_chanda=is_mixed_chanda 
        )
        db.session.add(new_chanda)
        db.session.commit()
        flash(f"เพิ่มฉันท์ '{name}' สำเร็จ!", 'success')
        return redirect(url_for('admin.list_chandas'))
    return render_template('admin/add_chanda.html')

@admin.route('/chandas/edit/<int:chanda_id>', methods=['GET', 'POST'])
@admin_required 
def edit_chanda(chanda_id):
    chanda_to_edit = Chanda.query.get_or_404(chanda_id)
    if request.method == 'POST':
        chanda_to_edit.name = request.form.get('name')
        
        is_mixed_chanda = request.form.get('is_mixed_chanda') == 'on'
        if is_mixed_chanda:
            chanda_to_edit.pattern = None 
        else:
            chanda_to_edit.pattern = request.form.get('pattern') 
        
        chanda_to_edit.syllable_count = int(request.form.get('syllable_count'))
        chanda_to_edit.description_short = request.form.get('description_short')
        chanda_to_edit.pariyat_url = request.form.get('pariyat_url')
        chanda_to_edit.is_mixed_chanda = is_mixed_chanda 
        
        db.session.commit()
        flash(f"แก้ไขข้อมูลฉันท์ '{chanda_to_edit.name}' สำเร็จแล้ว!", 'success')
        return redirect(url_for('admin.list_chandas'))
    return render_template('admin/edit_chanda.html', chanda=chanda_to_edit)

@admin.route('/chandas/delete/<int:chanda_id>', methods=['POST'])
@admin_required 
def delete_chanda(chanda_id):
    chanda_to_delete = Chanda.query.get_or_404(chanda_id)
    chanda_name = chanda_to_delete.name
    if chanda_to_delete.is_mixed_chanda: 
        for sub_type in chanda_to_delete.upajati_sub_types:
            db.session.delete(sub_type)

    db.session.delete(chanda_to_delete)
    db.session.commit()
    flash(f"ลบฉันท์ '{chanda_name}' ออกจากระบบเรียบร้อยแล้ว", 'success')
    return redirect(url_for('admin.list_chandas'))


# --- Routes for Verse Example Management ---
@admin.route('/examples')
@admin_required 
def list_examples():
    examples = VerseExample.query.order_by(VerseExample.title).all()
    return render_template('admin/list_examples.html', examples=examples)

@admin.route('/examples/add', methods=['GET', 'POST'])
@admin_required 
def add_example():
    chandas = Chanda.query.order_by(Chanda.name).all()
    if request.method == 'POST':
        new_example = VerseExample(
            title=request.form.get('title'),
            content=request.form.get('content'),
            layout_type=request.form.get('layout_type'),
            source_type=request.form.get('source_type'),
            source_details=request.form.get('source_details'),
            notes=request.form.get('notes'),
            translation=request.form.get('translation'), 
            chanda_id=int(request.form.get('chanda_id'))
        )
        db.session.add(new_example)
        db.session.commit()
        flash(f"เพิ่มตัวอย่าง '{new_example.title}' สำเร็จ!", 'success')
        return redirect(url_for('admin.list_examples'))
    return render_template('admin/add_example.html', chandas=chandas)

@admin.route('/examples/edit/<int:example_id>', methods=['GET', 'POST'])
@admin_required 
def edit_example(example_id):
    example_to_edit = VerseExample.query.get_or_404(example_id)
    chandas = Chanda.query.order_by(Chanda.name).all()
    if request.method == 'POST':
        example_to_edit.title = request.form.get('title')
        example_to_edit.content = request.form.get('content')
        example_to_edit.layout_type = request.form.get('layout_type')
        example_to_edit.source_type = request.form.get('source_type')
        example_to_edit.source_details = request.form.get('source_details')
        example_to_edit.notes = request.form.get('notes')
        example_to_edit.translation = request.form.get('translation') 
        example_to_edit.chanda_id = int(request.form.get('chanda_id'))
        db.session.commit()
        flash(f"แก้ไขตัวอย่าง '{example_to_edit.title}' สำเร็จ!", 'success')
        return redirect(url_for('admin.list_examples'))
    return render_template('admin/edit_example.html', example=example_to_edit, chandas=chandas)

@admin.route('/examples/delete/<int:example_id>', methods=['POST'])
@admin_required 
def delete_example(example_id):
    example_to_delete = VerseExample.query.get_or_404(example_id)
    title = example_to_delete.title
    db.session.delete(example_to_delete)
    db.session.commit()
    flash(f"ลบตัวอย่าง '{title}' สำเร็จ!", 'success')
    return redirect(url_for('admin.list_examples'))


# --- Routes for Poetic Word Management ---
@admin.route('/words')
@admin_required 
def list_words():
    search_query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    if search_query:
        query = PoeticWord.query.filter(
            (PoeticWord.word.contains(search_query)) | 
            (PoeticWord.meaning.contains(search_query)) |
            (PoeticWord.prosody.contains(search_query))
        )
    else:
        query = PoeticWord.query
    words = query.order_by(PoeticWord.word).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/list_words.html', words=words, search_query=search_query)

@admin.route('/words/add', methods=['GET', 'POST'])
@admin_required 
def add_word():
    if request.method == 'POST':
        word = request.form.get('word')
        prosody = request.form.get('prosody')
        meaning = request.form.get('meaning')
        existing_word = PoeticWord.query.filter_by(word=word).first()
        if existing_word:
            flash(f"คำศัพท์ '{word}' นี้มีอยู่แล้วในระบบ", 'danger')
        else:
            new_word = PoeticWord(word=word, prosody=prosody, meaning=meaning)
            db.session.add(new_word)
            db.session.commit()
            flash(f"เพิ่มคำศัพท์ '{word}' สำเร็จ!", 'success')
            return redirect(url_for('admin.list_words'))
    return render_template('admin/add_word.html')

@admin.route('/words/edit/<int:word_id>', methods=['GET', 'POST'])
@admin_required 
def edit_word(word_id):
    word_to_edit = PoeticWord.query.get_or_404(word_id)
    if request.method == 'POST':
        word_to_edit.word = request.form.get('word')
        word_to_edit.prosody = request.form.get('prosody')
        word_to_edit.meaning = request.form.get('meaning')
        db.session.commit()
        flash(f"แก้ไขคำศัพท์ '{word_to_edit.word}' สำเร็จ!", 'success')
        return redirect(url_for('admin.list_words'))
    return render_template('admin/edit_word.html', word=word_to_edit)

@admin.route('/words/delete/<int:word_id>', methods=['POST'])
@admin_required 
def delete_word(word_id):
    word_to_delete = PoeticWord.query.get_or_404(word_id)
    word_text = word_to_delete.word
    db.session.delete(word_to_delete)
    db.session.commit()
    flash(f"ลบคำศัพท์ '{word_text}' สำเร็จ!", 'success')
    return redirect(url_for('admin.list_words'))


# --- Routes for User Management ---
@admin.route('/users')
@admin_required
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template('admin/list_users.html', users=users, title='จัดการผู้ใช้')

# NEW: Add User
@admin.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin_form = request.form.get('is_admin') == 'on' # Checkbox value

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f"ชื่อผู้ใช้ '{username}' นี้มีอยู่แล้วในระบบ", 'danger')
            return redirect(url_for('admin.add_user'))
        
        new_user = User(username=username, is_admin=is_admin_form)
        new_user.set_password(password) # Hash the password
        db.session.add(new_user)
        db.session.commit()
        flash(f"เพิ่มผู้ใช้ '{username}' สำเร็จ!", 'success')
        return redirect(url_for('admin.list_users'))
    return render_template('admin/add_user.html', title='เพิ่มผู้ใช้ใหม่')

# NEW: Edit User
@admin.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_password = request.form.get('password')
        new_is_admin = request.form.get('is_admin') == 'on'

        # Check for username change conflict
        if user_to_edit.username != new_username:
            existing_user_with_new_name = User.query.filter_by(username=new_username).first()
            if existing_user_with_new_name and existing_user_with_new_name.id != user_id:
                flash(f"ชื่อผู้ใช้ '{new_username}' นี้มีอยู่แล้วในระบบ", 'danger')
                return redirect(url_for('admin.edit_user', user_id=user_id))
            user_to_edit.username = new_username
        
        if new_password: # Only update password if provided
            user_to_edit.set_password(new_password)
        
        user_to_edit.is_admin = new_is_admin
        
        db.session.commit()
        flash(f"แก้ไขผู้ใช้ '{user_to_edit.username}' สำเร็จ!", 'success')
        return redirect(url_for('admin.list_users'))
    return render_template('admin/edit_user.html', user=user_to_edit, title='แก้ไขผู้ใช้')

# NEW: Delete User
@admin.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    
    # Prevent self-deletion
    if user_to_delete.id == current_user.id:
        flash("ไม่สามารถลบบัญชีผู้ใช้ที่คุณกำลังล็อกอินอยู่ได้", 'danger')
        return redirect(url_for('admin.list_users'))

    username = user_to_delete.username
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"ลบผู้ใช้ '{username}' สำเร็จ!", 'success')
    return redirect(url_for('admin.list_users'))