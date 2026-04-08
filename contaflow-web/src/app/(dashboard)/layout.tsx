import Link from 'next/link'
import { logout } from '../login/actions'
import { LogOut, Bell } from 'lucide-react'

export default async function DashboardRootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const user = { email: 'demo@contaflow.co' }

  return (
    <div className="min-h-screen bg-base flex flex-col">
      {/* Topbar Global (Aplicable a Lobby y sub-paneles) */}
      <header className="h-16 bg-white border-b border-border-main flex items-center justify-between px-6 sticky top-0 z-50 shadow-sm">
        <Link href="/dashboard" className="text-xl font-black text-primary tracking-tighter hover:opacity-80 transition-opacity">
          ContaFlow <span className="text-sm font-medium text-text-muted ml-2">App</span>
        </Link>
        
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-3">
             <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm">
              {user.email.charAt(0).toUpperCase()}
            </div>
            <span className="text-sm font-medium text-text-main hidden sm:inline-block">{user.email}</span>
          </div>

          <button className="p-2 text-text-muted hover:text-primary transition-colors relative">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
          </button>

          <form action={logout}>
            <button className="p-2 text-text-muted hover:text-red-600 transition-colors" title="Cerrar Sessión">
              <LogOut className="w-5 h-5" />
            </button>
          </form>
        </div>
      </header>

      {/* Contenedor Principal (Donde se inyecta el Lobby o los Sidebars específicos) */}
      <div className="flex-1 flex flex-col min-h-0 bg-base">
        {children}
      </div>
    </div>
  )
}
