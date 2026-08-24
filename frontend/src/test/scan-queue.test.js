import { describe, expect, it } from 'vitest';
import {
  MAX_RETRY_ATTEMPTS,
  classifyFailure,
  isEligibleForRetry,
  retryDelayMs,
} from '../scan/lib';

describe('staff offline queue retry policy', () => {
  it('uses bounded exponential backoff for temporary failures', () => {
    expect(retryDelayMs(1)).toBe(5_000);
    expect(retryDelayMs(2)).toBe(10_000);
    expect(retryDelayMs(99)).toBe(300_000);
    expect(classifyFailure(503)).toBe('temporary');
    expect(classifyFailure(429)).toBe('temporary');
  });

  it('classifies validation and authorization failures as permanent', () => {
    expect(classifyFailure(400)).toBe('permanent');
    expect(classifyFailure(403)).toBe('permanent');
    expect(MAX_RETRY_ATTEMPTS).toBeGreaterThan(0);
  });

  it('does not replay terminal or not-yet-due operations after a reload', () => {
    const now = Date.parse('2026-08-24T10:00:00.000Z');
    expect(isEligibleForRetry({ status: 'queued' }, now)).toBe(true);
    expect(isEligibleForRetry({ status: 'retrying', next_retry_at: '2026-08-24T10:00:01.000Z' }, now)).toBe(false);
    expect(isEligibleForRetry({ status: 'dead_letter' }, now)).toBe(false);
    expect(isEligibleForRetry({ status: 'succeeded' }, now)).toBe(false);
  });
});
