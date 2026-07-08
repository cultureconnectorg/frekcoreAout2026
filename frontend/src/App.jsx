import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Certify } from './pages/Certify';
import Moment from './pages/Moment';
import MyMoments from './pages/MyMoments';
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

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Fenetre d'acces publique #1 — le premier geste */}
        <Route path="/" element={<Moment />} />
        <Route path="/mine" element={<MyMoments />} />

        {/* Certify = Manifeste + landing historique */}
        <Route path="/certify" element={<Certify />} />
        <Route path="/manifeste" element={<Certify />} />
        
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

        {/* PWA Scanner Staff terrain */}
        <Route path="/scan/*" element={<ScanApp />} />

        {/* Nouvelles pages utilisateur — additives, aucun fichier existant modifie */}
        <Route path="/accueil" element={<Accueil />} />
        <Route path="/profil/:frekId" element={<Profil />} />
        <Route path="/scanner" element={<Scanner />} />
        <Route path="/poste" element={<Poste />} />
        <Route path="/card/:frekId" element={<Card />} />
        <Route path="/atlas" element={<Atlas />} />
        <Route path="/proof/:hash" element={<Proof />} />
        <Route path="/explorer" element={<Explorer />} />
        <Route path="/admin/pdf" element={<AdminPdf />} />
        
        {/* Redirections anciennes URLs */}
      </Routes>
    </BrowserRouter>
  );
}

export default App;
