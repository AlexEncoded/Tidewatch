param(
    [string]$OutputFile = "tidewatch-backup.sql"
)

$ErrorActionPreference = "Stop"
$databaseUrl = $env:DATABASE_URL
if ([string]::IsNullOrWhiteSpace($databaseUrl)) {
    throw "Define DATABASE_URL before creating a backup."
}

Write-Host "Creating PostgreSQL backup at $OutputFile"
pg_dump --dbname=$databaseUrl --format=custom --file=$OutputFile
if ($LASTEXITCODE -ne 0) {
    throw "pg_dump failed with exit code $LASTEXITCODE."
}
Write-Host "Backup created successfully. Store it in approved backup storage."
