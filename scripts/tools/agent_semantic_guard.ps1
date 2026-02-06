param(
  [Parameter(Mandatory = $true)][string]$Task,
  [string]$RepoRoot = ".",
  [string]$PolicyPath = "scripts/config/agent/agent_workflow_policy.json",
  [string[]]$ChangedPaths,
  [string]$OutputPath,
  [switch]$Help
)

if ($Help) {
  @"
NAME
  agent_semantic_guard.ps1

SYNOPSIS
  Runs semantic workflow review using a Codex subprocess and writes a JSON artifact.

USAGE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\tools\agent_semantic_guard.ps1 -Task "fix login flow"
"@ | Write-Host
  return
}

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RepoRoot)) {
  throw "RepoRoot not found: $RepoRoot"
}
$resolvedRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$resolvedPolicyPath = Join-Path $resolvedRoot $PolicyPath
if (-not (Test-Path -LiteralPath $resolvedPolicyPath)) {
  throw "Policy file not found: $resolvedPolicyPath"
}

$policy = Get-Content -LiteralPath $resolvedPolicyPath -Raw | ConvertFrom-Json
$semantic = $policy.semanticReview
if (-not $semantic.enabled) {
  $result = [pscustomobject]@{
    Status = "SKIPPED"
    Engine = "disabled"
    Summary = "Semantic review disabled by policy."
    Findings = @()
    GeneratedAt = (Get-Date).ToString("o")
  }
  if (-not $OutputPath) {
    $outDir = Join-Path $resolvedRoot "logs/agent/guard"
    if (-not (Test-Path -LiteralPath $outDir)) { $null = New-Item -ItemType Directory -Path $outDir -Force }
    $OutputPath = Join-Path $outDir ("semantic_{0}.json" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
  }
  $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding ascii
  Write-Host "Semantic artifact: $OutputPath"
  return
}

$codex = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codex) {
  throw "codex CLI not found on PATH."
}

if (-not $ChangedPaths -or $ChangedPaths.Count -eq 0) {
  $git = Get-Command git -ErrorAction SilentlyContinue
  if ($git) {
    try {
      $changed = git -C $resolvedRoot diff --name-only --cached
      if (-not $changed -or $changed.Count -eq 0) {
        $changed = git -C $resolvedRoot diff --name-only
      }
      $ChangedPaths = @($changed | Where-Object { $_ -and $_.Trim() -ne "" })
    } catch {
      $ChangedPaths = @()
    }
  } else {
    $ChangedPaths = @()
  }
}

$schemaPath = Join-Path $resolvedRoot $semantic.schemaPath
if (-not (Test-Path -LiteralPath $schemaPath)) {
  throw "Semantic schema not found: $schemaPath"
}

$timeoutSec = if ($semantic.timeoutSec) { [int]$semantic.timeoutSec } else { 180 }
$model = if ($semantic.model) { [string]$semantic.model } else { "" }
$maxFindings = if ($semantic.maxFindings) { [int]$semantic.maxFindings } else { 6 }

$changedText = if ($ChangedPaths -and $ChangedPaths.Count -gt 0) { ($ChangedPaths -join "`n") } else { "<none>" }

$prompt = @"
You are a workflow compliance reviewer.

Goal:
- Review workflow/process risk for this task.
- Focus on scope drift, missing spec updates, missing verification evidence, and unsafe operational behavior.
- Do not invent repository facts; if uncertain, report uncertainty.

Task:
$Task

Changed paths:
$changedText

Instructions:
- Return strictly valid JSON per the provided schema.
- Keep findings concise and actionable.
- At most $maxFindings findings.
"@

$tmpOut = [System.IO.Path]::GetTempFileName()
$tmpErr = [System.IO.Path]::GetTempFileName()

$args = @(
  "exec",
  "--skip-git-repo-check",
  "--sandbox", "read-only",
  "-C", $resolvedRoot,
  "--output-schema", $schemaPath,
  "-o", $tmpOut,
  "-"
)
if ($model) {
  $args = @("exec", "--skip-git-repo-check", "--sandbox", "read-only", "-C", $resolvedRoot, "-m", $model, "--output-schema", $schemaPath, "-o", $tmpOut, "-")
}

try {
  $oldEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $prompt | & $codex.Source @args 2> $tmpErr | Out-Null
  } finally {
    $ErrorActionPreference = $oldEap
  }
  if ($LASTEXITCODE -ne 0) {
    $errText = ""
    if (Test-Path -LiteralPath $tmpErr) { $errText = (Get-Content -LiteralPath $tmpErr -Raw) }
    throw "codex exec failed (exit $LASTEXITCODE). $errText"
  }

  if (-not (Test-Path -LiteralPath $tmpOut)) {
    throw "Semantic output file missing: $tmpOut"
  }

  $semanticRaw = Get-Content -LiteralPath $tmpOut -Raw
  $semanticJson = $semanticRaw | ConvertFrom-Json
  $findings = @()
  if ($semanticJson.findings) {
    $findings = @($semanticJson.findings)
  }

  $result = [pscustomobject]@{
    Status = if ($findings.Count -gt 0) { "WARN" } else { "PASS" }
    Engine = "codex_subprocess"
    Model = if ($model) { $model } else { $null }
    Summary = $semanticJson.summary
    Findings = $findings
    ChangedPaths = @($ChangedPaths)
    GeneratedAt = (Get-Date).ToString("o")
  }

  if (-not $OutputPath) {
    $outDir = Join-Path $resolvedRoot "logs/agent/guard"
    if (-not (Test-Path -LiteralPath $outDir)) { $null = New-Item -ItemType Directory -Path $outDir -Force }
    $OutputPath = Join-Path $outDir ("semantic_{0}.json" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
  } else {
    $parent = Split-Path -Path $OutputPath -Parent
    if ($parent -and -not (Test-Path -LiteralPath $parent)) { $null = New-Item -ItemType Directory -Path $parent -Force }
  }

  $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding ascii
  Write-Host "Semantic artifact: $OutputPath"
} finally {
  if (Test-Path -LiteralPath $tmpOut) { Remove-Item -LiteralPath $tmpOut -Force -ErrorAction SilentlyContinue }
  if (Test-Path -LiteralPath $tmpErr) { Remove-Item -LiteralPath $tmpErr -Force -ErrorAction SilentlyContinue }
}
