import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useConfig, useUpdateConfig } from '@/hooks/useConfig';
import { GeneralConfig } from '@/components/config/sections/GeneralConfig';
import { IngestionConfigSection } from '@/components/config/sections/IngestionConfig';
import { EmbeddingConfigSection } from '@/components/config/sections/EmbeddingConfig';
import { RetrievalConfigSection } from '@/components/config/sections/RetrievalConfig';
import { LLMConfigSection } from '@/components/config/sections/LLMConfig';
import { AgentsConfigSection } from '@/components/config/sections/AgentsConfig';
import { VectorStoreConfigSection } from '@/components/config/sections/VectorStoreConfig';
import { ConversationConfigSection } from '@/components/config/sections/ConversationConfig';
import { ObservabilityConfigSection } from '@/components/config/sections/ObservabilityConfig';

export function Config() {
  const { data, isLoading } = useConfig();
  const { mutate: updateConfig, isPending } = useUpdateConfig();
  const [localConfig, setLocalConfig] = useState<any>({});
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (data?.config) {
      setLocalConfig(data.config);
      setHasChanges(false);
    }
  }, [data]);

  const handleSave = () => {
    updateConfig({ config: localConfig, validateOnly: false });
    setHasChanges(false);
  };

  const handleExport = () => {
    window.location.href = '/api/v1/admin/config/export';
  };

  if (isLoading) {
    return <p className="text-sm text-muted">Loading configuration...</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-display">Configuration</h2>
          <p className="text-sm text-muted">Manage your project settings.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>
            Export YAML
          </Button>
          <Button onClick={handleSave} disabled={!hasChanges || isPending}>
            {isPending ? 'Saving...' : 'Save changes'}
          </Button>
        </div>
      </div>

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
          <GeneralConfig
            config={localConfig}
            onChange={(value) => {
              setLocalConfig(value);
              setHasChanges(true);
            }}
          />
        </TabsContent>
        <TabsContent value="ingestion">
          <IngestionConfigSection
            config={localConfig}
            onChange={(value) => {
              setLocalConfig(value);
              setHasChanges(true);
            }}
          />
        </TabsContent>
        <TabsContent value="embedding">
          <EmbeddingConfigSection
            config={localConfig}
            onChange={(value) => {
              setLocalConfig(value);
              setHasChanges(true);
            }}
          />
        </TabsContent>
        <TabsContent value="retrieval">
          <RetrievalConfigSection
            config={localConfig}
            onChange={(value) => {
              setLocalConfig(value);
              setHasChanges(true);
            }}
          />
        </TabsContent>
        <TabsContent value="llm">
          <LLMConfigSection
            config={localConfig}
            onChange={(value) => {
              setLocalConfig(value);
              setHasChanges(true);
            }}
          />
        </TabsContent>
        <TabsContent value="agents">
          <AgentsConfigSection
            config={localConfig}
            onChange={(value) => {
              setLocalConfig(value);
              setHasChanges(true);
            }}
          />
        </TabsContent>
        <TabsContent value="vector-store">
          <VectorStoreConfigSection
            config={localConfig}
            onChange={(value) => {
              setLocalConfig(value);
              setHasChanges(true);
            }}
          />
        </TabsContent>
        <TabsContent value="conversation">
          <ConversationConfigSection
            config={localConfig}
            onChange={(value) => {
              setLocalConfig(value);
              setHasChanges(true);
            }}
          />
        </TabsContent>
        <TabsContent value="observability">
          <ObservabilityConfigSection
            config={localConfig}
            onChange={(value) => {
              setLocalConfig(value);
              setHasChanges(true);
            }}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
