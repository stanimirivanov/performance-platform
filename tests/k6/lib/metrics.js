import { check } from 'k6';
import http from 'k6/http';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics for business transactions
export const checkoutDuration = new Trend('checkout_duration', true);
export const searchDuration = new Trend('search_duration', true);
export const successfulTransactions = new Counter('successful_transactions');
export const failedTransactions = new Counter('failed_transactions');
export const errorRate = new Rate('error_rate');
EOF;

cat > (lib / http.js) << 'EOF';

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
