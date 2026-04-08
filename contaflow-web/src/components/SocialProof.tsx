"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

export default function SocialProof() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = 12450;
    const duration = 2000;
    const increment = end / (duration / 16);

    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);

    return () => clearInterval(timer);
  }, []);

  return (
    <section className="py-12 bg-white border-y border-border-main relative z-10">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          
          <div className="flex-1 text-center md:text-left">
            <p className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
              Compatible con los principales ERPs de Colombia
            </p>
            <div className="flex flex-wrap justify-center md:justify-start items-center gap-6 sm:gap-10">
              <span className="text-2xl font-black text-gray-400 tracking-tighter">SIIGO</span>
              <span className="text-2xl font-black text-gray-400 tracking-tighter">ALEGRA</span>
              <span className="text-xl font-bold text-gray-400 tracking-tight">SIIGO CONTADOR</span>
            </div>
          </div>

          <div className="hidden md:block w-px h-16 bg-border-main mx-4" />

          <div className="flex-1 text-center md:text-right">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="inline-flex flex-col items-center md:items-end"
            >
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-primary">
                  {count.toLocaleString('es-CO')}
                </span>
                <span className="text-3xl font-bold text-primary">+</span>
              </div>
              <p className="text-sm font-medium text-text-muted mt-1">
                Causaciones procesadas automáticamente
              </p>
            </motion.div>
          </div>

        </div>
      </div>
    </section>
  );
}
