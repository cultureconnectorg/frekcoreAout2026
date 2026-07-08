import { Link } from 'react-router-dom';

/**
 * FREKCORE Brand — logo + wordmark cliquable.
 * Renvoie toujours vers la porte d'entrée ("/universe" par défaut, ou une route
 * fournie via la prop `to`). Design blanc/bleu v1.0.
 */
export default function BrandLogo({
  to = '/universe',
  variant = 'light',
  size = 'md',
  showWordmark = false,
  className = '',
  testId = 'brand-logo',
}) {
  const sizes = {
    sm: { img: 'h-7', text: 'text-base' },
    md: { img: 'h-9', text: 'text-xl' },
    lg: { img: 'h-11', text: 'text-2xl' },
  };
  const s = sizes[size] || sizes.md;
  const textColor = variant === 'dark' ? 'text-white' : 'text-slate-900';

  return (
    <Link
      to={to}
      aria-label="FREKCORE — retour à la porte d'entrée"
      data-testid={testId}
      className={`inline-flex items-center gap-2.5 group focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 rounded-md transition-all ${className}`}
    >
      <img
        src="/frek-logo.png"
        alt=""
        aria-hidden="true"
        className={`${s.img} w-auto transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3 group-active:scale-95`}
        style={{ filter: variant === 'light' ? 'none' : 'brightness(1.6)' }}
      />
      {showWordmark && (
        <span
          className={`${s.text} font-bold tracking-tight ${textColor} transition-colors group-hover:text-blue-600`}
        >
          FREKCORE
        </span>
      )}
    </Link>
  );
}
