import { check, sleep } from 'k6';
import http from 'k6/http';
import { getApiUrl, getHeaders } from '../../lib/config.js';
import {
  checkoutDuration,
  failedTransactions,
  successfulTransactions,
  transactionErrorRate,
} from '../../lib/metrics.js';

export const options = {
  scenarios: {
    checkout_flow: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 20,
      maxVUs: 100,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 50 },
        { duration: '30s', target: 10 },
      ],
    },
  },
  thresholds: {
    biz_checkout_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const startTime = Date.now();
  const headers = getHeaders();

  // Step 1: Get cart
  const cartResponse = http.get(getApiUrl('/cart'), { headers });
  const cartLoaded = check(cartResponse, {
    'cart loaded': (r) => r.status === 200,
  });

  // Step 2: Initiate checkout
  const checkoutData = JSON.stringify({
    cartId: 'example-cart',
    paymentMethod: 'credit-card',
    shippingAddress: {
      street: '123 Test St',
      city: 'Test City',
      country: 'US',
    },
  });

  const checkoutResponse = http.post(getApiUrl('/checkout'), checkoutData, {
    headers,
  });

  const checkoutSuccess = check(checkoutResponse, {
    'checkout successful': (r) => r.status === 201 || r.status === 200,
    'checkout response has orderId': (r) => r.json('orderId') !== undefined,
  });

  // Record metrics
  const duration = Date.now() - startTime;
  checkoutDuration.add(duration);

  if (checkoutSuccess) {
    successfulTransactions.add(1);
    transactionErrorRate.add(false);
  } else {
    failedTransactions.add(1);
    transactionErrorRate.add(true);
  }

  sleep(Math.random() * 2 + 1);
}
