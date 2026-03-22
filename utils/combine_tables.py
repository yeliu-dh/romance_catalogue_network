import os, sys, importlib
import json
import re
from rapidfuzz import process, fuzz
import pandas as pd




def split_by_ff(s: str):
    if "ff" in s:
        left, right = s.split("ff", 1)
        return left.strip(), "ff" + right.strip()
    return s.strip(), None



def complie_index_table(index_table):
    """
    key:str 
    title of text
    
    value:dict
    {"collection": ,
    "mss":
    "ff":
    "page":
    }
    
    """
            
    index_table_clean={}
    for coll, works in index_table.items():
        for work in works:
            title = work['name'].lower().strip()
            page = work['page']
            mss_ff = work["mss"].lower().strip()

            mss, ff = split_by_ff(mss_ff)

            if title not in index_table_clean:
                index_table_clean[title] = []# one title=> plu mss!

            index_table_clean[title].append({
                'collection':coll.lower(),
                "mss_ff":mss_ff,
                'mss':mss,
                'ff': ff,
                'page': page
            })
    return index_table_clean



def extract_cycle(s):
    if "cycle" in s.lower():
        left, right = s.split(":", 1)
        return left.strip().lower(), right.strip().lower()
    return None, s.strip().lower()
    
def extract_author(s):
    if ", by" in s:
        left, right = s.split(", by", 1)
        return left.strip().lower(), right.strip().lower()
    return s.strip().lower(), None

def get_short_title(s):
    if '(' in s:
        s=re.sub(r'\s*\(.*?\)', '', s).strip()
        # re.sub(pattern, replacement, string)
        # 0+ space, (, 1+ letters, )
    if "," in s:
        first, rest=s.split(',',1)
        return first

    return s






def get_mss_info(title_theme, index_table_clean, score_cutoff=70):
    """
    get mss info from index table by the title of text

    """    
    # 1. EXACT match
    if title_theme in index_table_clean:
        title_index=title_theme
        return title_index, index_table_clean[title_theme]
    
    # 2. FUZZY match
    result = process.extractOne(
        title_theme,
        index_table_clean.keys(),
        scorer=fuzz.ratio,
        score_cutoff=score_cutoff
    )
    
    if result:
        best_match, score, _ = result
        title_index=best_match
        # print(f"Fuzzy match: {best_match} (score={score})")
        return title_index, index_table_clean[best_match]
    # print(f"[No match] found for {title}")
    return None, []



def compile_combined_table(index_table_clean,theme_table):
    
    # -----STEP1:match mss info and theme info -----
    table_clean=[]
    for theme, works in theme_table.items():
        for work in works:
            # ---theme---
            page=work['page'] 
            s=work['title']
            cycle, title_author = extract_cycle(s)
            title_theme, author =extract_author(title_author)
            
            # ---mss---  
            # 高分 exact / near match; 低分 short title match  
            title_index, mss_info=get_mss_info(title_theme, index_table_clean, score_cutoff=80)
            
            if not mss_info:
                short_title_theme=get_short_title(title_theme)
                # print('short title:',short_title)
                title_index, mss_info=get_mss_info(short_title_theme, index_table_clean, score_cutoff=60)

            if not mss_info:
                print(f"[No match] title theme'{title_theme}' not found in table index!")
                data={
                    'title_theme':title_theme,
                    'title_index':None,
                    'author':author,
                    'theme':theme.lower(),
                    'cycle':cycle,
                    'collection': None,
                    'mss_ff': None,
                    'mss':None,
                    'ff': None,
                    'page':page
                } 
                table_clean.append(data)
                
            for info in mss_info:
                data={
                    'title_theme':title_theme,
                    'title_index':title_index,
                    'author':author,
                    'theme':theme.lower(),
                    'cycle':cycle,
                    'collection': info.get("collection",None),
                    "mss_ff":info.get('mss_ff',None),
                    'mss': info.get("mss",None),
                    'ff': info.get("ff",None),
                    'page':page
                } 
                table_clean.append(data)


    # -----STEP2: add no match in index_table in table_clean!------
    table_clean_title_index=set([data['title_index'] for data in table_clean])

    index_table_nomatch = {
        title_index: data
        for title_index, data in index_table_clean.items()
        if title_index not in table_clean_title_index
    }
    print(f"no match title index: {index_table_nomatch.keys()}\n")

    for title_index, infos in index_table_nomatch.items():
        # print(title_index)
        # print(len(infos))
        for info in infos :
            data={
                'title_theme':None,
                'title_index':title_index,
                'author':None,
                'theme':None,
                'cycle':None,
                'collection': info.get('collection',None),
                "mss_ff":info.get('mss_ff',None),
                'mss':info.get('mss',None),
                'ff': info.get('ff',None),
                'page':info.get('page',None),
            } 
            table_clean.append(data)
            
            
    ##------------- STEP3:to_csv-----------
    df_table=pd.DataFrame(table_clean)
    def compile_mss_index(row):
        coll=row["collection"]
        mss_ff=row['mss_ff']
        
        if mss_ff and coll:
            if not mss_ff.startswith(coll):
                mss_index=f"{coll} {mss_ff}"
            else : 
                mss_index=f"{mss_ff}"
        else :
            mss_index=None
    
        return mss_index
    df_table['mss_index']=df_table.apply(lambda row : compile_mss_index(row), axis=1)
    
    return df_table


