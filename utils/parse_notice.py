import os, sys, importlib
import json
import pandas as pd
import pdfplumber
from collections import defaultdict
import re
from rapidfuzz import process, fuzz


def extract_words_with_size(path_pdf, page_num):

    with pdfplumber.open(path_pdf) as pdf:

        page = pdf.pages[page_num-1]

        words = page.extract_words(extra_attrs=["size"])

    return words, page.width


def group_words_to_lines(words):

    lines = defaultdict(list)

    for w in words:
        y = round(w["top"], 1)
        lines[y].append(w)

    sorted_lines = sorted(lines.items(), key=lambda x: x[0])

    result = []

    for y, ws in sorted_lines:

        ws = sorted(ws, key=lambda x: x["x0"])

        text = " ".join(w["text"] for w in ws)

        avg_size = sum(w["size"] for w in ws) / len(ws)

        result.append({
            "text": text,
            "size": avg_size,
            "words": ws
        })

    return result


def extract_notice_by_size(lines, prefix, follow_lines=2):

    notices = {}

    for i, line in enumerate(lines):

        # 标题字体阈值
        if line["size"] >= 12:
            block = [line["text"]]            
    
            if block[0].lower().strip().startswith(tuple(prefix)):            # check if a mss indice!
                mss=block[0].lower().strip()
                for j in range(1, follow_lines + 1):
                    if i + j < len(lines):
                        block.append(lines[i + j]["text"])

                notices[mss]=" ".join(block[1:])

    return notices


import re
def eliminate_ponc(s):
    clean_s=re.sub(r'[^\w\s]','',s)
    clean_s=clean_s.strip().lower()
    return clean_s

def get_notice_info(notices):
    notice_info=[]
    for mss, notice in notices.items():
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
            "mss":mss,
            "mateiral":material,
            "cent":cent,
            "size":size,
            }
        
        notice_info.append(info)    
    
    return notice_info


    
    
# def extract_notice(words, page_width, sorted_by="top",follow_lines=1):
#     """
#     Extract centered titles and the following lines
#     """

#     # -----------------------
#     # group words into lines
#     # -----------------------
#     lines = defaultdict(list)

#     for w in words:
#         y = round(w[sorted_by], 1)
#         lines[y].append(w)

#     # sort lines
#     sorted_lines = sorted(lines.items(), key=lambda x: x[0])

#     text_lines = []

#     for y, ws in sorted_lines:

#         ws = sorted(ws, key=lambda x: x["x0"])
#         text = " ".join(w["text"] for w in ws)

#         x0 = ws[0]["x0"]
#         x1 = ws[-1]["x1"]

#         center = (x0 + x1) / 2

#         text_lines.append({
#             "text": text,
#             "center": center
#         })

#     # -----------------------
#     # detect centered lines
#     # -----------------------
#     notices = []
#     page_center = page_width / 2
#     tolerance = page_width * 0.1   # 10% width

#     for i, line in enumerate(text_lines):

#         if abs(line["center"] - page_center) < tolerance:

#             block = [line["text"]]

#             for j in range(1, follow_lines + 1):
#                 if i + j < len(text_lines):
#                     block.append(text_lines[i + j]["text"])

#             notices.append(block)

#     return notices


def get_el_by_fuzzy_research(list_research, contexts, cutoff=70):
    for r in list_research:
        el_contains=[c for c in contexts if r in c]
        if el_contains :
            el=el_contains[0].strip()
            return r, el
        
        #若没有匹配，进行模糊搜索：
        result=process.extractOne(
            r, 
            contexts,
            scorer=fuzz.ratio,
            score_cutoff=cutoff
        )

        if result:            
            # print(result[0])
            idx_result=contexts.index(result[0])
            el=contexts[idx_result].strip()
            # print(f"fuzzy result:{result[0]}")
            
            return result[0],el
        else:
            # print(f"no match for '{r}'!")
            return None, None



# def get_notice_info(notice):
#     #---init---
#     material,cent, size, nb_page, nb_col, nb_lines=None, None, None, None, None, None
        
#     notice_el=notice.split(";")
#     # print(notice_el)
    
#     # #---materia---
#     material=notice_el[0]
#     # print(f"material: {material}")


#     # #---cent & size---   
#     if 'cent' in notice_el[1]:#如果有cent，按cent切分
#         cent=eliminate_ponc(notice_el[1].split("cent")[0])
#         size=eliminate_ponc(notice_el[1].split("cent")[1])
    
#     else: # 没有则找大写切分呢
#         first_upper_idx = next((i for i, c in enumerate(notice_el[1]) if c.isupper()), None)
#         if first_upper_idx:# 若有大写
#             # print(f"first_upper_idx:{first_upper_idx}; first supper :{notice_el[1][first_upper_idx]}")
#             cent=eliminate_ponc(notice_el[1][:first_upper_idx])
#             size=eliminate_ponc(notice_el[1][first_upper_idx:])
  
#     # print(f"century:{cent}")
#     # print(f"size: {size}")
#     # print("\n")
    
    
#     # # ---ff---
#     ff_el=notice_el[2].split(",")
#     # print(f"contexts of 3e el of notice: {ff_el}")

#     #取ff类似字样后的数字！    
#     page_ff=ff_el[0].split()
#     # print(page_ff)
#     first_el_with_f=[_ for _ in page_ff if 'f' in _][0]
#     idx_ff=page_ff.index(first_el_with_f)
#     nb_page=eliminate_ponc(page_ff[idx_ff+1])
#     # print('nb_page:',nb_page)
    

#     col_match, columns=get_el_by_fuzzy_research(list_research=["columns"], contexts=ff_el, cutoff=70)
#     if columns:
#         columns_list=[eliminate_ponc(_) for _ in columns.split()]
#         idx_col=columns_list.index(col_match)#取col前的一个词
#         nb_col=columns_list[idx_col-1]
    
    
#     lines_match, lines_per_page=get_el_by_fuzzy_research(list_research=["lines"], contexts=ff_el, cutoff=70)
#     if lines_per_page:        
#         lines_per_page_list=[eliminate_ponc(_) for _ in lines_per_page.split()]
#         idx_lines=lines_per_page_list.index(lines_match)#取col前的一个词
#         nb_lines=lines_per_page_list[idx_lines-1]
    
#     # print(f"page: {nb_page}")
#     # print(f"nb of columns: {nb_col}")
#     # print(f"lines_per_page: {nb_lines}")
    
#     info={"mateiral":material,
#           "cent":cent,
#           "size":size,
#           "nb_page":nb_page,
#           "nb_columns":nb_col,
#           "lines_per_page":nb_lines
#           }
    
    
#     return info
