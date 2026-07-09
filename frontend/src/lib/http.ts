import { env } from './env'
import { supabase } from './supabase'

export class ApiError extends Error {
  status: number | null
  body: any
  isNetworkError: boolean

  constructor({
    message,
    status = null,
    body = null,
    isNetworkError = false,
  }: {
    message: string
    status?: number | null
    body?: any
    isNetworkError?: boolean
  }) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
    this.isNetworkError = isNetworkError

    // Ensure correct prototype chain for built-in Error extension
    Object.setPrototypeOf(this, ApiError.prototype)
  }
}

interface RequestOptions extends RequestInit {
  timeout?: number
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { timeout = 15000, headers = {}, ...restOptions } = options
  const url = `${env.apiBaseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`

  // 1. Prepare Request Headers
  const requestHeaders = new Headers(headers)
  if (!requestHeaders.has('Content-Type') && !(restOptions.body instanceof FormData)) {
    requestHeaders.set('Content-Type', 'application/json')
  }

  // 2. Automatically inject Supabase Bearer Token
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession()
    if (session?.access_token) {
      requestHeaders.set('Authorization', `Bearer ${session.access_token}`)
    }
  } catch (err) {
    // Non-blocking auth fetch logging; fail-safe to let request proceed
    console.warn('Could not fetch active Supabase auth session token:', err)
  }

  // 3. Configure Timeout Handling via AbortController
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: requestHeaders,
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    // Handle unsuccessful HTTP statuses
    if (!response.ok) {
      let errorBody: any = null
      try {
        errorBody = await response.json()
      } catch {
        // Fall back if response is not JSON
        try {
          errorBody = await response.text()
        } catch {
          errorBody = null
        }
      }

      throw new ApiError({
        message: errorBody?.detail || `API request failed with status ${response.status}`,
        status: response.status,
        body: errorBody,
        isNetworkError: false,
      })
    }

    // Return empty object/null for 204 No Content responses
    if (response.status === 204) {
      return null as T
    }

    // Try parsing as JSON
    return (await response.json()) as T
  } catch (error: any) {
    clearTimeout(timeoutId)

    // Re-throw if it's already an ApiError we constructed
    if (error instanceof ApiError) {
      throw error
    }

    // Handle request abortion (timeouts)
    if (error.name === 'AbortError') {
      throw new ApiError({
        message: `API request timed out after ${timeout}ms`,
        isNetworkError: false,
      })
    }

    // Handle network errors (connection issues, CORS failures, DNS failures)
    return (() => {
      throw new ApiError({
        message: error?.message || 'A network error occurred. Please check your connection.',
        isNetworkError: true,
      })
    })()
  }
}

// Thin HTTP verb convenience helpers
export const http = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'GET' }),

  post: <T>(path: string, body?: any, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  put: <T>(path: string, body?: any, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  patch: <T>(path: string, body?: any, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'DELETE' }),
}
