import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function BlogPost() {
  return (
    <main className="min-h-screen flex flex-col bg-white">
      <Navbar />
      <div className="flex-1 pt-32 pb-24 container mx-auto px-4 sm:px-6 lg:px-8 max-w-3xl">
        <div className="mb-8">
          <div className="flex items-center gap-3 text-sm font-bold mb-4">
            <span className="text-primary bg-primary-light px-3 py-1 rounded-full">Editorial</span>
            <span className="text-text-muted">Marzo 2026</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-text-main mb-6 leading-tight tracking-tight">
            Todo lo que necesitas saber sobre procesos y automatización contable en 2026
          </h1>
        </div>
        <div className="w-full h-64 md:h-96 bg-primary-light rounded-2xl mb-12 flex items-center justify-center">
          <span className="text-primary text-2xl md:text-3xl font-bold opacity-30">Imagen ilustrativa</span>
        </div>
        <div className="prose prose-lg text-text-muted max-w-none">
          <p className="font-medium text-text-main text-xl mb-6">
            La contabilidad moderna en Colombia requiere de herramientas ágiles y conocimiento profundo sobre las normativas vigentes. En este artículo detallado exploramos las mejores estrategias tecnológicas para optimizar operaciones tributarias.
          </p>
          <p className="mb-6 leading-relaxed">
            Los contadores colombianos enfrentan uno de los ecosistemas fiscales más dinámicos de Latinoamérica. Entre resoluciones de la DIAN, cambios en la facturación electrónica, el documento soporte electrónico, y las constantes modificaciones del PUC (Plan Único de Cuentas), el tiempo se ha vuelto el activo más valioso de cualquier firma contable.
          </p>
          <h2 className="text-2xl font-bold text-text-main mt-10 mb-4 tracking-tight">El impacto del trabajo manual</h2>
          <p className="mb-6 leading-relaxed">
            Causar facturas a mano ya no es sostenible en pleno 2026. La digitación manual no solo toma valiosas horas de tiempo productivo, sino que incrementa exponencialmente el riesgo de errores en la aplicación de retenciones en la fuente, IVA descontable, e ICA. Un simple "dedazo" o un error de asignación de cuenta puede derivar en requerimientos de la DIAN y en auditorías que toman semanas o meses en resolverse.
          </p>
          <h2 className="text-2xl font-bold text-text-main mt-10 mb-4 tracking-tight">La llegada de la automatización inteligente (IA)</h2>
          <p className="mb-6 leading-relaxed">
            Con herramientas como ContaFlow, la recepción de archivos y su traducción contable ocurre en cuestión de segundos. Al simplemente arrastrar un PDF o cargar lotes masivos, la inteligencia artificial no solo extrae el documento mediante OCR semántico avanzado, sino que entiende perfectamente el contexto: si compraste equipos de cómputo, sabe distinguirlos como activos fijos o como gasto de mantenimiento dependiendo del negocio, del proveedor, y de la historia acumulativa de tus causaciones previas.
          </p>
          <p className="mb-6 leading-relaxed">
            Esta es la verdadera ventaja competitiva del contador del futuro: cambiar horas interminables de digitación rústica por horas de análisis financiero de alto nivel para aportar valor a sus clientes. El software moderno debe aprender de nosotros y facilitar nuestro flujo de trabajo, nunca atrasarlo.
          </p>
        </div>
      </div>
      <Footer />
    </main>
  );
}
