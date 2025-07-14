# app/analyzer/logic.py
from ..extensions import db
from .. import models

# ==============================================================================
#  ส่วนที่ 1: สร้างฐานข้อมูลหน่วยเสียงพื้นฐานตามอักขระวิธีที่กำหนด (ใหม่ทั้งหมด)
# ==============================================================================

def generate_possible_syllables():
    """
    สร้าง list ของหน่วยเสียงพื้นฐาน (syllable building blocks) ที่เป็นไปได้ทั้งหมด
    ตามอักขระวิธีบาลีที่กำหนด โดยเรียงลำดับจากยาวที่สุดไปสั้นที่สุด
    เพื่อให้ตรรกะ "longest match first" ทำงานได้อย่างถูกต้อง
    """
    consonants = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
    vowels_char = "าิีุูเโ"
    niggahita_vowels = "อึอุ" # สำหรับสร้าง Xึ, Xุํ

    # 1. สระลอย (Independent Vowels)
    # อ อา อิ อี อุ อู เอ โอ
    syllables = list("ออาอิอีอุอูเอโอ")

    # 2. พยัญชนะ + สระ (อา อิ อี อุ อู เ โ)
    for c in consonants + "อ": # รวม 'อ' เข้าไปด้วย
        # กา ขา..., กี ขี..., กู ขู..., เก เข..., โก โข...
        for v in "าีูเโ":
            syllable = (v + c) if v in "เโ" else (c + v)
            syllables.append(syllable)
        # กิ ขิ... (เป็น C + ิ)
        syllables.append(c + "ิ")
        # กุ ขุ...
        syllables.append(c + "ุ")

    # 3. พยัญชนะเสียงสระอะลอย (ก ข ค...)
    syllables.extend(list(consonants))

    # 4. พยัญชนะ + นิคหิต (กํ ขํ..., กึ ขึ..., กุํ ขุํ...)
    for c in consonants + "อ":
        syllables.append(c + "ํ") # กํ
        syllables.append(c + "ึ") # กึ (มาจาก อึ)
        syllables.append(c + "ุ" + "ํ") # กุํ (มาจาก อุํ)

    # 5. พยัญชนะควบกล้ำ (เช่น พฺย, สฺว) และหน่วยเสียงที่ซับซ้อน
    # สร้างจากพยัญชนะ 2 ตัว + พินทุ
    virama_consonants = [c + "ฺ" for c in consonants]
    for c1_v in virama_consonants:
        for c2 in consonants:
            # รูปแบบ Cฺ + C (เช่น พฺ + ย -> พฺย)
            cluster = c1_v + c2
            syllables.append(cluster)
            # รูปแบบ Cฺ + C + Vowel (เช่น พฺย + า -> พฺยา)
            for v in vowels_char:
                syllable_with_vowel = (v + cluster) if v in "เโ" else (cluster + v)
                syllables.append(syllable_with_vowel)
            # รูปแบบ Cฺ + C + Niggahita (เช่น ตฺว + ํ -> ตฺวํ)
            syllables.append(cluster + "ํ")
            syllables.append(cluster + "ึ")
            syllables.append(cluster + "ุ" + "ํ")
    
    # *** สำคัญมาก: เรียงจากยาวไปสั้น ***
    return sorted(syllables, key=len, reverse=True)

# สร้างค่าคงที่ไว้เลย ไม่ต้องสร้างใหม่ทุกครั้ง
POSSIBLE_NUCLEI = generate_possible_syllables()
CONSONANTS = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
VIRAMA = "ฺ"

# ==============================================================================
#  ส่วนที่ 2: ตรรกะการแบ่งพยางค์ (Syllabification Logic) (ใหม่ทั้งหมด)
# ==============================================================================

def _syllabify_word(word: str) -> list:
    """
    ฟังก์ชันผู้ช่วย: ทำหน้าที่แบ่งพยางค์ใน "คำ" เดียวเท่านั้น
    """
    if not word:
        return []

    raw_syllables = []
    i = 0
    while i < len(word):
        # 1. หา "แกนพยางค์" (Nucleus) ที่ยาวที่สุดที่ตรงกัน
        # เช่น ใน "พฺยญฺชน", ที่ i=0 จะเจอ "พฺย" ก่อน "พ"
        found_nucleus = None
        for nucleus in POSSIBLE_NUCLEI:
            if word[i:].startswith(nucleus):
                found_nucleus = nucleus
                break
        
        # Fallback: ถ้าไม่เจอในระบบ (ซึ่งไม่ควรเกิด) ให้ใช้ 1 ตัวอักษร
        if not found_nucleus:
            found_nucleus = word[i]

        current_pos = i + len(found_nucleus)
        
        # 2. ตรวจหา "ตัวสะกด" (Coda)
        # ตัวสะกดคือพยัญชนะ + พินทุ (Cฺ) ที่อยู่ท้ายแกนพยางค์
        coda = ""
        # ตรวจสอบว่ายังมีตัวอักษรเหลือในคำ และตัวถัดไปเป็นรูปแบบ Cฺ
        if current_pos + 1 < len(word) and (word[current_pos] in CONSONANTS) and (word[current_pos + 1] == VIRAMA):
            coda = word[current_pos : current_pos + 2]

        full_syllable = found_nucleus + coda
        raw_syllables.append(full_syllable)
        i += len(full_syllable)
        
    return raw_syllables


# +++ ฟังก์ชันหลักฉบับปรับปรุงใหม่ +++
def syllabify_and_analyze(text: str) -> list:
    """
    ฟังก์ชันหลักที่ทำงานตามขั้นตอน:
    1. ทำความสะอาด Input
    2. แยกเป็น "คำ" จากการเว้นวรรค
    3. ส่งแต่ละคำไปให้ _syllabify_word เพื่อแบ่งพยางค์
    4. รวบรวมพยางค์ทั้งหมด แล้วส่งไปวิเคราะห์ครุ-ลหุ
    """
    # 1. ทำความสะอาด Input (เหมือนเดิม)
    allowed_chars = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬออาอิอีอุอูเอโอาิีุูเโฺํึ " # เพิ่ม space
    cleaned_text = "".join(char for char in text if char in allowed_chars)
    
    if not cleaned_text.strip():
        return []

    # 2. แยกเป็น "คำ"
    words = cleaned_text.strip().split()

    # 3. แบ่งพยางค์ในแต่ละคำ แล้วรวบรวมผลลัพธ์
    all_raw_syllables = []
    for word in words:
        syllables_in_word = _syllabify_word(word)
        all_raw_syllables.extend(syllables_in_word)

    # 4. วิเคราะห์ครุ-ลหุ (ใช้ฟังก์ชันเดิมได้เลย)
    return analyze_prosody(all_raw_syllables)


def analyze_prosody(raw_syllables: list) -> list:
    """
    วิเคราะห์ว่าแต่ละพยางค์เป็นครุหรือลหุ
    *** ไม่มีการเปลี่ยนแปลงฟังก์ชันนี้ เพราะยังทำงานได้ถูกต้อง ***
    """
    syllables_result = []
    for syl_str in raw_syllables:
        # กฎพื้นฐาน: ถ้ามีตัวสะกด (ฺ) หรือนิคหิต (ํ, ึ) เป็นครุเสมอ
        if "ฺ" in syl_str or "ํ" in syl_str or "ึ" in syl_str:
            analysis = {"syllable": syl_str, "type": "garu"}
        # ถ้าเป็นสระเสียงยาว (อา อี อู เอ โอ) เป็นครุ
        elif any(v in syl_str for v in "าีูเโ"):
            analysis = {"syllable": syl_str, "type": "garu"}
        # ที่เหลือเป็นลหุ (สระเสียงสั้นและไม่มีตัวสะกด)
        else:
            analysis = {"syllable": syl_str, "type": "lahu"}
        syllables_result.append(analysis)
    return syllables_result


# ==============================================================================
#  ส่วนที่ 3: การระบุฉันท์ (Identify Chanda)
# ==============================================================================
# *** ไม่มีการเปลี่ยนแปลงในส่วนนี้ ***
def identify_chanda_logic(verses_prosody_data: list) -> dict:
    # ... โค้ดส่วนนี้เหมือนเดิมทุกประการ ...
    identified_results = []
    Chanda = models.Chanda
    for verse_index, verse_syllables_data in enumerate(verses_prosody_data):
        if not verse_syllables_data:
            identified_results.append({"verse_num": verse_index + 1, "matches": [], "notes": "ไม่มีข้อมูลพยางค์"})
            continue

        verse_prosody_string = "".join([syl['type'].replace('lahu', 'U').replace('garu', '-') for syl in verse_syllables_data])
        syllable_count = len(verse_prosody_string)
        possible_matches = []
        
        fixed_vutta_chandas = Chanda.query.all()
        for chanda_info_obj in fixed_vutta_chandas:
            if chanda_info_obj.syllable_count == syllable_count:
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
                else: 
                    pattern = chanda_info_obj.pattern
                    if verse_prosody_string == pattern:
                        possible_matches.append({
                            "id": chanda_info_obj.id, 
                            "name": chanda_info_obj.name,
                            "match_type": "ตรงตามรูปแบบเป๊ะ",
                            "pattern": pattern
                        })
        
        identified_results.append({
            "verse_num": verse_index + 1,
            "matches": possible_matches,
            "notes": "ไม่พบฉันท์ที่ตรงกัน" if not possible_matches else ""
        })
    
    all_chanda_patterns = {c.id: {"name": c.name, "pattern": c.pattern} for c in Chanda.query.all()}
    
    return {"results_by_verse": identified_results, "syllable_patterns": all_chanda_patterns}