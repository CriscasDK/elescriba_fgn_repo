#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO RÁPIDO - Estado Sistema Dash UI
Ejecutar para entender problemas actuales antes de cualquier corrección
"""

import os
import subprocess

def diagnosticar_estado():
    print("🔍 DIAGNÓSTICO DEL SISTEMA DASH UI")
    print("=" * 50)
    
    # 1. Verificar archivos clave
    print("\n📁 ARCHIVOS CLAVE:")
    archivos = [
        "core/consultas.py",
        "core/consultas_backup.py", 
        "app_dash.py",
        "interfaz_principal.py"
    ]
    
    for archivo in archivos:
        if os.path.exists(archivo):
            size = os.path.getsize(archivo)
            print(f"  ✅ {archivo} ({size} bytes)")
        else:
            print(f"  ❌ {archivo} - NO EXISTE")
    
    # 2. Verificar funciones duplicadas en consultas.py
    print("\n🔍 FUNCIONES EN core/consultas.py:")
    try:
        with open("core/consultas.py", "r") as f:
            content = f.read()
            
        functions = []
        for i, line in enumerate(content.split('\n'), 1):
            if line.strip().startswith('def '):
                func_name = line.strip().split('(')[0].replace('def ', '')
                functions.append(f"  Línea {i}: {func_name}")
        
        for func in functions:
            print(func)
            
    except Exception as e:
        print(f"  ❌ Error leyendo consultas.py: {e}")
    
    # 3. Buscar consultas problemáticas
    print("\n🚨 CONSULTAS PROBLEMÁTICAS:")
    problemas = ["d.fecha", "d.tipo_documental", "WHERE departamento"]
    
    try:
        with open("core/consultas.py", "r") as f:
            content = f.read()
            
        for problema in problemas:
            if problema in content:
                print(f"  ❌ ENCONTRADO: {problema}")
            else:
                print(f"  ✅ NO ENCONTRADO: {problema}")
                
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # 4. Verificar estructura correcta en Streamlit
    print("\n✅ ESTRUCTURA CORRECTA (interfaz_principal.py):")
    try:
        with open("interfaz_principal.py", "r") as f:
            lines = f.readlines()
            
        # Buscar consulta correcta alrededor de línea 1133
        for i in range(1130, 1150):
            if i < len(lines) and "SELECT DISTINCT" in lines[i]:
                print(f"  Línea {i+1}: {lines[i].strip()}")
                for j in range(1, 6):
                    if i+j < len(lines) and lines[i+j].strip():
                        print(f"  Línea {i+j+1}: {lines[i+j].strip()}")
                break
                
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # 5. Estado de procesos
    print("\n🔄 PROCESOS ACTIVOS:")
    try:
        result = subprocess.run(['pgrep', '-f', 'app_dash.py'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print(f"  ✅ Dash corriendo (PID: {result.stdout.strip()})")
        else:
            print("  ❌ Dash NO está corriendo")
    except:
        print("  ❓ No se pudo verificar procesos")
    
    print("\n" + "=" * 50)
    print("📋 PRÓXIMA ACCIÓN RECOMENDADA:")
    print("1. Revisar ESTADO_SESION_DASH_22SEP2025.md")
    print("2. Restaurar desde backup limpio")
    print("3. Replicar estructura de interfaz_principal.py")
    print("4. Probar función por función")

if __name__ == "__main__":
    diagnosticar_estado()