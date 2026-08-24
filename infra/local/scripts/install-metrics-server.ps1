$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
$MetricsServerManifest = Join-Path $RepoRoot "infra/local/kind/metrics-server.yaml"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Installing metrics-server" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if cluster exists
$existingClusters = kind get clusters 2>$null
if ($existingClusters -notcontains "perfeng-local") {
    Write-Error "Cluster 'perfeng-local' does not exist. Run 'make cluster-up' first."
    exit 1
}

# Check if manifest exists
if (-not (Test-Path $MetricsServerManifest)) {
    Write-Error "Manifest not found: $MetricsServerManifest"
    exit 1
}

# Apply the metrics-server manifest
Write-Host "Applying metrics-server manifest..." -ForegroundColor Green
kubectl apply -f $MetricsServerManifest

# Wait for metrics-server to be ready
Write-Host "Waiting for metrics-server to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod `
    -l k8s-app=metrics-server `
    -n kube-system `
    --timeout=120s

# Verify installation
Write-Host "Verifying metrics-server..." -ForegroundColor Yellow
kubectl get apiservice v1beta1.metrics.k8s.io

Write-Host ""
Write-Host "Metrics-server installed successfully!" -ForegroundColor Green

# Test metrics
Write-Host ""
Write-Host "Testing node metrics..." -ForegroundColor Yellow
Start-Sleep -Seconds 15
kubectl top nodes 2>$null