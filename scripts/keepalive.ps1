param(
    [string]$Url = $env:RENDER_SERVICE_URL,
    [int]$Interval = 540
)

if (-not $Url) {
    Write-Host "Usage: .\scripts\keepalive.ps1 -Url 'https://kyoka-lavalink.onrender.com' -Interval 540" -ForegroundColor Yellow
    exit 1
}

python "$PSScriptRoot\keepalive.py" --url "$Url" --interval $Interval

