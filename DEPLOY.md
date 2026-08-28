# Deploy en Fly.io + Neon Postgres (100% gratis)

Guia para desplegar ALSI BALANCE en [Fly.io](https://fly.io) (hosting) +
[Neon](https://neon.tech) (Postgres gratis).

## Costos

| Servicio | Plan | Costo |
|---|---|---|
| Fly.io | 3 VMs shared-cpu 256MB | **$0/mes** |
| Neon Postgres | 0.5GB | **$0/mes** |
| **Total** | | **$0/mes para siempre** |

Limitaciones:
- 256MB RAM: justo. Si crece, upgrade a 512MB cuesta ~$3/mes.
- Postgres 0.5GB: alcanza para miles de movimientos. Para crecer, Neon escala gratis hasta 0.5GB.

## Limitaciones aceptables para MVP

- **Archivos subidos (comprobantes)** se borran en cada redeploy. Para conservar:
  - Migrar a Cloudflare R2 (gratis 10GB) - futuro
- **Web Push requiere HTTPS** ✓ Fly.io lo da automatico
- **1 solo worker de gunicorn** por la limitacion de 256MB

## Prerequisitos

1. Cuenta en [fly.io](https://fly.io) (signup con GitHub)
2. Cuenta en [neon.tech](https://neon.tech) (signup con GitHub)
3. Repo en GitHub con este codigo
4. Credenciales de Google OAuth (https://console.cloud.google.com/apis/credentials)
5. Claves VAPID (generar localmente con `python manage.py generar_vapid`)

## Paso 1: Crear Postgres en Neon

1. Ir a https://console.neon.tech
2. Sign up con GitHub
3. Click "Create Project" → nombre: `alsi-balance`
4. Region: elegir **US East (Ohio)** o **South America (São Paulo)** (más cercano a Colombia)
5. Postgres version: latest (16 o 17)
6. Click "Create Project"
7. En el dashboard del proyecto, click "Connection Details"
8. Copiar el `DATABASE_URL` (formato: `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require`)

## Paso 2: Instalar Fly.io CLI

**Windows (PowerShell):**
```powershell
irm https://fly.io/install.ps1 | ie
```

**Mac/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

Verificar instalación:
```bash
fly version
```

## Paso 3: Login en Fly.io

```bash
fly auth login
```

Te abre el navegador para autenticar con GitHub.

## Paso 4: Crear la app en Fly.io

Dentro del directorio del proyecto:
```bash
cd "C:\alsi balance"
fly launch
```

**Lo que te pregunta:**
- **App name**: `alsi-balance` (o el que quieras, te dice si está disponible)
- **Region**: elegir el más cercano a Colombia. Opciones:
  - `gru` (São Paulo, Brasil) - recomendado
  - `eze` (Buenos Aires)
  - `iad` (Virginia, US)
- **Postgres**: decir **No** (usamos Neon externo)
- **Redis**: **No**
- **Deploy now**: **No** (configuramos secrets primero)

## Paso 5: Setear variables secretas

```bash
fly secrets set DJANGO_SECRET_KEY="<valor-seguro>"
fly secrets set DJANGO_DEBUG="False"
fly secrets set DATABASE_URL="postgresql://user:pass@host/neondb?sslmode=require"

# Gmail OAuth (los que ya tenes en tu .env local)
fly secrets set GOOGLE_OAUTH_CLIENT_ID="<tu-client-id>"
fly secrets set GOOGLE_OAUTH_CLIENT_SECRET="<tu-client-secret>"
fly secrets set GOOGLE_OAUTH_REDIRECT_URI="https://alsi-balance.fly.dev/gmail/callback/"

# VAPID (generar con python manage.py generar_vapid)
fly secrets set VAPID_PUBLIC_KEY="<clave-publica>"
fly secrets set VAPID_PRIVATE_KEY="<pem-completo>"
fly secrets set VAPID_CLAIMS_SUB="mailto:admin@tu-dominio.com"

# Auto-sync Gmail
fly secrets set GMAIL_AUTO_SYNC="1"
fly secrets set GMAIL_AUTO_SYNC_INTERVAL="60"
```

**Generar SECRET_KEY seguro** (en tu PC):
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Paso 6: Deploy

```bash
fly deploy
```

Esto:
1. Compila el Dockerfile
2. Sube la imagen a Fly.io
3. Ejecuta el `release_command` (migrate + collectstatic)
4. Inicia la app con gunicorn

Tarda 2-5 minutos la primera vez.

## Paso 7: Crear superusuario

```bash
fly ssh console -C "python manage.py createsuperuser"
```

Segui las instrucciones para username/password.

## Paso 8: Actualizar Google OAuth

En https://console.cloud.google.com/apis/credentials:

1. Click en tu OAuth 2.0 Client ID
2. En "Authorized JavaScript origins":
   - Agregar: `https://alsi-balance.fly.dev`
3. En "Authorized redirect URIs":
   - Agregar: `https://alsi-balance.fly.dev/gmail/callback/`
4. Save

## Paso 9: Probar

Abrir `https://alsi-balance.fly.dev`:
- Login con el superusuario
- Ir a `/gmail/conectar/` → autorizar Gmail
- Ver logs: `fly logs`
- Debería verse: "ALSI Gmail: thread de sincronizacion iniciado (cada 60s)"

## Comandos utiles

```bash
fly logs              # ver logs en vivo
fly status            # estado de la app
fly ssh console       # shell dentro del container
fly deploy            # redesplegar despues de cambios
fly secrets list      # ver variables secretas
fly secrets unset X   # eliminar una variable
```

## Troubleshooting

**Deploy falla con "out of memory"**:
Reducir workers (ya está en 1) o aumentar memoria:
```bash
fly scale memory 512  # ahora cuesta $3/mes
```

**Gmail sync no aparece en logs**:
- Verificar `GMAIL_AUTO_SYNC=1` en secrets: `fly secrets list`
- Ver logs: `fly logs | grep "ALSI Gmail"`

**Error 500 al cargar**:
- `fly logs | tail -100` para ver el traceback
- Probable causa: variable de entorno faltante

**Web Push no funciona**:
- Verificar HTTPS (Fly.io lo da automatico)
- En Brave browser: desactivar Shields

**Postgres connection refused**:
- Verificar `DATABASE_URL` este correcto en secrets
- Verificar que Neon este en region accesible desde Fly.io
- Probar: `fly ssh console -C "python manage.py dbshell"`

## Si necesitas upgrade

```bash
fly scale memory 512  # mas RAM
fly scale cpus 2       # mas CPU (sigue free hasta cierto punto)
```

Cuando excedas el free tier de Fly.io, te cobran por uso real (~$3-5/mes tipico).