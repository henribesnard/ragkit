import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { GeneralConfig } from '@/components/config/sections/GeneralConfig';
import { IngestionConfigSection } from '@/components/config/sections/IngestionConfig';
import { EmbeddingConfigSection } from '@/components/config/sections/EmbeddingConfig';
import { RetrievalConfigSection } from '@/components/config/sections/RetrievalConfig';
import { LLMConfigSection } from '@/components/config/sections/LLMConfig';
import { AgentsConfigSection } from '@/components/config/sections/AgentsConfig';
import { VectorStoreConfigSection } from '@/components/config/sections/VectorStoreConfig';
import { ConversationConfigSection } from '@/components/config/sections/ConversationConfig';
import { ObservabilityConfigSection } from '@/components/config/sections/ObservabilityConfig';

interface AdvancedConfigTabsProps {
  config: any;
  onChange: (value: any) => void;
}

export function AdvancedConfigTabs({ config, onChange }: AdvancedConfigTabsProps) {
  return (
    <Tabs defaultValue="general">
      <TabsList>
        <TabsTrigger value="general">General</TabsTrigger>
        <TabsTrigger value="ingestion">Ingestion</TabsTrigger>
        <TabsTrigger value="embedding">Embedding</TabsTrigger>
        <TabsTrigger value="retrieval">Retrieval</TabsTrigger>
        <TabsTrigger value="llm">LLM</TabsTrigger>
        <TabsTrigger value="agents">Agents</TabsTrigger>
        <TabsTrigger value="vector-store">Vector Store</TabsTrigger>
        <TabsTrigger value="conversation">Conversation</TabsTrigger>
        <TabsTrigger value="observability">Observability</TabsTrigger>
      </TabsList>

      <TabsContent value="general">
        <GeneralConfig config={config} onChange={onChange} />
      </TabsContent>
      <TabsContent value="ingestion">
        <IngestionConfigSection config={config} onChange={onChange} />
      </TabsContent>
      <TabsContent value="embedding">
        <EmbeddingConfigSection config={config} onChange={onChange} />
      </TabsContent>
      <TabsContent value="retrieval">
        <RetrievalConfigSection config={config} onChange={onChange} />
      </TabsContent>
      <TabsContent value="llm">
        <LLMConfigSection config={config} onChange={onChange} />
      </TabsContent>
      <TabsContent value="agents">
        <AgentsConfigSection config={config} onChange={onChange} />
      </TabsContent>
      <TabsContent value="vector-store">
        <VectorStoreConfigSection config={config} onChange={onChange} />
      </TabsContent>
      <TabsContent value="conversation">
        <ConversationConfigSection config={config} onChange={onChange} />
      </TabsContent>
      <TabsContent value="observability">
        <ObservabilityConfigSection config={config} onChange={onChange} />
      </TabsContent>
    </Tabs>
  );
}
