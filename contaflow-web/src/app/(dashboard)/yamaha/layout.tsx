'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, FileType, Bike, Users, Settings, ChevronLeft } from 'lucide-react'

export default function YamahaLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  const navItems = [
    { name: 'Panel Principal', href: '/yamaha', icon: LayoutDashboard },
    { name: 'Facturas Repuestos', href: '/yamaha/repuestos', icon: FileType },
    { name: 'Facturas de Motos', href: '/yamaha/motos', icon: Bike },
    { name: 'Pago a Empleados', href: '/yamaha/empleados', icon: Users },
  ]

  return (
    <div className="flex-1 flex min-h-0 bg-base w-full max-w-[1600px] mx-auto">
      
      {/* Sidebar de Yamaha */}
      <aside className="w-72 bg-white border-r border-border-main hidden lg:flex flex-col">
        <div className="p-6">
          <Link href="/dashboard" className="inline-flex items-center text-sm font-medium text-text-muted hover:text-primary transition-colors mb-6">
            <ChevronLeft className="w-4 h-4 mr-1" />
            Volver al Lobby
          </Link>
          
          <div className="flex items-center gap-3">
             <div className="w-10 h-10 rounded-xl bg-red-50 text-red-600 flex items-center justify-center font-bold">
               Y
             </div>
             <div>
               <h2 className="text-sm font-bold text-text-main">Incolmotos Yamaha</h2>
               <p className="text-xs text-text-muted">Área de Automatización</p>
             </div>
          </div>
        </div>
        
        <nav className="flex-1 px-4 py-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            const Icon = item.icon
            return (
              <Link 
                key={item.href} 
                href={item.href} 
                className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 ${
                  isActive 
                    ? 'bg-red-50 text-red-600 font-semibold' 
                    : 'text-text-muted hover:bg-gray-50 hover:text-text-main font-medium'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-red-600' : 'text-gray-400'}`} />
                {item.name}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-border-main">
          <Link href="#" className="flex items-center gap-3 px-3 py-2.5 text-text-muted hover:text-text-main hover:bg-gray-50 font-medium rounded-lg transition-colors">
            <Settings className="w-5 h-5" />
            Configuración Yamaha
          </Link>
        </div>
      </aside>

      {/* Contenido Modular */}
      <main className="flex-1 overflow-y-auto p-4 md:p-8 bg-base">
        {children}
      </main>
      
    </div>
  )
}
