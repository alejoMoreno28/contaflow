---
description: Protocolo Estricto de Seguridad antes de modificar ContaFlow (Antigravity/Claude Rules)
---

## 🚦 PROTOCOLO ROJO: Actualización Sensible (Obligatorio)

**ESTA HABILIDAD SE DISPARA CUANDO:** El usuario (o cualquier humano) te solicita "actualizar", "agregar una función", "modificar algo", o "sumar código" al proyecto ContaFlow.

**NUNCA INICIES LA MODIFICACIÓN DE CÓDIGO DIRECTAMENTE.**
Como Agente de IA avanzado (Antigravity/Claude), tienes estrictamente prohibido dar por sentado o dañar la versión de producción (`yamaha_app.py`) o la Core API (`main.py`) que actualmente operan a la perfección.

Sigue rigurosamente estos 5 pasos ANTES de emitir parches:

1. **Analiza el Alcance Funcional:** Responde al usuario detallando exactamente qué archivos o pipelines pretende afectar su pedida.
2. **Evalúa Catástrofes por PRN:** Pregúntate en voz alta: *¿Este cambio altera la longitud estricta de 220 caracteres o la matemática de los subtotales/IVA del PRN contable?*. Si es un "sí", emite una advertencia de alto riesgo.
3. **Plantea el "Implementation Plan":** Crea y explica en la interfaz un Plan de Implementación paso por paso, dejando clarísimo cómo evitarás que el sistema actual colapse.
4. **Requiere Doble OK Manual:** Pídele confirmación humana explícita *"Dame luz verde o un 'Ok' para iniciar la inyección real del código"*.
5. **Exige Validación TDD Post-Modificación:** Una vez termines de editar el código, tienes obligación de decirle al humano que corra `pytest tests/ -v -s` en su entorno virtual para probar que la máquina PRN sigue sacando todo en verde.
