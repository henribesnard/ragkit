export interface MetricsSummary {
  period: string;
  queries: QueryMetrics;
  ingestion: IngestionMetrics;
  components: Record<string, ComponentMetrics>;
  generated_at: string;
}

export interface QueryMetrics {
  total: number;
  success: number;
  failed: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  by_intent: Record<string, number>;
}

export interface IngestionMetrics {
  total_runs: number;
  total_documents: number;
  total_chunks: number;
  avg_duration_seconds: number;
  last_run?: string;
  errors: number;
}

export interface ComponentMetrics {
  name: string;
  calls: number;
  errors: number;
  avg_latency_ms: number;
  last_error?: string;
}

export interface MetricPoint {
  timestamp: string;
  value: number;
}
