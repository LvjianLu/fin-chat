function formatApiDetail(detail: unknown): string {
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => formatApiDetail(item))
      .filter(Boolean)
      .join('; ');
  }

  if (detail && typeof detail === 'object') {
    const payload = detail as Record<string, unknown>;
    const message = typeof payload.msg === 'string' ? payload.msg : null;
    const location = Array.isArray(payload.loc)
      ? payload.loc.map((part) => String(part)).join('.')
      : null;

    if (message) {
      return location ? `${location}: ${message}` : message;
    }

    return JSON.stringify(payload);
  }

  return detail == null ? '' : String(detail);
}

export function extractApiErrorMessage(error: unknown): string {
  const payload = error as {
    response?: { data?: { detail?: unknown } };
    message?: string;
  };
  const detail = payload.response?.data?.detail;

  if (detail !== undefined) {
    const formatted = formatApiDetail(detail);
    if (formatted) {
      return formatted;
    }
  }

  return payload.message || 'Request failed';
}
