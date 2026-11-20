$ErrorActionPreference = "Stop"

foreach ($command in @("createdb", "dropdb", "psql", "pg_dump", "pg_restore", "alembic")) {
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

    $libpqDatabaseUrl = $env:DATABASE_URL
    $env:DATABASE_URL = "postgresql+psycopg://tidewatch:tidewatch@localhost:5432/$databaseName"
    Push-Location (Join-Path $PSScriptRoot "..\apps\api")
    try {
        alembic upgrade head
        if ($LASTEXITCODE -ne 0) {
            throw "Could not apply the Tidewatch database migrations to the recovery database."
        }
    }
    finally {
        Pop-Location
        $env:DATABASE_URL = $libpqDatabaseUrl
    }

    $migrationVersionBefore = psql --dbname=$env:DATABASE_URL --tuples-only --no-align --command "SELECT version_num FROM alembic_version;"
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($migrationVersionBefore -join "").Trim())) {
        throw "Could not verify the migrated Tidewatch schema before backup."
    }
    $clientVersion = pg_restore --version
    if ($LASTEXITCODE -ne 0 -or $clientVersion -notmatch "\(PostgreSQL\)\s+(\d+)") {
        throw "Could not determine the pg_restore client version."
    }
    $clientMajorVersion = [int]$Matches[1]
    $serverVersionNumberText = psql --dbname=$env:DATABASE_URL --tuples-only --no-align --command "SHOW server_version_num;"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not determine the PostgreSQL server version."
    }
    $serverMajorVersion = [math]::Floor([int]($serverVersionNumberText -join "").Trim() / 10000)
    if ($clientMajorVersion -ne $serverMajorVersion) {
        throw "PostgreSQL client major version $clientMajorVersion must match server major version $serverMajorVersion for the recovery integration test."
    }

    psql --dbname=$env:DATABASE_URL --command "CREATE TABLE recovery_probe (id integer PRIMARY KEY, value text NOT NULL, committed_at timestamptz NOT NULL); INSERT INTO recovery_probe VALUES (1, 'before-backup', CURRENT_TIMESTAMP);"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not seed the isolated PostgreSQL recovery database."
    }
    $schemaBefore = psql --dbname=$env:DATABASE_URL --tuples-only --no-align --command "SELECT string_agg(table_name, ',' ORDER BY table_name) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($schemaBefore -join "").Trim())) {
        throw "Could not list the Tidewatch schema tables before backup."
    }

    . (Join-Path $PSScriptRoot "postgres-backup.ps1") -OutputFile $backupFile

    psql --dbname=$env:DATABASE_URL --command "INSERT INTO recovery_probe VALUES (2, 'after-backup', CURRENT_TIMESTAMP);"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not mutate the isolated PostgreSQL recovery database."
    }

    $simulatedRpoSecondsText = psql --dbname=$env:DATABASE_URL --tuples-only --no-align --command "SELECT EXTRACT(EPOCH FROM ((SELECT committed_at FROM recovery_probe WHERE id = 2) - (SELECT committed_at FROM recovery_probe WHERE id = 1)));"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not measure the simulated recovery point objective."
    }
    $simulatedRpoSeconds = [double]::Parse(
        ($simulatedRpoSecondsText -join "").Trim(),
        [System.Globalization.CultureInfo]::InvariantCulture
    )

    $recoveryStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    . (Join-Path $PSScriptRoot "postgres-restore.ps1") -BackupFile $backupFile -ConfirmRestore

    $restoredRows = psql --dbname=$env:DATABASE_URL --tuples-only --no-align --command "SELECT id || ':' || value FROM recovery_probe ORDER BY id;"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not verify the restored PostgreSQL database."
    }
    if (($restoredRows -join "`n").Trim() -ne "1:before-backup") {
        throw "PostgreSQL restore did not recover the expected pre-backup state: $restoredRows"
    }
    $migrationVersionAfter = psql --dbname=$env:DATABASE_URL --tuples-only --no-align --command "SELECT version_num FROM alembic_version;"
    if ($LASTEXITCODE -ne 0 -or ($migrationVersionAfter -join "").Trim() -ne ($migrationVersionBefore -join "").Trim()) {
        throw "PostgreSQL restore did not recover the Tidewatch Alembic migration version."
    }
    $schemaAfter = psql --dbname=$env:DATABASE_URL --tuples-only --no-align --command "SELECT string_agg(table_name, ',' ORDER BY table_name) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
    if ($LASTEXITCODE -ne 0 -or ($schemaAfter -join "").Trim() -ne ($schemaBefore -join "").Trim()) {
        throw "PostgreSQL restore did not recover the Tidewatch application schema."
    }
    $recoveryStopwatch.Stop()
    $simulatedRtoSeconds = $recoveryStopwatch.Elapsed.TotalSeconds

    $rpoText = $simulatedRpoSeconds.ToString("F3", [System.Globalization.CultureInfo]::InvariantCulture)
    $rtoText = $simulatedRtoSeconds.ToString("F3", [System.Globalization.CultureInfo]::InvariantCulture)
    Write-Host "Local PostgreSQL recovery drill passed (simulated RPO: ${rpoText}s, RTO: ${rtoText}s)."
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
