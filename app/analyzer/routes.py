# app/analyzer/routes.py
from flask import Blueprint, render_template, request, jsonify
from ..models import Chanda
from ..analyzer import logic 

analyzer = Blueprint('analyzer', __name__)

@analyzer.route('/specific/<int:chanda_id>')
def analyzer_page(chanda_id):
    chanda_info = Chanda.query.get_or_404(chanda_id)
    return render_template('analyzer/analyzer_page.html', chanda=chanda_info)

@analyzer.route('/identify') # URL: /analyzer/identify
def identify_page():
    return render_template('analyzer/identify_page.html', title="ระบุฉันท์อัตโนมัติ")

# --- API Endpoint สำหรับการแบ่งพยางค์และวิเคราะห์ ---
@analyzer.route('/api/analyze', methods=['POST'])
def analyze_api():
    data = request.get_json()
    input_verses = data.get('verses', []) 
    
    is_initial_text_input = False
    if input_verses and isinstance(input_verses[0], str):
        is_initial_text_input = True
    
    prosody_results_for_frontend = [] 
    
    if is_initial_text_input:
        # กรณี 1: การแบ่งพยางค์ครั้งแรกจากข้อความดิบที่ผู้ใช้ป้อนเข้ามา
        for verse_text in input_verses:
            if verse_text.strip():
                # logic.syllabify_and_analyze จะทำทั้ง Clean, Syllabify, และ Analyze Prosody
                analyzed_syllables = logic.syllabify_and_analyze(verse_text) 
                prosody_results_for_frontend.append({
                    "syllables_data": analyzed_syllables,
                    "notes": "แบ่งพยางค์เริ่มต้น",
                    "determined_pattern": None, 
                    "matches": [] 
                })
            else:
                prosody_results_for_frontend.append({
                    "syllables_data": [],
                    "notes": "ไม่มีข้อความสำหรับบาทนี้",
                    "determined_pattern": None,
                    "matches": []
                })
        
        return jsonify({
            "results_by_verse": prosody_results_for_frontend,
            "syllable_patterns": {} 
        })
    else:
        # กรณี 2: การวิเคราะห์ครั้งสุดท้ายจากพยางค์ที่แก้ไขแล้ว
        # input_verses ตอนนี้คือ list ของ list ของ raw syllable strings
        
        analyzed_input_syllables_per_verse = []
        for raw_syllable_list in input_verses:
            if raw_syllable_list:
                # สำหรับพยางค์ที่แก้ไขแล้ว (string) ต้องวิเคราะห์ prosody ใหม่
                analyzed_input_syllables_per_verse.append(logic.analyze_prosody(raw_syllable_list))
            else:
                analyzed_input_syllables_per_verse.append([])
        
        identification_results = logic.identify_chanda_logic(analyzed_input_syllables_per_verse)
        
        return jsonify(identification_results)

# --- API Endpoint สำหรับการระบุฉันท์ (จากพยางค์ที่แก้ไขแล้ว) ---
@analyzer.route('/api/identify', methods=['POST'])
def identify_chanda_api():
    data = request.get_json()
    corrected_syllables_by_verse = data.get('verses', [])

    analyzed_input_syllables_per_verse = []
    for raw_syllable_list in corrected_syllables_by_verse:
        if raw_syllable_list:
            analyzed_input_syllables_per_verse.append(logic.analyze_prosody(raw_syllable_list))
        else:
            analyzed_input_syllables_per_verse.append([])
    
    identification_results = logic.identify_chanda_logic(analyzed_input_syllables_per_verse)
    
    return jsonify({
        "prosody_results": identification_results["results_by_verse"], 
        "identification": {
            "results_by_verse": identification_results["results_by_verse"], 
            "syllable_patterns": identification_results["syllable_patterns"] 
        }
    })