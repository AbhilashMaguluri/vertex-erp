// ---------------------------------------------------------------------------
// Vertex API service — streaming fetch client with action support
// ---------------------------------------------------------------------------

import type { VertexRequest, VertexSSEvent, UIAction } from '../types/vertex';
import { getAccessToken } from '@/shared/lib/axios';

const getVertexApiUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && envUrl.startsWith('http')) {
    try {
      const url = new URL(envUrl);
      return `${url.origin}/api/vertex/message`;
    } catch {
      // Fallback if URL parsing fails
    }
  }
  return '/api/vertex/message';
};

/**
 * Stream a message to Vertex and yield parsed SSE events.
 */
export async function streamMessage(
  request: VertexRequest,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
  onAction: (action: UIAction) => void,
  signal?: AbortSignal,
): Promise<void> {
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token = getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const targetUrl = getVertexApiUrl();
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
      signal,
    });

    if (!response.ok) {
      const text = await response.text().catch(() => 'Unknown error');
      onError(`Server error (${response.status}): ${text}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError('Streaming is not supported in this browser.');
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;

        const jsonStr = trimmed.slice(6);
        try {
          const event: VertexSSEvent = JSON.parse(jsonStr);

          switch (event.type) {
            case 'token':
              onToken(event.content);
              break;
            case 'action':
              onAction(event.action);
              break;
            case 'done':
              onDone();
              return;
            case 'error':
              onError(event.content);
              return;
          }
        } catch {
          // Malformed JSON — skip
        }
      }
    }

    onDone();
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      return;
    }
    const message =
      err instanceof Error ? err.message : 'Failed to connect to Vertex.';
    onError(message);
  }
}
