"use client";

import { motion } from "framer-motion";
import { UploadCloud, Sparkles, CheckCircle2 } from "lucide-react";

const steps = [
  {
    num: "01",
    icon: UploadCloud,
    title: "Sube el PDF",
    desc: "Arrastra la factura o súbela desde tu computador. Cualquier formato."
  },
  {
    num: "02",
    icon: Sparkles,
    title: "La IA extrae todo",
    desc: "Proveedor, ítems, valores, impuestos y retenciones. Sin que toques nada."
  },
  {
    num: "03",
    icon: CheckCircle2,
    title: "Exporta a tu ERP",
    desc: "Un clic y la factura queda causada en Siigo o Alegra con todas las cuentas correctas."
  }
];

export default function HowItWorks() {
  return (
    <section id="como-funciona" className="py-24 bg-base relative overflow-hidden">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl relative z-10">
        <div className="text-center mb-20">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-text-main mb-6 tracking-tight">
            Tres pasos. Treinta segundos.
          </h2>
        </div>

        <div className="relative">
          {/* Connecting line for desktop */}
          <div className="hidden md:block absolute top-[60px] left-[15%] right-[15%] h-0.5 bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative">
            {steps.map((step, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.2 }}
                className="flex flex-col items-center text-center group"
              >
                {/* Number & Icon Container */}
                <div className="relative mb-8">
                  <span className="absolute -top-6 -left-8 text-7xl font-black text-white drop-shadow-sm select-none transition-transform group-hover:scale-110">
                    {step.num}
                  </span>
                  <div className="relative w-24 h-24 bg-primary rounded-2xl flex items-center justify-center shadow-xl shadow-primary/20 rotate-3 group-hover:rotate-0 transition-transform">
                    <step.icon className="w-10 h-10 text-white" />
                  </div>
                </div>

                <h3 className="text-2xl font-bold text-text-main mb-4">
                  {step.title}
                </h3>
                <p className="text-text-muted leading-relaxed max-w-sm">
                  {step.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
