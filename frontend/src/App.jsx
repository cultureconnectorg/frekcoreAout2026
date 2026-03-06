import { Nav } from './components/layout/Nav';
import { Footer } from './components/layout/Footer';
import { Hero } from './components/sections/Hero';
import { Philosophie } from './components/sections/Philosophie';
import { Architecture } from './components/sections/Architecture';
import { Produits } from './components/sections/Produits';
import { Verifier } from './components/sections/Verifier';
import { Spec } from './components/sections/Spec';
import { FrekId } from './components/sections/FrekId';
import { CultureConnect } from './components/sections/CultureConnect';
import { Ecosysteme } from './components/sections/Ecosysteme';
import { Roadmap } from './components/sections/Roadmap';

function App() {
  return (
    <div className="min-h-screen bg-dark text-light">
      <Nav />
      <main>
        <Hero />
        <Philosophie />
        <Architecture />
        <Produits />
        <Verifier />
        <Spec />
        <FrekId />
        <CultureConnect />
        <Ecosysteme />
        <Roadmap />
      </main>
      <Footer />
    </div>
  );
}

export default App;
