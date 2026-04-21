[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ForwardArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Set-DotEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [string]$Value
    )

    if (-not [string]::IsNullOrWhiteSpace($Name)) {
        [Environment]::SetEnvironmentVariable($Name, $Value, "Process")
    }
}

function Import-DotEnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing .env file: $Path"
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $separatorIndex = $trimmed.IndexOf("=")
        if ($separatorIndex -lt 1) {
            continue
        }

        $name = $trimmed.Substring(0, $separatorIndex).Trim()
        $value = $trimmed.Substring($separatorIndex + 1).Trim()

        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        Set-DotEnvValue -Name $name -Value $value
    }
}

function Get-RequiredEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Required environment variable is missing: $Name"
    }

    return $value
}

function Get-OptionalEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [string]$Default = ""
    )

    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $Default
    }

    return $value
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$dotenvPath = Join-Path $repoRoot ".env"

Import-DotEnvFile -Path $dotenvPath

$postgresHost = Get-OptionalEnvValue -Name "POSTGRES_HOST" -Default "10.2.3.22"
$postgresPort = Get-OptionalEnvValue -Name "POSTGRES_PORT" -Default "5432"
$postgresUser = Get-RequiredEnvValue -Name "POSTGRES_USER"
$postgresPassword = Get-RequiredEnvValue -Name "POSTGRES_PASSWORD"
$postgresDatabase = Get-OptionalEnvValue -Name "POSTGRES_DATABASE" -Default "master"

$encodedUser = [System.Uri]::EscapeDataString($postgresUser)
$encodedPassword = [System.Uri]::EscapeDataString($postgresPassword)
$encodedDatabase = [System.Uri]::EscapeDataString($postgresDatabase)

$connectionString = "postgresql://${encodedUser}:${encodedPassword}@${postgresHost}:${postgresPort}/${encodedDatabase}"

$npxArgs = @("-y", "@modelcontextprotocol/server-postgres", $connectionString)
if ($ForwardArgs) {
    $npxArgs += $ForwardArgs
}

& npx @npxArgs
