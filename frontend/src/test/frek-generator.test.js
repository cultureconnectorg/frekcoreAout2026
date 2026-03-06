import { describe, it, expect } from 'vitest';
import { generateFrekJson, validateWizardState } from '../utils/frek-generator';

describe('frek-generator utilities', () => {
  const validWizardState = {
    artist: {
      name: 'DJ Test',
      legal_name: 'Test Legal',
      territory: 'MQ',
    },
    event: {
      name: 'Test Event',
      date: '2026-03-06',
      start_time: '22:00',
      venue: 'Test Venue',
      city: 'Test City',
      context: 'live',
    },
    tracklist: [
      { position: 1, title: 'Track 1', artist: 'Artist 1', isrc: 'FR-ABC-26-00001', start_time: '00:00' },
      { position: 2, title: 'Track 2', artist: 'Artist 2', isrc: '', start_time: '03:30' },
    ],
    audioFingerprint: {
      method: 'sha256-fft-rms-zcr',
      value: 'a'.repeat(64),
      algorithm: 'Test Algorithm',
      sample_rate: 44100,
      fft_size: 2048,
      duration: 3600,
    },
  };

  describe('generateFrekJson', () => {
    it('should generate valid FREK JSON document', async () => {
      const result = await generateFrekJson(validWizardState);
      
      expect(result.document).toBeDefined();
      expect(result.mixId).toMatch(/^FREK-2026-MQ-\d{3}$/);
      expect(result.createdAt).toBeDefined();
      expect(result.signatureValue).toHaveLength(64);
    });

    it('should include all required fields in generated document', async () => {
      const result = await generateFrekJson(validWizardState);
      const doc = result.document;

      expect(doc.frek_version).toBe('0.4');
      expect(doc.mix_id).toBeDefined();
      expect(doc.created_at).toBeDefined();
      expect(doc.artist).toBeDefined();
      expect(doc.event).toBeDefined();
      expect(doc.tracklist).toBeDefined();
      expect(doc.audio_fingerprint).toBeDefined();
      expect(doc.timestamp).toBeDefined();
      expect(doc.operator).toBeDefined();
      expect(doc.signature).toBeDefined();
    });

    it('should include artist data correctly', async () => {
      const result = await generateFrekJson(validWizardState);
      
      expect(result.document.artist.name).toBe('DJ Test');
      expect(result.document.artist.legal_name).toBe('Test Legal');
      expect(result.document.artist.territory).toBe('MQ');
    });

    it('should include event data correctly', async () => {
      const result = await generateFrekJson(validWizardState);
      const event = result.document.event;
      
      expect(event.name).toBe('Test Event');
      expect(event.date).toBe('2026-03-06');
      expect(event.start_time).toBe('22:00');
      expect(event.venue).toBe('Test Venue');
      expect(event.city).toBe('Test City');
      expect(event.context).toBe('live');
    });

    it('should include tracklist with correct structure', async () => {
      const result = await generateFrekJson(validWizardState);
      const tracklist = result.document.tracklist;
      
      expect(tracklist).toHaveLength(2);
      expect(tracklist[0].position).toBe(1);
      expect(tracklist[0].title).toBe('Track 1');
      expect(tracklist[0].artist).toBe('Artist 1');
      expect(tracklist[0].isrc).toBe('FR-ABC-26-00001');
    });

    it('should omit empty optional fields in tracklist', async () => {
      const result = await generateFrekJson(validWizardState);
      const track2 = result.document.tracklist[1];
      
      expect(track2.isrc).toBeUndefined();
    });

    it('should include audio fingerprint data', async () => {
      const result = await generateFrekJson(validWizardState);
      const fp = result.document.audio_fingerprint;
      
      expect(fp.method).toBe('sha256-fft-rms-zcr');
      expect(fp.value).toBe('a'.repeat(64));
      expect(fp.sample_rate).toBe(44100);
      expect(fp.fft_size).toBe(2048);
    });

    it('should generate SHA-256 self-signature', async () => {
      const result = await generateFrekJson(validWizardState);
      
      expect(result.document.signature.method).toBe('sha256-self');
      expect(result.document.signature.value).toHaveLength(64);
      expect(result.document.signature.value).toMatch(/^[a-f0-9]{64}$/);
    });

    it('should include timestamp with timezone', async () => {
      const result = await generateFrekJson(validWizardState);
      const ts = result.document.timestamp;
      
      expect(ts.captured_at).toBeDefined();
      expect(ts.timezone).toBeDefined();
      expect(ts.source).toBe('device');
    });

    it('should handle empty tracklist', async () => {
      const stateNoTracks = { ...validWizardState, tracklist: [] };
      const result = await generateFrekJson(stateNoTracks);
      
      expect(result.document.tracklist).toEqual([]);
    });

    it('should handle missing optional artist fields', async () => {
      const stateMinimal = {
        ...validWizardState,
        artist: { name: 'DJ Minimal', territory: 'XX' },
      };
      const result = await generateFrekJson(stateMinimal);
      
      expect(result.document.artist.name).toBe('DJ Minimal');
      expect(result.document.artist.legal_name).toBeUndefined();
    });
  });

  describe('validateWizardState', () => {
    it('should pass validation for complete state', () => {
      const validation = validateWizardState(validWizardState);
      
      expect(validation.isValid).toBe(true);
      expect(Object.keys(validation.errors).filter(k => !k.includes('Warning'))).toHaveLength(0);
    });

    it('should fail validation for missing artist name', () => {
      const state = { ...validWizardState, artist: { ...validWizardState.artist, name: '' } };
      const validation = validateWizardState(state);
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors.artistName).toBeDefined();
    });

    it('should fail validation for missing event name', () => {
      const state = { ...validWizardState, event: { ...validWizardState.event, name: '' } };
      const validation = validateWizardState(state);
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors.eventName).toBeDefined();
    });

    it('should fail validation for missing event date', () => {
      const state = { ...validWizardState, event: { ...validWizardState.event, date: '' } };
      const validation = validateWizardState(state);
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors.eventDate).toBeDefined();
    });

    it('should warn for missing fingerprint', () => {
      const state = { ...validWizardState, audioFingerprint: { ...validWizardState.audioFingerprint, value: '' } };
      const validation = validateWizardState(state);
      
      expect(validation.isValid).toBe(true); // Still valid, just warning
      expect(validation.errors.fingerprintWarning).toBeDefined();
    });
  });
});
