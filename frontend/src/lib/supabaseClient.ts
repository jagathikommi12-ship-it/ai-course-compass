import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!url || !anonKey) {
  throw new Error(
    'Missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY — copy .env.example to .env and fill them in.',
  )
}

// Safe to use in the browser: the anon key only ever grants what RLS
// policies allow (see supabase/migrations/0002_rls_policies.sql). It is
// NOT the service_role key, which must never appear in frontend code.
export const supabase = createClient(url, anonKey)
