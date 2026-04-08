"use client";

import { motion } from "framer-motion";
import { MessageCircle } from "lucide-react";

export default function CTA() {
  return (
    <section className="py-24 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-primary to-primary-hover -z-10" />
      
      {/* Decorative blurred circles */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-white/10 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-primary-dark/50 blur-3xl rounded-full -translate-x-1/2 translate-y-1/2 pointer-events-none" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl text-center relative z-10">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-white mb-6 tracking-tight leading-tight"
        >
          ¿Listo para automatizar tu contabilidad?
        </motion.h2>
        
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-xl text-primary-light/90 mb-10 max-w-2xl mx-auto"
        >
          Únete a los contadores que ya ahorran horas cada semana causándolas en Automático.
        </motion.p>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a href="/#precios" className="w-full sm:w-auto px-8 py-4 bg-white text-primary rounded-xl font-bold text-lg hover:bg-primary-light hover:scale-[1.02] transition-transform shadow-xl text-center">
            Empezar ahora
          </a>
          <a href="https://wa.me/573183867147?text=Hola%20ContaFlow%2C%20quiero%20m%C3%A1s%20informaci%C3%B3n" target="_blank" rel="noopener noreferrer" className="w-full sm:w-auto px-8 py-4 bg-transparent border-2 border-white/30 text-white rounded-xl font-bold text-lg hover:bg-white/10 hover:scale-[1.02] transition-transform text-center">
            Hablar con nosotros
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
          className="mt-8 flex items-center justify-center gap-2 text-primary-light/80 text-sm"
        >
          <MessageCircle className="w-4 h-4" />
          <a href="https://wa.me/573183867147?text=Hola%20ContaFlow%2C%20quiero%20m%C3%A1s%20informaci%C3%B3n" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
            ¿Dudas? Escríbenos al WhatsApp
          </a>
        </motion.div>
      </div>
    </section>
  );
}
