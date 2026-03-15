import { extractApiErrorMessage } from '@/services/error';

describe('API error helpers', () => {
  it('returns backend string detail directly', () => {
    expect(
      extractApiErrorMessage({
        response: {
          data: {
            detail: 'Backend not initialized: OPENROUTER_API_KEY not set in environment',
          },
        },
      })
    ).toBe('Backend not initialized: OPENROUTER_API_KEY not set in environment');
  });

  it('formats FastAPI validation details into readable text', () => {
    expect(
      extractApiErrorMessage({
        response: {
          data: {
            detail: [
              {
                loc: ['body', 'session_id'],
                msg: 'Input should be a valid string',
              },
            ],
          },
        },
      })
    ).toBe('body.session_id: Input should be a valid string');
  });

  it('falls back to the generic error message', () => {
    expect(extractApiErrorMessage(new Error('Network Error'))).toBe('Network Error');
  });
});
