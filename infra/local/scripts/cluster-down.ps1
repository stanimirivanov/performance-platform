$ErrorActionPreference = "Stop"

$ClusterName = "perfeng-local"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Stopping PerfEng Local Kubernetes Cluster" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if cluster exists - capture output without error
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
    Write-Host "Cluster '$ClusterName' does not exist" -ForegroundColor Yellow
    exit 0
}

# Delete cluster
kind delete cluster --name $ClusterName

Write-Host ""
Write-Host "Cluster deleted successfully!" -ForegroundColor Green