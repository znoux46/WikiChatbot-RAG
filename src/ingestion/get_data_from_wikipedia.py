import wikipedia
import os

def get_html_page_from_wikipedia(keyword="Hồ Chí Minh", output_path=None):
    wikipedia.set_lang("vi")

    pages = wikipedia.search(keyword)
    if (pages is None) or (len(pages) == 0):
        raise ValueError(f"Không tìm thấy trang Wikipedia cho từ khóa: {keyword}")
    print("Found pages:", pages)
    
    # Lấy trang đầu tiên từ kết quả tìm kiếm
    page = wikipedia.page(pages[0])

    if not page:
        raise ValueError(f"Không tìm thấy trang Wikipedia cho từ khóa: {keyword}")
    
    html_content = page.html()
    print(f"Đã lấy nội dung HTML từ Wikipedia cho '{keyword}'")

    if output_path is None:
        # Tạo path để lưu file raw html vào data/raw_data/wikipedia/
        output_path = os.path.join("data", "raw_data", "wikipedia", f"{page.title.replace(' ', '_')}.html")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Đã lưu HTML vào: {output_path}")

    return output_path