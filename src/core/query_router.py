"""
Router inteligente para dirigir consultas al servicio más apropiado
"""

import logging
import time
from typing import List, Dict, Any, Optional
from enum import Enum

from .models import QueryRequest, QueryResponse, QueryType
from .base_query_service import BaseQueryService, DatabaseQueryService, RAGQueryService

class QueryRouter:
    """Router inteligente que determina qué servicio usar para cada consulta"""
    
    def __init__(self):
        self.services: Dict[str, BaseQueryService] = {}
        self.fallback_enabled = True
        
        # Estadísticas de uso
        self.stats = {
            'total_queries': 0,
            'database_queries': 0,
            'rag_queries': 0,
            'hybrid_queries': 0,
            'fallback_used': 0
        }
    
    def register_service(self, name: str, service: BaseQueryService):
        """Registrar un servicio de consulta"""
        self.services[name] = service
        logging.info(f"✅ Servicio '{name}' registrado en el router")
    
    async def route_query(self, request: QueryRequest) -> QueryResponse:
        """Rutear consulta al servicio más apropiado"""
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        try:
            # 1. Evaluar capacidades de cada servicio
            service_scores = await self._evaluate_services(request)
            
            # 2. Seleccionar estrategia de ejecución
            strategy = self._select_strategy(service_scores, request)
            
            # 3. Ejecutar consulta según estrategia
            response = await self._execute_strategy(strategy, request, service_scores)
            
            # 4. Actualizar estadísticas
            self._update_stats(strategy, response)
            
            # 5. Agregar metadata del router
            response.router_metadata = {
                'strategy_used': strategy,
                'service_scores': service_scores,
                'routing_time_ms': int((time.time() - start_time) * 1000)
            }
            
            return response
            
        except Exception as e:
            logging.error(f"Error en router: {e}")
            return await self._fallback_response(request, str(e))
    
    async def _evaluate_services(self, request: QueryRequest) -> Dict[str, float]:
        """Evaluar qué tan capaz es cada servicio para la consulta"""
        scores = {}
        
        for name, service in self.services.items():
            try:
                score = service.is_capable(request.text)
                scores[name] = score
                logging.debug(f"Servicio '{name}': score {score:.2f}")
            except Exception as e:
                logging.warning(f"Error evaluando servicio '{name}': {e}")
                scores[name] = 0.0
        
        return scores
    
    def _select_strategy(self, scores: Dict[str, float], request: QueryRequest) -> str:
        """Seleccionar estrategia de ejecución"""
        # Obtener mejores scores
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_scores or sorted_scores[0][1] == 0.0:
            return "fallback"
        
        best_service, best_score = sorted_scores[0]
        
        # Si hay un claro ganador (>= 0.7)
        if best_score >= 0.7:
            return f"single_{best_service}"
        
        # Si hay múltiples servicios competentes
        if len(sorted_scores) >= 2 and sorted_scores[1][1] >= 0.4:
            return "hybrid"
        
        # Usar el mejor servicio disponible
        return f"single_{best_service}"
    
    async def _execute_strategy(self, strategy: str, request: QueryRequest, 
                              scores: Dict[str, float]) -> QueryResponse:
        """Ejecutar la estrategia seleccionada"""
        
        if strategy.startswith("single_"):
            service_name = strategy.replace("single_", "")
            return await self._execute_single(service_name, request)
        
        elif strategy == "hybrid":
            return await self._execute_hybrid(request, scores)
        
        elif strategy == "fallback":
            return await self._fallback_response(request, "No hay servicios capaces")
        
        else:
            raise ValueError(f"Estrategia desconocida: {strategy}")
    
    async def _execute_single(self, service_name: str, request: QueryRequest) -> QueryResponse:
        """Ejecutar consulta en un solo servicio"""
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Servicio '{service_name}' no encontrado")
        
        logging.info(f"🎯 Ejecutando consulta con servicio: {service_name}")
        return await service.process_query(request)
    
    async def _execute_hybrid(self, request: QueryRequest, scores: Dict[str, float]) -> QueryResponse:
        """Ejecutar consulta híbrida (múltiples servicios)"""
        logging.info("🔄 Ejecutando consulta híbrida")
        
        # Seleccionar los 2 mejores servicios
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_service = sorted_scores[0][0]
        secondary_service = sorted_scores[1][0] if len(sorted_scores) > 1 else None
        
        try:
            # Ejecutar consulta principal
            primary_response = await self._execute_single(primary_service, request)
            
            # Si la confianza es alta, usar solo la respuesta principal
            if primary_response.confidence >= 0.8:
                primary_response.method_used = QueryType.HYBRID
                return primary_response
            
            # Si no, combinar con servicio secundario
            if secondary_service:
                secondary_response = await self._execute_single(secondary_service, request)
                return self._combine_responses(primary_response, secondary_response)
            
            return primary_response
            
        except Exception as e:
            logging.error(f"Error en consulta híbrida: {e}")
            # Intentar solo con servicio secundario
            if secondary_service:
                return await self._execute_single(secondary_service, request)
            raise
    
    def _combine_responses(self, primary: QueryResponse, secondary: QueryResponse) -> QueryResponse:
        """Combinar respuestas de múltiples servicios"""
        # Determinar respuesta principal basada en confianza
        if secondary.confidence > primary.confidence * 1.2:
            main_response = secondary
            support_response = primary
        else:
            main_response = primary
            support_response = secondary
        
        # Combinar información
        combined_answer = f"{main_response.answer}\n\n---\n\n**Información complementaria:**\n{support_response.answer}"
        
        # Combinar fuentes
        all_sources = main_response.sources + support_response.sources
        unique_sources = []
        seen_ids = set()
        
        for source in all_sources:
            if source.identifier not in seen_ids:
                unique_sources.append(source)
                seen_ids.add(source.identifier)
        
        # Crear respuesta combinada
        return QueryResponse(
            query_id=f"hybrid_{int(time.time())}",
            original_query=main_response.original_query,
            method_used=QueryType.HYBRID,
            answer=combined_answer,
            confidence=max(main_response.confidence, secondary.confidence) * 0.95,  # Ligera penalización por híbrido
            execution_time_ms=main_response.execution_time_ms + support_response.execution_time_ms,
            sources=unique_sources[:10],  # Máximo 10 fuentes
            tokens_used=(main_response.tokens_used or 0) + (support_response.tokens_used or 0)
        )
    
    async def _fallback_response(self, request: QueryRequest, error_msg: str) -> QueryResponse:
        """Respuesta de fallback cuando no hay servicios disponibles"""
        self.stats['fallback_used'] += 1
        
        return QueryResponse(
            query_id=f"fallback_{int(time.time())}",
            original_query=request.text,
            method_used=QueryType.DATABASE,  # Fallback por defecto
            answer=f"Lo siento, no pude procesar tu consulta adecuadamente. {error_msg}",
            confidence=0.1,
            execution_time_ms=10,
            sources=[],
            error_info={"type": "fallback", "message": error_msg}
        )
    
    def _update_stats(self, strategy: str, response: QueryResponse):
        """Actualizar estadísticas de uso"""
        if strategy.startswith("single_database") or response.method_used == QueryType.DATABASE:
            self.stats['database_queries'] += 1
        elif strategy.startswith("single_rag") or response.method_used == QueryType.RAG:
            self.stats['rag_queries'] += 1
        elif strategy == "hybrid" or response.method_used == QueryType.HYBRID:
            self.stats['hybrid_queries'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del router"""
        return {
            **self.stats,
            'registered_services': list(self.services.keys()),
            'service_info': {name: service.get_service_info() 
                           for name, service in self.services.items()}
        }
    
    def get_service_health(self) -> Dict[str, Any]:
        """Verificar salud de los servicios"""
        health = {}
        
        for name, service in self.services.items():
            try:
                # Test básico de capacidad
                test_score = service.is_capable("consulta de prueba")
                health[name] = {
                    'status': 'healthy' if test_score > 0 else 'limited',
                    'capability_score': test_score,
                    'info': service.get_service_info()
                }
            except Exception as e:
                health[name] = {
                    'status': 'error',
                    'error': str(e),
                    'capability_score': 0.0
                }
        
        return health
