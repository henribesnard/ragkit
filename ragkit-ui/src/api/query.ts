import { apiClient } from './client';

const baseURL = apiClient.defaults.baseURL || '';

const resolveApiUrl = (path: string) => {
  if (!baseURL) {
    return path;
  }
  const normalized = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;
  return `${normalized}${path.startsWith('/') ? '' : '/'}${path}`;
};

export async function queryRag(payload: { query: string; history?: any[] }) {
  const response = await apiClient.post('/api/v1/query', payload);
  return response.data;
}

export async function queryRagStream(
  payload: { query: string; history?: any[] },
  callbacks: {
    onDelta: (content: string) => void;
    onFinal: (response: any) => void;
    onError: (error: Error) => void;
  }
) {
  const response = await fetch(resolveApiUrl('/api/v1/query/stream'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 501) {
      throw new Error('STREAMING_DISABLED');
    }
    throw new Error(`HTTP ${response.status}`);
  }

  if (!response.body) {
    throw new Error('STREAMING_BODY_MISSING');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finished = false;
  let errorReported = false;

  try {
    while (!finished) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line.startsWith('data:')) {
          continue;
        }
        const payloadText = line.slice(5).trim();
        if (!payloadText) {
          continue;
        }
        try {
          const event = JSON.parse(payloadText);
          if (event.type === 'delta') {
            callbacks.onDelta(event.content || '');
          } else if (event.type === 'final') {
            callbacks.onFinal(event);
            finished = true;
            break;
          } else if (event.type === 'error') {
            const error = new Error(event.message || 'Streaming error');
            callbacks.onError(error);
            errorReported = true;
            throw error;
          }
        } catch (error) {
          callbacks.onError(error as Error);
        }
      }
    }
  } catch (error) {
    if (!errorReported) {
      callbacks.onError(error as Error);
    }
    throw error;
  } finally {
    reader.releaseLock();
  }
}
