from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ======================================================================
#  ส่วนฐานข้อมูลและค่าคงที่
# ======================================================================

CHANDA_PATTERNS = {
    "pathyavatta":    {"name": "ปัฐยาวัตรฉันท์ ๘",     "pattern": "....U-U-"},
    "indavajira":     {"name": "อินทรวิเชียรฉันท์ ๑๑",   "pattern": "--U--UU-U--"},
    "upendavajira":   {"name": "อุเปนทรวิเชียรฉันท์ ๑๑", "pattern": "U-U--UU-U--"},
    "indavamsa":      {"name": "อินทรวงศ์ฉันท์ ๑๒",      "pattern": "--U--UU-U-U-"},
    "vamsattha":      {"name": "วังสัฏฐฉันท์ ๑๒",       "pattern": "U-U--UU-U-U-"},
    "vasantatilaka":  {"name": "วสันตดิลกฉันท์ ๑๔",   "pattern": "--U-UUU-UU-U--"},
}

def generate_syllable_db():
    db = {}
    consonants = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
    vowels = {"": "lahu", "า": "garu", "ิ": "lahu", "ี": "garu", "ุ": "lahu", "ู": "garu", "เ": "garu", "โ": "garu"}
    preceding_vowels = "เโ"
    for c in consonants:
        for v, v_type in vowels.items():
            syllable = (v + c) if v in preceding_vowels else (c + v)
            db[syllable] = {"type": v_type}
    db.update({"อ": {"type": "lahu"}, "อา": {"type": "garu"}, "อิ": {"type": "lahu"}, "อี": {"type": "garu"}, "อุ": {"type": "lahu"}, "อู": {"type": "garu"}, "เอ": {"type": "garu"}, "โอ": {"type": "garu"}})
    for c in consonants + "อ":
        db[c + "ํ"] = {"type": "garu"}
        db[c + "ึ"] = {"type": "garu"}
        db[c + "ุํ"] = {"type": "garu"}
    return db

SYLLABLE_DB = generate_syllable_db()
POSSIBLE_SYLLABLES = sorted(SYLLABLE_DB.keys(), key=len, reverse=True)
CONSONANTS = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
VIRAMA_CONSONANTS = [c + "ฺ" for c in CONSONANTS]

# ======================================================================
#  ส่วน Logic การวิเคราะห์
# ======================================================================
def syllabify_and_analyze(text: str) -> list:
    allowed_chars = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ" \
                    "ออาอิอีอุอูเอโอ" \
                    "าิีุูเโฺํึ"
    cleaned_text = "".join(char for char in text if char in allowed_chars)
    text = cleaned_text
    if not text: return []
    raw_syllables, i = [], 0
    while i < len(text):
        found_syllable = None
        for key in POSSIBLE_SYLLABLES:
            if text[i:].startswith(key):
                found_syllable = key
                break
        if not found_syllable:
            if i + 1 < len(text) and text[i:i+2] in VIRAMA_CONSONANTS:
                found_syllable = text[i:i+2]
            else:
                found_syllable = text[i]
        current_position = i + len(found_syllable)
        coda = ""
        if current_position + 1 < len(text):
            possible_coda = text[current_position:current_position+2]
            if possible_coda in VIRAMA_CONSONANTS: coda = possible_coda
        full_syllable = found_syllable + coda
        raw_syllables.append(full_syllable)
        i += len(full_syllable)
    return analyze_prosody(raw_syllables)

def analyze_prosody(raw_syllables: list) -> list:
    syllables_result = []
    for j, syl in enumerate(raw_syllables):
        analysis = {"syllable": syl, "type": "lahu"}
        base_syl, coda_part = syl, ""
        if len(syl) > 2 and syl[-2:] in VIRAMA_CONSONANTS:
            base_syl, coda_part = syl[:-2], syl[-2:]
        if coda_part or (base_syl in SYLLABLE_DB and SYLLABLE_DB[base_syl]["type"] == "garu"):
            analysis["type"] = "garu"
        elif base_syl in SYLLABLE_DB:
            analysis["type"] = SYLLABLE_DB[base_syl]["type"]
        
        # เราจะไม่ใช้กฎการมองไปข้างหน้าที่ซับซ้อน เพื่อความเสถียร
        # if analysis["type"] == "lahu" and j + 1 < len(raw_syllables):
        #     ...
        
        syllables_result.append(analysis)
    return syllables_result

# ======================================================================
#  ส่วนของ Web Server (Routes)
# ======================================================================
@app.route('/')
def index():
    return render_template('index.html', chandas=CHANDA_PATTERNS)

@app.route('/analyzer/<chanda_id>')
def analyzer_page(chanda_id):
    chanda_info = CHANDA_PATTERNS.get(chanda_id)
    if not chanda_info: return "ไม่พบฉันท์ที่ระบุ", 404
    return render_template('analyzer.html', chanda=chanda_info, chanda_id=chanda_id)

@app.route('/api/analyze', methods=['POST'])
def analyze_api():
    data = request.get_json()
    if not data or 'verses' not in data or not isinstance(data['verses'], list):
        return jsonify({'error': 'Invalid input, expected a list of verses.'}), 400
    results_by_verse = []
    for verse_text in data['verses']:
        syllables = syllabify_and_analyze(verse_text)
        results_by_verse.append(syllables)
    return jsonify(results_by_verse)

# ไม่จำเป็นต้องมี /api/re_analyze แล้ว เพราะการคำนวณใหม่เกิดขึ้นที่ Frontend ทั้งหมด
# if __name__ == '__main__':
#    ...

if __name__ == '__main__':
    app.run(debug=True)