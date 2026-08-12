import { describe, expect, it } from 'vitest';
import { cn } from './cn';

describe('cn', () => {
  it('joins truthy class names with a space', () => {
    expect(cn('a', 'b', 'c')).toBe('a b c');
  });
  it('drops falsey parts so conditional classes collapse cleanly', () => {
    expect(cn('a', false, null, undefined, 'b')).toBe('a b');
  });
  it('returns an empty string when nothing is truthy', () => {
    expect(cn(false, null, undefined)).toBe('');
  });
});
