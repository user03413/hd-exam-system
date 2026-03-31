// Cloudflare Pages Function - API 代理
// 匹配 /api/* 所有请求
export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  
  // 构建 Worker API URL
  const workerUrl = `https://hd-exam-api.771794850.workers.dev/api${url.pathname.replace('/api', '')}${url.search}`;
  
  console.log('Proxying to:', workerUrl);
  
  // 转发请求到 Worker
  const response = await fetch(workerUrl, {
    method: request.method,
    headers: request.headers,
    body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
  });
  
  return response;
}
