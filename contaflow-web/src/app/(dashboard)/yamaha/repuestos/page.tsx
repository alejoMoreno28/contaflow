'use client'

import { useState } from 'react'
import { UploadCloud, FileType, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react'

const IVA_MAYOR_COSTO = 'IVA_MAYOR_COSTO'
const DESCONTABLE = 'DESCONTABLE'

type AccountingPreview = {
  capitalized_vat: number
  deductible_vat: number
}

type Invoice = {
  numero_factura: string
  subtotal: number | string
  iva_total: number | string
  items?: Array<Record<string, unknown>>
  _accountingPreview?: AccountingPreview | null
  [key: string]: unknown
}

type ReferenceIssue = {
  referencia: string
  descripcion: string
  codigo_producto?: string
}

type ExtractResponse = {
  factura: Invoice
  accounting_preview?: AccountingPreview | null
  accounting_error?: string | null
  missing_refs?: ReferenceIssue[]
  duplicados?: ReferenceIssue[]
}

function isOilProduct(code: string) {
  const normalized = code.trim()
  return /^\d{13}$/.test(normalized)
    && normalized.slice(0, 3) === '003'
    && normalized.slice(3, 7) === '0001'
}

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
  const [facturas, setFacturas] = useState<Invoice[]>([])
  const [missingRefs, setMissingRefs] = useState<ReferenceIssue[]>([])
  const [duplicateRefs, setDuplicateRefs] = useState<ReferenceIssue[]>([])
  const [accountingErrors, setAccountingErrors] = useState<string[]>([])
  
  const [customCodes, setCustomCodes] = useState<Record<string, string>>({})
  const [customTreatments, setCustomTreatments] = useState<Record<string, string>>({})

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
    setAccountingErrors([])

    const todasFacturas: Invoice[] = []
    const todasFaltantes: ReferenceIssue[] = []
    const todosDuplicados: ReferenceIssue[] = []
    const todosErroresContables: string[] = []

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
        
        const data = await res.json() as ExtractResponse
        todasFacturas.push({
          ...data.factura,
          _accountingPreview: data.accounting_preview,
        })
        if (data.missing_refs) todasFaltantes.push(...data.missing_refs)
        if (data.duplicados) todosDuplicados.push(...data.duplicados)
        if (data.accounting_error) todosErroresContables.push(`${file.name}: ${data.accounting_error}`)
      }

      setFacturas(todasFacturas)
      
      // Filtrar referencias faltantes únicas
      const uniqueFaltantes: ReferenceIssue[] = []
      const map = new Map<string, boolean>()
      for (const item of todasFaltantes) {
        if(!map.has(item.referencia)){
            map.set(item.referencia, true)
            uniqueFaltantes.push(item)
        }
      }
      setMissingRefs(uniqueFaltantes)
      setDuplicateRefs(todosDuplicados)
      setAccountingErrors(todosErroresContables)

    } catch {
      alert("No se pudo conectar al servidor de Python. Asegúrate de que FastAPI esté corriendo en el puerto 8000.")
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCustomCodeChange = (ref: string, code: string) => {
    setCustomCodes({...customCodes, [ref]: code})
  }

  const handleTreatmentChange = (ref: string, treatment: string) => {
    setCustomTreatments({...customTreatments, [ref]: treatment})
  }

  const saveMissingRefs = async () => {
    const payload = missingRefs.map(m => {
        const prod = (customCodes[m.referencia] || "").trim()
        return {
            referencia: m.referencia,
            producto: prod,
            descripcion: m.descripcion,
            tratamiento_iva: isOilProduct(prod)
              ? (customTreatments[m.referencia] || "")
              : DESCONTABLE,
        }
    })

    if (payload.some(p => !/^\d{13}$/.test(p.producto))) {
        alert("Todos los códigos Siigo deben tener exactamente 13 dígitos.")
        return
    }
    if (payload.some(p => isOilProduct(p.producto) && !p.tratamiento_iva)) {
        alert("Debes seleccionar el tratamiento de IVA de cada producto 003/0001.")
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
    } catch {
        alert("Falla de red.")
    }
  }

  const generatePRN = async () => {
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(`${apiUrl}/api/generate-prn`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              facturas: facturas.map((factura) => {
                const cleanInvoice = {...factura}
                delete cleanInvoice._accountingPreview
                return cleanInvoice
              }),
            })
        })
        
        if (!res.ok) {
            const err = await res.json()
            alert("Error generando PRN: " + JSON.stringify(err))
            return
        }

        const blob = await res.blob()
        const filename = res.headers.get("Content-Disposition")?.split("filename=")[1] || "Lote_ContaFlow.zip"
        downloadBlob(blob, filename.replace(/"/g, ''))
    } catch {
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
                              value={customCodes[ref.referencia] || ''}
                              onChange={(e) => handleCustomCodeChange(ref.referencia, e.target.value)}
                              className="w-full sm:w-64 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-400 outline-none"
                          />
                          {isOilProduct(customCodes[ref.referencia] || '') && (
                            <select
                              value={customTreatments[ref.referencia] || ''}
                              onChange={(e) => handleTreatmentChange(ref.referencia, e.target.value)}
                              className="w-full sm:w-72 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-400 outline-none"
                            >
                              <option value="">Selecciona tratamiento de IVA</option>
                              <option value={IVA_MAYOR_COSTO}>Excluida — IVA mayor valor del costo</option>
                              <option value={DESCONTABLE}>Gravada — IVA descontable</option>
                            </select>
                          )}
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

      {accountingErrors.length > 0 && (
        <div className="p-6 bg-red-50 border border-red-200 rounded-2xl text-red-800">
          <h3 className="font-bold flex items-center gap-2"><AlertTriangle/> Validación contable pendiente</h3>
          {accountingErrors.map((error) => <p key={error} className="text-sm mt-2">{error}</p>)}
        </div>
      )}

      {/* VALIDACIÓN ESTRICTA Y DESCARGA */}
      {facturas.length > 0 && missingRefs.length === 0 && duplicateRefs.length === 0 && accountingErrors.length === 0 && (
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
                                  <th className="px-4 py-3 border-b">IVA mayor costo</th>
                                  <th className="px-4 py-3 border-b">IVA descontable</th>
                                  <th className="px-4 py-3 border-b">A Pagar</th>
                              </tr>
                          </thead>
                          <tbody>
                              {facturas.map((fac, idx) => {
                                  const sub = Number(fac.subtotal) || 0;
                                  const iva = Number(fac.iva_total) || 0;
                                  return (
                                  <tr key={idx} className="border-b last:border-0 hover:bg-gray-50">
                                      <td className="px-4 py-3 font-medium text-text-main">{fac.numero_factura}</td>
                                      <td className="px-4 py-3 text-text-muted">{fac.items?.length || 0}</td>
                                      <td className="px-4 py-3">${sub.toLocaleString()}</td>
                                      <td className="px-4 py-3">${(fac._accountingPreview?.capitalized_vat || 0).toLocaleString()}</td>
                                      <td className="px-4 py-3">${(fac._accountingPreview?.deductible_vat ?? iva).toLocaleString()}</td>
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
