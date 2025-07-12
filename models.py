# models.py

from extensions import db
# +++ เพิ่ม import ที่จำเป็นสำหรับระบบล็อกอิน +++
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
# ----------------------------------------------

# ======================================================================
#  Database Model: Chanda (ตารางเก็บข้อมูลฉันท์)
# ======================================================================
class Chanda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chanda_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    pattern = db.Column(db.String(200), nullable=False)
    syllable_count = db.Column(db.Integer, nullable=False)
    chanda_type = db.Column(db.String(50), nullable=False, default='vutta')
    description_short = db.Column(db.Text, nullable=True)
    pariyat_url = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"Chanda('{self.name}', '{self.pattern}')"

# +++ เพิ่ม Class User สำหรับเก็บข้อมูลผู้ใช้ Admin +++
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
# --------------------------------------------------

# ======================================================================
#  ส่วน Logic การวิเคราะห์ (ไม่มีการเปลี่ยนแปลง)
# ======================================================================

def generate_syllable_db():
    # ... โค้ดเดิม ไม่มีการเปลี่ยนแปลง ...
    db = {}
    consonants = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
    
    vowels_map = {
        '': {'type': 'lahu'},
        'า': {'type': 'garu'}, 'ิ': {'type': 'lahu'}, 'ี': {'type': 'garu'},
        'ุ': {'type': 'lahu'}, 'ู': {'type': 'garu'}, 'เ': {'type': 'garu'},
        'โ': {'type': 'garu'}
    }
    preceding_vowels = "เโ"
    
    for c in consonants:
        for v_char, props in vowels_map.items():
            syllable_form = (v_char + c) if v_char in preceding_vowels else (c + v_char)
            db[syllable_form] = props.copy()
            
    db.update({
        "อ": {"type": "lahu"}, "อา": {"type": "garu"}, 
        "อิ": {"type": "lahu"}, "อี": {"type": "garu"}, 
        "อุ": {"type": "lahu"}, "อู": {"type": "garu"}, 
        "เอ": {"type": "garu"}, "โอ": {"type": "garu"}
    })

    for c in consonants + "อ":
        db[c + "ํ"] = {"type": "garu"}
        db[c + "ึ"] = {"type": "garu"}
        db[c + "ุํ"] = {"type": "garu"}
    
    for c in consonants:
        db[c] = {"type": "lahu"} 
    
    return db

SYLLABLE_DB = generate_syllable_db()
POSSIBLE_SYLLABLES = sorted(SYLLABLE_DB.keys(), key=len, reverse=True)
CONSONANTS = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
VIRAMA_CONSONANTS = [c + "ฺ" for c in CONSONANTS]
VIRAMA = "ฺ"

def syllabify_and_analyze(text: str) -> list:
    # ... โค้ดเดิม ไม่มีการเปลี่ยนแปลง ...
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
    # ... โค้ดเดิม ไม่มีการเปลี่ยนแปลง ...
    syllables_result = []
    
    for j, syl_str in enumerate(raw_syllables):
        analysis = {"syllable": syl_str, "type": "lahu"}

        if "ํ" in syl_str or "ึ" in syl_str or "ุํ" in syl_str:
            analysis["type"] = "garu"
        elif "ฺ" in syl_str:
            analysis["type"] = "garu"
        elif syl_str in SYLLABLE_DB and SYLLABLE_DB[syl_str]["type"] == "garu":
            analysis["type"] = "garu"
        
        syllables_result.append(analysis)
    return syllables_result

def identify_chanda_logic(verses_prosody_data: list, db_instance, chanda_model) -> dict:
    # ... โค้ดเดิม ไม่มีการเปลี่ยนแปลง ...
    identified_results = []

    for verse_index, verse_syllables_data in enumerate(verses_prosody_data):
        if not verse_syllables_data:
            identified_results.append({"verse_num": verse_index + 1, "matches": [], "notes": "ไม่มีข้อมูลพยางค์"})
            continue

        verse_prosody_string = "".join([syl['type'].replace('lahu', 'U').replace('garu', '-') for syl in verse_syllables_data])
        syllable_count = len(verse_prosody_string)

        possible_matches = []
        
        fixed_vutta_chandas = chanda_model.query.filter_by(chanda_type='vutta').all()
        for chanda_info_obj in fixed_vutta_chandas:
            if chanda_info_obj.syllable_count == syllable_count:
                pattern = chanda_info_obj.pattern
                if verse_prosody_string == pattern:
                    possible_matches.append({
                        "id": chanda_info_obj.chanda_id,
                        "name": chanda_info_obj.name,
                        "match_type": "ตรงตามรูปแบบเป๊ะ",
                        "pattern": pattern
                    })
        
        pathyavatta_info = chanda_model.query.filter_by(chanda_id='pathyavatta').first()
        if pathyavatta_info and syllable_count == 8:
            is_pathyavatta = True
            notes = []
            
            if len(verse_syllables_data) > 2 and verse_syllables_data[1]['type'] == 'lahu' and verse_syllables_data[2]['type'] == 'lahu':
                is_pathyavatta = False
                notes.append("พยางค์ ๒-๓ เป็นลหุคู่กัน (ผิดกฎห้าม น-คณะ/ส-คณะ ส่วนต้น)")
            
            if len(verse_syllables_data) > 6:
                gana_567_string = verse_prosody_string[4:7]
                if verse_index % 2 == 0:
                    if gana_567_string != "U--":
                        is_pathyavatta = False
                        notes.append(f"พยางค์ ๕-๗ ไม่เป็น ย-คณะ (บังคับ U-- ได้ {gana_567_string})")
                else:
                    if gana_567_string != "U-U":
                        is_pathyavatta = False
                        notes.append(f"พยางค์ ๕-๗ ไม่เป็น ช-คณะ (บังคับ U-U ได้ {gana_567_string})")
            else:
                is_pathyavatta = False
                notes.append("จำนวนพยางค์ไม่ครบ ๘ หรือไม่พอตรวจคณะ ๕-๗")
            
            if is_pathyavatta:
                possible_matches.append({
                    "id": pathyavatta_info.chanda_id,
                    "name": pathyavatta_info.name,
                    "match_type": "ตรงตามกฎปัฐยาวัตร",
                    "pattern": pathyavatta_info.pattern,
                    "notes": "; ".join(notes) if notes else "ตรงตามกฎบังคับ"
                })

        identified_results.append({
            "verse_num": verse_index + 1,
            "matches": possible_matches,
            "notes": "ไม่พบฉันท์ที่ตรงกัน" if not possible_matches else ""
        })
    
    all_chanda_patterns = {c.chanda_id: {"name": c.name, "pattern": c.pattern} for c in chanda_model.query.all()}
    
    return {"results_by_verse": identified_results, "syllable_patterns": all_chanda_patterns}