import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Public pages
import { PublicLanding } from "./pages/PublicLanding";
import { Industry } from "./pages/Industry";

// App (standalone tool)
import { AppVerify } from "./pages/AppVerify";

// Docs layout and pages
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
        {/* PUBLIC LAYER */}
        <Route path="/" element={<PublicLanding />} />
        <Route path="/industry" element={<Industry />} />
        
        {/* APP LAYER - Standalone verification tool */}
        <Route path="/app" element={<AppVerify />} />
        
        {/* DOCS LAYER - Developer documentation */}
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
