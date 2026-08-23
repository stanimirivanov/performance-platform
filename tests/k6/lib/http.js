import { check } from 'k6';
import http from 'k6/http';

export function getWithChecks(url, params = {}, checks = {}) {
  const response = http.get(url, params);

  const defaultChecks = {
    'status is 200': (r) => r.status === 200,
    ...checks,
  };

  check(response, defaultChecks);
  return response;
}

export function postWithChecks(url, body, params = {}, checks = {}) {
  const response = http.post(url, body, params);

  const defaultChecks = {
    'status is 201': (r) => r.status === 201,
    'status is 200': (r) => r.status === 200,
    ...checks,
  };

  check(response, defaultChecks);
  return response;
}

export function generateRandomId(prefix = 'test') {
  return `${prefix}-${Math.random().toString(36).substring(2, 10)}`;
}

export function getCurrentTimestamp() {
  return new Date().toISOString();
}
