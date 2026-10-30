$ErrorActionPreference = 'Stop'
$taskProject = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskDocker = (Get-Command docker -ErrorAction SilentlyContinue).Source
if (-not $taskDocker) { $taskDocker = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe' }
$taskContainer = 'asdp5-manual-tests-' + [Guid]::NewGuid().ToString('N')
$taskReport = Join-Path $taskProject 'infra\build'
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
Push-Location $taskProject
try {
    & $taskDocker build --target test -f infra/Dockerfile -t asdp5-tests:manual .
    if ($LASTEXITCODE -ne 0) { throw 'Test image build failed.' }
    & $taskDocker create --name $taskContainer --label com.asdp.assignment=5 asdp5-tests:manual
    if ($LASTEXITCODE -ne 0) { throw 'Test container creation failed.' }
    & $taskDocker start -a $taskContainer
    $taskResult = $LASTEXITCODE
    & $taskDocker cp ($taskContainer + ':/reports/junit.xml') (Join-Path $taskReport 'junit.xml')
    if ($LASTEXITCODE -ne 0) { throw 'JUnit report could not be copied.' }
    if ($taskResult -ne 0) { throw 'Tests failed. See infra/build/junit.xml.' }
} finally {
    & $taskDocker rm -f $taskContainer 2>$null | Out-Null
    Pop-Location
}
