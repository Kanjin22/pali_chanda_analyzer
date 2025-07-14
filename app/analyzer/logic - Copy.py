# app/analyzer/logic.py
from ..extensions import db
from .. import models

def generate_syllable_db():
    db_map = {}
    consonants = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
    vowels_map = {'':{'type':'lahu'},'า':{'type':'garu'},'ิ':{'type':'lahu'},'ี':{'type':'garu'},'ุ':{'type':'lahu'},'ู':{'type':'garu'},'เ':{'type':'garu'},'โ':{'type':'garu'}}
    preceding_vowels = "เโ"
    for c in consonants:
        for v_char, props in vowels_map.items():
            syllable_form = (v_char + c) if v_char in preceding_vowels else (c + v_char)
            db_map[syllable_form] = props.copy()
    db_map.update({"อ":{"type":"lahu"},"อา":{"type":"garu"},"อิ":{"type":"lahu"},"อี":{"type":"garu"},"อุ":{"type":"lahu"},"อู":{"type":"garu"},"เอ":{"type":"garu"},"โอ":{"type":"garu"}})
    for c in consonants + "อ":
        db_map[c + "ํ"] = {"type": "garu"}
        db_map[c + "ึ"] = {"type": "garu"}
        db_map[c + "ุํ"] = {"type": "garu"}
    for c in consonants:
        db_map[c] = {"type": "lahu"} 
    return db_map

SYLLABLE_DB = generate_syllable_db()
POSSIBLE_SYLLABLES = sorted(SYLLABLE_DB.keys(), key=len, reverse=True)
CONSONANTS = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
VIRAMA_CONSONANTS = [c + "ฺ" for c in CONSONANTS]
VIRAMA = "ฺ"

# +++ ฟังก์ชัน syllabify_and_analyze ฉบับยกเครื่อง (Final Logic) +++
def syllabify_and_analyze(text: str) -> list:
    allowed_chars = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬออาอิอีอุอูเอโอาิีุูเโฺํึ"
    cleaned_text = "".join(char for char in text if char in allowed_chars)
    text = cleaned_text
    if not text: return []
    
    # +++ สร้าง list คำยกเว้นที่ซับซ้อน +++
    # เราจะให้โปรแกรมหาคำเหล่านี้ก่อนเป็นอันดับแรก
    # เรียงจากยาวไปสั้น
    exception_syllables = {
        "พฺยญฺ": {"type": "garu"}, # พยางค์ใน พฺยญฺชน
        "สฺวากฺ": {"type": "garu"},# พยางค์ใน สฺวากฺขาโต
        "ตฺวํ": {"type": "garu"},
        "มฺยา": {"type": "garu"},
    }
    possible_syllables = sorted(
        list(exception_syllables.keys()) + list(SYLLABLE_DB.keys()), 
        key=len, 
        reverse=True
    )

    raw_syllables = []
    i = 0
    while i < len(text):
        # 1. ตรวจสอบกับ List ที่รวมคำยกเว้นแล้วก่อน
        found_syllable = None
        for key in possible_syllables:
            if text[i:].startswith(key):
                # ตรวจสอบกฎ "นิคหิต"
                if "ํ" in key and i + len(key) < len(text) and text[i + len(key)] == 'ฺ':
                    continue # ถ้าเจอ ํ แล้วมี ฺ ต่อท้าย ให้ข้ามไป ถือว่าไม่ตรง
                
                found_syllable = key
                break
        
        # 2. ถ้าไม่เจอ ให้ใช้ Fallback เดิม
        if not found_syllable:
            found_syllable = text[i]

        # 3. ตรวจสอบตัวสะกด (Coda)
        current_position = i + len(found_syllable)
        coda = ""

        # กฎ: จะหา Coda ก็ต่อเมื่อ...
        # 3.1) พยางค์ที่เจอไม่มีนิคหิต
        # 3.2) ยังมีข้อความเหลือ
        # 3.3) ตัวถัดไปคือพยัญชนะ + พินทุ
        if "ํ" not in found_syllable and current_position + 1 < len(text) and text[current_position:current_position+2] in VIRAMA_CONSONANTS:
            # 3.4) กฎสำคัญ: ตรวจสอบว่าหลังจากตัวสะกดแล้ว มันไม่ใช่พยัญชนะควบกล้ำที่เริ่มพยางค์ใหม่
            # เช่น ใน "สูปพฺยญฺชน" เราเจอ "ป" แล้วตัวถัดไปคือ "พฺ"
            # เราต้องรู้ว่า "พฺย" เป็น onset ของพยางค์ใหม่ ไม่ใช่ "พฺ" เป็นตัวสะกดของ "ป"
            next_onset_candidate_pos = current_position + 2
            is_followed_by_cluster = False
            if next_onset_candidate_pos + 1 < len(text) and text[next_onset_candidate_pos:next_onset_candidate_pos+2] in VIRAMA_CONSONANTS:
                 is_followed_by_cluster = True # ถ้าตามด้วย Cฺ แสดงว่าเป็นควบกล้ำแน่นอน
            
            if not is_followed_by_cluster:
                coda = text[current_position:current_position+2]

        full_syllable = found_syllable + coda
        raw_syllables.append(full_syllable)
        i += len(full_syllable)
        
    return analyze_prosody(raw_syllables)


def analyze_prosody(raw_syllables: list) -> list:
    # ... โค้ดส่วนนี้เหมือนเดิม ...
    syllables_result = []
    for j, syl_str in enumerate(raw_syllables):
        analysis = {"syllable": syl_str, "type": "lahu"}
        if "ํ" in syl_str or "ึ" in syl_str or "ุํ" in syl_str: analysis["type"] = "garu"
        elif "ฺ" in syl_str: analysis["type"] = "garu"
        elif syl_str in SYLLABLE_DB and SYLLABLE_DB[syl_str]["type"] == "garu": analysis["type"] = "garu"
        syllables_result.append(analysis)
    return syllables_result


def identify_chanda_logic(verses_prosody_data: list) -> dict:
    identified_results = []
    Chanda = models.Chanda
    for verse_index, verse_syllables_data in enumerate(verses_prosody_data):
        if not verse_syllables_data:
            identified_results.append({"verse_num": verse_index + 1, "matches": [], "notes": "ไม่มีข้อมูลพยางค์"})
            continue

        verse_prosody_string = "".join([syl['type'].replace('lahu', 'U').replace('garu', '-') for syl in verse_syllables_data])
        syllable_count = len(verse_prosody_string)
        possible_matches = []
        
        # ใช้ Chanda Model ที่ import เข้ามา
        # แก้ไข: ค้นหาจากฐานข้อมูลทั้งหมด
        fixed_vutta_chandas = Chanda.query.all()
        for chanda_info_obj in fixed_vutta_chandas:
            # ใช้ chanda_info_obj.id (Integer)
            if chanda_info_obj.syllable_count == syllable_count:
                # ตรวจสอบว่าเป็นปัฐยาวัตรหรือไม่
                if 'ปัฐยาวัตร' in chanda_info_obj.name:
                    is_pathyavatta = True
                    notes = []
                    if len(verse_syllables_data) > 2 and verse_syllables_data[1]['type'] == 'lahu' and verse_syllables_data[2]['type'] == 'lahu':
                        is_pathyavatta = False
                        notes.append("พยางค์ ๒-๓ เป็นลหุคู่กัน")
                    if len(verse_syllables_data) > 6:
                        gana_567_string = verse_prosody_string[4:7]
                        if verse_index % 2 == 0:
                            if gana_567_string != "U--":
                                is_pathyavatta = False
                                notes.append("พยางค์ ๕-๗ ไม่เป็น ย-คณะ")
                        else:
                            if gana_567_string != "U-U":
                                is_pathyavatta = False
                                notes.append("พยางค์ ๕-๗ ไม่เป็น ช-คณะ")
                    else:
                        is_pathyavatta = False
                        notes.append("จำนวนพยางค์ไม่ครบ ๘")
                    
                    if is_pathyavatta:
                        possible_matches.append({
                            "id": chanda_info_obj.id,
                            "name": chanda_info_obj.name,
                            "match_type": "ตรงตามกฎปัฐยาวัตร",
                            "pattern": chanda_info_obj.pattern,
                            "notes": "; ".join(notes) if notes else "ตรงตามกฎบังคับ"
                        })
                else: # ถ้าเป็นฉันท์อื่นๆ
                    pattern = chanda_info_obj.pattern
                    if verse_prosody_string == pattern:
                        possible_matches.append({
                            "id": chanda_info_obj.id, 
                            "name": chanda_info_obj.name,
                            "match_type": "ตรงตามรูปแบบเป๊ะ",
                            "pattern": pattern
                        })
        
        # *** จัดการย่อหน้าของบรรทัดนี้ให้ถูกต้อง ***
        identified_results.append({
            "verse_num": verse_index + 1,
            "matches": possible_matches,
            "notes": "ไม่พบฉันท์ที่ตรงกัน" if not possible_matches else ""
        })
    
    all_chanda_patterns = {c.id: {"name": c.name, "pattern": c.pattern} for c in Chanda.query.all()}
    
    return {"results_by_verse": identified_results, "syllable_patterns": all_chanda_patterns}