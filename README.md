# 🛠️ Gestor de Servicios de Licencias Autodesk y Rhino Zoo

Aplicación gráfica y de línea de comandos para administrar fácilmente los servicios de licencias **Autodesk (gestionado por NSSM)** y **Rhino Zoo (McNeelZoo8)** en entornos Windows.

Este gestor permite configurar todas las opciones mediante un archivo externo `config.ini`, facilitando ajustes sin necesidad de modificar el código fuente.

---

## ⚙️ Funcionalidades Principales

- **Iniciar, detener o reiniciar** servicios de licencias Autodesk (`lmgrd.exe`) y Rhino Zoo (`McNeelZoo8`).
- **Visualización en tiempo real** del estado de ambos servicios mediante comandos internos de Windows (`sc`, `tasklist`).
- **Detección y eliminación automática de procesos residuales** (ej: `lmgrd.exe`, `adskflex.exe`) al detener el servicio Autodesk.
- **Visualización del log en tiempo real** para el servidor de licencias Autodesk (mediante PowerShell).
- **Acceso directo** al administrador gráfico del Zoo (`ZooAdmin.Wpf.exe`).
- Completo **soporte para uso por línea de comandos (CLI)**.
- Configuración sencilla y centralizada en archivo externo `config.ini`.

---

## 🔧 Configuración Externa (`config.ini`)

La aplicación carga automáticamente la configuración desde un archivo `config.ini`. Si el archivo no existe, será creado automáticamente con valores predeterminados al primer inicio.

### 📌 Ejemplo de estructura del archivo `config.ini`:

```ini
[Autodesk]
service_name = AutodeskLicenseServer
process_names = lmgrd.exe, adskflex.exe
working_dir = C:\Autodesk
lmgrd_path = C:\Autodesk\lmgrd.exe
license_file = C:\Autodesk\SERVER1-AULES00155d06fb06-2024.lic
log_file = C:\Autodesk\logs\AutodeskLicenseLog.log
launch_args = -z -c %(license_file)s -l %(log_file)s

[Zoo]
service_name = McNeelZoo8
admin_exe = C:\Program Files (x86)\Zoo 8\ZooAdmin.Wpf.exe

[UI]
refresh_ms = 5000
window_size = 400x350
show_te_jodes = 1

[CLI]
allow_non_admin_cli = 1
```

**Modifica estos valores según tu entorno y necesidades.**

---

## 🖥️ Ejecución por Línea de Comandos

La aplicación también permite administrar los servicios mediante comandos en terminal (CLI):

```bash
LicenseServerGUI.exe --start-zoo
LicenseServerGUI.exe --restart-autodesk
LicenseServerGUI.exe --status
LicenseServerGUI.exe --config D:\ruta\personalizada\config.ini --stop-autodesk
```

---

## 📌 Requisitos

- Windows con permisos de administrador (para interactuar con los servicios).
- PowerShell habilitado (para visualización de logs en tiempo real).
- Rhino Zoo 8 (opcional, para administración gráfica).

---

## 🛡️ Comprobación del Estado

- 🟢 **Activo**: Servicio ejecutándose correctamente.
- 🔴 **Detenido**: Servicio no activo.
- 🟠 **Proceso activo sin servicio**: Proceso ejecutándose pero el servicio detenido (requiere atención).
- ⚪ **Desconocido**: Estado del servicio no identificado.

---

## 📁 Ruta del Administrador del Zoo

Asegúrate de indicar correctamente la ruta del ejecutable del administrador gráfico del Zoo en `config.ini`:

```ini
[Zoo]
admin_exe = C:\Program Files (x86)\Zoo 8\ZooAdmin.Wpf.exe
```

---

## 🚧 Problemas Comunes

- Si recibes un aviso de que falta el archivo `config.ini`, simplemente ejecuta la aplicación una vez para generarlo automáticamente.
- En caso de error de permisos, ejecuta la aplicación como administrador.
