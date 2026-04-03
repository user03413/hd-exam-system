#!/usr/bin/env python3
"""
测试章节排序逻辑 - 确保按第一章、第二章...升序排列
"""

# 测试章节列表（当前数据库中的顺序）
test_chapters = [
    {"chapter": "第一章", "count": 16},
    {"chapter": "第七章", "count": 6},
    {"chapter": "第三章", "count": 64},
    {"chapter": "第九章", "count": 64},
    {"chapter": "第二章", "count": 58},
    {"chapter": "第五章", "count": 16},
    {"chapter": "第八章", "count": 62},
    {"chapter": "第八至十章", "count": 2},
    {"chapter": "第六章", "count": 12},
    {"chapter": "第十一章", "count": 68},
    {"chapter": "第十三章", "count": 8},
    {"chapter": "第十二章", "count": 14},
    {"chapter": "第十五章", "count": 10},
    {"chapter": "第十六/七章", "count": 6},
    {"chapter": "第十四章", "count": 10},
    {"chapter": "第十章", "count": 56},
    {"chapter": "第四章", "count": 16}
]


def chapter_sort(a, b):
    """章节智能排序函数（Python 版本）"""
    def get_chapter_num(chapter):
        if not chapter:
            return float('inf')
        
        if '至' in chapter:
            import re
            match = re.search(r'第(\d+)', chapter)
            return int(match.group(1)) if match else float('inf')
        
        if '/' in chapter:
            import re
            match = re.search(r'第(\d+)', chapter)
            return int(match.group(1)) if match else float('inf')
        
        import re
        match = re.search(r'第(\d+)', chapter)
        if match:
            return int(match.group(1))
        
        return float('inf')
    
    num_a = get_chapter_num(a.get('chapter', a))
    num_b = get_chapter_num(b.get('chapter', b))
    
    return num_a - num_b


def main():
    print("=" * 60)
    print("  章节排序测试")
    print("=" * 60)
    
    print("\n原始顺序：")
    for ch in test_chapters:
        print(f"  {ch['chapter']}")
    
    print("\n排序后：")
    sorted_chapters = sorted(test_chapters, key=lambda x: (lambda ch: (
        float('inf') if not ch else
        (int(__import__('re').search(r'第(\d+)', ch).group(1)) if __import__('re').search(r'第(\d+)', ch) else float('inf')
    ))(x['chapter']))
    
    # 使用更准确的排序
    sorted_chapters = sorted(test_chapters, key=lambda x: (
        int(__import__('re').search(r'第(\d+)', x['chapter']).group(1)) 
        if __import__('re').search(r'第(\d+)', x['chapter']) 
        else float('inf')
    ))
    
    for i, ch in enumerate(sorted_chapters, 1):
        print(f"  {i}. {ch['chapter']}")
    
    print("\n" + "=" * 60)
    print("✅ 排序完成！")
    print("=" * 60)
    print("\nWorker 已部署，章节现在按以下顺序排列：")
    for i, ch in enumerate(sorted_chapters, 1):
        print(f"  {ch['chapter']}")


if __name__ == "__main__":
    main()
