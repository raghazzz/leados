import axios from 'axios';

// This points to your FastAPI backend
const API = axios.create({
  baseURL: 'http://127.0.0.1:8001/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Lead functions ──────────────────────────

// Get all leads (with optional filters)
export const getLeads = async (page = 1, pageSize = 50, status = null, minScore = null) => {
  const params = { page, page_size: pageSize };
  if (status) params.status = status;
  if (minScore) params.min_score = minScore;
  const response = await API.get('/leads/', { params });
  return response.data;
};

// Create a single lead
export const createLead = async (leadData) => {
  const response = await API.post('/leads/', leadData);
  return response.data;
};

// Get one lead by ID
export const getLead = async (leadId) => {
  const response = await API.get(`/leads/${leadId}`);
  return response.data;
};

// Update a lead
export const updateLead = async (leadId, data) => {
  const response = await API.patch(`/leads/${leadId}`, data);
  return response.data;
};

// Upload a CSV file
export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await API.post('/leads/upload/csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// ── Email functions ──────────────────────────

// Generate an AI email for a lead
export const generateEmail = async (leadId, emailType = 'outreach') => {
  const response = await API.post('/emails/generate', {
    lead_id: leadId,
    email_type: emailType,
  });
  return response.data;
};

// Get all emails for a lead
export const getLeadEmails = async (leadId) => {
  const response = await API.get(`/emails/lead/${leadId}`);
  return response.data;
};

// ── Health check ──────────────────────────

export const healthCheck = async () => {
  const response = await API.get('/health');
  return response.data;
};