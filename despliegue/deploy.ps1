# despliegue/deploy.ps1
# Automatiza build + push + deploy del Asistente Clinico IA a Cloud Run.
# Se corre desde la RAIZ del proyecto: .\despliegue\deploy.ps1

$ErrorActionPreference = "Stop"

# --- Configuracion (ajustar solo si cambia el proyecto o la region) ---
$PROJECT_ID = "project-bf4e92f0-b111-49af-a10"
$REGION = "us-central1"
$REPO = "asistente-clinico-repo"
$IMAGEN = "asistente-clinico-api"
$IMAGEN_COMPLETA = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/${IMAGEN}:latest"

Write-Host "==> Construyendo la imagen Docker..." -ForegroundColor Cyan
docker build -t $IMAGEN_COMPLETA .
if ($LASTEXITCODE -ne 0) { Write-Host "Fallo el build. Abortando." -ForegroundColor Red; exit 1 }

Write-Host "==> Subiendo la imagen a Artifact Registry..." -ForegroundColor Cyan
docker push $IMAGEN_COMPLETA
if ($LASTEXITCODE -ne 0) { Write-Host "Fallo el push. Abortando." -ForegroundColor Red; exit 1 }

Write-Host "==> Desplegando en Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $IMAGEN `
    --image=$IMAGEN_COMPLETA `
    --region=$REGION `
    --platform=managed `
    --port=8000 `
    --memory=1Gi `
    --min-instances=0 `
    --max-instances=3 `
    --allow-unauthenticated `
    --env-vars-file=despliegue/env-cloudrun.yaml

if ($LASTEXITCODE -ne 0) { Write-Host "Fallo el deploy. Abortando." -ForegroundColor Red; exit 1 }

Write-Host "==> Listo. Servicio desplegado." -ForegroundColor Green