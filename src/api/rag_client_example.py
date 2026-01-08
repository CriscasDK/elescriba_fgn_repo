"""
Cliente de ejemplo para la API RAG
Muestra cómo integrar el sistema RAG en la interfaz principal de víctimas
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class RAGClient:
    """Cliente para consumir la API RAG desde la interfaz de víctimas"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def health_check(self) -> bool:
        """Verificar si la API está disponible"""
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error verificando salud de API: {e}")
            return False
    
    def consulta_rag(
        self, 
        pregunta: str, 
        usuario_id: str = "victimas_user",
        ip_cliente: str = "127.0.0.1",
        contexto_adicional: Optional[Dict] = None
    ) -> Dict:
        """
        Realizar consulta RAG y obtener respuesta con trazabilidad completa
        
        Args:
            pregunta: Consulta del usuario
            usuario_id: ID del usuario de la interfaz de víctimas
            ip_cliente: IP del cliente
            contexto_adicional: Contexto adicional para la consulta
            
        Returns:
            Diccionario con la respuesta completa del RAG
        """
        try:
            payload = {
                "pregunta": pregunta,
                "usuario_id": usuario_id,
                "ip_cliente": ip_cliente
            }
            
            if contexto_adicional:
                payload["contexto_adicional"] = contexto_adicional
            
            response = self.session.post(
                f"{self.api_base_url}/rag/consulta",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Error API: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error en consulta RAG: {e}")
            return {
                "error": str(e),
                "texto": "Lo siento, hubo un error procesando tu consulta.",
                "fuentes": [],
                "confianza": 0.0,
                "metodo": "error",
                "tiempo_respuesta": 0.0
            }
    
    def obtener_estado_sistema(self) -> Dict:
        """Obtener estado del sistema RAG"""
        try:
            response = self.session.get(f"{self.api_base_url}/rag/estado", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Error obteniendo estado: {response.status_code}")
        except Exception as e:
            print(f"Error obteniendo estado: {e}")
            return {"error": str(e)}

# Ejemplo de uso en la interfaz de víctimas
def ejemplo_integracion_victimas():
    """
    Ejemplo de cómo integrar el RAG en la interfaz de víctimas
    """
    
    # Inicializar cliente RAG
    rag_client = RAGClient("http://localhost:8000")
    
    # Verificar que la API esté disponible
    if not rag_client.health_check():
        print("❌ API RAG no está disponible")
        return
    
    print("✅ API RAG disponible")
    
    # Ejemplo de consulta
    pregunta = "¿Qué información hay sobre las víctimas de la Unión Patriótica?"
    
    print(f"\n🔍 Consultando: {pregunta}")
    
    # Realizar consulta
    resultado = rag_client.consulta_rag(
        pregunta=pregunta,
        usuario_id="victima_001",
        contexto_adicional={
            "seccion": "consulta_victimas",
            "tipo_usuario": "victima_directa"
        }
    )
    
    # Mostrar resultado
    if "error" not in resultado:
        print(f"\n📝 Respuesta: {resultado['texto']}")
        print(f"⏱️ Tiempo: {resultado['tiempo_respuesta']:.0f}ms")
        print(f"📊 Confianza: {resultado['confianza']:.1%}")
        print(f"🔧 Método: {resultado['metodo']}")
        
        # Mostrar fuentes con trazabilidad
        if resultado['fuentes']:
            print(f"\n📚 Fuentes ({len(resultado['fuentes'])}):")
            for i, fuente in enumerate(resultado['fuentes'], 1):
                print(f"\n[{fuente['cita']}] {fuente['nombre_archivo']}")
                print(f"   📄 Página: {fuente['pagina']}, Párrafo: {fuente['parrafo']}")
                print(f"   📈 Relevancia: {fuente['relevancia']:.2f}")
                print(f"   📝 Texto: {fuente['texto_resumen'] or fuente['texto_fuente'][:100]}...")
    else:
        print(f"❌ Error: {resultado['error']}")

# Función para integrar en Django/Flask de la interfaz de víctimas
def integrar_en_vista_victimas(request):
    """
    Ejemplo de cómo integrar en una vista de Django/Flask
    """
    
    # Este código iría en la vista de la interfaz de víctimas
    rag_client = RAGClient()
    
    if request.method == "POST":
        pregunta = request.POST.get('pregunta', '')
        usuario_id = request.user.id if hasattr(request, 'user') else 'anonimo'
        ip_cliente = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        # Realizar consulta RAG
        resultado_rag = rag_client.consulta_rag(
            pregunta=pregunta,
            usuario_id=usuario_id,
            ip_cliente=ip_cliente,
            contexto_adicional={
                "seccion": "consulta_documentos",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # El resultado_rag se puede pasar directamente al template
        # para mostrar la respuesta con trazabilidad completa
        
        return {
            'respuesta_rag': resultado_rag,
            'pregunta': pregunta,
            'timestamp': datetime.now()
        }

if __name__ == "__main__":
    # Ejecutar ejemplo
    ejemplo_integracion_victimas()
