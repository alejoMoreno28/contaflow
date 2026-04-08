import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

const posts = [
  { slug: "causar-facturas-siigo", title: "Cómo causar facturas de compra en Siigo paso a paso", cat: "Tutoriales", date: "15 Mar 2026", desc: "Aprende el flujo exacto para ingresar facturas de proveedores evitando errores comunes en Siigo Nube." },
  { slug: "que-es-el-puc", title: "¿Qué es el PUC y cómo usarlo correctamente?", cat: "Conceptos", date: "12 Mar 2026", desc: "El Plan Único de Cuentas es la base de la contabilidad colombiana. Descubre la mejor forma de estructurarlo." },
  { slug: "retenciones-colombia-2026", title: "Retenciones en Colombia 2026: guía completa", cat: "Guías", date: "05 Mar 2026", desc: "Conoce las nuevas bases y tarifas de retención en la fuente aplicables para el nuevo año gravable." },
  { slug: "factura-electronica-vs-cuenta-cobro", title: "Factura electrónica vs cuenta de cobro: diferencias clave", cat: "Conceptos", date: "28 Feb 2026", desc: "No todas las transacciones requieren factura electrónica. Entiende cuándo es válido aceptar una cuenta de cobro." },
  { slug: "conectar-empresa-dian", title: "Cómo conectar tu empresa con la DIAN en 5 minutos", cat: "Tutoriales", date: "20 Feb 2026", desc: "Te mostramos el paso a paso en el portal de la DIAN para habilitar tu software de facturación y recepción." },
  { slug: "uvt-2026", title: "UVT 2026: valor actual e impacto en tu contabilidad", cat: "Novedades", date: "15 Feb 2026", desc: "La resolución de la nueva UVT afecta topes de retención y declaración de renta. Descubre cómo ajustarte." },
];

export default function Blog() {
  return (
    <main className="min-h-screen flex flex-col bg-base overflow-hidden">
      <Navbar />
      <div className="flex-1 pt-32 pb-24 container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-text-main mb-6 tracking-tight">Blog ContaFlow</h1>
          <p className="text-xl text-text-muted">Tips, guías y novedades sobre automatización contable</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {posts.map((post) => (
            <article key={post.slug} className="bg-white rounded-2xl border border-border-main overflow-hidden shadow-sm hover:shadow-lg transition-shadow flex flex-col">
              <div className="w-full h-48 bg-primary-light flex items-center justify-center">
                <span className="text-primary-dark font-black text-3xl opacity-30">ContaFlow</span>
              </div>
              <div className="p-6 flex-1 flex flex-col">
                <div className="flex items-center gap-3 text-xs font-bold mb-3">
                  <span className="text-primary">{post.cat}</span>
                  <span className="text-text-muted">{post.date}</span>
                </div>
                <h2 className="text-xl font-bold text-text-main mb-3 leading-tight">{post.title}</h2>
                <p className="text-text-muted text-sm mb-6 flex-1 leading-relaxed">{post.desc}</p>
                <Link href={`/blog/${post.slug}`} className="inline-flex items-center gap-2 text-primary font-bold text-sm hover:text-primary-hover w-max group">
                  Leer más <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>
            </article>
          ))}
        </div>
      </div>
      <Footer />
    </main>
  );
}
