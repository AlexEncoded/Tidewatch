$ErrorActionPreference = "Stop"
$script:DumpExitCode = 0
$script:RestoreExitCodes = [System.Collections.Generic.Queue[int]]::new()
$script:RestoreCalls = [System.Collections.Generic.List[string]]::new()

function Assert-Equal($Actual, $Expected, $Message) {
    if ($Actual -ne $Expected) {
        throw "$Message (expected '$Expected', got '$Actual')"
    }
}

function pg_dump {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    if ($script:DumpExitCode -eq 0) {
        $fileArgument = $Arguments | Where-Object { $_ -like "--file=*" } | Select-Object -First 1
        if ($null -ne $fileArgument) {
            $outputFile = $fileArgument -replace "^--file=", ""
        }
        else {
            $fileIndex = [array]::IndexOf($Arguments, "--file")
            if ($fileIndex -lt 0 -or $fileIndex + 1 -ge $Arguments.Count) {
                throw "pg_dump mock did not receive a --file output path: $Arguments"
            }
            $outputFile = $Arguments[$fileIndex + 1]
        }
        [System.IO.File]::WriteAllText($outputFile, "valid archive")
    }
    $global:LASTEXITCODE = $script:DumpExitCode
}

function pg_restore {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $script:RestoreCalls.Add(($Arguments -join " "))
    $global:LASTEXITCODE = $script:RestoreExitCodes.Dequeue()
}

$temporaryDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("tidewatch-pg-test-" + [guid]::NewGuid().ToString("N"))
$previousDatabaseUrl = $env:DATABASE_URL
New-Item -ItemType Directory -Path $temporaryDirectory | Out-Null
$env:DATABASE_URL = "postgresql://test:test@localhost/tidewatch"

try {
    $backup = Join-Path $temporaryDirectory "backup.dump"
    [System.IO.File]::WriteAllText($backup, "previous complete archive")
    $script:DumpExitCode = 1
    $backupFailed = $false
    try {
        . (Join-Path $PSScriptRoot "postgres-backup.ps1") -OutputFile $backup
    }
    catch {
        $backupFailed = $true
    }
    Assert-Equal $backupFailed $true "A failed pg_dump must fail the backup command"
    Assert-Equal ([System.IO.File]::ReadAllText($backup)) "previous complete archive" "A failed backup must preserve the previous archive"
    Assert-Equal (Get-ChildItem -LiteralPath $temporaryDirectory -Force | Where-Object Name -Like "*.tmp" | Measure-Object | Select-Object -ExpandProperty Count) 0 "A failed backup must remove its temporary file"

    $script:DumpExitCode = 0
    . (Join-Path $PSScriptRoot "postgres-backup.ps1") -OutputFile $backup
    Assert-Equal ([System.IO.File]::ReadAllText($backup)) "valid archive" "A successful backup must replace the destination"

    $script:RestoreCalls.Clear()
    $script:RestoreExitCodes.Enqueue(1)
    $restoreFailed = $false
    try {
        . (Join-Path $PSScriptRoot "postgres-restore.ps1") -BackupFile $backup -ConfirmRestore
    }
    catch {
        $restoreFailed = $true
    }
    Assert-Equal $restoreFailed $true "An invalid archive must fail restore"
    Assert-Equal $script:RestoreCalls.Count 1 "An invalid archive must not invoke destructive restore"

    $script:RestoreCalls.Clear()
    $script:RestoreExitCodes.Enqueue(0)
    $script:RestoreExitCodes.Enqueue(0)
    . (Join-Path $PSScriptRoot "postgres-restore.ps1") -BackupFile $backup -ConfirmRestore
    Assert-Equal $script:RestoreCalls.Count 2 "A valid archive must be inspected and then restored"
    Assert-Equal ($script:RestoreCalls[1] -match "--clean") $true "Restore must retain its explicit clean semantics"

    Write-Host "PostgreSQL backup and restore safety tests passed."
}
finally {
    if ($null -eq $previousDatabaseUrl) {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:DATABASE_URL = $previousDatabaseUrl
    }
    Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
}
