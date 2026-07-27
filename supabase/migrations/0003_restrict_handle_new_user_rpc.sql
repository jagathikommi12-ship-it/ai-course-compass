-- handle_new_user() is a SECURITY DEFINER trigger function; PostgREST auto-exposes
-- every function in the public schema as an RPC endpoint by default, so without
-- this it's callable directly at /rest/v1/rpc/handle_new_user by anon/authenticated.
-- It should only ever fire via the auth.users insert trigger, never be called
-- directly, so revoke the RPC-callable EXECUTE grant.
--
-- Found by Supabase's built-in security advisor after applying 0001/0002.
revoke all on function public.handle_new_user() from public, anon, authenticated;
