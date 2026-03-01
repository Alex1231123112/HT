import http from "k6/http";
import { check } from "k6";

export const options = {
  vus: 20,
  duration: "30s",
  thresholds: {
    "http_req_duration": ["p(95)<0.5"],
  },
};

export default function () {
  const res = http.get("http://localhost:8000/health");
  check(res, { "status is 200": (r) => r.status === 200 });
}
