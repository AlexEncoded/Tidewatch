param(
    [string]$OutputFile = "tidewatch-backup.dump"
)

$ErrorActionPreference = "Stop"
$databaseUrl = $env:DATABASE_URL
if ([string]::IsNullOrWhiteSpace($databaseUrl)) {
    throw "Define DATABASE_URL before creating a backup."
}

$resolvedOutputFile = if ([System.IO.Path]::IsPathRooted($OutputFile)) {
    $OutputFile
}
else {
    Join-Path (Get-Location).Path $OutputFile
}
$destination = [System.IO.Path]::GetFullPath($resolvedOutputFile)
$directory = [System.IO.Path]::GetDirectoryName($destination)
if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
    throw "Backup directory does not exist: $directory"
}
$temporaryFile = Join-Path $directory ("." + [System.IO.Path]::GetFileName($destination) + "." + [guid]::NewGuid().ToString("N") + ".tmp")

try {
    Write-Host "Creating PostgreSQL backup at $destination"
    pg_dump --dbname=$databaseUrl --format=custom --file $temporaryFile
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump failed with exit code $LASTEXITCODE."
    }
    if (-not (Test-Path -LiteralPath $temporaryFile -PathType Leaf)) {
        throw "pg_dump did not create a non-empty backup."
    }
    if ((Get-Item -Force -LiteralPath $temporaryFile).Length -eq 0) {
        throw "pg_dump did not create a non-empty backup."
    }

    [System.IO.File]::Move($temporaryFile, $destination, $true)
    Write-Host "Backup created successfully. Store it in approved backup storage."
}
finally {
    if (Test-Path -LiteralPath $temporaryFile) {
        Remove-Item -LiteralPath $temporaryFile -Force
    }
}
