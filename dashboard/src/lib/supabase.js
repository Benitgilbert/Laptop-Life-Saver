import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY

if (!supabaseUrl || !supabaseKey) {
    console.error(`
        ❌ ERROR: Missing Supabase environment variables!
        
        If you are seeing this on Vercel:
        1. Go to your Project Settings > Environment Variables.
        2. Ensure your keys are named EXACTLY:
           - VITE_SUPABASE_URL
           - VITE_SUPABASE_KEY
        3. Re-deploy your project.
        
        Vite requires the 'VITE_' prefix for variables to be exposed to the client.
    `)
}

export const supabase = createClient(supabaseUrl || '', supabaseKey || '')
