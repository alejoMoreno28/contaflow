"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Check, Heart } from "lucide-react";

export default function Pricing() {
  const [volume, setVolume] = useState<number>(100);
  const monthlyPricePerCausacion = 510;
  const paygPricePerCausacion = 600;

  return (
    <section id="precios" className="py-24 bg-base relative">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl sm:text-4xl md:text-5xl font-bold text-text-main mb-6 tracking-tight"
          >
            Precios pensados para contadores colombianos
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-lg text-text-muted"
          >
            Paga solo por lo que usas. Sin sorpresas.
          </motion.p>
        </div>

        <div className="flex flex-col lg:flex-row items-center justify-center gap-8 max-w-5xl mx-auto">
          
          {/* Pay As You Go Card */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="w-full lg:w-1/2 bg-white rounded-3xl p-8 border border-border-main shadow-xl relative"
          >
            <div className="inline-block px-3 py-1 bg-gray-100 rounded-full text-text-muted text-xs font-bold mb-6">
              Volumen variable
            </div>
            <h3 className="text-2xl font-bold text-text-main mb-2">Créditos flexibles</h3>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-5xl font-black text-text-main">${paygPricePerCausacion}</span>
              <span className="text-text-muted">COP / causación</span>
            </div>
            <p className="text-sm text-text-muted mb-8">IVA incluido</p>

            <ul className="space-y-4 mb-10">
              {["Compra cuando necesites", "Nunca vencen", "Úsalos en todas tus empresas"].map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-text-muted font-medium">
                  <Check className="w-5 h-5 text-gray-400" />
                  {f}
                </li>
              ))}
            </ul>

            <button className="w-full py-4 rounded-xl border-2 border-border-main text-text-main font-bold hover:border-text-muted transition-colors">
              Comprar créditos
            </button>
          </motion.div>

          {/* Monthly Plan Card */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="w-full lg:w-1/2 bg-gradient-to-br from-primary to-primary-hover rounded-3xl p-8 border border-primary-light/20 shadow-2xl relative lg:scale-105 z-10"
          >
            <div className="absolute -top-4 right-8 bg-green-400 text-green-950 px-4 py-1 rounded-full text-xs font-bold shadow-lg flex items-center gap-1">
              <Heart className="w-3 h-3 fill-current" />
              Más popular — 15% descuento
            </div>
            
            <h3 className="text-2xl font-bold text-white mb-2">Plan mensual</h3>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-5xl font-black text-white">${monthlyPricePerCausacion}</span>
              <span className="text-white/80">COP / causación</span>
            </div>
            <p className="text-sm text-white/70 mb-8">IVA incluido</p>

            <div className="mb-8 p-4 bg-white/10 rounded-xl border border-white/20">
              <label className="block text-white text-sm font-medium mb-3">
                Volumen estimado mensual: <span className="font-bold">{volume} causaciones</span>
              </label>
              <input
                type="range"
                min="100"
                max="500"
                step="100"
                value={volume}
                onChange={(e) => setVolume(Number(e.target.value))}
                className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer accent-white"
              />
              <div className="flex justify-between text-xs text-white/60 mt-2 font-medium">
                <span>100</span>
                <span>200</span>
                <span>500</span>
              </div>
              <div className="mt-4 pt-4 border-t border-white/20 flex justify-between items-center">
                <span className="text-white font-medium">Total estimado:</span>
                <span className="text-xl font-bold text-white">${(volume * monthlyPricePerCausacion).toLocaleString('es-CO')} COP/mes</span>
              </div>
            </div>

            <ul className="space-y-4 mb-10">
              {["Costos predecibles", "Renovación automática", "Cancela cuando quieras"].map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-white font-medium text-sm md:text-base">
                  <Check className="w-5 h-5 text-white/80" />
                  {f}
                </li>
              ))}
            </ul>

            <button className="w-full py-4 rounded-xl bg-white text-primary font-bold hover:bg-primary-light transition-colors shadow-lg">
              Empezar con plan mensual
            </button>
          </motion.div>

        </div>

        {/* Free Tier CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="mt-16 flex flex-col items-center text-center"
        >
          <p className="text-text-muted font-medium mb-6">
            25 causaciones gratis para empezar · Sin tarjeta de crédito requerida
          </p>
          <button className="px-8 py-4 bg-green-500 text-white rounded-xl font-bold text-lg hover:bg-green-600 transition-colors shadow-xl shadow-green-500/30">
            Crear cuenta GRATIS
          </button>
        </motion.div>
      </div>
    </section>
  );
}
