'use client'

import { useState } from 'react'
import { UploadCloud, FileType, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react'

// Utilidad para descargar archivos desde memoria
function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

export default function RepuestosPage() {
  const [files, setFiles] = useState<File[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [facturas, setFacturas] = useState<any[]>([])
  const [missingRefs, setMissingRefs] = useState<any[]>([])
  const [duplicateRefs, setDuplicateRefs] = useState<any[]>([])
  
  const [customCodes, setCustomCodes] = useState<Record<string, string>>({})

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const processFiles = async () => {
    if (files.length === 0) return
    setIsProcessing(true)
    setFacturas([])
    setMissingRefs([])
    setDuplicateRefs([])

    let todasFacturas = []
    let todasFaltantes = []
    let todosDuplicados = []

    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append("file", file)
        
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(`${apiUrl}/api/extract`, {
          method: "POST",
          body: formData
        })
        
        if (!res.ok) {
          const err = await res.json()
          alert(`Error en ${file.name}: ${err.detail || 'Fallo de IA'}`)
          continue
        }
        
        const data = await res.json()
        todasFacturas.push(data.factura)
        if (data.missing_refs) todasFaltantes.push(...data.missing_refs)
        if (data.duplicados) todosDuplicados.push(...data.duplicados)
      }

      setFacturas(todasFacturas)
      
      // Filtrar referencias faltantes únicas
      const uniqueFaltantes = []
      const map = new Map()
      for (const item of todasFaltantes) {
        if(!map.has(item.referencia)){
            map.set(item.referencia, true)
            uniqueFaltantes.push(item)
        }
      }
      setMissingRefs(uniqueFaltantes)
      setDuplicateRefs(todosDuplicados)

    } catch (e) {
      alert("No se pudo conectar al servidor de Python. Asegúrate de que FastAPI esté corriendo en el puerto 8000.")
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCustomCodeChange = (ref: string, code: string) => {
    setCustomCodes({...customCodes, [ref]: code})
  }

  const saveMissingRefs = async () => {
    // Calcular cta_inv
    const payload = missingRefs.map(m => {
        const prod = customCodes[m.referencia] || ""
        const cta_sufijo = prod.substring(3, 7) || "0000"
        return {
            referencia: m.referencia,
            producto: prod,
            descripcion: m.descripcion,
            cta_inv: "14350102" + cta_sufijo
        }
    })

    if (payload.some(p => !p.producto)) {
        alert("Debes llenar todos los códigos Siigo.")
        return
    }

    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(`${apiUrl}/api/add-reference`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        })
        if (res.ok) {
            alert("¡Referencias insertadas en Google Sheets con éxito!")
            setMissingRefs([]) // Limpia para que se habiliten los PRN
        } else {
            alert("Error al guardar en el Excel matriz.")
        }
    } catch (e) {
        alert("Falla de red.")
    }
  }

  const generatePRN = async () => {
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(`${apiUrl}/api/generate-prn`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ facturas: facturas })
        })
        
        if (!res.ok) {
            const err = await res.json()
            alert("Error generando PRN: " + JSON.stringify(err))
            return
        }

        const blob = await res.blob()
        const filename = res.headers.get("Content-Disposition")?.split("filename=")[1] || "Lote_ContaFlow.zip"
        downloadBlob(blob, filename.replace(/"/g, ''))
    } catch (e) {
        alert("Error de red conectando al motor de PRN.")
    }
  }

  return (
    <div className="max-w-4xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-text-main flex items-center gap-3">
          <FileType className="text-red-500" />
          Automatización de Repuestos
        </h1>
        <p className="text-text-muted mt-2">
          Sube tus facturas combinadas. Nuestro motor se encargará conectar con Siigo.
        </p>
      </div>

      {!facturas.length && (
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-3xl p-12 text-center hover:border-red-400 transition-colors relative shadow-sm">
        <input 
          type="file" 
          multiple 
          accept="application/pdf"
          onChange={handleFileChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        />
        <div className="w-20 h-20 mx-auto bg-gray-50 rounded-full flex items-center justify-center mb-4">
          <UploadCloud className="w-10 h-10 text-gray-400" />
        </div>
        <h3 className="text-xl font-bold text-text-main mb-2">
           {files.length > 0 ? `${files.length} archivos seleccionados` : "Arrastra los PDFs aquí"}
        </h3>
        <p className="text-text-muted max-w-sm mx-auto">
          Archivos permitidos: PDF de Incolmotos Yamaha.
        </p>
        
        {files.length > 0 && (
          <button 
            onClick={(e) => { e.stopPropagation(); processFiles(); }}
            disabled={isProcessing}
            className="mt-6 px-8 py-3 bg-red-600 text-white font-bold rounded-xl shadow-lg hover:bg-red-700 transition-all z-20 relative disabled:opacity-70"
          >
            {isProcessing ? <><Loader2 className="w-5 h-5 animate-spin inline mr-2"/> Procesando magia...</> : "🚀 Extraer Inteligencia"}
          </button>
        )}
      </div>
      )}

      {/* ERRORES Y REFERENCIAS FALTANTES */}
      {duplicateRefs.length > 0 && (
          <div className="p-6 bg-red-50 border border-red-200 rounded-2xl text-red-800">
              <h3 className="font-bold flex items-center gap-2"><AlertTriangle/> Códigos duplicados detectados</h3>
              <p className="text-sm mt-2">Hay códigos producto Siigo que están mapeados a múltiples referencias. Corrige tu excel.</p>
          </div>
      )}

      {missingRefs.length > 0 && (
          <div className="p-6 bg-orange-50 border border-orange-200 rounded-2xl text-orange-900 shadow-sm">
              <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
                  <AlertTriangle className="w-6 h-6"/> Se detectaron {missingRefs.length} referencias nuevas
              </h3>
              <p className="text-sm mb-4">La IA no pudo asignarles cuenta contable. Clasifícalas para insertarlas en tu matriz.</p>
              
              <div className="space-y-4">
                  {missingRefs.map((ref, idx) => (
                      <div key={idx} className="flex flex-col sm:flex-row items-center gap-4 bg-white p-4 rounded-xl border border-orange-100">
                          <div className="flex-1">
                              <span className="font-mono text-sm bg-orange-100 px-2 py-1 rounded text-orange-800">{ref.referencia}</span>
                              <p className="text-xs text-text-muted mt-1 truncate">{ref.descripcion}</p>
                          </div>
                          <input 
                              type="text" 
                              placeholder="Cód Siigo (Ej: 0020089...)"
                              onChange={(e) => handleCustomCodeChange(ref.referencia, e.target.value)}
                              className="w-full sm:w-64 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-400 outline-none"
                          />
                      </div>
                  ))}
              </div>
              
              <button 
                onClick={saveMissingRefs}
                className="mt-6 w-full py-3 bg-orange-600 text-white font-bold rounded-xl hover:bg-orange-700 transition"
              >
                  ✅ Confirmar y Guardar en Matriz
              </button>
          </div>
      )}

      {/* VALIDACIÓN ESTRICTA Y DESCARGA */}
      {facturas.length > 0 && missingRefs.length === 0 && duplicateRefs.length === 0 && (
          <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 text-green-900 p-6 rounded-2xl flex items-center justify-between">
                  <div>
                      <h3 className="font-bold flex items-center gap-2 text-lg"><CheckCircle2/> Verificación Mágica Completa</h3>
                      <p className="text-sm mt-1">El 100% de los códigos hacen Match con Inteligencia ContaFlow.</p>
                  </div>
                  <button 
                      onClick={generatePRN}
                      className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl shadow-lg transition-transform hover:scale-105"
                  >
                      ⬇️ Empaquetar y Descargar PRNs
                  </button>
              </div>

              <div className="bg-white rounded-2xl border border-border-main p-6 overflow-hidden">
                  <h4 className="font-bold text-text-main mb-4">Auditoría Financiera Preliminar</h4>
                  <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                          <thead className="bg-gray-50 text-gray-500 font-medium">
                              <tr>
                                  <th className="px-4 py-3 rounded-tl-xl border-b">Documento</th>
                                  <th className="px-4 py-3 border-b">Ítems</th>
                                  <th className="px-4 py-3 border-b">Subtotal</th>
                                  <th className="px-4 py-3 border-b">A Pagar</th>
                              </tr>
                          </thead>
                          <tbody>
                              {facturas.map((fac, idx) => {
                                  const sub = parseFloat(fac.subtotal) || 0;
                                  const iva = parseFloat(fac.iva_total) || 0;
                                  return (
                                  <tr key={idx} className="border-b last:border-0 hover:bg-gray-50">
                                      <td className="px-4 py-3 font-medium text-text-main">{fac.numero_factura}</td>
                                      <td className="px-4 py-3 text-text-muted">{fac.items?.length || 0}</td>
                                      <td className="px-4 py-3">${sub.toLocaleString()}</td>
                                      <td className="px-4 py-3 font-bold text-red-600">${(sub+iva).toLocaleString()}</td>
                                  </tr>
                                  )
                              })}
                          </tbody>
                      </table>
                  </div>
              </div>
          </div>
      )}

    </div>
  )
}
