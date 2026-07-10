async function $apiReq(method, path, body) {
  const token = localStorage.getItem('tma_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  const cfg = { method: method, headers: headers };
  if (body) cfg.body = JSON.stringify(body);
  
  let fullPath = path;
  if (!path.startsWith('/auth') && !path.startsWith('/admin') && !path.startsWith('/staff')) {
    fullPath = '/trekker' + path;
  }
  
  const res = await fetch('/api' + fullPath, cfg);
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || data.message || 'Request failed');
  return data;
}

export const $api = {
  get: (p) => $apiReq('GET', p, null),
  post: (p, b) => $apiReq('POST', p, b),
  put: (p, b) => $apiReq('PUT', p, b),
  delete: (p) => $apiReq('DELETE', p, null),
};

export default $api;
