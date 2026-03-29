import axios from 'axios';

const API = axios.create({
  baseURL: 'http://127.0.0.1:8001/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Leads ──────────────────────────
export const getLeads = async (page = 1, pageSize = 50) => {
  const response = await API.get('/leads/', { params: { page, page_size: pageSize } });
  return response.data;
};

export const createLead = async (leadData) => {
  const response = await API.post('/leads/', leadData);
  return response.data;
};

export const getLead = async (leadId) => {
  const response = await API.get(`/leads/${leadId}`);
  return response.data;
};

export const updateLead = async (leadId, data) => {
  const response = await API.patch(`/leads/${leadId}`, data);
  return response.data;
};

export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await API.post('/leads/upload/csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// ── Emails ──────────────────────────
export const generateEmail = async (leadId, emailType = 'outreach') => {
  const response = await API.post('/emails/generate', {
    lead_id: leadId,
    email_type: emailType,
  });
  return response.data;
};

export const getLeadEmails = async (leadId) => {
  const response = await API.get(`/emails/lead/${leadId}`);
  return response.data;
};

// ── Health ──────────────────────────
export const healthCheck = async () => {
  const response = await API.get('/health');
  return response.data;
};