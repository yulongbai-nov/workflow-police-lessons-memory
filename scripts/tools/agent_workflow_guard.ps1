param(
  [Parameter(Mandatory = $true)][string]$Task,
  [ValidateSet("warn", "block")][string]$Mode = "warn",
  [string]$RepoRoot = ".",
  [string]$PolicyPath = "scripts/config/agent/agent_workflow_policy.json",
  [string[]]$ChangedPaths,
  [switch]$SkipSemantic,
  [switch]$Help
)

if ($Help) {
  @"
NAME
  agent_workflow_guard.ps1

SYNOPSIS
  Runs deterministic workflow checks and optional semantic review, then writes guard artifact.

USAGE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\tools\agent_workflow_guard.ps1 -Task "update auth flow" -Mode warn
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
$detFindings = @()

function Add-DetFinding {
  param(
    [string]$Severity,
    [string]$Code,
    [string]$Message
  )
  $script:detFindings += [pscustomobject]@{
    Severity = $Severity
    Code = $Code
    Message = $Message
  }
}

if ($policy.requiredDocs) {
  foreach ($doc in @($policy.requiredDocs)) {
    $path = Join-Path $resolvedRoot $doc
    if (-not (Test-Path -LiteralPath $path)) {
      Add-DetFinding -Severity "high" -Code "missing-required-doc" -Message "Missing required doc/path: $doc"
    }
  }
}

if ($policy.deterministicChecks.requireSpecDocs) {
  $specRoot = if ($policy.specRoot) { [string]$policy.specRoot } else { ".specs" }
  if (-not (Test-Path -LiteralPath (Join-Path $resolvedRoot $specRoot))) {
    Add-DetFinding -Severity "medium" -Code "missing-spec-root" -Message "Spec root missing: $specRoot"
  } else {
    $specFiles = Get-ChildItem -Path (Join-Path $resolvedRoot $specRoot) -Recurse -File -Filter "*.md" -ErrorAction SilentlyContinue
    if (-not $specFiles -or $specFiles.Count -eq 0) {
      Add-DetFinding -Severity "medium" -Code "empty-spec-root" -Message "No spec markdown files found under $specRoot"
    }
  }
}

if ($policy.preflight.required -and $policy.deterministicChecks.requirePreflightArtifact) {
  $glob = if ($policy.preflight.artifactGlob) { [string]$policy.preflight.artifactGlob } else { "logs/agent/preflight/*.json" }
  $preflightPath = Join-Path $resolvedRoot ($glob -replace '/', '\')
  $matches = Get-ChildItem -Path $preflightPath -File -ErrorAction SilentlyContinue
  if (-not $matches -or $matches.Count -eq 0) {
    Add-DetFinding -Severity "medium" -Code "missing-preflight-artifact" -Message "No preflight artifact found matching: $glob"
  } else {
    $latest = $matches | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($policy.preflight.maxAgeHours) {
      $ageHours = ((Get-Date) - $latest.LastWriteTime).TotalHours
      if ($ageHours -gt [double]$policy.preflight.maxAgeHours) {
        Add-DetFinding -Severity "medium" -Code "stale-preflight-artifact" -Message ("Latest preflight artifact is stale ({0:N1}h old)." -f $ageHours)
      }
    }
  }
}

$semanticObj = [pscustomobject]@{
  Status = "SKIPPED"
  ArtifactPath = $null
  Findings = @()
}

if (-not $SkipSemantic -and $policy.semanticReview.enabled) {
  $semanticScript = Join-Path $resolvedRoot "scripts/tools/agent_semantic_guard.ps1"
  if (Test-Path -LiteralPath $semanticScript) {
    $semanticOutPath = Join-Path $resolvedRoot ("logs/agent/guard/semantic_{0}.json" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $semanticArgs = @{
      Task = $Task
      RepoRoot = $resolvedRoot
      PolicyPath = $PolicyPath
      OutputPath = $semanticOutPath
    }
    if ($ChangedPaths -and @($ChangedPaths).Count -gt 0) {
      $semanticArgs["ChangedPaths"] = @($ChangedPaths)
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $semanticScript @semanticArgs
    if ($LASTEXITCODE -ne 0) {
      Add-DetFinding -Severity "medium" -Code "semantic-run-failed" -Message "Semantic guard script exited non-zero."
      $semanticObj = [pscustomobject]@{
        Status = "ERROR"
        ArtifactPath = $semanticOutPath
        Findings = @()
      }
    } elseif (Test-Path -LiteralPath $semanticOutPath) {
      $sem = Get-Content -LiteralPath $semanticOutPath -Raw | ConvertFrom-Json
      $semFindings = @()
      if ($sem.Findings) { $semFindings = @($sem.Findings) }
      $semanticObj = [pscustomobject]@{
        Status = $sem.Status
        ArtifactPath = $semanticOutPath
        Findings = $semFindings
      }
    }
  } else {
    Add-DetFinding -Severity "medium" -Code "missing-semantic-script" -Message "Semantic script not found: scripts/tools/agent_semantic_guard.ps1"
  }
}

$blockSeverities = @()
if ($policy.semanticReview.blockOnSeverity) {
  $blockSeverities = @($policy.semanticReview.blockOnSeverity | ForEach-Object { $_.ToString().ToLowerInvariant() })
}

$semanticBlocking = $false
if ($blockSeverities.Count -gt 0 -and $semanticObj.Findings.Count -gt 0) {
  foreach ($f in @($semanticObj.Findings)) {
    $sev = ""
    if ($f.severity) { $sev = $f.severity.ToString().ToLowerInvariant() }
    if ($blockSeverities -contains $sev) { $semanticBlocking = $true; break }
  }
}

$detHigh = @($detFindings | Where-Object { $_.Severity -eq "high" }).Count
$detMedium = @($detFindings | Where-Object { $_.Severity -eq "medium" }).Count
$semanticCount = @($semanticObj.Findings).Count

$status = "PASS"
if ($detHigh -gt 0 -or $detMedium -gt 0 -or $semanticCount -gt 0) {
  $status = "WARN"
}
if ($Mode -eq "block") {
  if ($detHigh -gt 0 -or $semanticBlocking) {
    $status = "BLOCK"
  }
}

$guardDir = Join-Path $resolvedRoot "logs/agent/guard"
if (-not (Test-Path -LiteralPath $guardDir)) {
  $null = New-Item -ItemType Directory -Path $guardDir -Force
}
$artifactPath = Join-Path $guardDir ("guard_{0}.json" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

$result = [pscustomobject]@{
  Status = $status
  Mode = $Mode
  Task = $Task
  DeterministicFindings = @($detFindings)
  DeterministicSummary = [pscustomobject]@{
    High = $detHigh
    Medium = $detMedium
    Total = @($detFindings).Count
  }
  Semantic = $semanticObj
  GeneratedAt = (Get-Date).ToString("o")
}

$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $artifactPath -Encoding ascii

Write-Host "Guard artifact: $artifactPath"
Write-Host ("Guard status: {0} (det={1}, semantic={2})" -f $status, @($detFindings).Count, $semanticCount)

if ($status -eq "BLOCK") {
  exit 2
}
