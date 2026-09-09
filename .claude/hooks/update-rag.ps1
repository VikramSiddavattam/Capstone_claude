#Requires -Version 5.1
# PostToolUse hook: updates rag/project-intelligence.md after changes to
# documents/*.md, src/**, or README.md

# Read tool event from stdin
$jsonInput = [Console]::In.ReadToEnd()
if (-not $jsonInput.Trim()) { exit 0 }

try {
    $event = $jsonInput | ConvertFrom-Json
} catch {
    exit 0
}

$filePath = $event.tool_input.file_path
if (-not $filePath) { exit 0 }

# Normalize path separators for matching
$normalized = $filePath -replace '\\', '/'

# Only trigger for watched paths
$isWatched = ($normalized -match '(^|[/\\])documents[/\\]') -or
             ($normalized -match '(^|[/\\])src[/\\]') -or
             ($normalized -match '(^|[/\\])README\.md$')

if (-not $isWatched) { exit 0 }

# Locate repo root (.claude/hooks/ -> .claude/ -> repo root)
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ragFile  = Join-Path $repoRoot "rag\project-intelligence.md"

if (-not (Test-Path $ragFile)) { exit 0 }

# ---- Build Source Code Map ----
$srcDir = Join-Path $repoRoot "src"
if (Test-Path $srcDir) {
    $srcFiles = Get-ChildItem -Path $srcDir -Recurse -File |
        Where-Object {
            $_.Extension -in @('.py', '.html', '.js', '.ts', '.css') -and
            $_.FullName -notmatch '__pycache__' -and
            $_.FullName -notmatch '\.pyc$'
        } |
        Sort-Object FullName |
        ForEach-Object { $_.FullName.Replace($repoRoot + '\', '').Replace('\', '/') }
    $srcMapContent = ($srcFiles -join "`n").Trim()
} else {
    $srcMapContent = "(src/ not found)"
}

# ---- Build SDLC Sync Notes ----
$artifacts = @(
    "requirements.md",
    "design-document.md",
    "design-review.md",
    "implementation-plan.md",
    "implementation-summary.md",
    "code-review.md",
    "qa-report.md",
    "pull-request.md"
)
$docsDir   = Join-Path $repoRoot "documents"
$syncLines = foreach ($artifact in $artifacts) {
    $artifactPath = Join-Path $docsDir $artifact
    if (Test-Path $artifactPath) {
        $ts = (Get-Item $artifactPath).LastWriteTime.ToString("yyyy-MM-dd HH:mm")
        "- documents/$artifact - exists (updated $ts)"
    } else {
        "- documents/$artifact - not yet generated"
    }
}
$syncContent = ($syncLines -join "`n").Trim()

# ---- Patch the RAG file ----
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$content   = Get-Content $ragFile -Raw -Encoding UTF8

# Update Last Sync timestamp
$content = $content -replace 'Last Sync: .*', "Last Sync: $timestamp"

# Update Source Code Map section (between markers)
$content = $content -replace '(?s)(<!-- BEGIN:source-code-map -->)\r?\n.*?\r?\n(<!-- END:source-code-map -->)', "`$1`n$srcMapContent`n`$2"

# Update SDLC Sync Notes section (between markers)
$content = $content -replace '(?s)(<!-- BEGIN:sdlc-sync -->)\r?\n.*?\r?\n(<!-- END:sdlc-sync -->)', "`$1`n$syncContent`n`$2"

Set-Content $ragFile $content -NoNewline -Encoding UTF8

$trigger = ($normalized -split '/')[-1]
Write-Host "rag/project-intelligence.md updated (triggered by: $trigger)"
