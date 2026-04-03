// 直接测试现有部署的API - 检查章节排序
const testExistingAPI = async () => {
  const apiUrl = 'https://hd-exam-api.771794850.workers.dev/api/chapters';
  
  console.log('🔍 正在测试现有部署的API...');
  console.log('📍 API地址:', apiUrl);
  console.log('');
  
  try {
    const response = await fetch(apiUrl);
    const data = await response.json();
    
    console.log('✅ API响应成功！');
    console.log('');
    console.log('📚 章节列表（当前部署版本）:');
    console.log('');
    
    data.forEach((ch, i) => {
      console.log(`${i+1}. ${ch.chapter} (${ch.count}题)`);
    });
    
    console.log('');
    console.log('ℹ️  如果上面的顺序不对，说明部署的还是旧版本代码！');
    
  } catch (error) {
    console.error('❌ 请求失败:', error.message);
  }
};

testExistingAPI();
