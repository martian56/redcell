import { afterEach, describe, expect, it, vi } from 'vitest';
import { fmtElapsed, fmtTokens, hhmmss, sevShort, sevVar, timeAgo } from './format';

describe('sevVar', () => {
  it('maps each severity to its color token', () => {
    expect(sevVar('critical')).toBe('var(--color-crit)');
    expect(sevVar('high')).toBe('var(--color-high)');
    expect(sevVar('medium')).toBe('var(--color-med)');
    expect(sevVar('low')).toBe('var(--color-low)');
    expect(sevVar('info')).toBe('var(--color-info)');
  });
});

describe('sevShort', () => {
  it('abbreviates each severity', () => {
    expect(sevShort('critical')).toBe('CRIT');
    expect(sevShort('high')).toBe('HIGH');
    expect(sevShort('medium')).toBe('MED');
    expect(sevShort('low')).toBe('LOW');
    expect(sevShort('info')).toBe('INFO');
  });
});

describe('fmtTokens', () => {
  it('leaves values under 1k as plain integers', () => {
    expect(fmtTokens(0)).toBe('0');
    expect(fmtTokens(999)).toBe('999');
  });
  it('formats thousands with one decimal and a k suffix', () => {
    expect(fmtTokens(1000)).toBe('1.0k');
    expect(fmtTokens(1500)).toBe('1.5k');
  });
  it('formats millions with two decimals and an M suffix', () => {
    expect(fmtTokens(1_000_000)).toBe('1.00M');
    expect(fmtTokens(2_500_000)).toBe('2.50M');
  });
});

describe('fmtElapsed', () => {
  it('zero-pads hours, minutes, and seconds', () => {
    expect(fmtElapsed(0)).toBe('00:00:00');
    expect(fmtElapsed(59)).toBe('00:00:59');
    expect(fmtElapsed(3661)).toBe('01:01:01');
    expect(fmtElapsed(3600 * 12 + 34 * 60 + 56)).toBe('12:34:56');
  });
});

describe('hhmmss', () => {
  it('renders the local wall-clock time of an ISO string', () => {
    // No trailing Z: parsed as local time, so the output is timezone-stable.
    expect(hhmmss('2026-08-12T09:07:05')).toBe('09:07:05');
  });
});

describe('timeAgo', () => {
  afterEach(() => vi.useRealTimers());

  it('describes the distance from now in the largest fitting unit', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-08-12T12:00:00Z'));
    const ago = (ms: number) => new Date(Date.now() - ms).toISOString();
    expect(timeAgo(ago(5_000))).toBe('5s ago');
    expect(timeAgo(ago(5 * 60_000))).toBe('5m ago');
    expect(timeAgo(ago(3 * 3_600_000))).toBe('3h ago');
    expect(timeAgo(ago(2 * 86_400_000))).toBe('2d ago');
  });
});
