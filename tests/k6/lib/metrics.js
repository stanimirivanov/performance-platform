import { Counter, Gauge, Rate, Trend } from 'k6/metrics';

// ============================================
// Business Transaction Metrics
// ============================================

/**
 * Checkout flow duration (complete transaction time)
 */
export const checkoutDuration = new Trend('biz_checkout_duration', true);

/**
 * Search flow duration (query to results displayed)
 */
export const searchDuration = new Trend('biz_search_duration', true);

/**
 * Account operations duration
 */
export const accountOperationDuration = new Trend(
  'biz_account_operation_duration',
  true,
);

// ============================================
// Transaction Status Metrics
// ============================================

/**
 * Successful transaction count
 */
export const successfulTransactions = new Counter(
  'biz_successful_transactions',
);

/**
 * Failed transaction count
 */
export const failedTransactions = new Counter('biz_failed_transactions');

/**
 * Transaction error rate
 */
export const transactionErrorRate = new Rate('biz_transaction_error_rate');

// ============================================
// Endpoint Throughput Metrics
// ============================================

/**
 * Checkout endpoint throughput
 */
export const checkoutThroughput = new Counter('api_checkout_throughput');

/**
 * Search endpoint throughput
 */
export const searchThroughput = new Counter('api_search_throughput');

/**
 * Account endpoint throughput
 */
export const accountThroughput = new Counter('api_account_throughput');

// ============================================
// Performance Metrics
// ============================================

/**
 * Time to first byte (TTFB)
 */
export const timeToFirstByte = new Trend('perf_ttfb', true);

/**
 * Time to complete response
 */
export const timeToComplete = new Trend('perf_ttc', true);

/**
 * Active virtual users gauge
 */
export const activeVUs = new Gauge('perf_active_vus');

// ============================================
// Resource Metrics (if applicable)
// ============================================

/**
 * Memory usage during test (if measured)
 */
export const memoryUsage = new Gauge('res_memory_mb');

/**
 * CPU usage during test (if measured)
 */
export const cpuUsage = new Gauge('res_cpu_percent');

// ============================================
// Helper Functions
// ============================================

/**
 * Record a transaction duration and success status.
 * @param {Trend} metric - Trend metric to record duration
 * @param {number} startTime - Transaction start time (Date.now())
 * @param {boolean} success - Whether transaction succeeded
 */
export function recordTransaction(metric, startTime, success = true) {
  const duration = Date.now() - startTime;
  metric.add(duration);

  if (success) {
    successfulTransactions.add(1);
    transactionErrorRate.add(false);
  } else {
    failedTransactions.add(1);
    transactionErrorRate.add(true);
  }

  return duration;
}

/**
 * Record time to first byte from HTTP response.
 * @param {Object} response - k6 HTTP response
 */
export function recordTTFB(response) {
  if (response && response.timings) {
    timeToFirstByte.add(response.timings.waiting);
    timeToComplete.add(response.timings.duration);
  }
}

/**
 * Update active VU gauge.
 * @param {number} vuCount - Current number of active VUs
 */
export function updateActiveVUs(vuCount) {
  activeVUs.add(vuCount);
}
