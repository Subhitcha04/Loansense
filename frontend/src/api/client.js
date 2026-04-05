import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
});

// ── Applicants ──
export const getApplicants   = ()     => client.get('/applicants');
export const getApplicant    = (id)   => client.get(`/applicants/${id}`);
export const createApplicant = (data) => client.post('/applicants/', data);

// ── Applications ──
export const getApplications    = ()         => client.get('/applications');
export const getApplication     = (id)       => client.get(`/applications/${id}`);
export const submitApplication  = (data)     => client.post('/applications/', data);
export const makeDecision       = (id, data) => client.post(`/applications/${id}/decision`, data);

// ── Loans ──
export const getLoans       = ()   => client.get('/loans');
export const getLoan        = (id) => client.get(`/loans/${id}`);
export const getLoanSchedule = (id) => client.get(`/loans/${id}/schedule`);
export const getLoanStatus  = (id) => client.get(`/loans/${id}/status`);
export const makePayment    = (id) => client.post(`/loans/${id}/pay`);

// ── Analytics ──
export const getPortfolio        = () => client.get('/analytics/portfolio');
export const getRiskDistribution = () => client.get('/analytics/risk-distribution');
export const getRepaymentTrends  = () => client.get('/analytics/repayment-trends');

// ── Webhooks ──
export const registerWebhook  = (data) => client.post('/webhooks/register', data);
export const getWebhookEvents = ()     => client.get('/webhooks/events');
export const getEndpoints     = ()     => client.get('/webhooks/endpoints');
export const deleteEndpoint   = (id)   => client.delete(`/webhooks/endpoints/${id}`);

export default client;
