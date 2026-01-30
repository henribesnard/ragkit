import { useEffect, useRef, useState } from 'react';
import { createWebSocket } from '@/api/websocket';

export function useWebSocket() {
  const [lastMessage, setLastMessage] = useState<any>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const socket = createWebSocket((message) => setLastMessage(message));
    socketRef.current = socket;
    return () => {
      socket.close();
    };
  }, []);

  return { lastMessage, socket: socketRef.current };
}
