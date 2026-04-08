import Link from 'next/link'
import { Building2, Plus } from 'lucide-react'

export default function LobbyPage() {
  return (
    <div className="max-w-6xl mx-auto w-full p-6 md:p-12 space-y-12">
      <div className="text-center max-w-2xl mx-auto space-y-4">
        <h1 className="text-3xl md:text-5xl font-bold text-text-main tracking-tight">Selecciona tu Empresa</h1>
        <p className="text-lg text-text-muted">
          Elige el entorno de trabajo al que deseas acceder. Cada empresa tiene sus propias facturas y configuraciones.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Entorno Yamaha */}
        <Link 
          href="/yamaha" 
          className="group bg-white rounded-3xl p-8 border hover:border-primary border-border-main transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 flex flex-col h-full relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-red-600 group-hover:scale-y-150 transition-transform origin-top" />
          <div className="w-16 h-16 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <Building2 className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-text-main mb-2">Incolmotos Yamaha</h2>
          <p className="text-text-muted mb-6">
            Entorno exclusivo configurado facturación Siigo / Alegra.
          </p>
          <div className="mt-auto flex items-center text-primary font-medium group-hover:translate-x-2 transition-transform">
            Ingresar al panel &rarr;
          </div>
        </Link>
        
        {/* Próximamente / Agregar Nueva */}
        <button className="group border-2 border-dashed border-gray-300 rounded-3xl p-8 flex flex-col items-center justify-center text-center hover:border-primary hover:bg-primary/5 transition-colors h-full min-h-[300px]">
          <div className="w-16 h-16 rounded-full bg-gray-50 flex items-center justify-center text-gray-400 mb-4 group-hover:bg-white group-hover:shadow-md transition-all">
            <Plus className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold text-text-main mb-2">Agregar cliente</h3>
          <p className="text-text-muted">Conecta una nueva empresa a ContaFlow.</p>
        </button>

      </div>
    </div>
  )
}
