"""上传文件到对象存储"""
import os
from coze_coding_dev_sdk.s3 import S3SyncStorage


def upload_file_to_storage(file_path: str, custom_name: str = None) -> dict:
    """
    上传文件到对象存储
    
    Args:
        file_path: 本地文件路径
        custom_name: 自定义文件名（可选）
        
    Returns:
        包含文件key和访问URL的字典
    """
    # 初始化存储客户端
    storage = S3SyncStorage(
        endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
        access_key="",
        secret_key="",
        bucket_name=os.getenv("COZE_BUCKET_NAME"),
        region="cn-beijing",
    )
    
    # 读取文件内容
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    # 确定文件名
    if custom_name:
        file_name = custom_name
    else:
        file_name = os.path.basename(file_path)
    
    # 确定Content-Type
    if file_name.endswith('.xlsx'):
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif file_name.endswith('.xls'):
        content_type = "application/vnd.ms-excel"
    elif file_name.endswith('.pdf'):
        content_type = "application/pdf"
    else:
        content_type = "application/octet-stream"
    
    print(f"正在上传文件: {file_name}")
    print(f"文件大小: {len(file_content) / 1024:.2f} KB")
    
    # 上传文件
    key = storage.upload_file(
        file_content=file_content,
        file_name=f"exam_questions/{file_name}",
        content_type=content_type,
    )
    
    print(f"文件已上传，key: {key}")
    
    # 生成访问URL
    url = storage.generate_presigned_url(key=key, expire_time=86400 * 7)  # 7天有效期
    
    print(f"访问URL: {url}")
    
    return {
        "key": key,
        "url": url,
        "file_name": file_name,
        "file_size": len(file_content),
    }


if __name__ == "__main__":
    file_path = "/tmp/热工自动控制试题集.xlsx"
    
    result = upload_file_to_storage(file_path)
    
    print(f"\n===== 上传完成 =====")
    print(f"文件名: {result['file_name']}")
    print(f"文件大小: {result['file_size'] / 1024:.2f} KB")
    print(f"对象Key: {result['key']}")
    print(f"下载链接: {result['url']}")
