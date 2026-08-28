# ALSI BALANCE

Sistema interno de tesorería para **Agropesquera La Sinuana S.A.S.**

Aplicación web modular en **Django + Python** para llevar el control,
conciliación y análisis de los movimientos financieros de la cuenta
bancaria de la empresa. Diseñada con arquitectura limpia, preparada para
crecer por fases.

> **Estado actual:** MVP Fase 1 — Base funcional, ejecutable localmente.

---

## 1. Funcionalidades implementadas

### MVP Base (Fase 1)
- [x] Proyecto Django con apps separadas por responsabilidad.
- [x] Autenticación de usuarios (login, logout, registro) con roles.
- [x] CRUD completo de **movimientos** (ingresos y egresos).
- [x] CRUD de **categorías** con control de acceso por rol.
- [x] Cálculo de **saldo** (saldo inicial + ingresos − egresos).
- [x] **Dashboard** con tarjetas de resumen y 7 gráficas (Chart.js).
- [x] Filtros de movimientos por tipo, estado, categoría, fechas y búsqueda libre.
- [x] **Detección de duplicados** por heurística (valor, fecha, referencia).
- [x] **Auditoría** automática de todas las acciones sobre movimientos.
- [x] **Panel de administración** de Django con modelos personalizados.
- [x] **PWA** con `manifest.json` y service worker.
- [x] Diseño responsive con **TailwindCSS** y paleta azul ALSI.

### Fase 2 — Reportes y Excel
- [x] **Reporte financiero** en pantalla: saldo inicial, ingresos, egresos, balance y saldo final del periodo.
- [x] Desglose por categoría (ingresos y egresos).
- [x] Detalle de movimientos del periodo.
- [x] **Exportación a Excel (.xlsx)** con `openpyxl`:
  - `Exportar movimientos` (todos los filtrados)
  - `Exportar ingresos`
  - `Exportar egresos`
  - `Exportar reporte financiero` (4 hojas: resumen + cat. ingresos + cat. egresos + detalle)
- [x] Filtros por rango: este mes, mes anterior, este año, personalizado.

### Fase 3 — Gmail + Bancolombia
- [x] **Flujo OAuth 2.0** con Google (botón "Conectar Gmail").
- [x] Token almacenado cifrado en base de datos (no se guarda contraseña).
- [x] Lectura de correos de Bancolombia via Gmail API.
- [x] **`BancolombiaEmailParser`** modular con regex y soporte para formatos colombianos.
- [x] Modelo `EmailProcesado` con `message_id` único → **evita duplicados**.
- [x] **Deduplicación** de movimientos por `email_message_id`.
- [x] Botón **"Sincronizar Gmail"** en el dashboard.
- [x] Manejo de correos no reconocidos → estado `IGNORADO`.

### Fase 4 — PWA y pulido
- [x] Diseño responsive (mobile first).
- [x] Sidebar con menú hamburguesa en móvil.
- [x] PWA: `manifest.webmanifest`, service worker con cache de estáticos.
- [x] Indicador de conexión Gmail en sidebar.
- [x] Validaciones de formularios (valor > 0, fechas válidas, etc.).

## 2. Cosas que NO se implementaron (por diseño)

- ❌ OCR de comprobantes (el modelo `Comprobante` queda listo para una fase futura).
- ❌ Celery / Redis (la sincronización Gmail se ejecuta manualmente o por comando).
- ❌ Múltiples cuentas bancarias (placeholder en `conciliacion`).
- ❌ Sistema contable, conciliación bancaria avanzada, facturación, nómina, etc.

---

## 3. Requisitos

- Python **3.10+** (probado con 3.11).
- `pip` actualizado.
- (Opcional para producción) PostgreSQL 13+.

No se requieren servicios externos para correr el MVP.

---

## 4. Instalación local

```bash
# 1. Clonar o descomprimir el proyecto
cd "C:\alsi balance"

# 2. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear archivo .env a partir del ejemplo
copy .env.example .env           # Windows
# cp .env.example .env           # Linux / macOS

# 5. Aplicar migraciones
python manage.py migrate

# 6. Crear datos iniciales (admin + categorías + configuración)
python manage.py seed_initial

# 7. Iniciar el servidor
python manage.py runserver
```

Abrir en el navegador: <http://127.0.0.1:8000/>

> Usuario por defecto: **`admin`** / **`alsi2026`**

---

## 5. Variables de entorno

Definidas en `.env` (basado en `.env.example`):

| Variable | Descripción | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta de Django | `dev-insecure-key-change-me` |
| `DJANGO_DEBUG` | Modo depuración | `True` |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos (CSV) | `127.0.0.1,localhost,testserver` |
| `DATABASE_URL` | URL de base de datos | `sqlite:///db.sqlite3` |
| `APP_NAME` | Nombre mostrado en UI | `ALSI BALANCE` |
| `APP_COMPANY` | Empresa | `Agropesquera La Sinuana S.A.S.` |

Para usar PostgreSQL en producción:

```env
DATABASE_URL=postgres://alsi:secret@db-host:5432/alsi_balance
```

---

## 6. Estructura del proyecto

```
alsi balance/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── config/                  # Configuración Django (settings, urls, wsgi, asgi)
│
├── core/                    # Núcleo: constantes, config, saldo, utilitarios
│   ├── management/commands/
│   │   └── seed_initial.py  # Carga categorías y admin inicial
│   └── templatetags/
│       └── core_extras.py   # Filtros de plantilla (abs_valor, cop, etc.)
│
├── usuarios/                # Modelo Usuario + autenticación
│   ├── models.py            # Usuario(AbstractUser) con rol
│   ├── permissions.py       # Decorador administrador_required
│   └── views.py             # Login, logout, registro, perfil
│
├── categorias/              # Categorías configurables (ingreso/egreso)
│
├── movimientos/             # Modelo principal del sistema
│   ├── models.py            # Movimiento, Comprobante
│   ├── services.py          # crear / actualizar / eliminar (con auditoría)
│   ├── selectors.py         # Lectura + filtros + agregaciones
│   ├── deduplicacion.py     # Heurística de duplicados
│   └── views.py             # CRUD + conciliacion
│
├── dashboard/               # Dashboard principal con tarjetas y gráficas
│
├── auditoria/               # RegistroAuditoria + registrar_auditoria()
│
├── conciliacion/            # Placeholder para Fase 2 (CuentaBancaria, Conciliacion)
│
├── media/                   # Archivos subidos (comprobantes)
├── static/                  # CSS, JS, manifest, íconos
└── templates/               # Templates globales (base.html, partials, ...)
```

---

## 7. Modelo de datos principal

```text
Usuario (AbstractUser)
├── username, email, password
├── rol: ADMINISTRADOR | USUARIO
├── documento, telefono, cargo
└── es_administrador (property)

Categoria
├── nombre, tipo (INGRESO|EGRESO), color, activo
└── descripcion

Movimiento
├── tipo (INGRESO|EGRESO)
├── fecha, hora, valor, concepto, descripcion
├── categoria (FK), subcategoria, banco, cuenta
├── referencia, tercero, saldo_despues
├── origen (EMAIL|MANUAL|OCR|IMPORTACION_EXCEL|OTRO)
├── estado_conciliacion (PENDIENTE|CONCILIADO|OBSERVADO)
├── comprobante (FK → Comprobante)
├── email_message_id, creado_por
└── creado_en, actualizado_en

Comprobante
├── imagen, archivo, mime_type, tamano_bytes
├── texto_ocr (placeholder Fase 4)
└── subido_por

RegistroAuditoria
├── usuario, accion, movimiento (FK)
├── datos_anteriores (JSON), datos_nuevos (JSON)
└── ip, user_agent, fecha
```

---

## 8. Patrones aplicados

- **Separación por capas**: `models.py` → `services.py` (escritura) →
  `selectors.py` (lectura) → `views.py` (orquestación HTTP).
- **Auditoría transversal**: todas las mutaciones pasan por `services.py`
  y registran en `RegistroAuditoria`.
- **Configuración por entorno**: `python-dotenv` + `DATABASE_URL`.
- **Single source of truth**: constantes de tipos en `core.models` y
  reutilizadas por todas las apps.
- **Deduplicación determinista** basada en reglas explícitas, no en ML.

---

## 9. Comandos útiles

```bash
# Servidor de desarrollo
python manage.py runserver 127.0.0.1:8765

# Crear otro administrador
python manage.py createsuperuser

# Datos iniciales (idempotente)
python manage.py seed_initial

# Estado del sistema (DB, conteos, Gmail conectado)
python manage.py status

# Ejecutar tests
python manage.py test

# Generar migraciones tras cambiar modelos
python manage.py makemigrations
python manage.py migrate

# Consola de Python con el entorno Django
python manage.py shell

# Recolectar estáticos (producción)
python manage.py collectstatic

# === Gmail ===
# Sincronizar correos manualmente (usa days_back)
python manage.py sincronizar_gmail --dias 30

# Sincronizar SOLO correos nuevos desde la ultima sincronizacion
python manage.py sincronizar_recientes

# Borrar correos ignorados para re-procesarlos
python manage.py reintentar_gmail --si

# Reset completo + sincronizacion (util al ajustar el parser)
python manage.py reset_y_sincronizar --si --dias 60

# Ver contenido de correos ignorados
python manage.py ver_correo --limite 5

# Probar el parser con texto pegado manualmente
python manage.py probar_parser --cuerpo "Bancolombia: Transferiste $50000..." --no-guardar

# Generar claves VAPID para notificaciones push
python manage.py generar_vapid

# === Diagnostico ===
# Ver estado completo del sistema (DB, conteos, Gmail, pendientes)
python manage.py status

# === Datos de ejemplo ===
# Crear 100 movimientos aleatorios de los ultimos 90 dias
python manage.py crear_datos_ejemplo --cantidad 100

# Borrar movimientos, emails, comprobantes (CONSERVAR usuarios y config)
python manage.py reset_total --si

# === Iconos PWA ===
# Regenerar favicon, icon-192.png, icon-512.png
python scripts/generar_iconos.py
```

---

## 10. Roles y permisos

| Acción | Administrador | Usuario |
|---|:-:|:-:|
| Ver dashboard / movimientos / categorías | ✅ | ✅ |
| Crear movimientos | ✅ | ✅ |
| Editar / eliminar movimientos | ✅ | ❌ |
| Cambiar estado de conciliación | ✅ | ✅ |
| Crear / editar / eliminar categorías | ✅ | ❌ |
| Acceder al panel `/admin` | ✅ | ❌ |

---

## 11. Tests

```bash
python manage.py test
```

Cobertura actual (57 tests):


- `core`: cálculo de balance y saldo, configuración del sistema.
- `usuarios`: roles, login, registro.
- `categorias`: unicidad, listado autenticado.
- `movimientos`: CRUD, validación de valor, **deduplicación**, paginación y filtros por rango.
- `dashboard`: render con y sin autenticación, selector de rango.
- **`reportes`**: cálculo de reporte (saldo inicial, ingresos, egresos, balance, saldo final), exportación Excel con sus 4 hojas, separación ingresos/egresos.
- **`gmail_integration`**:
  - Parser de correos Bancolombia (10+ casos con formatos colombiano y US)
  - Detección de remitente y deduplicación por `message_id`
  - Registro de emails procesados y manejo de ignorados
  - Endpoint debug `/gmail/debug/` (solo admin)
  - Tests del flujo completo de sincronización

---

## 12. Configuración de Gmail

Para activar la integración con Gmail se requieren credenciales OAuth de Google:

1. Crear un proyecto en https://console.cloud.google.com/
2. Habilitar la **Gmail API**.
3. Crear credenciales OAuth 2.0 tipo "Web application".
4. Configurar el redirect URI: `http://tu-dominio/gmail/callback/`
5. Agregar al archivo `.env`:

```env
GOOGLE_OAUTH_CLIENT_ID=xxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
GOOGLE_OAUTH_REDIRECT_URI=http://127.0.0.1:8765/gmail/callback/
```

6. Reiniciar el servidor.
7. Hacer clic en **"Conectar Gmail"** desde el dashboard o el sidebar.

Sin estas credenciales, los demás módulos funcionan normalmente.
El parser y la deduplicación pueden probarse con `procesar_correo_simulado()`.

---

## 13. Licencia y confidencialidad

Software de uso interno para **Agropesquera La Sinuana S.A.S.**
Toda la información financiera cargada al sistema es confidencial y no
debe salir del entorno autorizado.
