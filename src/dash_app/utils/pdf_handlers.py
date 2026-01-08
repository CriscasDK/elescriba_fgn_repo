"""Utilidades para manejo y descarga de archivos PDF."""

import os
import glob
from typing import Optional, Dict, Any
from flask import send_file, abort


def convertir_ruta_bd_a_real(ruta_bd: str) -> Optional[str]:
    """
    Convierte ruta de BD (/mnt/UP/...) a ruta real del sistema (/home/lab4/caso_UP/UP/...).

    Args:
        ruta_bd: Ruta almacenada en la base de datos

    Returns:
        Ruta real del archivo si existe, None en caso contrario
    """
    if not ruta_bd or ruta_bd == 'N/A':
        return None

    # Reemplazar /mnt/UP/ por /home/lab4/caso_UP/UP/
    ruta_real = ruta_bd.replace('/mnt/UP/', '/home/lab4/caso_UP/UP/')

    # Verificar que el archivo existe
    if os.path.exists(ruta_real):
        return ruta_real

    return None


def obtener_ruta_pdf_real(doc: Dict[str, Any]) -> Optional[str]:
    """
    Obtiene la ruta real del PDF desde los metadatos del documento.

    Args:
        doc: Diccionario con metadatos del documento

    Returns:
        Ruta real del PDF si existe, None en caso contrario
    """
    # Intentar diferentes campos de ruta
    rutas_candidatas = [
        doc.get('ruta'),
        doc.get('ruta_documento'),
        doc.get('ruta_completa')
    ]

    for ruta in rutas_candidatas:
        if ruta and ruta != 'N/A':
            ruta_real = convertir_ruta_bd_a_real(ruta)
            if ruta_real:
                return ruta_real

    return None


def create_download_endpoint(app):
    """
    Crea el endpoint Flask para descarga de PDFs.

    Args:
        app: Instancia de la aplicación Dash
    """
    @app.server.route('/download_pdf/<path:archivo>')
    def download_pdf(archivo):
        """Endpoint para descargar archivos PDF"""
        try:
            # Buscar el archivo específico
            patron_busqueda = f"/home/lab4/caso_UP/**/{archivo}"
            archivos_encontrados = glob.glob(patron_busqueda, recursive=True)

            if archivos_encontrados:
                ruta_archivo = archivos_encontrados[0]  # Tomar el primero encontrado
                if os.path.exists(ruta_archivo):
                    return send_file(ruta_archivo, as_attachment=True, download_name=archivo)

            # Si no se encuentra, error 404
            abort(404)

        except Exception as e:
            print(f"Error al descargar PDF {archivo}: {str(e)}")
            abort(500)
