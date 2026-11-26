import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const CUSTOMERS = Number(__ENV.CUSTOMERS || 1000);

export const options = {
  scenarios: {
    black_friday_reads: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 50),
      timeUnit: '1s',
      duration: __ENV.DURATION || '1m',
      preAllocatedVUs: 50,
      maxVUs: 300,
    },
  },
  summaryTrendStats: ['avg', 'p(95)', 'p(99)', 'max'],
};

export default function () {
  const customerId = Math.floor(Math.random() * CUSTOMERS) + 1;
  const res = http.get(`${BASE_URL}/orders?customer_id=${customerId}`, { timeout: '10s' });
  check(res, { 'status 200': (r) => r.status === 200 });
}
