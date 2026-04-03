// 测试章节排序算法 - 修复版
const testChapters = [
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
];

console.log("原始顺序:");
testChapters.forEach((ch, i) => console.log(`${i+1}. ${ch.chapter}`));

console.log("\n\n排序后:");

// 绝对可靠的排序算法
function chapterSort(a, b) {
  // 中文数字映射
  const numMap = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14,
    '十五': 15, '十六': 16, '十七': 17, '十八': 18,
    '十九': 19, '二十': 20
  };
  
  function getChapterNumber(chapterStr) {
    if (!chapterStr) return 999;
    
    // 匹配 "第X章" 中的 X
    const match = chapterStr.match(/第([一二三四五六七八九十]+)/);
    if (match && match[1]) {
      const chineseNum = match[1];
      
      // 先尝试直接找映射
      if (numMap[chineseNum]) {
        return numMap[chineseNum];
      }
      
      // 处理 "第十X" 这种情况
      if (chineseNum.startsWith('十')) {
        const rest = chineseNum.substring(1);
        const base = 10;
        const add = rest ? (numMap[rest] || 0) : 0;
        return base + add;
      }
    }
    
    // 备用方法：提取阿拉伯数字
    const numMatch = chapterStr.match(/第(\d+)/);
    if (numMatch && numMatch[1]) {
      return parseInt(numMatch[1]);
    }
    
    return 999;
  }
  
  const chapterA = typeof a === 'string' ? a : (a.chapter || '');
  const chapterB = typeof b === 'string' ? b : (b.chapter || '');
  
  const numA = getChapterNumber(chapterA);
  const numB = getChapterNumber(chapterB);
  
  return numA - numB;
}

const sorted = [...testChapters].sort(chapterSort);
console.log("\n排序结果:");
sorted.forEach((ch, i) => console.log(`${i+1}. ${ch.chapter}`));

console.log("\n");
