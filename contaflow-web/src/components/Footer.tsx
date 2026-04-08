"use client";

import { Zap } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-white pt-20 pb-10 border-t border-border-main">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          
          <div className="md:col-span-1">
            <a href="/" className="flex items-center gap-2 mb-4">
              <img src="/logo.png" alt="ContaFlow Logo" className="h-8 w-auto object-contain" />
            </a>
            <p className="text-text-muted text-sm leading-relaxed mb-6">
              Automatización contable impulsada por inteligencia artificial para
              contadores y firmas en Colombia.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-text-main mb-6">Producto</h4>
            <ul className="space-y-4 text-sm text-text-muted">
              <li><a href="#como-funciona" className="hover:text-primary transition-colors">Cómo funciona</a></li>
              <li><a href="#precios" className="hover:text-primary transition-colors">Precios</a></li>
              <li><a href="#blog" className="hover:text-primary transition-colors">Blog</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-text-main mb-6">Empresa</h4>
            <ul className="space-y-4 text-sm text-text-muted">
              <li><a href="#" className="hover:text-primary transition-colors">Sobre nosotros</a></li>
              <li><a href="https://wa.me/573183867147?text=Hola%20ContaFlow%2C%20quiero%20m%C3%A1s%20informaci%C3%B3n" target="_blank" rel="noopener noreferrer" className="hover:text-primary transition-colors">Contacto</a></li>
              <li><a href="https://wa.me/573183867147?text=Hola%20ContaFlow%2C%20quiero%20m%C3%A1s%20informaci%C3%B3n" target="_blank" rel="noopener noreferrer" className="hover:text-primary transition-colors hover:text-[#25D366]">WhatsApp</a></li>
            </ul>
            <div className="mt-8 pt-4 border-t border-border-main">
              <p className="text-sm font-medium text-text-main mb-2">Contáctanos directamente</p>
              <a href="https://wa.me/573183867147?text=Hola%20ContaFlow%2C%20quiero%20m%C3%A1s%20informaci%C3%B3n" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm text-text-muted hover:text-[#25D366] transition-colors mb-2 font-medium">
                <span className="text-lg">📱</span> WhatsApp: +57 318 386 7147
              </a>
              <a href="mailto:info@contaflow.co" className="flex items-center gap-2 text-sm text-text-muted hover:text-primary transition-colors font-medium">
                <span className="text-lg">✉️</span> info@contaflow.co
              </a>
            </div>
          </div>

          <div>
            <h4 className="font-bold text-text-main mb-6">Legal</h4>
            <ul className="space-y-4 text-sm text-text-muted">
              <li><a href="#" className="hover:text-primary transition-colors">Política de privacidad</a></li>
              <li><a href="#" className="hover:text-primary transition-colors">Términos y condiciones</a></li>
            </ul>
          </div>

        </div>

        <div className="border-t border-border-main pt-8">
          <p className="text-center text-sm text-text-muted">
            © 2026 ContaFlow SAS · Hecho en Colombia 🇨🇴
          </p>
        </div>
      </div>
    </footer>
  );
}
