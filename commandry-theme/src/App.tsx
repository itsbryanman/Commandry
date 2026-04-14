import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import AgentDetail from './pages/AgentDetail';
import CostDashboard from './pages/CostDashboard';
import MCPServers from './pages/MCPServers';
import Prompts from './pages/Prompts';
import Traces from './pages/Traces';
import SettingsPage from './pages/Settings';
import Login from './pages/Login';
import NotFound from './pages/NotFound';

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
        <TopBar />
        <main className="flex-1">{children}</main>
      </div>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="*"
          element={
            <AppLayout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/agents" element={<Agents />} />
                <Route path="/agents/:id" element={<AgentDetail />} />
                <Route path="/cost" element={<CostDashboard />} />
                <Route path="/mcp-servers" element={<MCPServers />} />
                <Route path="/prompts" element={<Prompts />} />
                <Route path="/traces" element={<Traces />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </AppLayout>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
