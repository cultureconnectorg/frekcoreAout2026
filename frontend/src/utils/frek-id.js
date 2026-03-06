/**
 * Generate FREK-ID in format: FREK-YYYY-XX-NNN
 * @param {string} eventDate - Event date in YYYY-MM-DD format
 * @param {string} territory - ISO 3166-1 alpha-2 territory code
 * @returns {string} Generated FREK-ID
 */
export function generateFrekId(eventDate, territory) {
  const year = eventDate ? eventDate.split('-')[0] : new Date().getFullYear().toString();
  const territoryCode = territory?.toUpperCase() || 'XX';
  const sequenceNumber = String(Math.floor(Math.random() * 900) + 100).padStart(3, '0');
  
  return `FREK-${year}-${territoryCode}-${sequenceNumber}`;
}

/**
 * Parse FREK-ID into components
 * @param {string} frekId - FREK-ID string
 * @returns {object} Parsed components
 */
export function parseFrekId(frekId) {
  const match = frekId?.match(/^FREK-(\d{4})-([A-Z]{2})-(\d{3,})$/);
  if (!match) return null;
  
  return {
    prefix: 'FREK',
    year: match[1],
    territory: match[2],
    sequence: match[3],
  };
}

/**
 * Validate FREK-ID format
 * @param {string} frekId - FREK-ID to validate
 * @returns {boolean} True if valid
 */
export function isValidFrekId(frekId) {
  return /^FREK-\d{4}-[A-Z]{2}-\d{3,}$/.test(frekId);
}

export default { generateFrekId, parseFrekId, isValidFrekId };
