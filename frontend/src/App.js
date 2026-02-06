import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Public pages
import { PublicLanding } from "./pages/PublicLanding";
import { Standard } from "./pages/Standard";
import { Manifesto } from "./pages/Manifesto";
import { Industry } from "./pages/Industry";
import { PublicVerify } from "./pages/PublicVerify";

// Docs layout and pages (existing technical documentation - unchanged)
import { DocsLayout } from "./components/DocsLayout";
import { DocsManifesto } from "./pages/docs/DocsManifesto";
import { DocsArchitecture } from "./pages/docs/DocsArchitecture";
import { DocsSpec } from "./pages/docs/DocsSpec";
import { DocsGovernance } from "./pages/docs/DocsGovernance";
import { DocsChangelog } from "./pages/docs/DocsChangelog";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* PUBLIC LAYER - New public-facing pages */}
        <Route path="/" element={<PublicLanding />} />
        <Route path="/standard" element={<Standard />} />
        <Route path="/manifesto" element={<Manifesto />} />
        <Route path="/industry" element={<Industry />} />
        <Route path="/verify" element={<PublicVerify />} />
        
        {/* DOCS LAYER - Existing technical documentation (unchanged) */}
        <Route path="/docs" element={<DocsLayout><DocsManifesto /></DocsLayout>} />
        <Route path="/docs/architecture" element={<DocsLayout><DocsArchitecture /></DocsLayout>} />
        <Route path="/docs/spec" element={<DocsLayout><DocsSpec /></DocsLayout>} />
        <Route path="/docs/governance" element={<DocsLayout><DocsGovernance /></DocsLayout>} />
        <Route path="/docs/changelog" element={<DocsLayout><DocsChangelog /></DocsLayout>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
