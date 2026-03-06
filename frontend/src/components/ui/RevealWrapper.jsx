import { motion } from 'framer-motion';
import { useScrollReveal } from '../../hooks/useScrollReveal';

export function RevealWrapper({ children, className = '', delay = 0 }) {
  const { ref, isVisible } = useScrollReveal();

  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 30 }}
      animate={isVisible ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
      transition={{ duration: 0.7, ease: 'easeOut', delay }}
    >
      {children}
    </motion.div>
  );
}

export default RevealWrapper;
