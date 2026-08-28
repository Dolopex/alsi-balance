# Deploy en Railway

Guia paso a paso para desplegar ALSI BALANCE en [Railway](https://railway.app).

## Por que Railway

- Background threads funcionan (Gmail auto-sync cada 60s)
- HTTPS automatico (requerido para Web Push)
- Postgres incluido gratis en tier limitado
- $5 USD de credito gratis para empezar, despues ~$5/mes

## Prerequisitos

1. Cuenta en [railway.app](https://railway.app) (login con GitHub)
2. Este proyecto en un repo de GitHub (publico o privado)
4. Credenciales de Google OAuth (ver seccion abajo)
5. Claves VAPID generadas (ver seccion abajo)

## Paso 1: Preparar el repo

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/tu-usuario/alsi-balance.git
git push -u origin main
```

## Paso 2: Crear proyecto en Railway

1. Ir a https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Seleccionar el repo `alsi-balance`
4. Railway detecta automaticamente que es Python/Django

## Paso 3: Agregar Postgres

1. En el dashboard del proyecto, click "+ New"
2. Seleccionar "Database" -> "PostgreSQL"
3. Railway crea la instancia y setea `DATABASE_URL` automaticamente

## Paso 4: Variables de entorno

En el dashboard del proyecto -> Variables, agregar:

| Variable | Valor |
|---|---|
| `DJANGO_SECRET_KEY` | Generar uno nuevo (ver abajo) |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `.up.railway.app,.railway.app` |
| `GOOGLE_OAUTH_CLIENT_ID` | Tu client ID de Google |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Tu client secret de Google |
| `GOOGLE_OAUTH_REDIRECT_URI` | `https://tu-app.up.railway.app/gmail/callback/` |
| `VAPID_PUBLIC_KEY` | Clave publica VAPID |
| `VAPID_PRIVATE_KEY` | Clave privada VAPID (PEM completo) |
| `VAPID_CLAIMS_SUB` | `mailto:admin@tu-dominio.com` |
| `GMAIL_AUTO_SYNC` | `1` |
| `GMAIL_AUTO_SYNC_INTERVAL` | `60` |

**Generar SECRET_KEY seguro** (correr localmente):
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Paso 5: Configurar Google OAuth

En [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. Editar tu OAuth 2.0 Client ID
2. Agregar a "Authorized JavaScript origins":
   - `https://tu-app.up.railway.app`
3. Agregar a "Authorized redirect URIs":
   - `https://tu-app.up.railway.app/gmail/callback/`
4. Guardar

## Paso 6: Generar claves VAPID

Correr localmente (con el `.env` actualizado):
```bash
python manage.py generar_vapid
```

Copia el output a las variables `VAPID_PUBLIC_KEY` y `VAPID_PRIVATE_KEY` en Railway.

## Paso 7: Primer deploy

Railway deploya automaticamente al hacer push a GitHub (si configuraste el deploy from GitHub).

El `Procfile` incluye:
- `web`: arranca gunicorn
- `release`: corre `migrate` y `collectstatic` antes de cada deploy

## Paso 8: Crear superusuario

Una vez deployado, desde tu maquina local:

```bash
railway login
railway link  # seleccionar el proyecto
railway run python manage.py createsuperuser
```

Seguir las instrucciones para usuario/contrasena.

## Paso 9: Probar

1. Abrir `https://tu-app.up.railway.app`
2. Login con el superusuario
3. Ir a `/gmail/conectar/` -> autorizar Gmail
4. Ir a `/admin/gmail_integration/emailprocesado/` -> ver correos procesados
5. Esperar 60 segundos -> el auto-sync deberia correr

## Limitaciones

- **Archivos subidos (comprobantes)** se borran en cada redeploy por el filesystem efímero. Para conservar:
  - Migrar a Cloudflare R2 (gratis hasta10GB)
  - O usar un volumen persistente de Railway ($0.25/GB/mes)
- **Web Push requiere HTTPS** (Railway lo da automaticamente ✓)
- **Gmail Watch en tiempo real** (Pub/Sub) requiere setup adicional en Google Cloud (opcional)

## Costos estimados

| Concepto | Costo |
|---|---|
| Web service (512MB RAM) | $5/mes |
| Postgres (256MB) | Incluido gratis |
| **Total** | **~$5/mes** |

Primeros meses: $5 USD de credito gratis incluidos.

## Troubleshooting

**El deploy falla con "ALLOWED_HOSTS"**:
Verificar que `DJANGO_ALLOWED_HOSTS=.up.railway.app` este configurado.

**Gmail sync no corre**:
Verificar logs del deploy - deberia decir "ALSI Gmail: thread de sincronizacion iniciado".

**Web Push no funciona**:
Verificar que la URL sea HTTPS (Railway lo da automatico). En Brave browser, desactivar Shields.

**Error 500 al cargar la pagina**:
Revisar logs en Railway dashboard. Usualmente es variable de entorno faltante.