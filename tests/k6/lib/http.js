import { check } from 'k6';
import http from 'k6/http';
import { logError } from './checks.js';
import { getHeaders, TIMEOUT } from './config.js';

/**
 * Perform GET request with default checks.
 * @param {string} path - API endpoint path (without base URL)
 * @param {Object} options - Additional k6 HTTP options
 * @param {Object} customChecks - Additional checks to perform
 * @returns {Object} HTTP response
 */
export function getRequest(path, options = {}, customChecks = {}) {
  const url = path.startsWith('http') ? path : getApiUrl(path);
  const headers = getHeaders();

  const response = http.get(url, {
    headers,
    timeout: TIMEOUT,
    ...options,
  });

  const defaultChecks = {
    'GET status is 200': (r) => r.status === 200,
    ...customChecks,
  };

  const passed = check(response, defaultChecks);

  if (!passed) {
    logError(`GET ${url} failed: status=${response.status}`);
  }

  return response;
}

/**
 * Perform POST request with default checks.
 * @param {string} path - API endpoint path
 * @param {Object} body - Request body
 * @param {Object} options - Additional k6 HTTP options
 * @param {Object} customChecks - Additional checks to perform
 * @returns {Object} HTTP response
 */
export function postRequest(path, body, options = {}, customChecks = {}) {
  const url = path.startsWith('http') ? path : getApiUrl(path);
  const headers = getHeaders();

  const response = http.post(url, JSON.stringify(body), {
    headers,
    timeout: TIMEOUT,
    ...options,
  });

  const defaultChecks = {
    'POST status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    ...customChecks,
  };

  const passed = check(response, defaultChecks);

  if (!passed) {
    logError(`POST ${url} failed: status=${response.status}`);
  }

  return response;
}

/**
 * Perform PUT request with default checks.
 * @param {string} path - API endpoint path
 * @param {Object} body - Request body
 * @param {Object} options - Additional k6 HTTP options
 * @param {Object} customChecks - Additional checks to perform
 * @returns {Object} HTTP response
 */
export function putRequest(path, body, options = {}, customChecks = {}) {
  const url = path.startsWith('http') ? path : getApiUrl(path);
  const headers = getHeaders();

  const response = http.put(url, JSON.stringify(body), {
    headers,
    timeout: TIMEOUT,
    ...options,
  });

  const defaultChecks = {
    'PUT status is 200': (r) => r.status === 200,
    ...customChecks,
  };

  const passed = check(response, defaultChecks);

  if (!passed) {
    logError(`PUT ${url} failed: status=${response.status}`);
  }

  return response;
}

/**
 * Perform DELETE request with default checks.
 * @param {string} path - API endpoint path
 * @param {Object} options - Additional k6 HTTP options
 * @param {Object} customChecks - Additional checks to perform
 * @returns {Object} HTTP response
 */
export function deleteRequest(path, options = {}, customChecks = {}) {
  const url = path.startsWith('http') ? path : getApiUrl(path);
  const headers = getHeaders();

  const response = http.del(url, null, {
    headers,
    timeout: TIMEOUT,
    ...options,
  });

  const defaultChecks = {
    'DELETE status is 200 or 204': (r) => r.status === 200 || r.status === 204,
    ...customChecks,
  };

  const passed = check(response, defaultChecks);

  if (!passed) {
    logError(`DELETE ${url} failed: status=${response.status}`);
  }

  return response;
}

/**
 * Perform request with retry logic.
 * @param {Function} requestFn - Request function to call
 * @param {Array} args - Arguments for the request function
 * @param {number} maxRetries - Maximum number of retries
 * @param {number} retryDelayMs - Delay between retries in milliseconds
 * @returns {Object} HTTP response
 */
export function requestWithRetry(
  requestFn,
  args = [],
  maxRetries = 3,
  retryDelayMs = 1000,
) {
  let lastResponse;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    lastResponse = requestFn(...args);

    // Success if status is 2xx or 3xx
    if (lastResponse.status >= 200 && lastResponse.status < 400) {
      return lastResponse;
    }

    // Don't retry on 4xx client errors (except 408 and 429)
    if (lastResponse.status >= 400 && lastResponse.status < 500) {
      if (lastResponse.status !== 408 && lastResponse.status !== 429) {
        return lastResponse;
      }
    }

    // Wait before retry with exponential backoff
    if (attempt < maxRetries) {
      sleep(retryDelayMs * (attempt + 1));
    }
  }

  return lastResponse;
}
