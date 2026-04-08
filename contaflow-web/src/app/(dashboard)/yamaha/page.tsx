import Link from 'next/link'
import { FileType, Bike, Users, ArrowRight } from 'lucide-react'

export default function YamahaDashboardPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      <div>
        <h1 className="text-3xl font-bold text-text-main tracking-tight">Panel de Control: Yamaha</h1>
        <p className="text-text-muted mt-2">Selecciona el flujo de automatización contable que deseas ejecutar el día de hoy.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pt-4">
        
        {/* Módulo Original: Repuestos */}
        <Link 
          href="/yamaha/repuestos"
          className="group bg-white rounded-3xl p-6 border border-border-main hover:border-red-500 hover:shadow-xl hover:shadow-red-500/10 transition-all flex flex-col h-full relative overflow-hidden"
        >
           <div className="absolute top-0 right-0 p-4">
             <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
               Activo
             </span>
           </div>
           
           <div className="w-14 h-14 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mb-6">
             <FileType className="w-7 h-7" />
           </div>
           
           <h3 className="text-xl font-bold text-text-main mb-2">Facturas de Repuestos</h3>
           <p className="text-text-muted mb-8 text-sm flex-1">
             Sube PDFs combinados de Incolmotos. Genera PRNs contables respetando las cuentas específicas de cada referencia.
           </p>
           
           <div className="flex items-center text-red-600 font-semibold group-hover:translate-x-1 transition-transform">
             Cargar documentos <ArrowRight className="w-4 h-4 ml-1" />
           </div>
        </Link>
        
        {/* Módulo Próximo: Motos */}
        <Link 
          href="/yamaha/motos"
          className="group bg-white rounded-3xl p-6 border border-border-main hover:border-gray-300 transition-all flex flex-col h-full relative"
        >
           <div className="absolute top-0 right-0 p-4">
             <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
               Desarrollo
             </span>
           </div>
           
           <div className="w-14 h-14 rounded-2xl bg-gray-50 text-gray-400 flex items-center justify-center mb-6">
             <Bike className="w-7 h-7" />
           </div>
           
           <h3 className="text-xl font-bold text-text-main mb-2">Facturas de Motos</h3>
           <p className="text-text-muted mb-8 text-sm flex-1">
             Modelo entrenado para procesar inventario específico de motocicletas con sus números de VIN/Chasis.
           </p>

           <div className="flex items-center text-text-muted font-medium">
             Próximamente...
           </div>
        </Link>
        
        {/* Módulo Próximo: Empleados */}
        <Link 
          href="/yamaha/empleados"
          className="group bg-white rounded-3xl p-6 border border-border-main hover:border-gray-300 transition-all flex flex-col h-full relative"
        >
           <div className="absolute top-0 right-0 p-4">
             <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
               Desarrollo
             </span>
           </div>
           
           <div className="w-14 h-14 rounded-2xl bg-gray-50 text-gray-400 flex items-center justify-center mb-6">
             <Users className="w-7 h-7" />
           </div>
           
           <h3 className="text-xl font-bold text-text-main mb-2">Pago a Empleados</h3>
           <p className="text-text-muted mb-8 text-sm flex-1">
             Automatización de causación de nómina y comprobantes de egreso pre-configurados para Siigo.
           </p>

           <div className="flex items-center text-text-muted font-medium">
             Próximamente...
           </div>
        </Link>

      </div>
    </div>
  )
}
