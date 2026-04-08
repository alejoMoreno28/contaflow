"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Cpu, Check } from "lucide-react";

export default function Feature() {
  const points = [
    "Memoria por proveedor (NIT)",
    "Memoria por referencia y producto",
    "Sugerencias automáticas de cuentas PUC",
    "Retenciones calculadas automáticamente",
    "Método de pago recordado"
  ];

  return (
    <section className="py-24 bg-white overflow-hidden">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        <div className="flex flex-col lg:flex-row items-center gap-16">
          
          {/* Info Side */}
          <div className="w-full lg:w-1/2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-light rounded-full text-primary-dark font-medium text-sm mb-6"
            >
              <Cpu className="w-4 h-4" />
              <span>Inteligencia que aprende</span>
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-text-main leading-tight mb-6"
            >
              Aprende una vez. <br className="hidden sm:block" />
              Automatiza para siempre.
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="text-lg text-text-muted mb-8 leading-relaxed"
            >
              La primera vez asignas la cuenta contable. ContaFlow la recuerda para ese proveedor. La segunda factura se causa sola, sin que toques nada. Con el tiempo, el 95% de tus facturas se procesan automáticamente.
            </motion.p>

            <ul className="space-y-4">
              {points.map((point, idx) => (
                <motion.li
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.3 + idx * 0.1 }}
                  className="flex items-center gap-3 text-text-main font-medium"
                >
                  <div className="w-6 h-6 rounded-full bg-primary-light flex items-center justify-center shrink-0">
                    <CheckCircle2 className="w-5 h-5 text-primary" />
                  </div>
                  {point}
                </motion.li>
              ))}
            </ul>
          </div>

          {/* Mockup Side */}
          <div className="w-full lg:w-1/2 relative">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="bg-base rounded-3xl p-6 sm:p-8 border border-border-main shadow-2xl relative"
            >
              {/* Fake UI Header */}
              <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm mb-6">
                <div>
                  <p className="text-sm font-bold">Yamaha Motor</p>
                  <p className="text-xs text-text-muted">NIT: 860.000.111-2</p>
                </div>
                <div className="bg-primary-light text-primary px-3 py-1 rounded-full text-xs font-bold">
                  Proveedor conocido
                </div>
              </div>

              {/* Fake UI Items */}
              <div className="space-y-4">
                <div className="bg-white p-4 rounded-xl border-l-4 border-primary shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <p className="text-sm font-bold">Mantenimiento Correctivo</p>
                    <p className="text-sm font-bold">$1.200.000</p>
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded text-text-muted">Cuenta PUC recomendada</span>
                    <span className="text-xs font-bold bg-primary text-white px-2 py-1 rounded shadow-sm inline-flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      51451001
                    </span>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-border-main opacity-80 backdrop-blur-sm">
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-xs font-medium text-text-muted">Retención en la fuente (11%)</p>
                    <p className="text-xs font-medium text-red-500">-$132.000</p>
                  </div>
                  <div className="flex justify-between items-center">
                    <p className="text-xs font-medium text-text-muted">IVA (19%)</p>
                    <p className="text-xs font-medium text-text-main">$228.000</p>
                  </div>
                </div>
              </div>

              {/* Badge Overlay */}
              <div className="absolute -right-6 lg:-right-12 top-1/2 -translate-y-1/2 bg-white p-4 rounded-2xl shadow-xl border border-primary/20 flex flex-col items-center gap-2 rotate-6">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Check className="w-6 h-6 text-green-600" />
                </div>
                <p className="text-xs font-bold text-center">¡100%<br />Automático!</p>
              </div>

            </motion.div>
          </div>

        </div>
      </div>
    </section>
  );
}
