# MIGRACIÓN CONTAFLOW V2: DE MVP A SAAS B2B MULTI-TENANT

Este documento almacena la memoria de estado y el plan maestro acordado entre el Administrador y Antigravity. Si una nueva instancia de IA lee esto, debe adherirse estrictamente a esta hoja de ruta de Next.js sin alterar el Streamlit original en la carpeta raíz.

## Contexto de la Transición
El sistema en `yamaha_app.py` funciona perfectamente en producción sobre Streamlit. La meta actual es reemplazar todo el frontend por una aplicación de clase mundial usando tecnología moderna (Next.js), dejando eventualmente el Python solo como una API Backend (FastAPI).

## Fases Acordadas

### Fase 1: Creación del Portal y Login (Actual)
* **Status:** INICIANDO
* **Directrices:** 
  - Zona de trabajo: `contaflow-web/`
  - Stack obligatorio: Next.js 14, Tailwind CSS, shadcn/ui.
  - Tareas: Configurar **Supabase Auth**, crear un dashboard multi-tenant (Login, Navbar con logo ContaFlow, Workspace selector).
  - El diseño estético es prioridad #1: Glassmorphism, paletas "Morado Tech" premium (ver `AGENTS.txt`).

### Fase 2: Conexión de API Mágica (Próximamente)
* **Status:** PENDIENTE
* **Directrices:** Convertir la lógica de extracción (Claude) de `yamaha_app.py` en a una API REST (FastAPI) externa.

### Fase 3: Lanzamiento y Reemplazo (Futuro)
* **Status:** PENDIENTE
* **Directrices:** Reemplazar y apagar la infraestructura antigua de Streamlit.
