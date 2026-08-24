$ErrorActionPreference = "Stop"

$ClusterName = "perfeng-local"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "PerfEng Local Kubernetes Cluster Status" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if cluster exists
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

if ($existingClusters -notcontains $ClusterName) {
    Write-Host "Cluster '$ClusterName' does not exist" -ForegroundColor Red
    exit 1
}

Write-Host "Cluster exists: $ClusterName" -ForegroundColor Green
Write-Host ""

# Show nodes
Write-Host "=== Nodes ===" -ForegroundColor Cyan
kubectl get nodes -o wide

Write-Host ""
Write-Host "=== Node Labels ===" -ForegroundColor Cyan
kubectl get nodes --show-labels

Write-Host ""
Write-Host "=== Node Taints ===" -ForegroundColor Cyan
kubectl get nodes -o custom-columns=NAME:.metadata.name, TAINTS:.spec.taints

Write-Host ""
Write-Host "=== Pods (all namespaces) ===" -ForegroundColor Cyan
kubectl get pods --all-namespaces -o wide

Write-Host ""
Write-Host "=== Resource Usage ===" -ForegroundColor Cyan
try {
    kubectl top nodes 2>&1 | Out-Host
}
catch {
    Write-Host "metrics-server not installed yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Kubernetes Version ===" -ForegroundColor Cyan
kubectl version --short 2>&1 | Out-Host