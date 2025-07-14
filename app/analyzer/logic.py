# app/analyzer/logic.py
from ..extensions import db
from .. import models

# ==============================================================================
#  ส่วนที่ 1: สร้างฐานข้อมูลหน่วยเสียงพื้นฐานตามอักขระวิธีที่กำหนด
# ==============================================================================

def generate_possible_syllables():
    """
    สร้าง list ของหน่วยเสียงพื้นฐาน (syllable building blocks) ที่เป็นไปได้ทั้งหมด
    ตามอักขระวิธีบาลีที่กำหนด โดยเรียงลำดับจากยาวที่สุดไปสั้นที่สุด
    เพื่อให้ตรรกะ "longest match first" ทำงานได้อย่างถูกต้อง
    """
    consonants = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
    vowels_char = "าิีุูเโ"

    syllables = list("ออาอิอีอุอูเอโอ")

    for c in consonants + "อ":
        for v in "าีูเโ":
            syllable = (v + c) if v in "เโ" else (c + v)
            syllables.append(syllable)
        syllables.append(c + "ิ")
        syllables.append(c + "ุ")

    syllables.extend(list(consonants))

    for c in consonants + "อ":
        syllables.append(c + "ํ")
        syllables.append(c + "ึ")
        syllables.append(c + "ุ" + "ํ")

    virama_consonants = [c + "ฺ" for c in consonants]
    for c1_v in virama_consonants:
        for c2 in consonants:
            cluster = c1_v + c2
            syllables.append(cluster)
            for v in vowels_char:
                syllable_with_vowel = (v + cluster) if v in "เโ" else (cluster + v)
                syllables.append(syllable_with_vowel)
            syllables.append(cluster + "ํ")
            syllables.append(cluster + "ึ")
            syllables.append(cluster + "ุ" + "ํ")
    
    return sorted(syllables, key=len, reverse=True)

POSSIBLE_NUCLEI = generate_possible_syllables()
CONSONANTS = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬ"
VIRAMA = "ฺ"

# ==============================================================================
#  ส่วนที่ 2: ตรรกะการแบ่งพยางค์ (Syllabification Logic)
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
        found_nucleus = None
        for nucleus in POSSIBLE_NUCLEI:
            if word[i:].startswith(nucleus):
                found_nucleus = nucleus
                break
        
        if not found_nucleus:
            found_nucleus = word[i]

        current_pos = i + len(found_nucleus)
        
        coda = ""
        if current_pos + 1 < len(word) and (word[current_pos] in CONSONANTS) and (word[current_pos + 1] == VIRAMA):
            coda = word[current_pos : current_pos + 2]

        full_syllable = found_nucleus + coda
        raw_syllables.append(full_syllable)
        i += len(full_syllable)
        
    return raw_syllables


def syllabify_and_analyze(text: str) -> list:
    """
    ฟังก์ชันหลักที่ทำงานตามขั้นตอน:
    1. ทำความสะอาด Input
    2. แยกเป็น "คำ" จากการเว้นวรรค
    3. ส่งแต่ละคำไปให้ _syllabify_word เพื่อแบ่งพยางค์
    4. รวบรวมพยางค์ทั้งหมด แล้วส่งไปวิเคราะห์ครุ-ลหุ
    """
    allowed_chars = "กขคฆงจฉชฌญฏฐฑฒณตถทธนปผพภมยรลวสหฬออาอิอีอุอูเอโอาิีุูเโฺํึ "
    cleaned_text = "".join(char for char in text if char in allowed_chars)
    
    if not cleaned_text.strip():
        return []

    words = cleaned_text.strip().split()

    all_raw_syllables = []
    for word in words:
        syllables_in_word = _syllabify_word(word)
        all_raw_syllables.extend(syllables_in_word)

    return analyze_prosody(all_raw_syllables)


def analyze_prosody(raw_syllables: list) -> list:
    """
    วิเคราะห์ว่าแต่ละพยางค์เป็นครุหรือลหุ
    """
    syllables_result = []
    for syl_str in raw_syllables:
        if "ฺ" in syl_str or "ํ" in syl_str or "ึ" in syl_str:
            analysis = {"syllable": syl_str, "type": "garu"}
        elif any(v in syl_str for v in "าีูเโ"):
            analysis = {"syllable": syl_str, "type": "garu"}
        else:
            analysis = {"syllable": syl_str, "type": "lahu"}
        syllables_result.append(analysis)
    return syllables_result


# ==============================================================================
#  ส่วนที่ 3: การระบุฉันท์ (Identify Chanda)
# ==============================================================================

# Helper function to normalize pattern string for internal comparison (always use hyphen for garu)
def _normalize_pattern_for_comparison(pattern_str):
    if pattern_str:
        return pattern_str.replace('–', '-') # Convert en-dash to hyphen for comparison
    return pattern_str

# Helper function to ensure pattern is ready for display (always use en-dash for garu)
def _normalize_pattern_for_display(pattern_str):
    if pattern_str:
        return pattern_str.replace('-', '–') # Convert hyphen to en-dash for display
    return pattern_str

# Helper function to check for exact or allowed (ปาทันตครุ) match
def _check_chanda_match(actual_prosody_string: str, target_pattern_for_comp: str) -> bool:
    """
    Checks if actual_prosody_string matches target_pattern_for_comp,
    allowing for Patantagaru (last syllable Lahu where Garu is expected).
    Returns True if matches or is Patantagaru, False otherwise.
    """
    if not actual_prosody_string or not target_pattern_for_comp:
        return False
    if len(actual_prosody_string) != len(target_pattern_for_comp):
        return False

    # Exact match
    if actual_prosody_string == target_pattern_for_comp:
        return True
    
    # Check for Patantagaru (Pādantagaru)
    # Requires matching lengths and only the last syllable differs from Garu to Lahu
    if (len(actual_prosody_string) > 0 and 
        actual_prosody_string[:-1] == target_pattern_for_comp[:-1] and # All but last char match
        target_pattern_for_comp[-1] == '-' and # Expected garu ('-')
        actual_prosody_string[-1] == 'U'): # Actual lahu ('U')
        return True # It's a Patantagaru!

    return False


def identify_chanda_logic(verses_prosody_data: list) -> dict:
    identified_results = []
    Chanda = models.Chanda
    UpajatiSubType = models.UpajatiSubType 

    upendavajira_pattern_obj = Chanda.query.filter_by(name='อุเปนทรวิเชียรฉันท์ ๑๑').first()
    indavajira_pattern_obj = Chanda.query.filter_by(name='อินทรวิเชียรฉันท์ ๑๑').first()
    upajati_chanda_obj = Chanda.query.filter_by(name='อุปชาติฉันท์ ๑๑').first()
    
    all_upajati_sub_types = UpajatiSubType.query.all() 

    # Get raw patterns from DB (might be hyphen or en-dash)
    upendavajira_pattern_raw_from_db = upendavajira_pattern_obj.pattern if upendavajira_pattern_obj else 'U–U––UU–U––'
    indavajira_pattern_raw_from_db = indavajira_pattern_obj.pattern if indavajira_pattern_obj else '––U––UU–U––'

    # Prepare patterns for internal Python comparison (always hyphens)
    upendavajira_pattern_for_comp = _normalize_pattern_for_comparison(upendavajira_pattern_raw_from_db)
    indavajira_pattern_for_comp = _normalize_pattern_for_comparison(indavajira_pattern_raw_from_db)

    # Prepare patterns for frontend display (always en-dashes)
    upendavajira_pattern_for_display = _normalize_pattern_for_display(upendavajira_pattern_raw_from_db)
    indavajira_pattern_for_display = _normalize_pattern_for_display(indavajira_pattern_raw_from_db)

    individual_verse_chanda_types = [None] * len(verses_prosody_data)
    # Store padantagaru status for individual verses to use in Upajati detection notes
    individual_verse_padantagaru_status = [False] * len(verses_prosody_data)


    fixed_vutta_chandas = Chanda.query.all()

    # --- รอบที่ 1: ตรวจสอบแต่ละบาทว่าเป็นฉันท์ใด (รวมถึง อินทรฯ และ อุเปนฯ แบบเดี่ยวๆ) ---
    for verse_index, verse_syllables_data in enumerate(verses_prosody_data):
        current_verse_matches = []
        
        determined_pattern_for_this_verse = None

        if not verse_syllables_data:
            identified_results.append({
                "verse_num": verse_index + 1,
                "matches": [],
                "notes": "ไม่มีข้อมูลพยางค์",
                "syllables_data": [], 
                "determined_pattern": determined_pattern_for_this_verse
            })
            continue

        verse_prosody_string = "".join([syl['type'].replace('lahu', 'U').replace('garu', '-') for syl in verse_syllables_data])
        syllable_count = len(verse_prosody_string)

        # *** ใช้ _check_chanda_match เพื่ออนุโลมปาทันตครุ ***
        is_indavajira_match = _check_chanda_match(verse_prosody_string, indavajira_pattern_for_comp)
        is_upendavajira_match = _check_chanda_match(verse_prosody_string, upendavajira_pattern_for_comp)

        if is_indavajira_match:
            individual_verse_chanda_types[verse_index] = 'อินทรวิเชียร'
            determined_pattern_for_this_verse = indavajira_pattern_for_display # Still display the standard pattern
            # Check if this particular match was due to padantagaru
            if verse_prosody_string != indavajira_pattern_for_comp: # If not an exact match
                individual_verse_padantagaru_status[verse_index] = True
        elif is_upendavajira_match:
            individual_verse_chanda_types[verse_index] = 'อุเปนทรวิเชียร'
            determined_pattern_for_this_verse = upendavajira_pattern_for_display # Still display the standard pattern
            # Check if this particular match was due to padantagaru
            if verse_prosody_string != upendavajira_pattern_for_comp: # If not an exact match
                individual_verse_padantagaru_status[verse_index] = True
        
        for chanda_info_obj in fixed_vutta_chandas:
            if chanda_info_obj.is_mixed_chanda: 
                continue

            if chanda_info_obj.syllable_count == syllable_count:
                # ตรรกะสำหรับปัฐยาวัตรฉันท์
                if 'ปัฐยาวัตร' in chanda_info_obj.name:
                    is_pathyavatta_strict = True # Use a stricter check for pathyavatta internal rules
                    pathyavatta_notes = []
                    
                    if len(verse_syllables_data) < 8:
                        is_pathyavatta_strict = False
                        pathyavatta_notes.append("จำนวนพยางค์ไม่ครบ ๘ พยางค์")
                    if len(verse_syllables_data) >= 3 and verse_syllables_data[1]['type'] == 'lahu' and verse_syllables_data[2]['type'] == 'lahu':
                        is_pathyavatta_strict = False
                        pathyavatta_notes.append("พยางค์ ๒-๓ เป็นลหุคู่กัน (ห้าม)")
                    if len(verse_syllables_data) >= 7:
                        gana_567_string = verse_prosody_string[4:7]
                        if verse_index % 2 == 0: # บาทคี่ (1, 3)
                            if gana_567_string != "U--":
                                is_pathyavatta_strict = False
                                pathyavatta_notes.append("บาทคี่: พยางค์ ๕-๗ ไม่เป็น ย-คณะ (U--) (ผิด)")
                        else: # บาทคู่ (2, 4)
                            if gana_567_string != "U-U":
                                is_pathyavatta_strict = False
                                pathyavatta_notes.append("บาทคู่: พยางค์ ๕-๗ ไม่เป็น ช-คณะ (U-U) (ผิด)")
                    else:
                        if is_pathyavatta_strict:
                            is_pathyavatta_strict = False
                            pathyavatta_notes.append("จำนวนพยางค์ไม่เพียงพอสำหรับการตรวจสอบคณะ (5-7)")
                    
                    if is_pathyavatta_strict:
                        current_verse_matches.append({
                            "id": chanda_info_obj.id,
                            "name": chanda_info_obj.name,
                            "match_type": "ตรงตามกฎปัฐยาวัตร",
                            "pattern": _normalize_pattern_for_display(chanda_info_obj.pattern),
                            "notes": "; ".join(pathyavatta_notes) if pathyavatta_notes else "ตรงตามกฎบังคับ"
                        })
                else: # Other fixed chandas
                    pattern_for_comp_chanda_obj = _normalize_pattern_for_comparison(chanda_info_obj.pattern)
                    # *** ใช้ _check_chanda_match สำหรับฉันท์ประเภทอื่นๆ ด้วย (ถ้าเหมาะสม) ***
                    if _check_chanda_match(verse_prosody_string, pattern_for_comp_chanda_obj): 
                        match_notes = []
                        if verse_prosody_string != pattern_for_comp_chanda_obj: # If not an exact match, it must be padantagaru
                            match_notes.append("ใช้กฎปาทันตครุ")

                        current_verse_matches.append({
                            "id": chanda_info_obj.id, 
                            "name": chanda_info_obj.name,
                            "match_type": "ตรงตามรูปแบบเป๊ะ" if not match_notes else "ตรงตามรูปแบบ (ปาทันตครุ)",
                            "pattern": _normalize_pattern_for_display(chanda_info_obj.pattern),
                            "notes": "; ".join(match_notes) if match_notes else ""
                        })
            
        identified_results.append({
            "verse_num": verse_index + 1,
            "matches": current_verse_matches,
            "notes": "ไม่พบฉันท์ที่ตรงกัน" if not current_verse_matches else "",
            "syllables_data": verse_syllables_data,
            "determined_pattern": determined_pattern_for_this_verse # This is now reliably set for Indavajira/Upendavajira
        })

    # --- รอบที่ 2: ตรวจสอบอุปชาติ (พิจารณาเป็นกลุ่ม 4 บาท) ---
    if upajati_chanda_obj:
        for i in range(0, len(verses_prosody_data), 4):
            if len(verses_prosody_data) - i >= 4:
                block_types = [individual_verse_chanda_types[j] for j in range(i, i + 4)]
                padantagaru_statuses = [individual_verse_padantagaru_status[j] for j in range(i, i + 4)]

                num_indavajira = block_types.count('อินทรวิเชียร')
                num_upendavajira = block_types.count('อุเปนทรวิเชียร')

                # เงื่อนไขการเป็นอุปชาติ: ต้องมีทั้ง อินทรวิเชียร และ อุเปนทรวิเชียร อย่างน้อยอย่างละ 1 บาท
                # และรวมกันแล้วต้องครบ 4 บาท (หมายถึงทุกบาทในบล็อก 4 นั้นต้องเป็นหนึ่งในสองประเภทนี้)
                if num_indavajira + num_upendavajira == 4 and num_indavajira > 0 and num_upendavajira > 0:
                    stanza_num = (i // 4) + 1
                    
                    current_block_sequence = ""
                    for vt in block_types:
                        if vt == 'อินทรวิเชียร':
                            current_block_sequence += "อิ"
                        elif vt == 'อุเปนทรวิเชียร':
                            current_block_sequence += "อุ"
                        else: 
                            current_block_sequence += "?" # ไม่ควรมาถึงตรงนี้ ถ้าเงื่อนไขด้านบนถูก

                    specific_upajati_name = "ไม่ระบุประเภท"
                    for upajati_type_info in all_upajati_sub_types:
                        if upajati_type_info.sequence_pattern == current_block_sequence:
                            specific_upajati_name = upajati_type_info.name
                            break

                    for k in range(4):
                        verse_idx_in_stanza = i + k
                        verse_type_in_stanza = block_types[k]

                        # determined_pattern is already set in Round 1, just ensure it's still correct.
                        # It should be the standard pattern (en-dash).
                        if verse_type_in_stanza == 'อินทรวิเชียร':
                            identified_results[verse_idx_in_stanza]["determined_pattern"] = indavajira_pattern_for_display
                        elif verse_type_in_stanza == 'อุเปนทรวิเชียร':
                            identified_results[verse_idx_in_stanza]["determined_pattern"] = upendavajira_pattern_for_display

                        notes_parts = [f"ประเภท: {specific_upajati_name}", f"อัตราส่วนในคาถา: อิ: {num_indavajira}, อุ: {num_upendavajira}"]
                        if padantagaru_statuses[k]: # If this specific verse used padantagaru
                            notes_parts.append("บาทนี้ใช้กฎปาทันตครุ")
                        notes_str = " (".join(notes_parts) + ")"

                        identified_results[verse_idx_in_stanza]["matches"].append({
                            "id": upajati_chanda_obj.id,
                            "name": upajati_chanda_obj.name,
                            "match_type": "เป็นส่วนหนึ่งของคาถาอุปชาติ",
                            "pattern": f"คาถาที่ {stanza_num} (บาทที่ {k+1}: {verse_type_in_stanza.replace('อินทรวิเชียร','อิ').replace('อุเปนทรวิเชียร','อุ')})",
                            "notes": notes_str
                        })
                        if identified_results[verse_idx_in_stanza]["notes"] == "ไม่พบฉันท์ที่ตรงกัน":
                            identified_results[verse_idx_in_stanza]["notes"] = ""

    all_chanda_patterns_for_display = {}
    for c in fixed_vutta_chandas:
        all_chanda_patterns_for_display[c.id] = {
            "name": c.name, 
            "pattern": _normalize_pattern_for_display(c.pattern) 
        }
    
    return {"results_by_verse": identified_results, "syllable_patterns": all_chanda_patterns_for_display}