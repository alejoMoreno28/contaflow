"use client";

import { motion } from "framer-motion";
import { Clock, AlertTriangle, RefreshCw, ArrowDown } from "lucide-react";

const problems = [
  {
    icon: Clock,
    title: "1 hora por factura digitando a mano",
    desc: "El tiempo que pierdes transcribiendo datos en lugar de analizar la información financiera."
  },
  {
    icon: AlertTriangle,
    title: "Errores en cuentas PUC y retenciones",
    desc: "Un simple dedazo puede causar multas y descuadres difíciles de encontrar a fin de mes."
  },
  {
    icon: RefreshCw,
    title: "Empezar desde cero con cada proveedor",
    desc: "Tu ERP no aprende. Tienes que volver a asignar la misma cuenta para la misma factura cada mes."
  }
];

export default function Problem() {
  return (
    <section className="py-24 bg-white">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl sm:text-4xl md:text-5xl font-bold text-text-main mb-6 tracking-tight"
          >
            ¿Cuánto tiempo pierdes causando facturas?
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-lg text-text-muted"
          >
            El proceso manual destruye tu productividad y te roba tiempo valioso.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {problems.map((item, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.15 }}
              className="bg-base rounded-2xl p-8 border border-border-main hover:shadow-lg transition-shadow"
            >
              <div className="w-14 h-14 bg-red-100 rounded-xl flex items-center justify-center mb-6">
                <item.icon className="w-7 h-7 text-red-500" />
              </div>
              <h3 className="text-xl font-bold text-text-main mb-3 leading-tight">
                {item.title}
              </h3>
              <p className="text-text-muted text-sm leading-relaxed">
                {item.desc}
              </p>
            </motion.div>
          ))}
        </div>

        <div className="mt-20 flex flex-col items-center justify-center">
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="flex flex-col items-center gap-4"
          >
            <div className="w-12 h-12 bg-primary-light rounded-full flex items-center justify-center">
              <ArrowDown className="w-6 h-6 text-primary" />
            </div>
            <p className="font-semibold text-primary">ContaFlow elimina todo eso:</p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
