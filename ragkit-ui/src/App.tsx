import { Route, Routes } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { Setup } from '@/pages/Setup';
import { Config } from '@/pages/Config';
import { Ingestion } from '@/pages/Ingestion';
import { Chatbot } from '@/pages/Chatbot';
import { Logs } from '@/pages/Logs';
import { NotFound } from '@/pages/NotFound';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="setup" element={<Setup />} />
        <Route path="config" element={<Config />} />
        <Route path="ingestion" element={<Ingestion />} />
        <Route path="chatbot" element={<Chatbot />} />
        <Route path="logs" element={<Logs />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
