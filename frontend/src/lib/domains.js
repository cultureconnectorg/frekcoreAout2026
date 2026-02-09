// Domain configuration for FREK
// frekcore.com = Public website (production)
// djproof = Developer portal / infrastructure

// Read from environment or use current origin
const getEnvOrOrigin = (envVar, fallback) => {
  if (typeof window === 'undefined') return fallback;
  return process.env[envVar] || fallback;
};

export const DOMAINS = {
  // Public website - defaults to current origin for local dev
  PUBLIC: getEnvOrOrigin('REACT_APP_PUBLIC_URL', window?.location?.origin || ''),
  
  // Developer portal URL
  DEVELOPER: getEnvOrOrigin('REACT_APP_DEVELOPER_URL', 'https://frek-demo.preview.emergentagent.com'),
  
  // Documentation base URL (developer portal)
  DOCS_BASE: getEnvOrOrigin('REACT_APP_DOCS_URL', 'https://frek-demo.preview.emergentagent.com/docs')
};

// Helper to get docs URL
export function getDocsUrl(path = '') {
  return `${DOMAINS.DOCS_BASE}${path}`;
}

// Check if we're on the developer portal
export function isDeveloperPortal() {
  if (typeof window === 'undefined') return false;
  return window.location.hostname.includes('djproof');
}

// Check if we're on the public site (frekcore.com)
export function isPublicSite() {
  if (typeof window === 'undefined') return true;
  return window.location.hostname.includes('frekcore') || !isDeveloperPortal();
}
