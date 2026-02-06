// Domain configuration for FREK
// frekcore.com = Public website
// djproof = Developer portal / infrastructure

export const DOMAINS = {
  // Public website (frekcore.com)
  PUBLIC: '',  // Same origin for public pages
  
  // Developer portal (djproof)
  DEVELOPER: 'https://djproof.preview.emergentagent.com',
  
  // Documentation base URL
  DOCS_BASE: 'https://djproof.preview.emergentagent.com/docs'
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

// Check if we're on the public site
export function isPublicSite() {
  if (typeof window === 'undefined') return true;
  return !window.location.hostname.includes('djproof');
}
