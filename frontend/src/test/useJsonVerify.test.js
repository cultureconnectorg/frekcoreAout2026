import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useJsonVerify } from '../hooks/useJsonVerify';
import {
  validFrekJson,
  validMinimalFrekJson,
  strongProofFrekJson,
  weakProofFrekJson,
  invalidMissingVersion,
  invalidWrongVersion,
  invalidBadFrekId,
  invalidMissingFields,
  invalidBadFingerprint,
  invalidJsonString,
  emptyObject,
} from './vectors';

describe('useJsonVerify', () => {
  describe('Valid Documents', () => {
    it('should validate a complete FREK v0.4 document', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(validFrekJson));
      });

      expect(result.current.result.isValid).toBe(true);
      expect(result.current.result.missing).toHaveLength(0);
      expect(result.current.error).toBeNull();
    });

    it('should validate a minimal FREK document', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(validMinimalFrekJson));
      });

      expect(result.current.result.isValid).toBe(true);
    });

    it('should extract correct summary data', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(validFrekJson));
      });

      const summary = result.current.result.summary;
      expect(summary.mixId).toBe('FREK-2026-MQ-001');
      expect(summary.artist).toBe('DJ Kathy');
      expect(summary.event).toBe('Culture Connect 2026');
      expect(summary.date).toBe('2026-03-06');
      expect(summary.tracksCount).toBe(2);
    });
  });

  describe('Proof Levels', () => {
    it('should detect strong proof level with RFC3161 and bitcoin anchor', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(strongProofFrekJson));
      });

      expect(result.current.result.proofLevel).toBe('strong');
    });

    it('should detect weak proof level without signatures', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(weakProofFrekJson));
      });

      expect(result.current.result.proofLevel).toBe('weak');
    });

    it('should detect standard proof level for normal documents', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(validFrekJson));
      });

      expect(result.current.result.proofLevel).toBe('standard');
    });
  });

  describe('Invalid Documents', () => {
    it('should fail on invalid JSON string', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(invalidJsonString);
      });

      expect(result.current.result.isValid).toBe(false);
      expect(result.current.error).toContain('JSON invalide');
    });

    it('should detect missing frek_version', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(invalidMissingVersion));
      });

      expect(result.current.result.missing).toContain('frek_version');
    });

    it('should warn on wrong version', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(invalidWrongVersion));
      });

      const versionCheck = result.current.result.checks.find(c => c.label === 'frek_version');
      expect(versionCheck.ok).toBe(false);
      expect(versionCheck.warn).toBe(true);
    });

    it('should fail on bad FREK-ID format', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(invalidBadFrekId));
      });

      const frekIdCheck = result.current.result.checks.find(c => c.label === 'Format FREK-ID');
      expect(frekIdCheck.ok).toBe(false);
    });

    it('should list all missing required fields', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(invalidMissingFields));
      });

      expect(result.current.result.isValid).toBe(false);
      expect(result.current.result.missing).toContain('artist');
      expect(result.current.result.missing).toContain('event');
      expect(result.current.result.missing).toContain('tracklist');
    });

    it('should fail on bad fingerprint format', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(invalidBadFingerprint));
      });

      const fpCheck = result.current.result.checks.find(c => c.label === 'Fingerprint');
      expect(fpCheck.ok).toBe(false);
    });

    it('should handle empty object', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(emptyObject));
      });

      expect(result.current.result.isValid).toBe(false);
      expect(result.current.result.missing.length).toBeGreaterThan(0);
    });
  });

  describe('FREK-ID Format Validation', () => {
    it('should accept valid FREK-ID: FREK-2026-MQ-001', async () => {
      const { result } = renderHook(() => useJsonVerify());
      const doc = { ...validMinimalFrekJson, mix_id: 'FREK-2026-MQ-001' };
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(doc));
      });

      const check = result.current.result.checks.find(c => c.label === 'Format FREK-ID');
      expect(check.ok).toBe(true);
    });

    it('should accept FREK-ID with long sequence: FREK-2026-FR-12345', async () => {
      const { result } = renderHook(() => useJsonVerify());
      const doc = { ...validMinimalFrekJson, mix_id: 'FREK-2026-FR-12345' };
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(doc));
      });

      const check = result.current.result.checks.find(c => c.label === 'Format FREK-ID');
      expect(check.ok).toBe(true);
    });

    it('should reject invalid FREK-ID formats', async () => {
      const { result } = renderHook(() => useJsonVerify());
      const invalidIds = [
        'INVALID',
        'FREK-2026-MQ',
        'FREK-26-MQ-001',
        'frek-2026-mq-001',
        '2026-MQ-001',
      ];

      for (const id of invalidIds) {
        const doc = { ...validMinimalFrekJson, mix_id: id };
        await act(async () => {
          await result.current.verifyJson(JSON.stringify(doc));
        });
        const check = result.current.result.checks.find(c => c.label === 'Format FREK-ID');
        expect(check.ok).toBe(false);
      }
    });
  });

  describe('Hook State Management', () => {
    it('should reset state correctly', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(validFrekJson));
      });

      expect(result.current.result).not.toBeNull();

      act(() => {
        result.current.reset();
      });

      expect(result.current.result).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.isVerifying).toBe(false);
    });

    it('should handle multiple verifications', async () => {
      const { result } = renderHook(() => useJsonVerify());
      
      await act(async () => {
        await result.current.verifyJson(JSON.stringify(validFrekJson));
      });
      expect(result.current.result.isValid).toBe(true);

      await act(async () => {
        await result.current.verifyJson(invalidJsonString);
      });
      expect(result.current.result.isValid).toBe(false);

      await act(async () => {
        await result.current.verifyJson(JSON.stringify(validMinimalFrekJson));
      });
      expect(result.current.result.isValid).toBe(true);
    });
  });
});
