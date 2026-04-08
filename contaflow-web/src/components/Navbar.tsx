"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Zap, Menu, X } from "lucide-react";

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-white/90 backdrop-blur-md shadow-md py-3"
          : "bg-transparent py-5"
      }`}
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        <div className="flex items-center justify-between">
          <a href="/" className="flex items-center gap-2">
            <img src="/logo.png" alt="ContaFlow Logo" className="h-8 w-auto object-contain" />
          </a>

          <nav className="hidden md:flex items-center gap-8">
            <a href="/#como-funciona" className="text-text-muted hover:text-primary transition-colors font-medium">
              Cómo funciona
            </a>
            <a href="/#precios" className="text-text-muted hover:text-primary transition-colors font-medium">
              Precios
            </a>
            <a href="/blog" className="text-text-muted hover:text-primary transition-colors font-medium">
              Blog
            </a>
          </nav>

          <div className="hidden md:flex items-center gap-4">
            <a href="/login" className="px-4 py-2 text-primary border border-primary rounded-lg font-medium hover:bg-primary-light transition-colors hover:scale-[1.02]">
              Ingresar
            </a>
            <a href="/#precios" className="px-4 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-hover transition-colors shadow-lg shadow-primary/30 hover:scale-[1.02]">
              Empezar gratis
            </a>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-text-main p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="absolute top-full left-0 right-0 bg-white shadow-xl p-4 md:hidden flex flex-col gap-4"
        >
          <a
            href="/#como-funciona"
            className="block px-4 py-2 text-text-main hover:bg-primary-light/50 rounded-lg font-medium"
            onClick={() => setMobileMenuOpen(false)}
          >
            Cómo funciona
          </a>
          <a
            href="/#precios"
            className="block px-4 py-2 text-text-main hover:bg-primary-light/50 rounded-lg font-medium"
            onClick={() => setMobileMenuOpen(false)}
          >
            Precios
          </a>
          <a
            href="/blog"
            className="block px-4 py-2 text-text-main hover:bg-primary-light/50 rounded-lg font-medium"
            onClick={() => setMobileMenuOpen(false)}
          >
            Blog
          </a>
          <div className="flex flex-col gap-3 pt-3 border-t border-border-main mt-1">
            <a href="/login" className="w-full text-center px-4 py-3 text-primary border border-primary rounded-lg font-medium hover:scale-[1.02] transition-transform">
              Ingresar
            </a>
            <a href="/#precios" className="w-full text-center px-4 py-3 bg-primary text-white rounded-lg font-medium shadow-lg shadow-primary/30 hover:scale-[1.02] transition-transform">
              Empezar gratis
            </a>
          </div>
        </motion.div>
      )}
    </header>
  );
}
