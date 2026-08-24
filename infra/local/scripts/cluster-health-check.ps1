$ErrorActionPreference = "Continue"

$ClusterName = "perfeng-local"
$Failed = 0

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "PerfEng Cluster Health Check" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check 1: Cluster exists
Write-Host "`nChecking cluster existence..." -ForegroundColor Yellow
$existingClusters = @()
try {
    $kindOutput = kind get clusters 2>&1
    if ($kindOutput -is [string]) {
        $existingClusters = @($kindOutput -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
    }
    elseif ($kindOutput -is [array]) {
        $existingClusters = @($kindOutput | ForEach-Object { $_.ToString().Trim() } | Where-Object { $_ -ne "" })
    }
}
catch {
    $existingClusters = @()
}

$existingClusters = $existingClusters | Where-Object { $_ -ne "No kind clusters found." -and $_ -notmatch "^No kind" }

if ($existingClusters -contains $ClusterName) {
    Write-Host "✓ Cluster '$ClusterName' exists" -ForegroundColor Green
}
else {
    Write-Host "✗ Cluster '$ClusterName' does not exist" -ForegroundColor Red
    $Failed = 1
    Write-Host "`nCluster health check failed!" -ForegroundColor Red
    exit $Failed
}

# Check 2: All nodes ready
Write-Host "`nChecking node readiness..." -ForegroundColor Yellow
$nodes = kubectl get nodes --no-headers 2>$null
if ($nodes) {
    $nodeLines = @($nodes) -split "`n" | Where-Object { $_.Trim() -ne "" }
    $totalNodes = $nodeLines.Count
    $readyNodes = ($nodeLines | Where-Object { $_ -match " Ready " }).Count
    Write-Host "Ready nodes: $readyNodes/$totalNodes"
    
    if ($readyNodes -lt $totalNodes) {
        Write-Host "✗ Not all nodes are ready" -ForegroundColor Red
        $Failed = 1
    }
    else {
        Write-Host "✓ All nodes are ready" -ForegroundColor Green
    }
}
else {
    Write-Host "✗ Cannot get node list" -ForegroundColor Red
    $Failed = 1
}

# Check 3: Node labels present
Write-Host "`nChecking node labels..." -ForegroundColor Yellow
$generatorNodes = kubectl get nodes -l workload=performance-generator --no-headers 2>$null
if ($generatorNodes) {
    Write-Host "✓ Generator node label present" -ForegroundColor Green
}
else {
    Write-Host "✗ Generator node label missing" -ForegroundColor Red
    $Failed = 1
}

$sutNodes = kubectl get nodes -l workload=sut --no-headers 2>$null
if ($sutNodes) {
    Write-Host "✓ SUT node label present" -ForegroundColor Green
}
else {
    Write-Host "✗ SUT node label missing" -ForegroundColor Red
    $Failed = 1
}

# Check 4: Control plane ready
Write-Host "`nChecking control plane..." -ForegroundColor Yellow
$controlPlane = kubectl get nodes -l node-role.kubernetes.io/control-plane --no-headers 2>$null
if ($controlPlane -match " Ready ") {
    Write-Host "✓ Control plane is ready" -ForegroundColor Green
}
else {
    Write-Host "✗ Control plane not ready" -ForegroundColor Red
    $Failed = 1
}

# Check 5: CoreDNS running
Write-Host "`nChecking CoreDNS..." -ForegroundColor Yellow
$coredns = kubectl get pods -n kube-system -l k8s-app=kube-dns --no-headers 2>$null
if ($coredns -match "Running") {
    Write-Host "✓ CoreDNS is running" -ForegroundColor Green
}
else {
    Write-Host "✗ CoreDNS not running" -ForegroundColor Red
    $Failed = 1
}

# Check 6: API server accessible
Write-Host "`nChecking API server..." -ForegroundColor Yellow
$healthz = kubectl get --raw /healthz 2>$null
if ($healthz -eq "ok") {
    Write-Host "✓ API server is healthy" -ForegroundColor Green
}
else {
    Write-Host "✗ API server not accessible" -ForegroundColor Red
    $Failed = 1
}

# Check 7: Metrics server (if installed)
Write-Host "`nChecking metrics-server..." -ForegroundColor Yellow
$metricsServer = kubectl get pods -n kube-system -l k8s-app=metrics-server --no-headers 2>$null
if ($metricsServer -match "Running") {
    Write-Host "✓ metrics-server is running" -ForegroundColor Green
}
else {
    Write-Host "⚠ metrics-server not installed (optional)" -ForegroundColor Yellow
}

Write-Host ""
if ($Failed -eq 0) {
    Write-Host "✓ All health checks passed!" -ForegroundColor Green
}
else {
    Write-Host "✗ Some health checks failed" -ForegroundColor Red
}

exit $Failed