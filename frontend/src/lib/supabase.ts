import { createClient } from '@supabase/supabase-js'
import { env } from './env'

// Initialize the Supabase browser client with public URL and anon key
export const supabase = createClient(env.supabaseUrl, env.supabaseAnonKey)
