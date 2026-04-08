import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  })

  // Para el Bypass temporal, simplemente retornamos la respuesta normal
  // ignorando la validación del usuario y los redireccionamientos de seguridad.
  
  return supabaseResponse
}
