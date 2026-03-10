"""使用视觉模型识别PDF页面内容"""
import os
import sys
import json
from coze_coding_dev_sdk import LLMClient
from coze_coding_dev_sdk.s3 import S3SyncStorage
from coze_coding_utils.runtime_ctx.context import new_context
from langchain_core.messages import SystemMessage, HumanMessage

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.pdf_page_extractor import extract_multiple_pages


def upload_image_to_storage(image_path: str, storage: S3SyncStorage) -> str:
    """上传图片到对象存储并返回URL"""
    with open(image_path, "rb") as f:
        image_content = f.read()
    
    file_name = os.path.basename(image_path)
    key = storage.upload_file(
        file_content=image_content,
        file_name=f"pdf_pages/{file_name}",
        content_type="image/png",
    )
    
    url = storage.generate_presigned_url(key=key, expire_time=3600)
    return url


def recognize_page_content(image_url: str, client: LLMClient, page_type: str = "content") -> dict:
    """
    使用视觉模型识别页面内容
    
    Args:
        image_url: 图片URL
        client: LLM客户端
        page_type: 页面类型 (cover, toc, content)
        
    Returns:
        识别结果
    """
    prompts = {
        "cover": """请识别这个PDF封面的内容，提取以下信息：
1. 书名
2. 作者
3. 出版社
4. 版本信息
以JSON格式返回结果。""",
        
        "toc": """这是教材的目录页，请识别并提取目录内容。
以JSON格式返回，格式如下：
{
  "chapters": [
    {"chapter_num": "第一章", "title": "章节标题", "page": "起始页码"},
    ...
  ]
}""",
        
        "content": """这是教材的内容页，请识别页面内容。
返回格式：
{
  "page_num": 页码,
  "chapter": "所属章节",
  "content": "页面主要内容（概括性描述，不需要逐字识别）",
  "key_points": ["知识点1", "知识点2", ...]
}"""
    }
    
    messages = [
        SystemMessage(content="你是一个专业的文档识别助手，擅长识别和提取PDF文档中的结构化信息。"),
        HumanMessage(content=[
            {
                "type": "text",
                "text": prompts.get(page_type, prompts["content"])
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            }
        ])
    ]
    
    response = client.invoke(
        messages=messages,
        model="doubao-seed-1-6-vision-250815",
        temperature=0.1
    )
    
    # 处理响应内容
    content = response.content
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = " ".join([item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"])
    else:
        text = str(content)
    
    # 尝试解析JSON
    try:
        # 提取JSON部分
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
        else:
            json_str = text.strip()
        
        return json.loads(json_str)
    except:
        return {"raw_text": text}


def analyze_textbook_structure(pdf_path: str = "/tmp/thermal_textbook.pdf", max_pages: int = 10):
    """
    分析教材结构
    
    Args:
        pdf_path: PDF文件路径
        max_pages: 最多分析的页数
        
    Returns:
        教材结构信息
    """
    print("初始化客户端...")
    ctx = new_context(method="analyze_textbook")
    client = LLMClient(ctx=ctx)
    
    storage = S3SyncStorage(
        endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
        access_key="",
        secret_key="",
        bucket_name=os.getenv("COZE_BUCKET_NAME"),
        region="cn-beijing",
    )
    
    print(f"提取PDF前{max_pages}页...")
    image_paths = extract_multiple_pages(pdf_path, 1, max_pages)
    
    results = {
        "cover": None,
        "toc": [],
        "pages": []
    }
    
    # 识别封面（第1页）
    print("\n识别封面...")
    cover_url = upload_image_to_storage(image_paths[0], storage)
    results["cover"] = recognize_page_content(cover_url, client, "cover")
    print(f"封面信息: {results['cover']}")
    
    # 识别目录页（第2-8页）
    print("\n识别目录...")
    for i in range(1, min(8, len(image_paths))):
        page_url = upload_image_to_storage(image_paths[i], storage)
        toc_info = recognize_page_content(page_url, client, "toc")
        if toc_info and "chapters" in toc_info:
            results["toc"].extend(toc_info["chapters"])
            print(f"第{i+1}页目录: 找到 {len(toc_info.get('chapters', []))} 个章节")
    
    # 识别前几页内容
    print("\n识别内容页...")
    for i in range(8, min(max_pages, len(image_paths))):
        page_url = upload_image_to_storage(image_paths[i], storage)
        content_info = recognize_page_content(page_url, client, "content")
        results["pages"].append(content_info)
        print(f"已识别第{i+1}页")
    
    return results


if __name__ == "__main__":
    result = analyze_textbook_structure(max_pages=10)
    
    # 保存结果
    output_path = "/tmp/textbook_structure.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_path}")
    print(f"\n教材结构:")
    print(f"  - 封面: {result['cover']}")
    print(f"  - 章节数: {len(result['toc'])}")
    print(f"  - 已识别页数: {len(result['pages'])}")
