export function createWebSocket(onMessage: (data: any) => void) {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.host;
  const socket = new WebSocket(`${protocol}://${host}/api/v1/admin/ws`);

  socket.addEventListener('message', (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      onMessage({ type: 'raw', data: event.data });
    }
  });

  return socket;
}
