# 🔧 GUÍA DE TROUBLESHOOTING - GRAFOS INLINE

## 📅 Actualizado: 03 Octubre 2025

---

## ❓ "Los botones 🌐 no funcionan"

### **Verificación rápida**:

1. **Revisar logs** en `dash_app_all.log`:
   ```bash
   tail -f dash_app_all.log | grep "UPDATE STORE"
   ```

2. **¿Ves esto?**
   ```
   🔍🔍🔍 UPDATE STORE CALLED!
   ✅ UPDATE STORE - Retornando nombre desde ID: <nombre>
   ```

   **SÍ** → Los botones **SÍ** funcionan. El problema está en AGE.

   **NO** → Hay problema con callbacks. Ver sección "Callbacks no ejecutan".

---

## ❌ "Error: out of shared memory"

### **Síntomas**:
```
❌ Error ejecutando Cypher: out of shared memory
HINT:  You might need to increase max_locks_per_transaction.
```

### **Causa**:
PostgreSQL AGE necesita más locks para consultas de grafos complejos.

### **Solución**:

```bash
# 1. Conectar como superusuario
sudo -u postgres psql

# 2. Aumentar límite
ALTER SYSTEM SET max_locks_per_transaction = 256;

# 3. Recargar configuración
SELECT pg_reload_conf();

# 4. O reiniciar PostgreSQL (más seguro)
\q
sudo systemctl restart postgresql
```

### **Verificar**:
```sql
SHOW max_locks_per_transaction;
```

Debería mostrar `256` (default es `64`).

---

## 🔍 "Modal/Container se abre solo al refrescar"

### **Verificación**:

1. **Revisar Store**:
   - `storage_type='memory'` → ✅ OK
   - `storage_type='local'` o `'session'` → ❌ Problema

2. **Revisar callbacks**:
   - `prevent_initial_call=True` → ✅ OK
   - Sin ese parámetro → ❌ Callbacks ejecutan al inicio

3. **Verificar lógica**:
   ```python
   if not triggered or triggered == '.' or triggered == '':
       raise PreventUpdate  # ← CORRECTO
   ```

   NO:
   ```python
   if not triggered or triggered == '.' or '':  # ← INCORRECTO
       return {}, ""  # ← INCORRECTO
   ```

---

## 🌐 "Botón muestra persona incorrecta"

### **Causa**:
IDs basados en índice (`index: i`) se desincroniza con datos.

### **Solución**:
Usar nombre directamente en ID:

```python
# ❌ INCORRECTO
html.Button("🌐", id={"type": "victima-red-btn", "index": i})

# ✅ CORRECTO
html.Button("🌐", id={"type": "victima-red-btn", "nombre": v['nombre']})
```

Y en callback:
```python
import json
triggered = callback_context.triggered[0]['prop_id']
prop_dict = json.loads(triggered.split('.')[0])
nombre = prop_dict.get('nombre')  # Extraer desde ID
```

---

## 🔄 "Callbacks no ejecutan"

### **Diagnóstico**:

1. **Revisar errores Dash**:
   ```
   Input / State wildcards not in Outputs
   ```

   **Problema**: Usar `MATCH` con Output sin pattern-matching.

   **Solución**: Usar `ALL`:
   ```python
   # ❌ INCORRECTO
   Input({"type": "btn", "nombre": MATCH}, "n_clicks")
   # Con Output simple sin pattern-matching

   # ✅ CORRECTO
   Input({"type": "btn", "nombre": ALL}, "n_clicks")
   ```

2. **Verificar dependencias**:
   ```python
   @app.callback(
       Output(...),
       Input(...),
       prevent_initial_call=True  # ← IMPORTANTE
   )
   ```

3. **Logs de debug**:
   ```python
   print(f"🔍 Triggered: {callback_context.triggered}")
   print(f"🔍 Inputs: {callback_context.inputs}")
   ```

---

## 📊 "Grafo no se visualiza"

### **Checklist**:

- [ ] ¿Container está visible? (`style={'display': 'none'}` vs `{}`)
- [ ] ¿AGE devuelve datos? (revisar logs para error de memoria)
- [ ] ¿Plotly recibe datos? (revisar `fig` en callback)
- [ ] ¿Hay nodos/aristas en los datos?

### **Verificar datos**:
```python
print(f"📊 Nodes: {len(nodes)}, Edges: {len(edges)}")
```

Si ambos son 0 → Problema con consulta AGE o datos vacíos.

---

## 🐛 DEBUGGING PASO A PASO

### **1. Verificar aplicación corriendo**:
```bash
ps aux | grep "python.*app_dash"
```

### **2. Ver logs en tiempo real**:
```bash
tail -f dash_app_all.log
```

### **3. Click en botón 🌐 y observar**:

**Esperado**:
```
🔍🔍🔍 UPDATE STORE CALLED!
✅ UPDATE STORE - Retornando nombre desde ID: <nombre>
✅ GRAPH INLINE TOGGLE - Abriendo grafo para <nombre>
✅ GRAPH CALLBACK - Store changed with valid name: <nombre>
```

**Si aparece**:
```
❌ Error ejecutando Cypher: out of shared memory
```
→ Ver sección "Error: out of shared memory"

**Si NO aparece nada**:
→ Ver sección "Callbacks no ejecutan"

---

## 📋 CHECKLIST RÁPIDO

- [ ] PostgreSQL corriendo
- [ ] AGE extension cargada (`LOAD 'age';`)
- [ ] `max_locks_per_transaction >= 256`
- [ ] Dash app corriendo (`http://0.0.0.0:8050/`)
- [ ] Stores con `storage_type='memory'`
- [ ] Callbacks con `prevent_initial_call=True`
- [ ] IDs de botones incluyen `nombre`
- [ ] Callback usa `ALL` no `MATCH`
- [ ] Lógica usa `raise PreventUpdate`, no `return {}, ""`

---

## 🆘 SI TODO LO DEMÁS FALLA

1. **Reiniciar aplicación Dash**:
   ```bash
   pkill -f "python.*app_dash"
   python app_dash.py &
   ```

2. **Reiniciar PostgreSQL**:
   ```bash
   sudo systemctl restart postgresql
   ```

3. **Limpiar caché del navegador**:
   - Ctrl + Shift + Delete
   - Borrar cookies y caché

4. **Revisar documentación completa**:
   - `SESION_GRAFOS_INLINE_03OCT2025.md`
   - Buscar error específico en ese documento

---

## 📞 CONTACTO

Para problemas no cubiertos aquí, revisar:
- `SESION_GRAFOS_INLINE_03OCT2025.md` (documentación completa)
- `README_ARQUITECTURA.md` (arquitectura del sistema)
- Logs: `dash_app_all.log`
- Código: `app_dash.py` (callbacks líneas 933-1086)
