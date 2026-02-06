param(
  [Parameter(Mandatory = $true)][string]$FeatureName,
  [string]$RepoRoot = ".",
  [string]$SpecRoot = ".specs",
  [switch]$Force,
  [switch]$Help
)

if ($Help) {
  @"
NAME
  init_feature_spec.ps1

SYNOPSIS
  Initializes design, requirements, and tasks documents for a feature.

USAGE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\tools\init_feature_spec.ps1 -FeatureName "my feature"
"@ | Write-Host
  return
}

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RepoRoot)) {
  throw "RepoRoot not found: $RepoRoot"
}

function Convert-ToSlug {
  param([string]$Name)
  $s = $Name.ToLowerInvariant()
  $s = [regex]::Replace($s, "[^a-z0-9]+", "-")
  $s = $s.Trim("-")
  if (-not $s) { $s = "feature" }
  return $s
}

function Write-IfMissing {
  param(
    [string]$Path,
    [string]$Content,
    [switch]$Overwrite
  )
  $parent = Split-Path -Path $Path -Parent
  if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    $null = New-Item -ItemType Directory -Path $parent -Force
  }

  if ((Test-Path -LiteralPath $Path) -and (-not $Overwrite)) {
    Write-Host "skip: $Path"
    return
  }
  Set-Content -LiteralPath $Path -Value $Content -Encoding ascii
  Write-Host "write: $Path"
}

$slug = Convert-ToSlug -Name $FeatureName
$specDir = Join-Path (Resolve-Path -LiteralPath $RepoRoot).Path (Join-Path $SpecRoot $slug)

$designPath = Join-Path $specDir "design.md"
$reqPath = Join-Path $specDir "requirements.md"
$tasksPath = Join-Path $specDir "tasks.md"

$designTemplate = @"
# Design Document: $FeatureName

## Overview

## Current Architecture

## Proposed Architecture

## Components

## Data and Control Flow

## Integration Points

## Migration and Rollout Strategy

## Performance, Reliability, Security, UX Considerations

## Risks and Mitigations

## Future Enhancements
"@

$reqTemplate = @"
# Requirements Document

## Introduction

## Glossary

## Requirements

### Requirement 1
**User Story:** As a <role>, I want <capability>, so that <value>.

#### Acceptance Criteria
1. THE SYSTEM SHALL ...
2. WHEN <condition>, THE SYSTEM SHALL ...
3. WHEN <event> OCCURS, THEN ...
"@

$tasksTemplate = @"
# Implementation Plan

- [ ] 1. Define implementation slices. _Requirements: 1_
- [ ] 2. Implement first slice. _Requirements: 1_
- [ ] 3. Validate and document outcomes. _Requirements: 1_

## Current Status Summary

- Active phase: design
- Next task: define implementation slices
"@

Write-IfMissing -Path $designPath -Content $designTemplate -Overwrite:$Force
Write-IfMissing -Path $reqPath -Content $reqTemplate -Overwrite:$Force
Write-IfMissing -Path $tasksPath -Content $tasksTemplate -Overwrite:$Force

Write-Host "Initialized spec at: $specDir"
