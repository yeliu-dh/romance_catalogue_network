import os, sys, importlib
import json
import re
import pandas as pd
import time
from tqdm import tqdm
import pdfplumber
from collections import defaultdict
import statistics

# -------------------------
# 1️⃣ extract words
# -------------------------
def extract_words_per_page(path_pdf, page_num):

    with pdfplumber.open(path_pdf) as pdf:

        page = pdf.pages[page_num-1]

        words = page.extract_words(extra_attrs=["size"])

    return words

def extract_words_start_end(path_pdf, start_page, end_page):

    with pdfplumber.open(path_pdf) as pdf:

        page = pdf.pages[start_page-1:end_page]

        words = page.extract_words(extra_attrs=["size"])

    return words


# -------------------------
# 2️⃣ group words → lines
# -------------------------
def group_words_to_lines(words):

    lines = defaultdict(list)

    for w in words:

        if not isinstance(w, dict):
            continue

        if "top" not in w:
            continue

        y = round(w["top"], 1)
        lines[y].append(w)

    sorted_lines = sorted(lines.items(), key=lambda x: x[0])

    result = []

    for y, ws in sorted_lines:

        ws = sorted(ws, key=lambda x: x["x0"])

        text = " ".join(w["text"] for w in ws)

        avg_size = sum(w.get("size", 0) for w in ws) / len(ws)

        x0 = ws[0]["x0"]
        x1 = ws[-1]["x1"]
        center = (x0 + x1) / 2

        result.append({
            "text": text.strip(),
            "size": avg_size,
            "center": center,
            "words": ws
        })

    return result


# -------------------------
# 3️⃣ detect notices
# -------------------------


def has_letter_and_digit(s):
    return any(c.isalpha() for c in s) and any(c.isdigit() for c in s)



def extract_notices(lines, follow_lines=3):
    prefix=['royal',
            'cotton',
            'harley',
            'lansdowne',
            'arundel',
            'burney',
            'sloane',
            'add',# 'additional'
            'egerton'
        ]

    notices = {}

    # 自动估计正文字体大小
    # sizes = [l["size"] for l in lines if l["size"] > 0]
    # body_size = statistics.median(sizes) if sizes else 10
    # print(f"body font size:{body_size}\n")
    
    # page_center = page_width / 2

    for i, line in enumerate(lines):

        text = line["text"]

        # -------------------------
        # 标题判断（多条件组合）
        # -------------------------
        # is_centered = abs(line["center"] - page_center) < page_width * 0.15
        is_large = line["size"] > 10 #body_size #* 1.2
        # is_short = len(text.split()) <= 10
        startswith_coll=text.lower().startswith(tuple(prefix))
        is_mixed=has_letter_and_digit(text)
        # print(f'is large:{is_large}; startswith_coll:{startswith_coll}; is_mixed: {is_mixed}!\n')
        # if is_centered and is_large and is_short:
        
        
        if is_large and startswith_coll and is_mixed:
            mss=text.lower().strip()
            # print(f"valid line: {line}\n")  
            block = []
            # -------------------------
            # 抓取后续行
            # -------------------------
            for j in range(1, follow_lines + 1):

                if i + j < len(lines):
                    next_text = lines[i + j]["text"]

                    # 跳过空行
                    if not next_text.strip():
                        continue
                    block.append(next_text)
            # block_s=" ".join(block)

            notices[mss]=" ".join(block) #.append(block)

    return notices



import re
def eliminate_ponc(s):
    clean_s=re.sub(r'[^\w\s]','',s)
    clean_s=clean_s.strip().lower()
    return clean_s


def get_notice_info(notices):
    notice_info=[]
    for mss, notice in notices.items():
        if notice.count(";")>=2:
            # print(mss)
            # print(f"{notice.count(';')} in '{notice}' \n")
            
            try:
                #---init---
                material,cent, size=None, None, None
                
                notice_el=notice.split(";")
                # print(notice_el)
                
                # #---materia---
                material=notice_el[0].lower().strip()
                # print(f"material: {material}")

                # #---cent & size---   
                if 'cent' in notice_el[1]:#如果有cent，按cent切分
                    cent=eliminate_ponc(notice_el[1].split("cent")[0])      
                    size=eliminate_ponc(notice_el[1].split("cent")[1])

                else: # 没有则找大写切分呢
                    first_upper_idx = next((i for i, c in enumerate(notice_el[1]) if c.isupper()), None)
                    if first_upper_idx:# 若有大写
                        # print(f"first_upper_idx:{first_upper_idx}; first supper :{notice_el[1][first_upper_idx]}")
                        cent=eliminate_ponc(notice_el[1][:first_upper_idx])
                        size=eliminate_ponc(notice_el[1][first_upper_idx:])
        
                info={
                    "notice":notice,
                    "mss":mss,
                    "material":material,
                    "cent":cent,
                    "size":size,
                    
                    }
            
                notice_info.append(info)    
            except Exception as e:
                print(f"[error] {e} \n")
                continue
    return notice_info


# -------------------------
# 4️⃣ full pipeline
# -------------------------
def extract_notice_pipeline(path_pdf, start_page, end_page):
    result=[]
    for p in range(start_page, end_page+1):
        print(f"page {p}".center(100, '-'))
        words_per_page= extract_words_per_page(path_pdf, page_num=p)
        lines = group_words_to_lines(words_per_page)
        # print(lines)
        notices = extract_notices(lines, follow_lines=2)
        print(notices)
        
        notice_info=get_notice_info(notices)
        print(notice_info)    
        result.extend(notice_info)
    return result







# ====================================CLEAN================================

from rapidfuzz import process, fuzz

def fuzzy_research(request, contexts, cutoff=70):
    # for r in list_research:
    # 若contexts中铀元素包含待查询内容
    el_contains=[c for c in contexts if request in c]
    if el_contains :
        el=el_contains[0].strip()
        return request
        
    #若没有匹配，进行模糊搜索：
    result=process.extractOne(
        request, 
        contexts,
        scorer=fuzz.ratio,
        score_cutoff=cutoff
    )
    if result:            
        # print(result[0])
        idx_result=contexts.index(result[0])
        el=contexts[idx_result].strip()
        # print(f"fuzzy result:{result[0]}")   
        return result[0]
    
    else:
        # print(f"no match for '{r}'!")
        return None
    
import re

def fuzzy_research2(request, contexts, cutoff=70): 
    if not request:
        return None
    
    for c in contexts :
        if c in request:
            return c  
    
    #若没有匹配，进行模糊搜索：
    result=process.extractOne(
        request, 
        contexts,
        scorer=fuzz.ratio,
        score_cutoff=cutoff
    )# results是request在contexts中的匹配，所以是从contexts中选
    
    if result:              
        return result[0]
    
    else:
        print(f"no match for '{request}'!")
        return None
    
    
    
    
    
# --- 罗马数字转换 ---
def roman_to_int(s):
    roman_map = {'i':1, 'v':5, 'x':10, 'l':50, 'c':100, 'd':500, 'm':1000}
    s = s.lower()
    
    total = 0
    prev = 0
    for char in reversed(s):
        if char not in roman_map:
            return None
        val = roman_map[char]
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    return total


# --- OCR 清洗 ---
def clean_ocr(text):
    text = text.lower()
    
    # 常见 OCR 错误替换（可以继续加）
    replacements = {
        ' ': '',
        '0': 'o',
        '1': 'i',
        '5': 's',
        'm': 'n',   # xmih → xnih（有时有用）
        'z': 's',   # zrth → srth
    }
    
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    return text


# --- 主函数 ---
def parse_century(text):
    if not text or not isinstance(text, str):
        return None
    
    text = text.lower().strip()
    
    # =========================
    # 🧩 情况1：包含 th → 罗马序数
    # =========================
    if 'th' in text:
        text_clean = clean_ocr(text)
        
        # 提取罗马部分
        match = re.search(r'([ivxlcdm]+)th', text_clean)
        if match:
            roman = match.group(1)
            num = roman_to_int(roman)
            
            # 简单合理性过滤
            if num and 1 <= num <= 30:
                return int(num)

        return None
    
    # =========================
    # 🧩 情况2：年份 → 世纪
    # =========================
    # 提取数字
    match = re.search(r'\d{3,4}', text)
    if match:
        year = int(match.group())
        
        # 世纪计算公式
        century = (year - 1) // 100 + 1
        return int(century)
    
    return None

# tests = [
#     'xvth',
#     'xmih',
#     'l ate xy th',
#     'zrth',
#     'about 1400',
#     'about 1824',
#     '1680',
#     None
# ]

# for t in tests:
#     print(t, "→", parse_century(t))