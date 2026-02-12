export interface ApiHealth {
  status: string;
  uptime_seconds: number;
  config_loaded: boolean;
  components: Record<string, ComponentHealth>;
}

export interface ComponentHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms?: number;
  error?: string;
}

export interface IngestionStatus {
  is_running: boolean;
  pending_documents: number;
  total_documents: number;
  total_chunks: number;
}

export interface IngestionRun {
  id: string;
  status: 'completed' | 'failed' | 'running';
  started_at: string;
  finished_at?: string;
  stats?: {
    documents_loaded: number;
    chunks_stored: number;
    duration_seconds: number;
    errors: number;
  };
}

export interface QueryLogEntry {
  query: string;
  intent: string | null;
  latency_ms: number;
  success: boolean;
  error: string | null;
  timestamp: string;
}
