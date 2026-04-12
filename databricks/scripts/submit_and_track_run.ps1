param(
    [string]$DatabricksHost = $env:DATABRICKS_HOST,
    [string]$DatabricksToken = $env:DATABRICKS_TOKEN,
    [string]$RunId,
    [string]$ExistingClusterId,
    [string]$NotebookBasePath = "/Shared/smartlive-databricks",
    [string]$InputPath = "dbfs:/FileStore/smartlive/raw/sync_records_sample.json",
    [string]$BronzeTable = "main.default.smartlive_sync_comments_bronze",
    [string]$SilverTable = "main.default.smartlive_sync_comments_silver",
    [string]$GoldTable = "main.default.smartlive_daily_metrics_gold",
    [string]$JobsApiVersion = "2.0",
    [int]$ShufflePartitions = 8,
    [int]$TargetPartitions = 8,
    [int]$PollSeconds = 10,
    [int]$MaxPolls = 90,
    [string]$RunName,
    [string]$OutputDir = "databricks/runs"
)

$ErrorActionPreference = "Stop"

function Require-Value {
    param(
        [string]$Value,
        [string]$Name
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "Missing required value: $Name"
    }

    return $Value
}

function Invoke-DatabricksApi {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null
    )

    $headers = @{
        Authorization = "Bearer $script:DatabricksToken"
    }
    $uri = "$script:DatabricksHost$Path"

    if ($null -eq $Body) {
        return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
    }

    $jsonBody = $Body | ConvertTo-Json -Depth 50
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -ContentType "application/json" -Body $jsonBody
}

function Is-TerminalState {
    param([string]$LifeCycleState)

    return @("TERMINATED", "SKIPPED", "INTERNAL_ERROR") -contains $LifeCycleState
}

function Get-TaskOutput {
    param([object]$TaskRun)

    if ($null -eq $TaskRun.run_id) {
        return $null
    }

    try {
        $output = Invoke-DatabricksApi -Method "GET" -Path "$script:JobsApiBasePath/runs/get-output?run_id=$($TaskRun.run_id)"
        if ($output.notebook_output.result) {
            try {
                return $output.notebook_output.result | ConvertFrom-Json -ErrorAction Stop
            }
            catch {
                return $output.notebook_output.result
            }
        }

        return $output
    }
    catch {
        return @{
            error = $_.Exception.Message
        }
    }
}

function Build-TaskSummary {
    param([object]$Status)

    $tasks = @()
    if ($null -eq $Status.tasks) {
        return $tasks
    }

    foreach ($task in @($Status.tasks)) {
        $tasks += [ordered]@{
            task_key = $task.task_key
            run_id = $task.run_id
            run_page_url = $task.run_page_url
            life_cycle_state = $task.state.life_cycle_state
            result_state = $task.state.result_state
            state_message = $task.state.state_message
            output = Get-TaskOutput -TaskRun $task
        }
    }

    return $tasks
}

function Write-LatestCopy {
    param(
        [string]$SourcePath,
        [string]$DestinationName
    )

    $destinationPath = Join-Path $script:OutputDirFullPath $DestinationName
    Copy-Item -LiteralPath $SourcePath -Destination $destinationPath -Force
}

$DatabricksHost = (Require-Value -Value $DatabricksHost -Name "DatabricksHost").TrimEnd("/")
$DatabricksToken = Require-Value -Value $DatabricksToken -Name "DatabricksToken"
$JobsApiVersion = Require-Value -Value $JobsApiVersion -Name "JobsApiVersion"
$JobsApiBasePath = "/api/$JobsApiVersion/jobs"

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $ExistingClusterId = Require-Value -Value $ExistingClusterId -Name "ExistingClusterId"
}

$templatePath = Join-Path $PSScriptRoot "..\submits\smartlive_comment_pipeline.submit.template.json"
$OutputDirFullPath = Join-Path (Get-Location) $OutputDir
New-Item -ItemType Directory -Force -Path $OutputDirFullPath > $null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$effectiveRunId = $RunId

if ([string]::IsNullOrWhiteSpace($effectiveRunId)) {
    $effectiveRunName = if ([string]::IsNullOrWhiteSpace($RunName)) {
        "smartlive-submit-$timestamp"
    }
    else {
        $RunName
    }

    $templateText = Get-Content -LiteralPath $templatePath -Raw
    $replacements = @{
        "__RUN_NAME__" = $effectiveRunName
        "__EXISTING_CLUSTER_ID__" = $ExistingClusterId
        "__WORKSPACE_NOTEBOOK_BASE__" = $NotebookBasePath.TrimEnd("/")
        "__INPUT_PATH__" = $InputPath
        "__BRONZE_TABLE__" = $BronzeTable
        "__SILVER_TABLE__" = $SilverTable
        "__GOLD_TABLE__" = $GoldTable
        "__SHUFFLE_PARTITIONS__" = [string]$ShufflePartitions
        "__TARGET_PARTITIONS__" = [string]$TargetPartitions
    }

    foreach ($placeholder in $replacements.Keys) {
        $templateText = $templateText.Replace($placeholder, $replacements[$placeholder])
    }

    $payload = $templateText | ConvertFrom-Json -Depth 50
    $submitResponse = Invoke-DatabricksApi -Method "POST" -Path "$JobsApiBasePath/runs/submit" -Body $payload
    $effectiveRunId = [string]$submitResponse.run_id

    $submitFile = Join-Path $OutputDirFullPath "${timestamp}-submit-response.json"
    ($submitResponse | ConvertTo-Json -Depth 50) | Set-Content -LiteralPath $submitFile -Encoding UTF8
    Write-LatestCopy -SourcePath $submitFile -DestinationName "latest-submit-response.json"
}

$status = $null
for ($attempt = 0; $attempt -lt $MaxPolls; $attempt++) {
    $status = Invoke-DatabricksApi -Method "GET" -Path "$JobsApiBasePath/runs/get?run_id=$effectiveRunId"
    if (Is-TerminalState -LifeCycleState $status.state.life_cycle_state) {
        break
    }

    Start-Sleep -Seconds $PollSeconds
}

$taskSummary = Build-TaskSummary -Status $status
$summary = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    tracked_via = "jobs/runs/submit"
    jobs_api_version = $JobsApiVersion
    run_id = $status.run_id
    run_name = $status.run_name
    run_page_url = $status.run_page_url
    life_cycle_state = $status.state.life_cycle_state
    result_state = $status.state.result_state
    state_message = $status.state.state_message
    number_in_job = $status.number_in_job
    start_time = $status.start_time
    end_time = $status.end_time
    tasks = $taskSummary
}

$statusFile = Join-Path $OutputDirFullPath "${timestamp}-run-status.json"
($summary | ConvertTo-Json -Depth 50) | Set-Content -LiteralPath $statusFile -Encoding UTF8
Write-LatestCopy -SourcePath $statusFile -DestinationName "latest-run-status.json"

$markdownLines = @(
    "# SmartLive Databricks Submit Summary",
    "",
    "- Generated at: $($summary.generated_at)",
    "- Run ID: $($summary.run_id)",
    "- Run name: $($summary.run_name)",
    "- Run URL: $($summary.run_page_url)",
    "- Life cycle state: $($summary.life_cycle_state)",
    "- Result state: $($summary.result_state)",
    "- Message: $($summary.state_message)",
    "",
    "## Tasks"
)

foreach ($task in $taskSummary) {
    $markdownLines += ""
    $markdownLines += "### $($task.task_key)"
    $markdownLines += "- Run ID: $($task.run_id)"
    $markdownLines += "- Run URL: $($task.run_page_url)"
    $markdownLines += "- Life cycle state: $($task.life_cycle_state)"
    $markdownLines += "- Result state: $($task.result_state)"
    $markdownLines += "- Message: $($task.state_message)"

    if ($null -ne $task.output) {
        $outputJson = $task.output | ConvertTo-Json -Depth 20
        $markdownLines += "- Output summary:"
        $markdownLines += '```json'
        $markdownLines += $outputJson
        $markdownLines += '```'
    }
}

$markdownFile = Join-Path $OutputDirFullPath "${timestamp}-run-summary.md"
$markdownLines | Set-Content -LiteralPath $markdownFile -Encoding UTF8
Write-LatestCopy -SourcePath $markdownFile -DestinationName "latest-run-summary.md"

Write-Output "Run ID: $($summary.run_id)"
Write-Output "Run URL: $($summary.run_page_url)"
Write-Output "Status JSON: $statusFile"
Write-Output "Summary MD: $markdownFile"
