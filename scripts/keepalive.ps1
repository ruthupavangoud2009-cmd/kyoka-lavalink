param(
    [string]$Url = $env:RENDER_SERVICE_URL,
    [int]$Interval = 540,
    [string]$Password = $env:LAVALINK_SERVER_PASSWORD
)

if (-not $Url) {
    $Url = "https://kyoka-lavalink.onrender.com"
}

python "$PSScriptRoot\keepalive.py" --url "$Url" --interval $Interval --password "$Password"
