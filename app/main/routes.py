# app/main/routes.py
from flask import Blueprint, render_template, redirect, url_for, request
from ..models import Chanda, VerseExample, PoeticWord 

main = Blueprint('main', __name__)


# --- Route to: app/templates/index.html ---
@main.route('/')
def index():
    return render_template('index.html')


# --- Route to: app/templates/analyzer/analyzer_index.html ---
@main.route('/analyzer')
def analyzer_index():
    # เรียงตาม ID เพื่อให้เป็นลำดับการเพิ่ม
    chandas = Chanda.query.order_by(Chanda.id).all() 
    return render_template('analyzer/analyzer_index.html', chandas=chandas)


# --- Route to: app/templates/main/chanda_list.html ---
# ใช้สำหรับแสดงรายการฉันท์ทั้งหมด
@main.route('/chanda_list')
def chanda_list():
    # ในหน้านี้อาจจะอยากเรียงตามชื่อ
    chandas = Chanda.query.order_by(Chanda.name).all()
    return render_template('main/chanda_list.html', title='รวมฉันท์', chandas=chandas)


# --- Route to: app/templates/main/dictionary.html ---
@main.route('/dictionary')
def dictionary():
    search_gana = request.args.get('gana', '').strip()
    search_prosody = request.args.get('prosody', '').strip()
    search_text = request.args.get('text', '').strip()

    query = PoeticWord.query

    final_prosody_search = ''

    if search_prosody:
        final_prosody_search = search_prosody
    elif search_gana:
        final_prosody_search = search_gana
    if final_prosody_search:
        query = query.filter(PoeticWord.prosody.contains(final_prosody_search))
        
    if search_text:
        query = query.filter(
            PoeticWord.word.contains(search_text) | 
            PoeticWord.meaning.contains(search_text)
        )
    
    words = query.order_by(PoeticWord.word).all()

    return render_template('main/dictionary.html', 
                           words=words,
                           search_gana=search_gana,
                           search_prosody=search_prosody,
                           search_text=search_text)


# --- Route to: app/templates/main/list_examples.html ---
@main.route('/examples')
def examples():
    source_filter = request.args.get('source', None)
    query = VerseExample.query
    if source_filter:
        query = query.filter_by(source_type=source_filter)
    all_examples = query.order_by(VerseExample.title).all()
    return render_template('main/list_examples.html', 
                           examples=all_examples, 
                           source_filter=source_filter)


# --- Route to: app/templates/main/example_detail.html ---
@main.route('/examples/<int:example_id>')
def example_detail(example_id):
    example = VerseExample.query.get_or_404(example_id)
    return render_template('main/example_detail.html', example=example)