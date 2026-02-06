import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Home } from "./pages/Home";
import { Docs } from "./pages/Docs";
import { Architecture } from "./pages/Architecture";
import { Spec } from "./pages/Spec";
import { Governance } from "./pages/Governance";
import { Changelog } from "./pages/Changelog";
import { Verify } from "./pages/Verify";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing page without sidebar */}
        <Route path="/" element={<Layout><Home /></Layout>} />
        
        {/* Documentation pages with sidebar */}
        <Route path="/docs" element={<Layout><Docs /></Layout>} />
        <Route path="/architecture" element={<Layout><Architecture /></Layout>} />
        <Route path="/spec" element={<Layout><Spec /></Layout>} />
        <Route path="/governance" element={<Layout><Governance /></Layout>} />
        <Route path="/changelog" element={<Layout><Changelog /></Layout>} />
        
        {/* Verify tool */}
        <Route path="/verify" element={<Layout><Verify /></Layout>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
