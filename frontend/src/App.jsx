import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Certify } from './pages/Certify';
import { Verify } from './pages/Verify';
import { Generate } from './pages/Generate';
import { Legal } from './pages/Legal';
import { Spec as SpecPage } from './pages/Spec';
import { Philosophy } from './pages/Philosophy';
import { Privacy } from './pages/Privacy';
import { Cookies } from './pages/Cookies';
import { Terms } from './pages/Terms';
import { Disclosure } from './pages/Disclosure';
import { Imprint } from './pages/Imprint';
import { Help } from './pages/Help';
import Dashboard from './pages/Dashboard';

// Page "À propos" simplifiée (ancien contenu accessible)
import { Nav } from './components/layout/Nav';
import { Footer } from './components/layout/Footer';
import { Hero } from './components/sections/Hero';
import { Philosophie } from './components/sections/Philosophie';
import { Architecture } from './components/sections/Architecture';
import { Spec } from './components/sections/Spec';
import { Roadmap } from './components/sections/Roadmap';

function AboutPage() {
  return (
    <div className="min-h-screen bg-dark text-light">
      <Nav />
      <main>
        <Hero />
        <Philosophie />
        <Architecture />
        <Spec />
        <Roadmap />
      </main>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Certify = Page principale */}
        <Route path="/" element={<Certify />} />
        
        {/* Vérification publique */}
        <Route path="/verify/:frekId" element={<Verify />} />
        
        {/* Génération attestation (ancien wizard) */}
        <Route path="/generate" element={<Generate />} />
        
        {/* À propos / Spec */}
        <Route path="/about" element={<AboutPage />} />
        
        {/* Pages de contenu */}
        <Route path="/legal" element={<Legal />} />
        <Route path="/spec" element={<SpecPage />} />
        <Route path="/philosophy" element={<Philosophy />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/cookies" element={<Cookies />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="/disclosure" element={<Disclosure />} />
        <Route path="/imprint" element={<Imprint />} />
        <Route path="/help" element={<Help />} />
        <Route path="/dashboard" element={<Dashboard />} />
        
        {/* Redirections anciennes URLs */}
        <Route path="/certify" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
