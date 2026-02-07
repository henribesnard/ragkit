import { apiClient } from './client';

export function createWebSocket(onMessage: (data: any) => void) {
  const baseURL = apiClient.defaults.baseURL || '';
  let wsUrl: string;

  try {
    const base = baseURL ? new URL(baseURL, window.location.origin) : new URL(window.location.origin);
    const wsBase = new URL('/api/v1/admin/ws', base);
    wsBase.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:';
    wsUrl = wsBase.toString();
  } catch {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    wsUrl = `${protocol}://${window.location.host}/api/v1/admin/ws`;
  }

  const socket = new WebSocket(wsUrl);

  socket.addEventListener('message', (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      onMessage({ type: 'raw', data: event.data });
    }
  });

  return socket;
}
