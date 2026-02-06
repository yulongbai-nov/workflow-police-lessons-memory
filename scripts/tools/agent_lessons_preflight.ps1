param(
  [Parameter(Mandatory = $true)][string]$Task,
  [string]$LessonsPath = "LESSONS.md",
  [int]$Top = 5,
  [switch]$Help
)

if ($Help) {
  @"
NAME
  agent_lessons_preflight.ps1

SYNOPSIS
  Selects task-relevant lessons and writes a preflight artifact.
"@ | Write-Host
  return
}

$ErrorActionPreference = "Stop"

function Get-Tokens {
  param([string]$Text)
  if (-not $Text) { return @() }
  return @(
    ($Text.ToLowerInvariant() -split '[\s\.,;:!\?\-_/\\]+') |
      Where-Object { $_.Length -ge 4 } |
      Sort-Object -Unique
  )
}

$tokens = Get-Tokens -Text $Task
$matches = @()

if (Test-Path -LiteralPath $LessonsPath) {
  $headings = Select-String -Path $LessonsPath -Pattern '^##\s+' | ForEach-Object { ($_ -replace '^##\s+', '').Trim() }
  foreach ($h in $headings) {
    $score = 0
    $lh = $h.ToLowerInvariant()
    foreach ($t in $tokens) {
      if ($lh.Contains($t)) { $score++ }
    }
    if ($score -gt 0) {
      $matches += [pscustomobject]@{
        Heading = $h
        Score = $score
      }
    }
  }
}

$matches = @($matches | Sort-Object -Property Score, Heading -Descending | Select-Object -First $Top)

$outDir = Join-Path (Get-Location).Path "logs/agent/preflight"
if (-not (Test-Path -LiteralPath $outDir)) { $null = New-Item -ItemType Directory -Path $outDir -Force }
$outPath = Join-Path $outDir ("preflight_{0}.json" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

$out = [pscustomobject]@{
  Task = $Task
  LessonsPath = $LessonsPath
  MatchCount = @($matches).Count
  Matches = @($matches)
  GeneratedAt = (Get-Date).ToString("o")
}
$out | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outPath -Encoding ascii

Write-Host "Preflight artifact: $outPath"
if ($matches.Count -eq 0) {
  Write-Host "No matching lesson headings."
} else {
  Write-Host "Matched lesson headings:"
  $matches | ForEach-Object { Write-Host "- $($_.Heading)" }
}
