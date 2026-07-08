import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Certify } from './pages/Certify';
import Moment from './pages/Moment';
import MyMoments from './pages/MyMoments';
import { Verify } from './pages/Verify';
import { Generate } from './pages/Generate';
import { Legal } from './pages/Legal';
import { Spec as SpecPage } from './pages/Spec';
import { Philosophy } from './pages/Philosophy';
import { Manifeste } from './pages/Manifeste';
import FK from './pages/FK';
import Identity from './pages/Identity';
import Universe from './pages/Universe';
import { Privacy } from './pages/Privacy';
import { Cookies } from './pages/Cookies';
import { Terms } from './pages/Terms';
import { Disclosure } from './pages/Disclosure';
import { Imprint } from './pages/Imprint';
import { Help } from './pages/Help';
import Dashboard from './pages/Dashboard';
import ScanApp from './scan/ScanApp';
import Accueil from './pages/Accueil';
import Profil from './pages/Profil';
import Scanner from './pages/Scanner';
import Poste from './pages/Poste';
import Card from './pages/Card';
import Atlas from './pages/Atlas';
import Proof from './pages/Proof';
import Explorer from './pages/Explorer';
import AdminPdf from './pages/AdminPdf';

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

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 14, filter: 'blur(6px)' }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
        exit={{ opacity: 0, y: -8, filter: 'blur(8px)' }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        style={{ willChange: 'transform, opacity, filter' }}
      >
        <Routes location={location}>
          {/* Fenetre d'acces publique #1 — le premier geste */}
          <Route path="/" element={<Moment />} />
          <Route path="/mine" element={<MyMoments />} />

          {/* Certify = ancien landing historique. Manifeste = page v1.0 refondue. */}
          <Route path="/certify" element={<Certify />} />
          <Route path="/manifeste" element={<Manifeste />} />

          {/* FK Cultural Object Container — creation & verification */}
          <Route path="/fk" element={<FK />} />

          {/* FREK Identity — Passkey attache */}
          <Route path="/identity" element={<Identity />} />

          {/* Univers FREKCORE — la porte d'entree unifiee */}
          <Route path="/universe" element={<Universe />} />
          <Route path="/create" element={<Universe />} />

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

          {/* CC2026 Private Monitor (accessible only via /dashboard direct URL) */}
          <Route path="/dashboard" element={<Dashboard />} />

          {/* PWA Staff Scanner */}
          <Route path="/scan/*" element={<ScanApp />} />

          {/* FREK v2 UX Reboot — Public routes */}
          <Route path="/accueil" element={<Accueil />} />
          <Route path="/profil/:frekId" element={<Profil />} />
          <Route path="/scanner" element={<Scanner />} />
          <Route path="/poste" element={<Poste />} />
          <Route path="/card/:frekId" element={<Card />} />
          <Route path="/atlas" element={<Atlas />} />
          <Route path="/proof/:hash" element={<Proof />} />
          <Route path="/explorer" element={<Explorer />} />

          {/* Admin PDF Batch Generation */}
          <Route path="/admin/pdf" element={<AdminPdf />} />

          {/* Redirects legacy */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AnimatedRoutes />
    </BrowserRouter>
  );
}

export default App;
