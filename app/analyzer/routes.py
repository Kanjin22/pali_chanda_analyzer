# app/analyzer/routes.py
from flask import Blueprint, render_template, request, jsonify, url_for
from . import logic
from ..models import Chanda

analyzer = Blueprint('analyzer', __name__)

@analyzer.route('/specific/<int:chanda_id>')
def analyzer_page(chanda_id):
    chanda_info = Chanda.query.get_or_404(chanda_id)
    return render_template('analyzer/analyzer_page.html', chanda=chanda_info)

@analyzer.route('/identify')
def identify_page():
    return render_template('analyzer/identify_page.html')


@analyzer.route('/api/analyze', methods=['POST'])
def analyze_api():
    data = request.get_json()
    if not data or 'verses' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    results_by_verse = []
    if all(isinstance(v, str) for v in data['verses']):
        for verse_text in data['verses']:
            results_by_verse.append(logic.syllabify_and_analyze(verse_text))
    elif all(isinstance(v, list) for v in data['verses']):
        for verse_syllables_list in data['verses']:
            results_by_verse.append(logic.analyze_prosody(verse_syllables_list))
    return jsonify(results_by_verse)


@analyzer.route('/api/identify_chanda', methods=['POST'])
def identify_chanda_api():
    data = request.get_json()
    if not data or 'verses' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    prosody_results_by_verse = [logic.analyze_prosody(verse_syllables_list) for verse_syllables_list in data['verses']]
    identification_results = logic.identify_chanda_logic(prosody_results_by_verse)
    return jsonify({
        "identification": identification_results,
        "prosody_results": prosody_results_by_verse
    })


@analyzer.route('/api/get_prosody', methods=['POST'])
def get_prosody_api():
    data = request.get_json()
    word = data.get('word', '')
    if not word:
        return jsonify({'error': 'No word provided'}), 400
    syllables_data = logic.syllabify_and_analyze(word)
    prosody_pattern = "".join([syl['type'].replace('lahu', 'U').replace('garu', '-') for syl in syllables_data])
    return jsonify({'prosody': prosody_pattern})