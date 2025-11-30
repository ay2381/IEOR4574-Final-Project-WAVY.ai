import { apiRequest } from './client';
import type { CreatePatientPayload, Patient } from '../types';

export const patientApi = {
  list: () => apiRequest<Patient[]>('/patients'),
  create: (payload: CreatePatientPayload) => apiRequest<Patient>('/patients', { method: 'POST', body: payload }),
  remove: (id: string) => apiRequest<void>(`/patients/${id}`, { method: 'DELETE' }),
};


