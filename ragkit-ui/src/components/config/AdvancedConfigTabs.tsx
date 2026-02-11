import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  return (
    <Tabs defaultValue="general">
      <TabsList>
        <TabsTrigger value="general">{t('config.tabs.general')}</TabsTrigger>
        <TabsTrigger value="ingestion">{t('config.tabs.ingestion')}</TabsTrigger>
        <TabsTrigger value="embedding">{t('config.tabs.embedding')}</TabsTrigger>
        <TabsTrigger value="retrieval">{t('config.tabs.retrieval')}</TabsTrigger>
        <TabsTrigger value="llm">{t('config.tabs.llm')}</TabsTrigger>
        <TabsTrigger value="agents">{t('config.tabs.agents')}</TabsTrigger>
        <TabsTrigger value="vector-store">{t('config.tabs.vectorStore')}</TabsTrigger>
        <TabsTrigger value="conversation">{t('config.tabs.conversation')}</TabsTrigger>
        <TabsTrigger value="observability">{t('config.tabs.observability')}</TabsTrigger>
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
