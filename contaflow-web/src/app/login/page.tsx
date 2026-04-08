'use client';

import { useActionState } from 'react';
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { login } from "./actions";
import { ArrowRight, Loader2 } from "lucide-react";

export default function Login() {
  const [state, formAction, isPending] = useActionState(async (prevState: any, formData: FormData) => {
    return await login(formData);
  }, null);

  return (
    <main className="min-h-screen flex flex-col bg-base relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-br from-primary-light/40 to-transparent -z-10 blur-3xl opacity-50" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-gradient-to-tl from-indigo-500/10 to-transparent -z-10 blur-3xl rounded-full opacity-50" />

      <Navbar />
      
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-32 mt-10">
        <div className="w-full max-w-md bg-white rounded-3xl shadow-xl border border-border-main p-8 sm:p-10 relative overflow-hidden group hover:shadow-2xl hover:border-primary/20 transition-all duration-500">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-indigo-500" />
          
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-text-main tracking-tight">Acceso Rápido</h1>
            <p className="text-sm text-text-muted mt-2">Prueba el nuevo panel de ContaFlow</p>
          </div>

          <form action={formAction} className="space-y-6">
            <button
              type="submit"
              disabled={isPending}
              className="w-full flex items-center justify-center gap-2 py-4 px-4 border border-transparent rounded-xl shadow-lg shadow-primary/20 text-white bg-primary hover:bg-primary-hover hover:scale-[1.02] active:scale-95 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-all duration-300 disabled:opacity-70 disabled:cursor-not-allowed text-lg font-bold"
            >
              {isPending ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <>
                  Ingresar a la Plataforma
                  <ArrowRight className="w-5 h-5 ml-1" />
                </>
              )}
            </button>
          </form>
          
          <div className="mt-8 text-center text-sm text-text-muted">
            <p>Acceso por correo y contraseña deshabilitado temporalmente para pruebas.</p>
          </div>
        </div>
      </div>
      <Footer />
    </main>
  );
}
