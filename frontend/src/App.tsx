import { NavLink, Route, Routes } from "react-router-dom";

import { ConnectionBanner } from "./components/ConnectionBanner";
import { useHealth } from "./hooks/useHealth";
import { HistoryPage } from "./pages/HistoryPage";
import { JobPage } from "./pages/JobPage";
import { NewAnalysisPage } from "./pages/NewAnalysisPage";

export default function App() {
  const health = useHealth();

  return (
    <>
      <ConnectionBanner />
      <header className="header">
        <div className="header-inner">
          <NavLink to="/" className="brand">
            🎵 Fake Music Hunter
            {health.data && <small>v{health.data.version}</small>}
          </NavLink>
          <nav className="nav">
            <NavLink to="/" end>Nuevo análisis</NavLink>
            <NavLink to="/jobs">Historial</NavLink>
          </nav>
        </div>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<NewAnalysisPage />} />
          <Route path="/jobs" element={<HistoryPage />} />
          <Route path="/jobs/:jobId" element={<JobPage />} />
          <Route path="*" element={<p>Página no encontrada.</p>} />
        </Routes>
      </main>
    </>
  );
}
