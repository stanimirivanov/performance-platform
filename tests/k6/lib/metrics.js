import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics for business transactions
export const checkoutDuration = new Trend('checkout_duration', true);
export const searchDuration = new Trend('search_duration', true);
export const successfulTransactions = new Counter('successful_transactions');
export const failedTransactions = new Counter('failed_transactions');
export const errorRate = new Rate('error_rate');
