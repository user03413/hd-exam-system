"""PDF内容获取工具"""
import os
import requests
from coze_coding_dev_sdk.fetch import FetchClient
from coze_coding_utils.runtime_ctx.context import new_context


def fetch_pdf_content(url: str) -> dict:
    """
    获取PDF文件内容
    
    Args:
        url: PDF文件的URL
        
    Returns:
        包含文档信息的字典，包括标题和文本内容
    """
    # 先尝试直接下载PDF文件
    try:
        print(f"正在下载PDF: {url[:100]}...")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # 保存到临时文件
        temp_pdf_path = "/tmp/thermal_textbook.pdf"
        with open(temp_pdf_path, "wb") as f:
            f.write(response.content)
        
        print(f"PDF已下载到: {temp_pdf_path}")
        print(f"文件大小: {len(response.content)} 字节")
        
        # 使用PyPDF2或pdfplumber提取文本
        try:
            import pdfplumber
            
            text_content = []
            page_texts = []
            with pdfplumber.open(temp_pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"总页数: {total_pages}")
                
                # 提取所有页面的文本
                for i, page in enumerate(pdf.pages):
                    if (i + 1) % 50 == 0:
                        print(f"正在处理第 {i+1}/{total_pages} 页...")
                    text = page.extract_text()
                    if text and len(text.strip()) > 10:  # 只保留有实质内容的页面
                        page_texts.append({
                            "page_num": i + 1,
                            "text": text.strip()
                        })
            
            print(f"提取到 {len(page_texts)} 页有效内容")
            
            # 如果提取的内容很少，可能是扫描版PDF，需要使用OCR
            if len(page_texts) < total_pages * 0.5:
                print("检测到可能是扫描版PDF，内容提取率较低")
                print("将使用视觉模型识别PDF内容...")
                
                # 返回基本信息，后续使用多模态模型处理
                return {
                    "title": "火电厂热工自动控制技术及应用",
                    "url": url,
                    "content": "PDF为扫描版，需要使用视觉模型处理",
                    "total_pages": total_pages,
                    "pdf_path": temp_pdf_path,
                    "status_code": 0,
                    "status_message": "success_ocr_needed",
                    "page_texts": page_texts,
                }
            
            # 合并所有页面文本
            full_text = "\n\n".join([f"--- 第 {p['page_num']} 页 ---\n{p['text']}" for p in page_texts])
            
            return {
                "title": "火电厂热工自动控制技术及应用",
                "url": url,
                "content": full_text,
                "total_pages": total_pages,
                "status_code": 0,
                "status_message": "success",
                "page_texts": page_texts,
            }
        except ImportError:
            print("pdfplumber未安装，尝试安装...")
            os.system("pip install pdfplumber -q")
            import pdfplumber
            
            text_content = []
            page_texts = []
            with pdfplumber.open(temp_pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"总页数: {total_pages}")
                
                for i, page in enumerate(pdf.pages):
                    if (i + 1) % 50 == 0:
                        print(f"正在处理第 {i+1}/{total_pages} 页...")
                    text = page.extract_text()
                    if text and len(text.strip()) > 10:
                        page_texts.append({
                            "page_num": i + 1,
                            "text": text.strip()
                        })
            
            print(f"提取到 {len(page_texts)} 页有效内容")
            
            if len(page_texts) < total_pages * 0.5:
                print("检测到可能是扫描版PDF，内容提取率较低")
                print("将使用视觉模型识别PDF内容...")
                
                return {
                    "title": "火电厂热工自动控制技术及应用",
                    "url": url,
                    "content": "PDF为扫描版，需要使用视觉模型处理",
                    "total_pages": total_pages,
                    "pdf_path": temp_pdf_path,
                    "status_code": 0,
                    "status_message": "success_ocr_needed",
                    "page_texts": page_texts,
                }
            
            full_text = "\n\n".join([f"--- 第 {p['page_num']} 页 ---\n{p['text']}" for p in page_texts])
            
            return {
                "title": "火电厂热工自动控制技术及应用",
                "url": url,
                "content": full_text,
                "total_pages": total_pages,
                "status_code": 0,
                "status_message": "success",
                "page_texts": page_texts,
            }
            
    except Exception as e:
        print(f"下载PDF失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "title": "",
            "url": url,
            "content": "",
            "status_code": -1,
            "status_message": f"失败: {str(e)}",
        }


if __name__ == "__main__":
    # 测试获取PDF内容
    test_url = "https://coze-coding-project.tos.coze.site/create_attachment/2026-03-10/3581539791940903_be3ac87a1510c50ea68a7686a818ae75_%E7%81%AB%E7%94%B5%E5%8E%82%E7%83%AD%E5%B7%A5%E8%87%AA%E5%8A%A8%E6%8E%A7%E5%88%B6%E6%8A%80%E6%9C%AF%E5%8F%8A%E5%BA%94%E7%94%A8%20%28%E5%88%98%E7%A6%BE%EF%BC%8C%E7%99%BD%E7%84%B0%EF%BC%8C%E6%9D%8E%E6%96%B0%E5%88%A9%E7%BC%96%E8%91%97,%20%E5%88%98%E7%A6%BE,%20%E7%99%BD%E7%84%B0,%20%E6%9D%8E%E6%96%B0%E5%88%A9%E7%BC%96%E8%91%97,%20%E5%88%98%E7%A6%BE,%20%E7%99%BD%E7%84%B0,%20%E6%9D%8E%E6%96%B0%E5%88%A9%29%20%28z-library.sk,%201lib.sk,%20z-lib.sk%29.pdf?sign=4895194411-5e30fe7814-0-468dce8bbf7a1d19acad478d6fa222bbbc3d65919346b4a9d1db459a34b0c2e6"
    result = fetch_pdf_content(test_url)
    
    print(f"标题: {result['title']}")
    print(f"状态码: {result['status_code']}")
    print(f"内容长度: {len(result['content'])} 字符")
    print(f"\n前1000字符:\n{result['content'][:1000]}")
