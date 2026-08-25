import { check, sleep } from 'k6';
import http from 'k6/http';
import { generateRandomId, getApiUrl, getHeaders } from '../../lib/config.js';

export const options = {
  scenarios: {
    account_flow: {
      executor: 'ramping-vus',
      startVUs: 5,
      stages: [
        { duration: '1m', target: 20 },
        { duration: '3m', target: 20 },
        { duration: '1m', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<400'],
    http_req_failed: ['rate<0.02'],
  },
};

export default function () {
  const headers = getHeaders();
  const userId = generateRandomId('user');

  // Get user profile
  const profileResponse = http.get(getApiUrl(`/users/${userId}`), { headers });
  check(profileResponse, {
    'profile loaded': (r) => r.status === 200 || r.status === 404,
  });

  // Update user preferences
  const updateResponse = http.put(
    getApiUrl(`/users/${userId}/preferences`),
    JSON.stringify({ theme: 'dark', language: 'en' }),
    { headers },
  );
  check(updateResponse, { 'preferences updated': (r) => r.status === 200 });

  sleep(Math.random() * 2 + 0.5); // 0.5-2.5 seconds
}
