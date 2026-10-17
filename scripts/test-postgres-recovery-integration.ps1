$ErrorActionPreference = "Stop"

foreach ($command in @("createdb", "dropdb", "psql")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required PostgreSQL client command not found: $command"
    }
}

$previousDatabaseUrl = $env:DATABASE_URL
$databaseName = "tidewatch_recovery_$([guid]::NewGuid().ToString('N'))"
$backupDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("tidewatch-recovery-" + [guid]::NewGuid().ToString("N"))
$backupFile = Join-Path $backupDirectory "recovery.dump"
New-Item -ItemType Directory -Path $backupDirectory | Out-Null
$databaseCreated = $false

try {
    createdb --host localhost --port 5432 --username tidewatch $databaseName
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create isolated PostgreSQL recovery database."
    }
    $databaseCreated = $true
    $env:DATABASE_URL = "postgresql://tidewatch:tidewatch@localhost:5432/$databaseName"

    psql --dbname=$env:DATABASE_URL --command "CREATE TABLE recovery_probe (id integer PRIMARY KEY, value text NOT NULL); INSERT INTO recovery_probe VALUES (1, 'before-backup');"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not seed the isolated PostgreSQL recovery database."
    }

    . (Join-Path $PSScriptRoot "postgres-backup.ps1") -OutputFile $backupFile

    psql --dbname=$env:DATABASE_URL --command "INSERT INTO recovery_probe VALUES (2, 'after-backup');"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not mutate the isolated PostgreSQL recovery database."
    }

    . (Join-Path $PSScriptRoot "postgres-restore.ps1") -BackupFile $backupFile -ConfirmRestore

    $restoredRows = psql --dbname=$env:DATABASE_URL --tuples-only --no-align --command "SELECT id || ':' || value FROM recovery_probe ORDER BY id;"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not verify the restored PostgreSQL database."
    }
    if (($restoredRows -join "`n").Trim() -ne "1:before-backup") {
        throw "PostgreSQL restore did not recover the expected pre-backup state: $restoredRows"
    }

    Write-Host "PostgreSQL backup and restore integration test passed."
}
finally {
    if ($databaseCreated) {
        dropdb --host localhost --port 5432 --username tidewatch --if-exists $databaseName
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not remove isolated recovery database $databaseName."
        }
    }
    if ($null -eq $previousDatabaseUrl) {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:DATABASE_URL = $previousDatabaseUrl
    }
    Remove-Item -LiteralPath $backupDirectory -Recurse -Force -ErrorAction SilentlyContinue
}
