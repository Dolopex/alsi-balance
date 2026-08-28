# Deploy en Vercel

Guia paso a paso para desplegar ALSI BALANCE en [Vercel](https://vercel.com) (hosting serverless gratuito).

## Por que Vercel

- Free tier generoso: 100GB bandwidth + 100k requests/mes
- HTTPS automatico (requerido para Web Push)
- Deploys automaticos desde GitHub
- Soporta Django via serverless functions

## Limitaciones a aceptar

- **Sin procesos long-running** (serverless). El sync de Gmail es **manual** via el boton en el dashboard
- **SQLite no funciona** (filesystem efimero). Hay que usar Postgres (Vercel Postgres gratis o Neon externo)
- **Archivos subidos (comprobantes) se borran** en cada deploy

## Prerequisitos

1. Cuenta en [vercel.com](https://vercel.com) (login con GitHub)
2. Repo en GitHub con este codigo
3. Credenciales de Google OAuth (https://console.cloud.google.com/apis/credentials)
4. Claves VAPID (generar localmente con `python manage.py generar_vapid`)

## Paso 1: Crear Postgres

### Opcion A — Vercel Postgres (recomendado)

1. En el dashboard de tu proyecto en Vercel
2. Tab "Storage" → "Create Database" → Postgres
3. Region: la mas cercana (sa-east-1 para Sudamerica)
4. Vercel crea la DB y setea `DATABASE_URL` automaticamente

### Opcion B — Neon externo

1. https://neon.tech → signup con GitHub
2. Create project `alsi-balance`
3. Region: US East o South America
4. Copia el connection string

## Paso 2: Conectar repo a Vercel

1. https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. "Import" tu repo `alsi-balance` desde GitHub
4. Vercel detecta automaticamente que es Python (por `vercel.json` y `api/index.py`)

## Paso 3: Configurar variables de entorno

En la pantalla de configuracion del proyecto en Vercel:

| Variable | Valor |
|---|---|
| `DJANGO_SECRET_KEY` | Generar con `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | `False` |
| `DATABASE_URL` | La URL de tu Postgres (Vercel la setea auto si usaste Vercel Postgres) |
| `GOOGLE_OAUTH_CLIENT_ID` | Tu client ID de Google |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Tu client secret de Google |
| `GOOGLE_OAUTH_REDIRECT_URI` | `https://TU-PROYECTO.vercel.app/gmail/callback/` |
| `VAPID_PUBLIC_KEY` | Clave publica VAPID |
| `VAPID_PRIVATE_KEY` | Clave privada VAPID (PEM completo) |
| `VAPID_CLAIMS_SUB` | `mailto:admin@tu-dominio.com` |

**NO** setees `GMAIL_AUTO_SYNC` — queda desactivado (sync manual).

## Paso 4: Configurar Google OAuth

En https://console.cloud.google.com/apis/credentials:

1. Edita tu OAuth 2.0 Client ID
2. "Authorized JavaScript origins":
   - `https://TU-PROYECTO.vercel.app`
3. "Authorized redirect URIs":
   - `https://TU-PROYECTO.vercel.app/gmail/callback/`
4. Save

## Paso 5: Primer deploy

Vercel deploya automaticamente al hacer el import. Esperar 2-5 minutos.

**El build command corre `python manage.py collectstatic --noinput` para juntar los archivos estaticos.**

## Paso 6: Correr migraciones

**Esto es importante** — Vercel no corre migraciones automaticamente (cada deploy seria riesgoso).

### Opcion A — Desde tu PC local

Configurar temporalmente la `DATABASE_URL` apuntando a Vercel/Neon, y correr:
```bash
DATABASE_URL="postgresql://..." python manage.py migrate
DATABASE_URL="postgresql://..." python manage.py createsuperuser
```

### Opcion B — Desde Vercel CLI

```bash
npm install -g vercel
vercel login
vercel link
vercel env pull .env.production
python manage.py migrate
python manage.py createsuperuser
```

## Paso 7: Probar

1. Abrir `https://TU-PROYECTO.vercel.app`
2. Login con el superusuario
3. Ir a `/gmail/conectar/` → autorizar Gmail
4. Click "Sincronizar Gmail" → el sync corre manual
5. Web Push funciona (HTTPS automatico)

## Workflow diario

```
1. Te llega un correo de Bancolombia (notificacion del celular)
2. Abrras TU-PROYECTO.vercel.app
3. Login
4. Click "Sincronizar Gmail" en el dashboard
5. Se importan los movimientos nuevos
6. Listo
```

## Comandos utiles

| Accion | Comando |
|---|---|
| Ver logs en vivo | Dashboard Vercel → tu proyecto → "Logs" |
| Forzar redeploy | Dashboard → "Deployments" → click en uno → "Redeploy" |
| Ver variables | Dashboard → "Settings" → "Environment Variables" |
| Rollback | Dashboard → "Deployments" → click en uno anterior → "Promote to Production" |

## Limitaciones y soluciones

| Limitacion | Solucion futura |
|---|---|
| Sin sync automatico Gmail | Usar Gmail Watch API + Pub/Sub (ver `gmail_integration/management/commands/setup_gmail_watch.py`) |
| Archivos subidos se pierden | Migrar a Cloudflare R2 (gratis 10GB) con django-storages |
| Function timeout 10s en free tier | Upgrade a Pro ($20/mes) para 60s timeout |

## Costos

| Concepto | Costo |
|---|---|
| Vercel free tier | $0 |
| Vercel Postgres free (256MB) | $0 |
| Bandwidth hasta 100GB/mes | $0 |
| **Total** | **$0/mes para siempre** |

Si excedes el free tier:
- Bandwidth: $0.15/GB adicional
- Functions: $0.60 por million de ejecuciones adicionales