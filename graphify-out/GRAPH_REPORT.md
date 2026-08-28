# Graph Report - C:\alsi balance  (2026-08-27)

## Corpus Check
- Corpus is ~27,390 words - fits in a single context window. You may not need a graph.

## Summary
- 653 nodes · 1115 edges · 79 communities (51 shown, 28 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 61 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- gmail_integration/services.py / sincronizar_correo
- dashboard/views.py / movimientos/selectors.py
- Movimiento / movimientos/services.py
- parsear() / BancolombiaParserTests
- Usuario / UsuarioCrearForm
- Categoria / categorias/views.py
- core/models.py / movimientos/views.py
- procesar_correo_simulado() / GmailServiceTests
- reportes/views.py / reportes/services.py
- MovimientoForm / MovimientoCreateView
- PushSubscription / notificaciones/views.py
- PermisosTests / MovimientoCRUDTests
- RegistroAuditoria / reset_total.py
- core_extras.py / abs_valor()
- ReportesViewsTests / ReportesServicesTests
- gmail_integration/apps.py / _es_comando_de_servido
- Conciliacion / CuentaBancaria
- context_processors.py / gmail_status()
- debug_gmail.py / Command
- reintentar_gmail.py / Command
- ver_correo.py / Command
- pagination_window() / pagination.py
- DashboardViewTests / .setUp()
- Command / generar_vapid.py
- settings.py / env_bool()
- Command / .add_arguments()
- generar_iconos.py / crear_icono()
- AuditoriaConfig / auditoria/apps.py
- CategoriasConfig / categorias/apps.py
- ConciliacionConfig / conciliacion/apps.py
- CoreConfig / core/apps.py
- DashboardConfig / dashboard/apps.py
- MovimientosConfig / movimientos/apps.py
- NotificacionesConfig / notificaciones/apps.py
- ReportesConfig / reportes/apps.py
- UsuariosConfig / usuarios/apps.py
- auditoria/migrations/0001_initial.py / Migration
- auditoria/migrations/0002_initial.py / Migration
- 0003_initial.py / Migration
- categorias/migrations/0001_initial.py / Migration
- conciliacion/migrations/0001_initial.py / Migratio
- asgi.py / ASGI config for ALSI BALANCE.
- config/urls.py / Configuracion de URLs del proyect
- wsgi.py / WSGI config for ALSI BALANCE.
- core/migrations/0001_initial.py / Migration
- gmail_integration/migrations/0001_initial.py / Mig
- movimientos/migrations/0001_initial.py / Migration
- movimientos/migrations/0002_initial.py / Migration
- 0003_movimiento_cuenta_destino_and_more.py / Migra
- notificaciones/migrations/0001_initial.py / Migrat
- sw.js / ASSETS
- usuarios/migrations/0001_initial.py / Migration

## God Nodes (most connected - your core abstractions)
1. `Movimiento` - 49 edges
2. `Categoria` - 27 edges
3. `parsear()` - 27 edges
4. `TipoMovimiento` - 22 edges
5. `sincronizar_correos()` - 22 edges
6. `Usuario` - 21 edges
7. `BancolombiaParserTests` - 19 edges
8. `ConfiguracionSistema` - 18 edges
9. `EmailProcesado` - 17 edges
10. `ConfiguracionGmail` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Command` --uses--> `RegistroAuditoria`  [INFERRED]
  movimientos/management/commands/reset_total.py → auditoria/models.py
- `gmail_status()` --calls--> `obtener_configuracion()`  [EXTRACTED]
  core/context_processors.py → gmail_integration/services.py
- `generar_reporte()` --calls--> `obtener_saldo_inicial()`  [EXTRACTED]
  reportes/services.py → core/selectors.py
- `_crear_movimiento_desde_parseado()` --references--> `Movimiento`  [EXTRACTED]
  gmail_integration/services.py → movimientos/models.py
- `exportar_egresos_excel()` --calls--> `listar_movimientos()`  [EXTRACTED]
  reportes/views.py → movimientos/selectors.py

## Import Cycles
- None detected.

## Communities (79 total, 28 thin omitted)

### Community 0 - "gmail_integration/services.py / sincronizar_correo"
Cohesion: 0.06
Nodes (46): ConfiguracionGmailAdmin, EmailProcesadoAdmin, register, Command, BaseCommand, Borra todos los movimientos y vuelve a sincronizar Gmail desde cero. Util…, Command, BaseCommand (+38 more)

### Community 1 - "dashboard/views.py / movimientos/selectors.py"
Cohesion: 0.08
Nodes (35): obtener_configuracion(), obtener_saldo_inicial(), Decimal, Selectores de lectura para modelos del nucleo., Devuelve el saldo inicial configurado o 0 si no existe ninguno., calcular_balance(), calcular_saldo(), Decimal (+27 more)

### Community 2 - "Movimiento / movimientos/services.py"
Cohesion: 0.07
Nodes (34): Servicios de auditoria., Crea un RegistroAuditoria sin bloquear el flujo principal., registrar_auditoria(), Command, BaseCommand, Verifica el estado del sistema: DB, Gmail, conteos., ComprobanteAdmin, MovimientoAdmin (+26 more)

### Community 3 - "parsear() / BancolombiaParserTests"
Cohesion: 0.07
Nodes (25): es_correo_bancolombia(), MovimientoParseado, _normalizar_valor(), parsear(), _parsear_fecha(), _parsear_formato_estandar(), _parsear_hora(), Decimal (+17 more)

### Community 4 - "Usuario / UsuarioCrearForm"
Cohesion: 0.07
Nodes (26): AbstractUser, Command, atomic, BaseCommand, Crea datos iniciales (seed) para ALSI BALANCE. - Crea un superusuario…, UserAdmin, UserCreationForm, register (+18 more)

### Community 5 - "Categoria / categorias/views.py"
Cohesion: 0.08
Nodes (24): CategoriaAdmin, register, CategoriaForm, Meta, Categoria, Meta, CategoriaModelTests, CategoriaViewTests (+16 more)

### Community 6 - "core/models.py / movimientos/views.py"
Cohesion: 0.14
Nodes (16): Modelo de categoria. Permite agrupar movimientos (ingresos/egresos) en…, Modelos para conciliacion bancaria. Esta app queda como placeholder para la…, ConfiguracionSistemaAdmin, register, ConfiguracionSistema, EstadoConciliacion, Meta, OrigenMovimiento (+8 more)

### Community 7 - "procesar_correo_simulado() / GmailServiceTests"
Cohesion: 0.07
Nodes (14): Command, BaseCommand, Procesa correos de prueba directamente en la base de datos. Util para verificar…, Command, BaseCommand, Procesa un correo pegado como texto (sin Gmail API). Permite probar el parser…, procesar_correo_simulado(), Procesa un correo simulado (util para tests). No consulta Gmail. Devuelve… (+6 more)

### Community 8 - "reportes/views.py / reportes/services.py"
Cohesion: 0.14
Nodes (28): _autosize(), _estilo_header(), exportar_egresos(), exportar_ingresos(), exportar_movimientos(), exportar_reporte_financiero(), Exportadores a Excel (.xlsx) usando openpyxl., Helper para que las vistas serialicen el workbook a una respuesta HTTP. (+20 more)

### Community 9 - "MovimientoForm / MovimientoCreateView"
Cohesion: 0.11
Nodes (16): DetailView, ComprobanteForm, Meta, MovimientoForm, MovimientoCreateView, MovimientoDeleteView, MovimientoDetailView, MovimientoListView (+8 more)

### Community 10 - "PushSubscription / notificaciones/views.py"
Cohesion: 0.11
Nodes (17): csrf_exempt, PushSubscriptionAdmin, register, Meta, PushSubscription, Modelo para suscripciones Web Push (notificaciones moviles)., Una suscripcion a Web Push de un navegador/dispositivo., Servicios para envio de notificaciones push. (+9 more)

### Community 11 - "PermisosTests / MovimientoCRUDTests"
Cohesion: 0.12
Nodes (5): MovimientoCRUDTests, MovimientoModelTests, PermisosTests, TestCase, Verifica que solo el administrador puede modificar movimientos.

### Community 12 - "RegistroAuditoria / reset_total.py"
Cohesion: 0.14
Nodes (8): register, RegistroAuditoriaAdmin, Meta, Modelo de auditoria: registra acciones sensibles sobre el sistema., RegistroAuditoria, Command, BaseCommand, Borra todos los datos de la aplicacion. Util antes de hacer pruebas pesadas o…

### Community 13 - "core_extras.py / abs_valor()"
Cohesion: 0.23
Nodes (11): abs_valor(), cop(), moneda(), Decimal, Filtros y template tags del nucleo., Devuelve el valor absoluto, soporta Decimal y numeros., Devuelve '+' si es INGRESO y '-' si es EGRESO., Formatea un valor como COP sin simbolo: 1.234.567,89 (siempre 2 decimales). (+3 more)

### Community 14 - "ReportesViewsTests / ReportesServicesTests"
Cohesion: 0.18
Nodes (3): TestCase, ReportesServicesTests, ReportesViewsTests

### Community 15 - "gmail_integration/apps.py / _es_comando_de_servido"
Cohesion: 0.32
Nodes (6): _es_comando_de_servidor(), GmailIntegrationConfig, _loop_autosync(), AppConfig, Detecta si Django se ejecuta con 'runserver' (no tests, migrate, etc)., Loop en background que sincroniza Gmail periodicamente.

### Community 16 - "Conciliacion / CuentaBancaria"
Cohesion: 0.33
Nodes (4): Conciliacion, CuentaBancaria, Meta, Sesion de conciliacion entre el sistema y el banco.

### Community 17 - "context_processors.py / gmail_status()"
Cohesion: 0.33
Nodes (5): app_brand(), gmail_status(), Context processors compartidos para todo el proyecto., Inyecta el estado de conexion de Gmail en todas las plantillas autenticadas., Inyecta el nombre de marca y la empresa en todas las plantillas.

### Community 18 - "debug_gmail.py / Command"
Cohesion: 0.33
Nodes (3): Command, BaseCommand, Lista correos de Gmail ignorados/no reconocidos con su contenido. Ayuda a…

### Community 19 - "reintentar_gmail.py / Command"
Cohesion: 0.33
Nodes (3): Command, BaseCommand, Reintenta procesar correos Gmail marcados como IGNORADO. Util cuando ajustamos…

### Community 20 - "ver_correo.py / Command"
Cohesion: 0.33
Nodes (3): Command, BaseCommand, Muestra el contenido completo de los correos IGNORADO.

### Community 21 - "pagination_window() / pagination.py"
Cohesion: 0.40
Nodes (4): pagination_window(), Template tags para paginacion con ventana (numerica + elipsis)., Genera lista de paginas a mostrar con elipsis. Retorna una lista de enteros…, simple_tag

### Community 23 - "Command / generar_vapid.py"
Cohesion: 0.40
Nodes (3): Command, BaseCommand, Genera un par de claves VAPID para Web Push. Las claves se imprimen en…

### Community 26 - "generar_iconos.py / crear_icono()"
Cohesion: 0.67
Nodes (3): crear_icono(), main(), Genera iconos PWA basicos con Pillow.

## Knowledge Gaps
- **18 isolated node(s):** `Migration`, `Migration`, `Migration`, `Meta`, `Migration` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Movimiento` connect `Movimiento / movimientos/services.py` to `gmail_integration/services.py / sincronizar_correo`, `dashboard/views.py / movimientos/selectors.py`, `core/models.py / movimientos/views.py`, `procesar_correo_simulado() / GmailServiceTests`, `reportes/views.py / reportes/services.py`, `MovimientoForm / MovimientoCreateView`, `PermisosTests / MovimientoCRUDTests`, `RegistroAuditoria / reset_total.py`?**
  _High betweenness centrality (0.191) - this node is a cross-community bridge._
- **Why does `Categoria` connect `Categoria / categorias/views.py` to `dashboard/views.py / movimientos/selectors.py`, `Movimiento / movimientos/services.py`, `Usuario / UsuarioCrearForm`, `core/models.py / movimientos/views.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `Usuario` connect `Usuario / UsuarioCrearForm` to `core/models.py / movimientos/views.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Movimiento` (e.g. with `ComprobanteAdmin` and `MovimientoAdmin`) actually correct?**
  _`Movimiento` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `Categoria` (e.g. with `CategoriaAdmin` and `CategoriaForm`) actually correct?**
  _`Categoria` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `gmail_integration/services.py / sincronizar_correo` be split into smaller, more focused modules?**
  _Cohesion score 0.05704365079365079 - nodes in this community are weakly interconnected._