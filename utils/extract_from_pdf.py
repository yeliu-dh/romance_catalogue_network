import pdfplumber
from collections import defaultdict




def extract_words_per_page(path_pdf, start_page=10):
    """
    read text of a certain page
    """
    with pdfplumber.open(path_pdf) as pdf:
        pages = pdf.pages[start_page:start_page+1]
        for i, page in enumerate(pages):
            words = page.extract_words()
    return words


def group_words_into_lines(words, y_tolerance=2):
    """
    按照提取出的词的bottom坐标，整理成行
    
    """
    
    lines = defaultdict(list)
    for w in words:
        # 用四舍五入避免轻微浮动
        line_key = round(w["bottom"] / y_tolerance) * y_tolerance
        lines[line_key].append(w)

    # 按从上到下排序
    sorted_lines = []
    for key in sorted(lines.keys()):
        # 每行内部按 x0 排序（从左到右）
        line_words = sorted(lines[key], key=lambda x: x["x0"])
        line_text = " ".join(w["text"] for w in line_words)
        sorted_lines.append(line_text.strip())
    return sorted_lines


def extract_text_from_pdf(path_pdf, start_page, end_page):
    all_lines=[]
    for page in range(start_page, end_page):
        print(f"page {page}".center(100,"-"))
        words=extract_words_per_page(path_pdf, page)
        lines = group_words_into_lines(words)
        all_lines.extend(lines)
        for line in lines:
            print(line)
    return all_lines
            
