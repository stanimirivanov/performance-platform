import { check, sleep } from 'k6';
import http from 'k6/http';
import { getApiUrl, getHeaders } from '../lib/config.js';
import { errorRate, searchDuration } from '../lib/metrics.js';

export const options = {
  scenarios: {
    search_flow: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 30,
      maxVUs: 50,
    },
  },
  thresholds: {
    search_duration: ['p(95)<300'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const startTime = Date.now();
  const headers = getHeaders();

  const searchQuery = `test-query-${Math.floor(Math.random() * 100)}`;
  const searchResponse = http.get(getApiUrl(`/search?q=${searchQuery}`), {
    headers,
  });

  const searchSuccess = check(searchResponse, {
    'search successful': (r) => r.status === 200,
    'search has results': (r) => r.json('results') !== undefined,
  });

  const duration = Date.now() - startTime;
  searchDuration.add(duration);
  errorRate.add(!searchSuccess);

  sleep(Math.random() * 3 + 1); // 1-4 seconds
}
