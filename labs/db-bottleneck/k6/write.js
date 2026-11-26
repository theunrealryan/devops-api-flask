import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export const options = {
  scenarios: {
    black_friday_checkout: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 20),
      timeUnit: '1s',
      duration: __ENV.DURATION || '2m',
      preAllocatedVUs: 20,
      maxVUs: 200,
    },
  },
  summaryTrendStats: ['avg', 'p(95)', 'p(99)', 'max'],
};

export default function () {
  const payload = JSON.stringify({
    customer_id: Math.floor(Math.random() * 100000) + 1,
    total: Math.round(Math.random() * 100000) / 100,
  });
  const res = http.post(`${BASE_URL}/orders`, payload, {
    headers: { 'Content-Type': 'application/json' },
    timeout: '10s',
  });
  check(res, { 'status 201': (r) => r.status === 201 });
}
