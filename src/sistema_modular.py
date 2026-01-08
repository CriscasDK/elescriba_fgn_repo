"""
Sistema principal que integra todos los servicios modulares
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional

from .core.query_router import QueryRouter
from .core.models import QueryRequest, QueryResponse, QueryType
from .database.postgresql_service import PostgreSQLDatabaseService
from .rag.azure_rag_service import AzureRAGService

class SistemaConsultaModular:
    """Sistema principal que orquesta todos los servicios de consulta"""
    
    def __init__(self):
        self.router = QueryRouter()
        self.database_service = None
        self.rag_service = None
        self.initialized = False
    
    async def initialize(self):
        """Inicializar todos los servicios"""
        logging.info("🚀 Inicializando Sistema de Consulta Modular...")
        
        try:
            # 1. Inicializar servicio de base de datos
            self.database_service = PostgreSQLDatabaseService()
            await self.database_service.initialize()
            self.router.register_service("database", self.database_service)
            
            # 2. Inicializar servicio RAG
            self.rag_service = AzureRAGService()
            self.router.register_service("rag", self.rag_service)
            
            self.initialized = True
            logging.info("✅ Sistema Modular inicializado correctamente")
            
            # Mostrar estado de servicios
            await self._log_service_status()
            
        except Exception as e:
            logging.error(f"❌ Error inicializando sistema: {e}")
            raise
    
    async def consulta(self, texto_consulta: str, filtros: Dict = None) -> QueryResponse:
        """Procesar consulta usando el sistema modular"""
        if not self.initialized:
            await self.initialize()
        
        # Crear request estructurado
        request = QueryRequest(
            text=texto_consulta,
            filters=filtros or {},
            metadata={}
        )
        
        # Rutear y procesar
        return await self.router.route_query(request)
    
    async def consulta_directa_bd(self, texto_consulta: str, filtros: Dict = None) -> QueryResponse:
        """Consulta directa a base de datos (bypass router)"""
        if not self.database_service:
            raise RuntimeError("Servicio de base de datos no disponible")
        
        request = QueryRequest(
            text=texto_consulta,
            filters=filtros or {},
            metadata={"force_service": "database"}
        )
        
        return await self.database_service.process_query(request)
    
    async def consulta_directa_rag(self, texto_consulta: str, filtros: Dict = None) -> QueryResponse:
        """Consulta directa a RAG (bypass router)"""
        if not self.rag_service:
            raise RuntimeError("Servicio RAG no disponible")
        
        request = QueryRequest(
            text=texto_consulta,
            filters=filtros or {},
            metadata={"force_service": "rag"}
        )
        
        return await self.rag_service.process_query(request)
    
    def get_estadisticas(self) -> Dict[str, Any]:
        """Obtener estadísticas completas del sistema"""
        if not self.initialized:
            return {"error": "Sistema no inicializado"}
        
        stats = {
            "router": self.router.get_stats(),
            "services": {}
        }
        
        # Estadísticas de servicios individuales
        if self.database_service:
            stats["services"]["database"] = self.database_service.get_service_info()
        
        if self.rag_service:
            stats["services"]["rag"] = self.rag_service.get_service_info()
        
        return stats
    
    def get_salud_servicios(self) -> Dict[str, Any]:
        """Verificar salud de todos los servicios"""
        if not self.initialized:
            return {"error": "Sistema no inicializado"}
        
        return self.router.get_service_health()
    
    async def _log_service_status(self):
        """Registrar estado de servicios en logs"""
        health = self.get_salud_servicios()
        
        logging.info("📊 Estado de Servicios:")
        for service_name, status in health.items():
            status_emoji = {
                'healthy': '✅',
                'limited': '⚠️',
                'error': '❌'
            }.get(status.get('status'), '❓')
            
            logging.info(f"  {status_emoji} {service_name}: {status.get('status', 'unknown')}")
            
            if 'info' in status:
                capabilities = status['info'].get('capabilities', [])
                if capabilities:
                    logging.info(f"    Capacidades: {', '.join(capabilities[:3])}...")
    
    def __del__(self):
        """Cleanup al destruir el objeto"""
        if hasattr(self, 'database_service') and self.database_service:
            try:
                self.database_service.close()
            except:
                pass

# Singleton global para compatibilidad con código existente
_sistema_global = None

def get_sistema_global():
    """Obtener instancia global del sistema"""
    global _sistema_global
    if _sistema_global is None:
        _sistema_global = SistemaConsultaModular()
    return _sistema_global

# Funciones de compatibilidad para interfaz existente
async def procesar_consulta_modular(texto: str, filtros: Dict = None) -> Dict[str, Any]:
    """Función de compatibilidad para procesar consultas"""
    sistema = get_sistema_global()
    response = await sistema.consulta(texto, filtros)
    
    # Convertir a formato esperado por interfaz existente
    return {
        "respuesta": response.answer,
        "metodo": response.method_used.value,
        "confianza": response.confidence,
        "tiempo_ejecucion": response.execution_time_ms,
        "fuentes": [
            {
                "tipo": source.type,
                "id": source.identifier,
                "relevancia": source.relevance_score,
                "metadata": source.metadata
            }
            for source in response.sources
        ],
        "tokens_usados": response.tokens_used,
        "metadata_router": getattr(response, 'router_metadata', {})
    }
