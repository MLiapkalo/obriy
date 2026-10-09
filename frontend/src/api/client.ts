import type { paths } from './schema';
import createClient from 'openapi-fetch';

export const api = createClient<paths>({
  baseUrl: window.location.origin,
  fetch: (request) => globalThis.fetch(request),
});
