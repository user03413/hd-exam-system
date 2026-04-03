// 测试章节排序算法
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

// 排序算法1 - 直接提取数字
function chapterSort1(a, b) {
  function getNum(ch) {
    if (!ch) return 999;
    const chapterStr = typeof ch === 'string' ? ch : (ch.chapter || '');
    const match = chapterStr.match(/第(\d+)/);
    return match ? parseInt(match[1]) : 999;
  }
  return getNum(a) - getNum(b);
}

const sorted1 = [...testChapters].sort(chapterSort1);
console.log("\n算法1结果:");
sorted1.forEach((ch, i) => console.log(`${i+1}. ${ch.chapter}`));

console.log("\n");
