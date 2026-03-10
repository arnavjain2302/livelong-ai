import axios from 'axios';

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

function formatChatResponse(response) {
  if (typeof response === 'string') {
    return response;
  }

  if (response?.answer) {
    return response.answer;
  }

  if (response?.response) {
    return response.response;
  }

  if (response?.message) {
    return response.message;
  }

  return JSON.stringify(response, null, 2);
}

export async function uploadPrescription(file) {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await api.post('/upload-prescription', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return data;
}

export async function sendChatMessage(query) {
  const { data } = await api.post('/chat', { query });
  return formatChatResponse(data);
}

export function getRequestErrorMessage(error, fallbackMessage) {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }

  if (typeof error.response?.data === 'string') {
    return error.response.data;
  }

  if (error.message === 'Network Error') {
    return 'Request could not reach the backend. Confirm FastAPI is running on http://localhost:8000.';
  }

  return fallbackMessage;
}
