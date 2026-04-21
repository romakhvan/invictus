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

$mongoUser = Get-RequiredEnvValue -Name "MONGO_USER_PROD"
$mongoPassword = Get-RequiredEnvValue -Name "MONGO_PASSWORD_PROD"
$mongoHosts = Get-RequiredEnvValue -Name "MONGO_HOSTS_PROD"
$mongoReplicaSet = Get-OptionalEnvValue -Name "MONGO_REPLICA_SET_PROD" -Default "rs0"
$mongoDbName = Get-OptionalEnvValue -Name "MONGO_DB_NAME_PROD" -Default "Cluster0"
$mongoAuthSource = Get-OptionalEnvValue -Name "MONGO_AUTH_SOURCE_PROD"

$connectionString = "mongodb://${mongoUser}:$mongoPassword@$mongoHosts/${mongoDbName}?replicaSet=${mongoReplicaSet}"
if (-not [string]::IsNullOrWhiteSpace($mongoAuthSource)) {
    $connectionString = "${connectionString}&authSource=${mongoAuthSource}"
}

[Environment]::SetEnvironmentVariable("MDB_MCP_CONNECTION_STRING", $connectionString, "Process")

$npxArgs = @("-y", "mongodb-mcp-server@latest", "--readOnly")
if ($ForwardArgs) {
    $npxArgs += $ForwardArgs
}

& npx @npxArgs
