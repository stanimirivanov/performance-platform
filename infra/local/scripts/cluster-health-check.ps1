$ErrorActionPreference = "Stop"

$ClusterName = "perfeng-local"
$Failed = 0

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "PerfEng Cluster Health Check" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Helper function to run kind commands using cmd /c
function Invoke-KindCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )
    
    $argString = $Arguments -join " "
    $command = "kind $argString 2>&1"
    
    $output = cmd /c $command
    $exitCode = $LASTEXITCODE
    
    return @{
        Output   = $output
        ExitCode = $exitCode
    }
}

# Check 1: Cluster exists
Write-Host ""
Write-Host "Checking cluster existence..." -ForegroundColor Yellow

$existingClusters = @()
$kindResult = Invoke-KindCommand -Arguments @("get", "clusters")
$kindOutput = $kindResult.Output

if ($kindOutput) {
    foreach ($line in $kindOutput) {
        $trimmed = $line.Trim()
        if ($trimmed -ne "" -and $trimmed -ne "No kind clusters found." -and $trimmed -notmatch "^No kind") {
            $existingClusters += $trimmed
        }
    }
}

if ($existingClusters -contains $ClusterName) {
    Write-Host "[OK] Cluster '$ClusterName' exists" -ForegroundColor Green
}
else {
    Write-Host "[FAIL] Cluster '$ClusterName' does not exist" -ForegroundColor Red
    $Failed = 1
    Write-Host ""
    Write-Host "Cluster health check failed!" -ForegroundColor Red
    exit $Failed
}

# Check 2: All nodes ready
Write-Host ""
Write-Host "Checking node readiness..." -ForegroundColor Yellow

$nodes = kubectl get nodes --no-headers 2>$null
if ($nodes) {
    $nodeLines = @($nodes -split "`n" | Where-Object { $_.Trim() -ne "" })
    $totalNodes = $nodeLines.Count
    $readyNodes = @($nodeLines | Where-Object { $_ -match " Ready " }).Count
    Write-Host "Ready nodes: $readyNodes/$totalNodes"
    
    if ($readyNodes -lt $totalNodes) {
        Write-Host "[FAIL] Not all nodes are ready" -ForegroundColor Red
        $Failed = 1
    }
    else {
        Write-Host "[OK] All nodes are ready" -ForegroundColor Green
    }
}
else {
    Write-Host "[FAIL] Cannot get node list" -ForegroundColor Red
    $Failed = 1
}

# Check 3: Node labels present
Write-Host ""
Write-Host "Checking node labels..." -ForegroundColor Yellow

$generatorNodes = kubectl get nodes -l workload=performance-generator --no-headers 2>$null
if ($generatorNodes) {
    Write-Host "[OK] Generator node label present" -ForegroundColor Green
}
else {
    Write-Host "[FAIL] Generator node label missing" -ForegroundColor Red
    $Failed = 1
}

$sutNodes = kubectl get nodes -l workload=sut --no-headers 2>$null
if ($sutNodes) {
    Write-Host "[OK] SUT node label present" -ForegroundColor Green
}
else {
    Write-Host "[FAIL] SUT node label missing" -ForegroundColor Red
    $Failed = 1
}

# Check 4: Control plane ready
Write-Host ""
Write-Host "Checking control plane..." -ForegroundColor Yellow

$controlPlane = kubectl get nodes -l node-role.kubernetes.io/control-plane --no-headers 2>$null
if ($controlPlane -match " Ready ") {
    Write-Host "[OK] Control plane is ready" -ForegroundColor Green
}
else {
    Write-Host "[FAIL] Control plane not ready" -ForegroundColor Red
    $Failed = 1
}

# Check 5: CoreDNS running
Write-Host ""
Write-Host "Checking CoreDNS..." -ForegroundColor Yellow

$coredns = kubectl get pods -n kube-system -l k8s-app=kube-dns --no-headers 2>$null
if ($coredns -match "Running") {
    Write-Host "[OK] CoreDNS is running" -ForegroundColor Green
}
else {
    Write-Host "[FAIL] CoreDNS not running" -ForegroundColor Red
    $Failed = 1
}

# Check 6: API server accessible
Write-Host ""
Write-Host "Checking API server..." -ForegroundColor Yellow

$healthz = kubectl get --raw /healthz 2>$null
if ($healthz -eq "ok") {
    Write-Host "[OK] API server is healthy" -ForegroundColor Green
}
else {
    Write-Host "[FAIL] API server not accessible" -ForegroundColor Red
    $Failed = 1
}

# Check 7: Metrics server (if installed)
Write-Host ""
Write-Host "Checking metrics-server..." -ForegroundColor Yellow

$metricsServer = kubectl get pods -n kube-system -l k8s-app=metrics-server --no-headers 2>$null
if ($metricsServer -match "Running") {
    Write-Host "[OK] metrics-server is running" -ForegroundColor Green
}
else {
    Write-Host "[WARN] metrics-server not installed (optional)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
if ($Failed -eq 0) {
    Write-Host "All health checks passed!" -ForegroundColor Green
}
else {
    Write-Host "Some health checks failed" -ForegroundColor Red
}
Write-Host "=========================================" -ForegroundColor Cyan

exit $Failed