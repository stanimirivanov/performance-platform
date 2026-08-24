export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
export const API_VERSION = __ENV.API_VERSION || 'v1';
export const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';

export function getHeaders(contentType = 'application/json') {
  const headers = {
    'Content-Type': contentType,
  };

  if (AUTH_TOKEN) {
    headers['Authorization'] = `Bearer ${AUTH_TOKEN}`;
  }

  return headers;
}

export function getApiUrl(path) {
  return `${BASE_URL}/api/${API_VERSION}${path}`;
}

export function generateRandomId(prefix = 'test') {
  return `${prefix}-${Math.random().toString(36).substring(2, 10)}`;
}
