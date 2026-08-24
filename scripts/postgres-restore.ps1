param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [switch]$ConfirmRestore
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmRestore) {
    throw "Restoration overwrites the target database. Re-run with -ConfirmRestore."
}
$databaseUrl = $env:DATABASE_URL
if ([string]::IsNullOrWhiteSpace($databaseUrl)) {
    throw "Define DATABASE_URL before restoring a backup."
}
if (-not (Test-Path -LiteralPath $BackupFile -PathType Leaf)) {
    throw "Backup file not found: $BackupFile"
}

Write-Host "Restoring PostgreSQL backup from $BackupFile"
pg_restore --clean --if-exists --dbname=$databaseUrl $BackupFile
if ($LASTEXITCODE -ne 0) {
    throw "pg_restore failed with exit code $LASTEXITCODE."
}
Write-Host "Restore completed. Run 'alembic upgrade head' and application smoke checks."
