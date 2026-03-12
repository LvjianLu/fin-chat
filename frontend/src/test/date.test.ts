import { formatDistanceToNow, formatDate } from '../utils/date';

describe('Date Utils', () => {
  it('formats distance to now correctly for minutes', () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
    const result = formatDistanceToNow(fiveMinutesAgo);
    expect(result).toContain('m ago');
  });

  it('returns "Just now" for times less than a minute ago', () => {
    const now = new Date();
    const thirtySecondsAgo = new Date(now.getTime() - 30 * 1000);
    const result = formatDistanceToNow(thirtySecondsAgo);
    expect(result).toBe('Just now');
  });

  it('formats date to readable string', () => {
    const date = new Date('2024-01-15T10:30:00');
    const result = formatDate(date);
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
  });
});
