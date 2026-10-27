/**
 * HTTP client for Placement Copilot REST API (v1).
 * Handles bearer token authorization, HTTP-only cookie credentials,
 * and transparent queued token refreshing on 401 Unauthorized responses.
 */
class ApiClient {
  constructor() {
    const envUrl = import.meta.env.VITE_API_BASE_URL || '';
    this.baseUrl = `${envUrl.replace(/\/$/, '')}/api/v1`;
    this.accessToken = null;
    this.isRefreshing = false;
    this.refreshPromise = null;
  }

  /**
   * Sets or clears the active memory-held JWT access token.
   * @param {string|null} token
   */
  setAccessToken(token) {
    this.accessToken = token;
  }

  /**
   * Retrieves the active memory-held access token.
   * @returns {string|null}
   */
  getAccessToken() {
    return this.accessToken;
  }

  /**
   * Attempts silent refresh via the HTTP-only refresh cookie.
   * Single-flight: all concurrent callers share the same active in-flight promise.
   * @returns {Promise<string|null>}
   */
  async tryRefreshToken() {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      try {
        const res = await fetch(`${this.baseUrl}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        });
        if (!res.ok) {
          return null;
        }
        const data = await res.json();
        const token = data.access_token || null;
        if (token) {
          this.setAccessToken(token);
          if (typeof window !== 'undefined') {
            localStorage.setItem('has_session', 'true');
          }
        }
        return token;
      } catch {
        return null;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  /**
   * Base HTTP request wrapper with silent 401 token refresh.
   * @param {string} endpoint - API path (e.g. '/dashboard/summary')
   * @param {RequestInit} [options={}] - Standard Fetch options
   * @returns {Promise<any>}
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers = new Headers(options.headers || {});

    if (this.accessToken && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${this.accessToken}`);
    }

    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const config = {
      ...options,
      headers,
      credentials: 'include',
    };

    let response = await fetch(url, config);

    // If 401 and not an auth endpoint, await single-flight silent refresh
    if (
      response.status === 401 &&
      !endpoint.includes('/auth/login') &&
      !endpoint.includes('/auth/refresh') &&
      !endpoint.includes('/auth/register')
    ) {
      const newToken = await this.tryRefreshToken();
      if (newToken) {
        headers.set('Authorization', `Bearer ${newToken}`);
        response = await fetch(url, { ...config, headers });
      } else {
        this.setAccessToken(null);
        if (typeof window !== 'undefined') {
          localStorage.removeItem('has_session');
          window.dispatchEvent(new CustomEvent('auth:expired'));
        }
      }
    }

    if (!response.ok) {
      let errorData = {};
      try {
        errorData = await response.json();
      } catch {
        errorData = {
          error: {
            code: 'HTTP_ERROR',
            message: response.statusText || `Request failed with status ${response.status}`,
          },
        };
      }
      throw (
        errorData.error || {
          code: 'UNKNOWN_ERROR',
          message: `HTTP error ${response.status}`,
        }
      );
    }

    if (response.status === 204) {
      return {};
    }

    return response.json();
  }

  /**
   * HTTP GET convenience method.
   * @param {string} endpoint
   * @param {HeadersInit} [headers]
   * @returns {Promise<any>}
   */
  get(endpoint, headers) {
    return this.request(endpoint, { method: 'GET', headers });
  }

  /**
   * HTTP POST convenience method.
   * @param {string} endpoint
   * @param {any} [body]
   * @param {HeadersInit} [headers]
   * @returns {Promise<any>}
   */
  post(endpoint, body, headers) {
    return this.request(endpoint, {
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
      headers,
    });
  }

  /**
   * HTTP PATCH convenience method.
   * @param {string} endpoint
   * @param {any} [body]
   * @param {HeadersInit} [headers]
   * @returns {Promise<any>}
   */
  patch(endpoint, body, headers) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
      headers,
    });
  }

  /**
   * HTTP DELETE convenience method.
   * @param {string} endpoint
   * @param {HeadersInit} [headers]
   * @returns {Promise<any>}
   */
  delete(endpoint, headers) {
    return this.request(endpoint, { method: 'DELETE', headers });
  }
}

export const api = new ApiClient();
export default api;
