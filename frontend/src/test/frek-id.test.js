import { describe, it, expect } from 'vitest';
import { generateFrekId, parseFrekId, isValidFrekId } from '../utils/frek-id';

describe('frek-id utilities', () => {
  describe('generateFrekId', () => {
    it('should generate valid FREK-ID format', () => {
      const id = generateFrekId('2026-03-06', 'MQ');
      expect(id).toMatch(/^FREK-2026-MQ-\d{3}$/);
    });

    it('should use event year in FREK-ID', () => {
      const id = generateFrekId('2025-12-31', 'FR');
      expect(id).toContain('FREK-2025-FR-');
    });

    it('should uppercase territory code', () => {
      const id = generateFrekId('2026-01-01', 'mq');
      expect(id).toMatch(/^FREK-2026-MQ-\d{3}$/);
    });

    it('should use current year if no date provided', () => {
      const currentYear = new Date().getFullYear().toString();
      const id = generateFrekId(null, 'XX');
      expect(id).toContain(`FREK-${currentYear}-XX-`);
    });

    it('should use XX for undefined territory', () => {
      const id = generateFrekId('2026-01-01', undefined);
      expect(id).toMatch(/^FREK-2026-XX-\d{3}$/);
    });

    it('should generate 3-digit sequence numbers', () => {
      const id = generateFrekId('2026-01-01', 'MQ');
      const sequence = id.split('-')[3];
      expect(sequence).toMatch(/^\d{3}$/);
      expect(parseInt(sequence)).toBeGreaterThanOrEqual(100);
      expect(parseInt(sequence)).toBeLessThanOrEqual(999);
    });
  });

  describe('parseFrekId', () => {
    it('should parse valid FREK-ID', () => {
      const parsed = parseFrekId('FREK-2026-MQ-001');
      expect(parsed).toEqual({
        prefix: 'FREK',
        year: '2026',
        territory: 'MQ',
        sequence: '001',
      });
    });

    it('should parse FREK-ID with long sequence', () => {
      const parsed = parseFrekId('FREK-2026-FR-12345');
      expect(parsed.sequence).toBe('12345');
    });

    it('should return null for invalid FREK-ID', () => {
      expect(parseFrekId('INVALID')).toBeNull();
      expect(parseFrekId('FREK-26-MQ-001')).toBeNull();
      expect(parseFrekId('frek-2026-mq-001')).toBeNull();
      expect(parseFrekId(null)).toBeNull();
      expect(parseFrekId(undefined)).toBeNull();
    });
  });

  describe('isValidFrekId', () => {
    it('should validate correct FREK-ID formats', () => {
      expect(isValidFrekId('FREK-2026-MQ-001')).toBe(true);
      expect(isValidFrekId('FREK-2025-FR-999')).toBe(true);
      expect(isValidFrekId('FREK-2030-XX-12345')).toBe(true);
    });

    it('should reject invalid FREK-ID formats', () => {
      expect(isValidFrekId('INVALID')).toBe(false);
      expect(isValidFrekId('FREK-26-MQ-001')).toBe(false);
      expect(isValidFrekId('frek-2026-mq-001')).toBe(false);
      expect(isValidFrekId('FREK-2026-M-001')).toBe(false);
      expect(isValidFrekId('FREK-2026-MQX-001')).toBe(false);
      expect(isValidFrekId('')).toBe(false);
    });
  });
});
