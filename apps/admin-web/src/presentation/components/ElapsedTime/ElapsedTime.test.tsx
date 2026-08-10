import { describe, expect, it } from 'vitest';
import { getElapsedUrgency } from './ElapsedTime';

describe('getElapsedUrgency', () => {
  it('is normal under 5 minutes', () => {
    expect(getElapsedUrgency(0)).toBe('normal');
    expect(getElapsedUrgency(4 * 60 * 1000)).toBe('normal');
  });

  it('is warning from 5 minutes up to (not including) 10', () => {
    expect(getElapsedUrgency(5 * 60 * 1000)).toBe('warning');
    expect(getElapsedUrgency(9 * 60 * 1000 + 59_000)).toBe('warning');
  });

  it('is critical at 10 minutes and beyond', () => {
    expect(getElapsedUrgency(10 * 60 * 1000)).toBe('critical');
    expect(getElapsedUrgency(60 * 60 * 1000)).toBe('critical');
  });
});
