#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.consultas import get_db_connection

def investigar_origen_nucs_invalidos():
    """Investigar el origen de los NUCs inválidos y verificar hipótesis de 4 dígitos"""

    print("=== INVESTIGACIÓN ORIGEN NUCs INVÁLIDOS ===")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Analizar los NUCs de 4 dígitos específicamente
        print("\n1. ANÁLISIS DE NUCs DE 4 DÍGITOS:")
        nucs_4_digitos = ['6310', '6399', '9356', '6176', '6337', '6386']

        for nuc_4 in nucs_4_digitos:
            print(f"\n--- NUC: {nuc_4} ---")

            # Buscar si existe un NUC completo que termine en estos 4 dígitos
            cur.execute("""
                SELECT DISTINCT COALESCE(m.nuc, d.nuc) as nuc_completo,
                       COUNT(*) as docs
                FROM documentos d
                LEFT JOIN metadatos m ON d.id = m.documento_id
                WHERE COALESCE(m.nuc, d.nuc) IS NOT NULL
                  AND LENGTH(COALESCE(m.nuc, d.nuc)) BETWEEN 21 AND 23
                  AND COALESCE(m.nuc, d.nuc) LIKE %s
                GROUP BY COALESCE(m.nuc, d.nuc)
                ORDER BY docs DESC
            """, (f'%{nuc_4}',))
            nucs_completos = cur.fetchall()

            if nucs_completos:
                print(f"   ✅ ENCONTRADO! NUCs completos que terminan en {nuc_4}:")
                for nuc_completo, docs in nucs_completos:
                    print(f"      {nuc_completo} ({docs} docs)")
            else:
                print(f"   ❌ No se encontraron NUCs completos que terminen en {nuc_4}")

            # Verificar en qué documentos aparece el NUC de 4 dígitos
            cur.execute("""
                SELECT d.archivo, d.despacho as despacho_doc, m.despacho as despacho_meta,
                       COALESCE(m.nuc, d.nuc) as nuc_valor,
                       d.id
                FROM documentos d
                LEFT JOIN metadatos m ON d.id = m.documento_id
                WHERE COALESCE(m.nuc, d.nuc) = %s
                LIMIT 3
            """, (nuc_4,))
            documentos = cur.fetchall()

            print(f"   📄 Documentos con NUC {nuc_4}:")
            for nombre, desp_doc, desp_meta, nuc_val, doc_id in documentos:
                print(f"      Doc ID {doc_id}: {nombre[:50]}...")
                print(f"         NUC: {nuc_val}")
                print(f"         Despacho doc: {desp_doc}")
                print(f"         Despacho meta: {desp_meta}")

        # 2. Investigar origen de NUCs muy largos
        print("\n\n2. ANÁLISIS DE NUCs MUY LARGOS:")
        cur.execute("""
            SELECT DISTINCT COALESCE(m.nuc, d.nuc) as nuc_largo,
                   LENGTH(COALESCE(m.nuc, d.nuc)) as longitud,
                   COUNT(*) as docs
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE COALESCE(m.nuc, d.nuc) IS NOT NULL
              AND LENGTH(COALESCE(m.nuc, d.nuc)) > 23
            GROUP BY COALESCE(m.nuc, d.nuc)
            ORDER BY docs DESC
            LIMIT 10
        """)
        nucs_largos = cur.fetchall()

        for nuc_largo, longitud, docs in nucs_largos:
            print(f"\n--- NUC LARGO: {nuc_largo} (L:{longitud}, {docs} docs) ---")

            # Verificar si contiene un NUC válido dentro
            if len(nuc_largo) >= 21:
                # Buscar si los primeros 21-23 caracteres forman un NUC válido
                for i in range(21, min(24, len(nuc_largo)+1)):
                    posible_nuc = nuc_largo[:i]
                    if posible_nuc.isdigit():
                        cur.execute("""
                            SELECT COUNT(*) as count_valido
                            FROM documentos d
                            LEFT JOIN metadatos m ON d.id = m.documento_id
                            WHERE COALESCE(m.nuc, d.nuc) = %s
                        """, (posible_nuc,))
                        count = cur.fetchone()[0]
                        if count > 0:
                            print(f"   ✅ Contiene NUC válido: {posible_nuc} ({count} docs)")
                            break

            # Ver documentos específicos
            cur.execute("""
                SELECT d.archivo, d.id
                FROM documentos d
                LEFT JOIN metadatos m ON d.id = m.documento_id
                WHERE COALESCE(m.nuc, d.nuc) = %s
                LIMIT 2
            """, (nuc_largo,))
            documentos = cur.fetchall()

            print(f"   📄 Documentos:")
            for nombre, doc_id in documentos:
                print(f"      Doc ID {doc_id}: {nombre[:60]}...")

        # 3. Verificar origen en tabla metadatos vs documentos
        print("\n\n3. ORIGEN DE NUCs INVÁLIDOS (metadatos vs documentos):")

        # NUCs inválidos en metadatos
        cur.execute("""
            SELECT m.nuc, LENGTH(m.nuc) as longitud, COUNT(*) as docs,
                   'metadatos' as origen
            FROM metadatos m
            WHERE m.nuc IS NOT NULL
              AND NOT (LENGTH(m.nuc) BETWEEN 21 AND 23 AND m.nuc ~ '^[0-9]+$')
            GROUP BY m.nuc
            ORDER BY docs DESC
            LIMIT 5
        """)
        invalidos_meta = cur.fetchall()

        # NUCs inválidos en documentos
        cur.execute("""
            SELECT d.nuc, LENGTH(d.nuc) as longitud, COUNT(*) as docs,
                   'documentos' as origen
            FROM documentos d
            WHERE d.nuc IS NOT NULL
              AND NOT (LENGTH(d.nuc) BETWEEN 21 AND 23 AND d.nuc ~ '^[0-9]+$')
            GROUP BY d.nuc
            ORDER BY docs DESC
            LIMIT 5
        """)
        invalidos_doc = cur.fetchall()

        print("   🔍 Top NUCs inválidos por origen:")
        print("   METADATOS:")
        for nuc, longitud, docs, origen in invalidos_meta:
            print(f"      {nuc[:30]}... (L:{longitud}) - {docs} docs")

        print("   DOCUMENTOS:")
        for nuc, longitud, docs, origen in invalidos_doc:
            print(f"      {nuc[:30]}... (L:{longitud}) - {docs} docs")

        # 4. Verificar patrones en archivos específicos
        print("\n\n4. PATRÓN EN NOMBRES DE ARCHIVOS:")
        cur.execute("""
            SELECT d.archivo,
                   COALESCE(m.nuc, d.nuc) as nuc_valor,
                   LENGTH(COALESCE(m.nuc, d.nuc)) as longitud
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE COALESCE(m.nuc, d.nuc) IN ('6310', '6399', '9356', '6176', '6337', '6386')
            LIMIT 10
        """)
        archivos_4_digitos = cur.fetchall()

        print("   📁 Archivos con NUCs de 4 dígitos:")
        for archivo, nuc, longitud in archivos_4_digitos:
            print(f"      {archivo[:60]}... | NUC: {nuc}")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigar_origen_nucs_invalidos()