# app/admin/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from ..extensions import db
from ..models import Chanda, User, VerseExample, PoeticWord

admin = Blueprint('admin', __name__)

# --- Main admin dashboard, redirects to list_chandas ---
@admin.route('/')
@login_required
def dashboard():
    return redirect(url_for('admin.list_chandas'))

# --- Chanda Management ---
# Route to: app/templates/admin/list_chandas.html
@admin.route('/chandas')
@login_required
def list_chandas():
    chandas = Chanda.query.order_by(Chanda.syllable_count, Chanda.name).all()
    return render_template('admin/list_chandas.html', chandas=chandas)

@admin.route('/chandas/add', methods=['GET', 'POST'])
@login_required
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
        new_chanda = Chanda(name=name, pattern=pattern, syllable_count=int(syllable_count), description_short=description, pariyat_url=pariyat_url)
        db.session.add(new_chanda)
        db.session.commit()
        flash(f"เพิ่มฉันท์ '{name}' สำเร็จ!", 'success')
        return redirect(url_for('admin.list_chandas'))
    return render_template('admin/add_chanda.html')

@admin.route('/chandas/edit/<int:chanda_id>', methods=['GET', 'POST'])
@login_required
def edit_chanda(chanda_id):
    chanda_to_edit = Chanda.query.get_or_404(chanda_id)
    if request.method == 'POST':
        chanda_to_edit.name = request.form.get('name')
        chanda_to_edit.pattern = request.form.get('pattern')
        chanda_to_edit.syllable_count = int(request.form.get('syllable_count'))
        chanda_to_edit.description_short = request.form.get('description_short')
        chanda_to_edit.pariyat_url = request.form.get('pariyat_url')
        db.session.commit()
        flash(f"แก้ไขข้อมูลฉันท์ '{chanda_to_edit.name}' สำเร็จแล้ว!", 'success')
        return redirect(url_for('admin.list_chandas'))
    return render_template('admin/edit_chanda.html', chanda=chanda_to_edit)

@admin.route('/chandas/delete/<int:chanda_id>', methods=['POST'])
@login_required
def delete_chanda(chanda_id):
    chanda_to_delete = Chanda.query.get_or_404(chanda_id)
    chanda_name = chanda_to_delete.name
    db.session.delete(chanda_to_delete)
    db.session.commit()
    flash(f"ลบฉันท์ '{chanda_name}' ออกจากระบบเรียบร้อยแล้ว", 'success')
    return redirect(url_for('admin.list_chandas'))


# --- Routes for Verse Example Management ---
@admin.route('/examples')
@login_required
def list_examples():
    examples = VerseExample.query.order_by(VerseExample.title).all()
    return render_template('admin/list_examples.html', examples=examples)

@admin.route('/examples/add', methods=['GET', 'POST'])
@login_required
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
            translation=request.form.get('translation'), # <-- เพิ่มบรรทัดนี้
            chanda_id=int(request.form.get('chanda_id'))
        )
        db.session.add(new_example)
        db.session.commit()
        flash(f"เพิ่มตัวอย่าง '{new_example.title}' สำเร็จ!", 'success')
        return redirect(url_for('admin.list_examples'))
    return render_template('admin/add_example.html', chandas=chandas)

@admin.route('/examples/edit/<int:example_id>', methods=['GET', 'POST'])
@login_required
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
        example_to_edit.translation = request.form.get('translation') # <-- เพิ่มบรรทัดนี้
        example_to_edit.chanda_id = int(request.form.get('chanda_id'))
        db.session.commit()
        flash(f"แก้ไขตัวอย่าง '{example_to_edit.title}' สำเร็จ!", 'success')
        return redirect(url_for('admin.list_examples'))
    return render_template('admin/edit_example.html', example=example_to_edit, chandas=chandas)

@admin.route('/examples/delete/<int:example_id>', methods=['POST'])
@login_required
def delete_example(example_id):
    example_to_delete = VerseExample.query.get_or_404(example_id)
    title = example_to_delete.title
    db.session.delete(example_to_delete)
    db.session.commit()
    flash(f"ลบตัวอย่าง '{title}' สำเร็จ!", 'success')
    return redirect(url_for('admin.list_examples'))


# --- Routes for Poetic Word Management ---
@admin.route('/words')
@login_required
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
@login_required
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
@login_required
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
@login_required
def delete_word(word_id):
    word_to_delete = PoeticWord.query.get_or_404(word_id)
    word_text = word_to_delete.word
    db.session.delete(word_to_delete)
    db.session.commit()
    flash(f"ลบคำศัพท์ '{word_text}' สำเร็จ!", 'success')
    return redirect(url_for('admin.list_words'))