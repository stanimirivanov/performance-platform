export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
export const API_VERSION = __ENV.API_VERSION || 'v1';
export const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';
export const TIMEOUT = parseInt(__ENV.TIMEOUT || '30000', 10);

export const API_BASE_URL = `${BASE_URL}/api/${API_VERSION}`;

/**
 * Get default headers for requests.
 * @param {string} contentType - Content type header value
 * @returns {Object} Headers object
 */
export function getHeaders(contentType = 'application/json') {
  const headers = {
    'Content-Type': contentType,
    Accept: 'application/json',
  };

  if (AUTH_TOKEN) {
    headers['Authorization'] = `Bearer ${AUTH_TOKEN}`;
  }

  return headers;
}

/**
 * Build a full API URL.
 * @param {string} path - API endpoint path
 * @returns {string} Full URL
 */
export function getApiUrl(path) {
  // Remove leading slash if present
  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
}

/**
 * Get workload profile configuration.
 * @returns {Object} Workload profile options
 */
export function getWorkloadProfile() {
  const profile = __ENV.WORKLOAD_PROFILE || 'smoke';

  const profiles = {
    smoke: {
      duration: '2m',
      arrivalRate: 5,
      maxVUs: 20,
      thresholds: {
        http_req_duration: ['p(95)<600'],
        http_req_failed: ['rate<0.02'],
      },
    },
    regression: {
      duration: '15m',
      arrivalRate: 50,
      maxVUs: 100,
      thresholds: {
        http_req_duration: ['p(95)<400', 'p(99)<800'],
        http_req_failed: ['rate<0.005'],
      },
    },
    stress: {
      duration: '10m',
      arrivalRate: 100,
      maxVUs: 500,
      thresholds: {
        http_req_duration: ['p(95)<1000'],
        http_req_failed: ['rate<0.1'],
      },
    },
  };

  return profiles[profile] || profiles.smoke;
}

/**
 * Generate a random integer between min and max (inclusive).
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} Random integer
 */
export function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Generate a random string ID.
 * @param {string} prefix - ID prefix
 * @returns {string} Random ID
 */
export function generateRandomId(prefix = 'test') {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
}

/**
 * Get current timestamp in ISO format.
 * @returns {string} ISO timestamp
 */
export function getCurrentTimestamp() {
  return new Date().toISOString();
}
