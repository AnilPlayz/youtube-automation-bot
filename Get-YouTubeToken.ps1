# PowerShell YouTube OAuth2 Token Generator
# Native Windows - No Python or Node needed!

$ClientId = $env:YOUTUBE_CLIENT_ID
$ClientSecret = $env:YOUTUBE_CLIENT_SECRET
if (-not $ClientId) { $ClientId = Read-Host "Enter OAuth Client ID" }
if (-not $ClientSecret) { $ClientSecret = Read-Host "Enter OAuth Client Secret" }
$RedirectUri = "http://localhost:8080/"
$Scope = "https://www.googleapis.com/auth/youtube.upload"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   YOUTUBE 1-CLICK AUTOMATIC TOKEN GENERATOR" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting local authorization server on port 8080..." -ForegroundColor Yellow

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:8080/")

try {
    $listener.Start()
} catch {
    Write-Host "[ERROR] Could not bind to port 8080. Make sure nothing else is using port 8080." -ForegroundColor Red
    pause
    exit
}

$AuthUrl = "https://accounts.google.com/o/oauth2/v2/auth?client_id=$ClientId&redirect_uri=[System.Web.HttpUtility]::UrlEncode($RedirectUri)&response_type=code&scope=[System.Web.HttpUtility]::UrlEncode($Scope)&access_type=offline&prompt=consent&login_hint=unknown726boy@gmail.com"
$AuthUrl = "https://accounts.google.com/o/oauth2/v2/auth?client_id=$ClientId&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.upload&access_type=offline&prompt=consent&login_hint=unknown726boy@gmail.com"

Write-Host "Opening your browser for authorization..." -ForegroundColor Green
Start-Process $AuthUrl

Write-Host "Waiting for you to click 'Allow' in your browser..." -ForegroundColor Yellow
$context = $listener.GetContext()
$request = $context.Request
$response = $context.Response

$query = $request.Url.Query
$code = ""

if ($query -match "code=([^&]+)") {
    $code = [System.Uri]::UnescapeDataString($matches[1])
}

$responseHtml = "<html><body style='font-family:sans-serif; text-align:center; padding-top:50px;'><h1>Success!</h1><p>You can close this tab and return to the application window.</p></body></html>"
$buffer = [System.Text.Encoding]::UTF8.GetBytes($responseHtml)
$response.ContentLength64 = $buffer.Length
$response.OutputStream.Write($buffer, 0, $buffer.Length)
$response.OutputStream.Close()
$listener.Stop()

if ([string]::IsNullOrWhiteSpace($code)) {
    Write-Host "[ERROR] Authorization failed or denied by user." -ForegroundColor Red
    pause
    exit
}

Write-Host "Exchanging authorization code for Refresh Token..." -ForegroundColor Green

$tokenUrl = "https://oauth2.googleapis.com/token"
$body = @{
    code = $code
    client_id = $ClientId
    client_secret = $ClientSecret
    redirect_uri = $RedirectUri
    grant_type = "authorization_code"
}

try {
    $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
    $refreshToken = $tokenResponse.refresh_token

    if ($refreshToken) {
        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host "   AUTHORIZATION SUCCESSFUL!" -ForegroundColor Green
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "YOUR YOUTUBE REFRESH TOKEN IS:" -ForegroundColor Yellow
        Write-Host "$refreshToken" -ForegroundColor White
        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Green

        # Update .env
        $envPath = Join-Path $PSScriptRoot ".env"
        if (Test-Path $envPath) {
            $envContent = Get-Content $envPath -Raw
            $envContent = $envContent -replace "YOUTUBE_REFRESH_TOKEN=.*", "YOUTUBE_REFRESH_TOKEN=$refreshToken"
            Set-Content -Path $envPath -Value $envContent
            Write-Host "Saved automatically to .env!" -ForegroundColor Cyan
        }
    } else {
        Write-Host "Received Access Token, but Refresh Token was not returned." -ForegroundColor Yellow
        Write-Host "Full response: $($tokenResponse | ConvertTo-Json)" -ForegroundColor Gray
    }
} catch {
    Write-Host "[ERROR] Failed to exchange code: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
