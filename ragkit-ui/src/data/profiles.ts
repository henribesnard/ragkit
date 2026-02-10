import { deepMerge } from '@/utils/deepMerge';

export interface RagProfile {
  id: string;
  name: string;
  tag: string;
  description: string;
  patch: Record<string, any>;
}

export const RAG_PROFILES: RagProfile[] = [
  {
    id: 'technical_docs',
    name: 'Technical Docs',
    tag: 'API / DevOps / SDK',
    description: 'Structured documentation with precise terminology and citations.',
    patch: {
      ingestion: {
        chunking: {
          strategy: 'fixed',
          fixed: { chunk_size: 800, chunk_overlap: 120 },
        },
      },
      retrieval: {
        architecture: 'hybrid',
        semantic: { enabled: true, weight: 0.3, top_k: 10 },
        lexical: { enabled: true, weight: 0.7, top_k: 10 },
      },
      llm: {
        primary: { params: { temperature: 0.1, max_tokens: 800 } },
      },
      agents: {
        response_generator: { behavior: { cite_sources: true } },
      },
    },
  },
  {
    id: 'faq_support',
    name: 'FAQ & Support',
    tag: 'Support / Knowledge Base',
    description: 'Fast answers for repetitive questions with concise responses.',
    patch: {
      ingestion: {
        chunking: {
          strategy: 'fixed',
          fixed: { chunk_size: 400, chunk_overlap: 60 },
        },
      },
      retrieval: {
        architecture: 'semantic',
        semantic: { enabled: true, top_k: 6, similarity_threshold: 0.15 },
      },
      llm: {
        primary: { params: { temperature: 0.2, max_tokens: 500 } },
      },
      agents: {
        response_generator: { behavior: { cite_sources: true } },
      },
    },
  },
  {
    id: 'scientific_research',
    name: 'Scientific Research',
    tag: 'Papers / Data',
    description: 'Longer context windows and conservative generation.',
    patch: {
      ingestion: {
        chunking: {
          strategy: 'fixed',
          fixed: { chunk_size: 1200, chunk_overlap: 150 },
        },
      },
      retrieval: {
        architecture: 'semantic',
        semantic: { enabled: true, top_k: 12, similarity_threshold: 0.1 },
      },
      llm: {
        primary: { params: { temperature: 0.05, max_tokens: 1200 } },
      },
      agents: {
        response_generator: { behavior: { cite_sources: true } },
      },
    },
  },
  {
    id: 'legal_regulatory',
    name: 'Legal & Regulatory',
    tag: 'Compliance / Policy',
    description: 'Hybrid retrieval with strict citation requirements.',
    patch: {
      ingestion: {
        chunking: {
          strategy: 'fixed',
          fixed: { chunk_size: 1000, chunk_overlap: 200 },
        },
      },
      retrieval: {
        architecture: 'hybrid',
        semantic: { enabled: true, weight: 0.4, top_k: 12 },
        lexical: { enabled: true, weight: 0.6, top_k: 12 },
      },
      llm: {
        primary: { params: { temperature: 0.1, max_tokens: 900 } },
      },
      agents: {
        response_generator: { behavior: { cite_sources: true } },
      },
    },
  },
  {
    id: 'reports_analysis',
    name: 'Reports & Analysis',
    tag: 'BI / Analytics',
    description: 'Larger chunks and broader retrieval for synthesis.',
    patch: {
      ingestion: {
        chunking: {
          strategy: 'fixed',
          fixed: { chunk_size: 1500, chunk_overlap: 200 },
        },
      },
      retrieval: {
        architecture: 'semantic',
        semantic: { enabled: true, top_k: 15, similarity_threshold: 0.05 },
      },
      llm: {
        primary: { params: { temperature: 0.3, max_tokens: 1200 } },
      },
      agents: {
        response_generator: { behavior: { cite_sources: true } },
      },
    },
  },
  {
    id: 'general_knowledge',
    name: 'General Knowledge',
    tag: 'Mixed Content',
    description: 'Balanced settings for diverse documentation.',
    patch: {
      ingestion: {
        chunking: {
          strategy: 'fixed',
          fixed: { chunk_size: 800, chunk_overlap: 100 },
        },
      },
      retrieval: {
        architecture: 'semantic',
        semantic: { enabled: true, top_k: 8, similarity_threshold: 0.1 },
      },
      llm: {
        primary: { params: { temperature: 0.4, max_tokens: 700 } },
      },
      agents: {
        response_generator: { behavior: { cite_sources: true } },
      },
    },
  },
];

export const applyProfilePatch = (config: Record<string, any>, profile: RagProfile) => {
  const base = JSON.parse(JSON.stringify(config || {}));
  return deepMerge(base, profile.patch);
};
