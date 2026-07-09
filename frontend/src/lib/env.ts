/**
 * Environment configuration module.
 *
 * Validates and exports browser-safe environment variables at application startup.
 * Never read import.meta.env directly outside this file.
 */

interface Env {
  apiBaseUrl: string;
  supabaseUrl: string;
  supabaseAnonKey: string;
}

const requiredEnvVars = {
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL,
  VITE_SUPABASE_ANON_KEY: import.meta.env.VITE_SUPABASE_ANON_KEY,
} as const;

// Validate all required environment variables on startup
for (const [key, value] of Object.entries(requiredEnvVars)) {
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
}

export const env: Env = {
  apiBaseUrl: requiredEnvVars.VITE_API_BASE_URL,
  supabaseUrl: requiredEnvVars.VITE_SUPABASE_URL,
  supabaseAnonKey: requiredEnvVars.VITE_SUPABASE_ANON_KEY,
};
