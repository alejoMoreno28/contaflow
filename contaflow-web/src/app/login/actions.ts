'use server'

import { redirect } from 'next/navigation'

export async function login(formData: FormData) {
  // Bypass total de la autenticación por ahora.
  // Directo al dashboard sin validar en Supabase.
  redirect('/dashboard')
}

export async function signup(formData: FormData) {
  redirect('/dashboard')
}

export async function logout() {
  redirect('/login')
}
