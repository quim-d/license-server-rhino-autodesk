# license-server-rhino-autodesk
Pequeño script para administrar los servidores de licencias de Rhino y Audesk

# 🛠️ Gestor del Servicio de Licencias

Esta aplicación permite controlar los servicios de licencias de **Autodesk** y **Rhino (Zoo)**.

---

## ⚙️ Funcionalidad Principal

- Iniciar, detener o reiniciar el servicio de licencias de Autodesk (`lmgrd.exe`)  
- Control directo del servicio de Rhino Zoo (`McNeelZoo8`)  
- El estado del servicio se comprueba mediante `sc` y `tasklist`  
- Botón para abrir el administrador gráfico del Zoo (`ZooAdmin.Wpf.exe`)  
- Soporte completo para uso por línea de comandos

---

## 🧩 Servicios Gestionados

- `AutodeskLicenseServer` (vía NSSM con `lmgrd.exe`)  
- `McNeelZoo8` (servicio oficial de Rhino Zoo 8)

---

## 🔍 Comprobación de Estado

- Si el servicio de Autodesk está detenido pero el proceso `lmgrd.exe` está activo → se muestra una advertencia  
- Zoo se gestiona directamente con comandos `sc`

---

## 📁 Ruta del Administrador del Zoo

- `C:\Ruta\Al\ZooAdmin.Wpf.exe` *(modifica esta ruta según tu sistema)*

---

## 💻 Ejecución por Línea de Comandos

Esta aplicación permite ejecutar acciones sin mostrar la interfaz gráfica:

```bash
python gestor_serveis.py --start-zoo
python gestor_serveis.py --restart-autodesk
python gestor_serveis.py --status
