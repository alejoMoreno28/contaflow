"use client";

import { motion } from "framer-motion";
import { Sparkles, ArrowRight, ShieldCheck } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden min-h-[90vh] flex items-center">
      {/* Background gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 bg-gradient-to-br from-base to-primary-light/40">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute bottom-[-10%] right-[-5%] w-[50%] h-[50%] rounded-full bg-primary-light blur-3xl" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        <div className="flex flex-col lg:flex-row items-center gap-16 lg:gap-8">
          
          {/* Left Content (60%) */}
          <div className="w-full lg:w-[60%] flex flex-col items-start text-left">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-full border border-primary/30 text-primary-dark font-medium text-sm mb-6 shadow-sm"
            >
              <Sparkles className="w-4 h-4 text-primary" />
              <span>✦ Automatización contable con IA</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-text-main tracking-tight leading-[1.1] mb-6"
            >
              Tu contabilidad,
              <br className="hidden sm:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary-hover relative">
                {" automatizada."}
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0, 1, 0] }}
                  transition={{ repeat: Infinity, duration: 1 }}
                  className="absolute -right-6 top-1 w-1 h-14 bg-primary inline-block lg:h-16"
                />
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg sm:text-xl text-text-muted mb-10 max-w-2xl leading-relaxed"
            >
              Sube el PDF, la IA extrae todo y exporta a Siigo o Alegra en segundos. Sin digitación manual, sin errores.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-col sm:flex-row items-start sm:items-center gap-4 w-full sm:w-auto"
            >
              <a href="#precios" className="group px-8 py-4 bg-primary text-white rounded-xl font-bold text-lg hover:bg-primary-hover hover:scale-[1.02] transition-all duration-300 shadow-xl shadow-primary/30 flex items-center justify-center gap-2 w-full sm:w-auto">
                Empieza gratis 
                <span className="font-normal opacity-90 text-sm hidden sm:inline">— 25 causaciones sin costo</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </a>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="mt-6 flex items-center gap-2 text-sm text-text-muted"
            >
              <ShieldCheck className="w-4 h-4 text-green-500" />
              <span>Sin tarjeta de crédito · Configuración en 2 min</span>
            </motion.div>

            {/* Social Proof Avatars */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.6 }}
              className="mt-12 flex items-center gap-4"
            >
              <div className="flex -space-x-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="w-10 h-10 rounded-full border-2 border-white bg-primary-light flex items-center justify-center text-xs font-bold text-primary-dark">
                    C{i}
                  </div>
                ))}
              </div>
              <p className="text-sm font-medium text-text-muted">
                Usado por contadores en <br className="hidden sm:block" /> toda Colombia 🇨🇴
              </p>
            </motion.div>
          </div>

          {/* Right Content - Floating Mockup (40%) */}
          <div className="w-full lg:w-[40%] relative">
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ type: "spring", stiffness: 50, delay: 0.3, duration: 0.8 }}
            >
              <motion.div
                animate={{ y: [-10, 10, -10] }}
                transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
                className="relative w-full aspect-[4/5] sm:aspect-[3/4] lg:aspect-square bg-white/40 backdrop-blur-2xl border border-white/60 rounded-3xl shadow-2xl overflow-hidden p-6 lg:p-8 flex flex-col"
              >
                {/* Mockup Header */}
                <div className="flex justify-between items-center mb-6 pb-4 border-b border-white/50">
                  <div>
                    <h3 className="font-bold text-text-main">Facturas subidas</h3>
                    <p className="text-xs text-text-muted">Procesando con IA...</p>
                  </div>
                  <div className="w-8 h-8 rounded-full border-t-2 border-primary border-r-2 animate-spin" />
                </div>

              {/* Mockup Table/List */}
              <div className="flex flex-col gap-4">
                {[
                  { ref: "CPFE-750304", name: "Incolmotos SAS", val: "$384.100" },
                  { ref: "CPFE-751726", name: "Yamaha Motor", val: "$5.623.904" },
                  { ref: "CPFE-753150", name: "Repuestos S.A.", val: "$289.632" },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + idx * 0.2 }}
                    className="flex justify-between items-center p-4 bg-white/70 rounded-xl shadow-sm border border-white/80"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary-light rounded-lg flex items-center justify-center">
                        <span className="text-primary font-bold text-xs">PDF</span>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-text-main">{item.ref}</p>
                        <p className="text-xs text-text-muted">{item.name}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-text-main">{item.val}</p>
                      <p className="text-[10px] text-green-600 font-bold bg-green-100 px-2 py-0.5 rounded-full inline-block mt-1">
                        Extraído
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Success notification overlay */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 2.5, type: "spring" }}
                  className="absolute bottom-6 left-1/2 -translate-x-1/2 w-[85%] bg-green-50 border border-green-200 p-4 rounded-xl shadow-lg flex items-center gap-3"
                >
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center shrink-0">
                    <ShieldCheck className="w-4 h-4 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-green-800">Causación exitosa</p>
                    <p className="text-xs text-green-600">Exportado a Siigo</p>
                  </div>
                </motion.div>
              </motion.div>
            </motion.div>
          </div>

        </div>
      </div>
    </section>
  );
}
