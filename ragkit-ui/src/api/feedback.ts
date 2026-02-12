import { apiClient } from './client';

export interface FeedbackPayload {
  message_id?: string;
  rating: 'up' | 'down';
  comment?: string;
  metadata?: Record<string, any>;
}

export async function submitFeedback(payload: FeedbackPayload) {
  const response = await apiClient.post('/api/v1/feedback', payload);
  return response.data;
}
