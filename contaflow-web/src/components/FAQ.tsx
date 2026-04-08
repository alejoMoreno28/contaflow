"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { ChevronDown } from "lucide-react";

const faqs = [
  {
    q: "¿Puedo manejar varias empresas desde una cuenta?",
    a: "Sí, puedes registrar y gestionar múltiples empresas bajo una sola cuenta. Cada empresa tendrá su propia memoria de proveedores y cuentas PUC para evitar confusiones."
  },
  {
    q: "¿Cuánto tiempo toma configurar ContaFlow?",
    a: "Menos de 2 minutos. Solo necesitas crear tu cuenta, configurar los accesos básicos a tu ERP (Siigo o Alegra) y puedes empezar a subir facturas inmediatamente."
  },
  {
    q: "¿Con qué software contable se conecta?",
    a: "Actualmente tenemos integración nativa con Siigo Nube, Siigo Contador y Alegra. Estamos trabajando para integrar Loggro y otros ERPs locales pronto."
  },
  {
    q: "¿Los créditos vencen?",
    a: "No. Si compras el paquete de créditos flexibles, estos no tienen fecha de vencimiento. Puedes usarlos a tu ritmo y en cualquiera de las empresas que gestiones."
  },
  {
    q: "¿Qué tipos de documentos puedo procesar?",
    a: "Facturas electrónicas de compra en PDF, cuentas de cobro, notas crédito y recibos de servicios públicos. Nuestra IA extrae datos de cualquier formato o estructura."
  },
  {
    q: "¿Necesito conocimientos técnicos?",
    a: "No, ContaFlow está diseñado para ser extremadamente intuitivo. Si sabes arrastrar un archivo PDF a una ventana de tu navegador, ya sabes usar ContaFlow."
  }
];

export default function FAQ() {
  const [openIdx, setOpenIdx] = useState<number | null>(0);

  return (
    <section className="py-24 bg-white">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-3xl">
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl sm:text-4xl font-bold text-text-main tracking-tight"
          >
            Preguntas frecuentes
          </motion.h2>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, idx) => {
            const isOpen = openIdx === idx;
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className="border border-border-main rounded-2xl overflow-hidden bg-base"
              >
                <button
                  onClick={() => setOpenIdx(isOpen ? null : idx)}
                  className="w-full flex justify-between items-center p-6 text-left"
                >
                  <span className="font-bold text-text-main md:text-lg pr-4">{faq.q}</span>
                  <ChevronDown
                    className={`w-5 h-5 text-primary shrink-0 transition-transform duration-300 ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                </button>
                <AnimatePresence>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="p-6 pt-0 text-text-muted leading-relaxed">
                        {faq.a}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
