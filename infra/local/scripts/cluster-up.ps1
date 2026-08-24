$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
$ClusterConfig = Join-Path $RepoRoot "infra/local/kind/cluster-config.yaml"
$ClusterName = "perfeng-local"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Starting PerfEng Local Kubernetes Cluster" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if kind is installed
if (-not (Get-Command kind -ErrorAction SilentlyContinue)) {
    Write-Error "kind is not installed. Install from: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
}
catch {
    Write-Error "Docker is not running"
    exit 1
}

# Check if cluster already exists - capture output without error
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
    # Ignore errors - just means no clusters
    $existingClusters = @()
}

# Filter out the "No kind clusters found." message
$existingClusters = $existingClusters | Where-Object { $_ -ne "No kind clusters found." -and $_ -notmatch "^No kind" }

if ($existingClusters -contains $ClusterName) {
    Write-Host "Cluster '$ClusterName' already exists" -ForegroundColor Yellow
    Write-Host "Use 'make cluster-down' to delete it first" -ForegroundColor Yellow
    exit 0
}

# Create cluster
Write-Host "Creating kind cluster '$ClusterName'..." -ForegroundColor Green
kind create cluster --name $ClusterName --config $ClusterConfig --wait 120s

Write-Host ""
Write-Host "Cluster created successfully!" -ForegroundColor Green

# Wait for nodes to be ready
Write-Host "Waiting for nodes to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Display cluster info
Write-Host ""
Write-Host "Cluster nodes:" -ForegroundColor Cyan
kubectl get nodes -o wide

Write-Host ""
Write-Host "Cluster setup complete!" -ForegroundColor Green