import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';

/**
 * PageTransition — wrapper cinématographique pour transitions inter-pages.
 * Effet : fade + subtile echelle + blur radial doux + slide horizontal minime.
 * Aligne le rythme d'entree/sortie sur toutes les pages (feeling "PlayStation Motion Design").
 */
export default function PageTransition({ children }) {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 12, filter: 'blur(6px)', scale: 0.995 }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)', scale: 1 }}
        exit={{ opacity: 0, y: -8, filter: 'blur(8px)', scale: 1.005 }}
        transition={{
          duration: 0.55,
          ease: [0.22, 1, 0.36, 1], // out-expo doux
        }}
        style={{ willChange: 'transform, opacity, filter' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
