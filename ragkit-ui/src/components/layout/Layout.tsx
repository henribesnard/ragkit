import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { useAppStore } from '@/stores/appStore';

export function Layout() {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);

  return (
    <div className="flex min-h-screen">
      <Sidebar open={sidebarOpen} />
      <div className="flex flex-1 flex-col">
        <Header />
        <main className="flex-1 px-8 py-10">
          <div className="animate-floatIn">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
