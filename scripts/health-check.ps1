param(
    [string]$Url = $env:RENDER_SERVICE_URL,
    [string]$Password = $env:LAVALINK_SERVER_PASSWORD
)

if (-not $Url) {
    $Url = "http://localhost:2333"
}
if (-not $Password) {
    $Password = "youshallnotpass"
}

python "$PSScriptRoot\health_check.py" --url "$Url" --password "$Password"

