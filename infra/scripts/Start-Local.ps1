param([string]$RepositoryUrl)
$ErrorActionPreference = 'Stop'
$taskInfra = Split-Path -Parent $PSScriptRoot
$taskDocker = (Get-Command docker -ErrorAction SilentlyContinue).Source
if (-not $taskDocker) { $taskDocker = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe' }
if (-not (Test-Path -LiteralPath $taskDocker)) { throw 'Docker CLI was not found. Start Docker Desktop and check its CLI installation.' }
$taskLocal = Join-Path $taskInfra '.local'
New-Item -ItemType Directory -Path $taskLocal -Force | Out-Null
$taskPasswordFile = Join-Path $taskLocal 'admin-password.txt'
if (-not (Test-Path -LiteralPath $taskPasswordFile)) {
    $taskBytes = New-Object byte[] 24
    $taskRng = [Security.Cryptography.RandomNumberGenerator]::Create()
    $taskRng.GetBytes($taskBytes)
    $taskRng.Dispose()
    [IO.File]::WriteAllText($taskPasswordFile, [Convert]::ToBase64String($taskBytes))
}
$taskEnv = Join-Path $taskInfra '.env'
if ($RepositoryUrl) { [IO.File]::WriteAllText($taskEnv, 'SCM_URL=' + $RepositoryUrl + [Environment]::NewLine) }
elseif (-not (Test-Path -LiteralPath $taskEnv)) { Copy-Item -LiteralPath (Join-Path $taskInfra '.env.example') -Destination $taskEnv }
& $taskDocker compose --env-file $taskEnv -f (Join-Path $taskInfra 'compose.yaml') up -d --build
if ($LASTEXITCODE -ne 0) { throw 'Local Jenkins startup failed. Inspect the Compose output.' }
Write-Output 'Jenkins: http://localhost:8081/ | user: admin'
Write-Output ('Password file: ' + $taskPasswordFile)
Write-Output 'Job: asdp-assignment-5 | pipeline: infra/Jenkinsfile'
Write-Output 'The analyzer is deployed at http://localhost:8000/ after a successful build.'
