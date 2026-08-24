$ErrorActionPreference = "Stop"

$ClusterName = "perfeng-local"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Stopping PerfEng Local Kubernetes Cluster" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if cluster exists
$existingClusters = kind get clusters 2>$null
if ($existingClusters -notcontains $ClusterName) {
    Write-Host "Cluster '$ClusterName' does not exist" -ForegroundColor Yellow
    exit 0
}

# Delete cluster
kind delete cluster --name $ClusterName

Write-Host ""
Write-Host "Cluster deleted successfully!" -ForegroundColor Green