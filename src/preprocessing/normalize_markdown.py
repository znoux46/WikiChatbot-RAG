import markitdown
import re
from pathlib import Path
import os

def normalize_markdown(md_text):

    lines = md_text.split('\n')
    normalized_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Nếu là header, giữ nguyên
        if line.strip().startswith('#'):
            normalized_lines.append(line)
            i += 1
            continue
        
        # Nếu là bullet point, table, hoặc dòng trống, giữ nguyên
        if (line.strip().startswith(('* ', '- ', '+ ', '|', '>')) or 
            re.match(r'^\s*\d+\.', line) or
            line.strip() == '' or
            line.strip().startswith(':')):
            normalized_lines.append(line)
            i += 1
            continue
        
        # Gộp các dòng liên tiếp không phải là đoạn đặc biệt
        paragraph = line
        i += 1
        while i < len(lines):
            next_line = lines[i]
            # Dừng nếu gặp dòng trống, header, bullet, table
            if (next_line.strip() == '' or 
                next_line.strip().startswith(('#', '* ', '- ', '+ ', '|', '>', ':')) or
                re.match(r'^\s*\d+\.', next_line)):
                break
            # Gộp dòng
            paragraph += ' ' + next_line.strip()
            i += 1
        
        normalized_lines.append(paragraph)
    
    # Join và làm sạch khoảng trắng thừa
    result = '\n'.join(normalized_lines)
    
    # Chuẩn hóa bullet points: chuyển tất cả thành *
    result = re.sub(r'^\s*[-+]\s+', '* ', result, flags=re.MULTILINE)
    
    # Loại bỏ khoảng trắng thừa ở cuối dòng
    result = re.sub(r' +\n', '\n', result)
    
    # Chuẩn hóa block quotes: chuyển : thành >
    result = re.sub(r'^:   \*', '>   *', result, flags=re.MULTILINE)
    result = re.sub(r'^:\s+', '> ', result, flags=re.MULTILINE)
    
    # Đảm bảo có dòng trống trước header
    result = re.sub(r'\n(#{1,6}\s)', r'\n\n\1', result)
    # Loại bỏ nhiều dòng trống liên tiếp (giữ tối đa 2)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()

def convert_html_to_normalized_md(html_file_path, output_md_file_path = None):

    md = markitdown.MarkItDown()   

    rs = md.convert(html_file_path)
    normalized_md = normalize_markdown(rs.text_content)

    if output_md_file_path is None:
        name = Path(html_file_path).stem
        output_md_file_path = "data/processed_data/{}.md".format(name)
    
    os.makedirs(os.path.dirname(output_md_file_path), exist_ok=True)
    with open(output_md_file_path, "w", encoding="utf-8") as f:
        f.write(normalized_md)

    print(f"Đã lưu markdown đã chuẩn hóa vào: {output_md_file_path}")

    return output_md_file_path

    