"""提取PDF页面为图片"""
import os
import fitz  # PyMuPDF
from PIL import Image


def pdf_page_to_image(pdf_path: str, page_num: int, output_dir: str = "/tmp/pdf_pages") -> str:
    """
    将PDF的指定页面转换为图片
    
    Args:
        pdf_path: PDF文件路径
        page_num: 页码（从1开始）
        output_dir: 输出目录
        
    Returns:
        生成的图片文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]  # PyMuPDF从0开始索引
    
    # 设置缩放比例，提高图片质量
    zoom = 2.0
    mat = fitz.Matrix(zoom, zoom)
    
    pix = page.get_pixmap(matrix=mat)
    img_path = os.path.join(output_dir, f"page_{page_num:03d}.png")
    pix.save(img_path)
    
    doc.close()
    
    return img_path


def extract_multiple_pages(pdf_path: str, start_page: int, end_page: int, output_dir: str = "/tmp/pdf_pages") -> list:
    """
    提取多个页面为图片
    
    Args:
        pdf_path: PDF文件路径
        start_page: 起始页码（从1开始）
        end_page: 结束页码
        output_dir: 输出目录
        
    Returns:
        图片路径列表
    """
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    
    doc = fitz.open(pdf_path)
    
    for page_num in range(start_page, min(end_page, len(doc)) + 1):
        page = doc[page_num - 1]
        
        # 设置缩放比例
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(output_dir, f"page_{page_num:03d}.png")
        pix.save(img_path)
        
        image_paths.append(img_path)
        
        if page_num % 10 == 0:
            print(f"已提取 {page_num} 页...")
    
    doc.close()
    
    return image_paths


if __name__ == "__main__":
    # 测试提取前10页
    pdf_path = "/tmp/thermal_textbook.pdf"
    
    print("提取PDF前10页...")
    images = extract_multiple_pages(pdf_path, 1, 10)
    print(f"已提取 {len(images)} 页:")
    for img in images:
        print(f"  - {img}")
