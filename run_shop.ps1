# run_shop.ps1
param(
    [Parameter(Mandatory=$true)][string]$NgrokAuthtoken
)

# Lưu authtoken (v3)
Write-Host "Saving ngrok authtoken..."
# Dùng `config add-authtoken` cho ngrok v3
.\ngrok.exe config add-authtoken $NgrokAuthtoken
if ($LASTEXITCODE -ne 0) {
    Write-Error "Lỗi khi lưu authtoken. Kiểm tra token và thử lại."
    exit 1
}

Write-Host "Authtoken saved. Starting ngrok tunnel (port 5000)..."

# Mở ngrok trong cửa sổ mới (không dùng -NoNewWindow vì conflict)
Start-Process -FilePath ".\ngrok.exe" -ArgumentList "http 5000" -WindowStyle Normal

# Đợi vài giây để ngrok khởi
Start-Sleep -Seconds 2

# Thử lấy forwarding url từ ngrok web UI
$attempt = 0
$forwardingUrl = $null
while ($attempt -lt 15 -and -not $forwardingUrl) {
    try {
        $api = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -UseBasicParsing -ErrorAction Stop
        if ($api.tunnels) {
            foreach ($t in $api.tunnels) {
                # ưu tiên URL https
                if ($t.public_url -and $t.public_url.StartsWith("https")) {
                    $forwardingUrl = $t.public_url
                    break
                }
                if (-not $forwardingUrl -and $t.public_url) {
                    $forwardingUrl = $t.public_url
                }
            }
        }
    } catch {
        # ngrok web ui chưa sẵn sàng, chờ thêm
    }
    if (-not $forwardingUrl) {
        Start-Sleep -Seconds 1
        $attempt++
    }
}

if (-not $forwardingUrl) {
    Write-Error "Không lấy được ngrok forwarding url sau 15 giây. Mở http://127.0.0.1:4040 để kiểm tra."
    exit 1
}

Write-Host "Ngrok forwarding url: $forwardingUrl"

# Chuẩn bị PUBLIC_BASE_URL và chạy Flask trong cửa sổ mới
$pub = $forwardingUrl.TrimEnd('/') + "/"
$pwd = (Get-Location).Path

Write-Host "Starting Flask with PUBLIC_BASE_URL = $pub"

$psCommand = @"
cd `"$pwd`"
`$env:PUBLIC_BASE_URL = `"$pub`"
`$env:SECRET_KEY = `"dev-secret-key-change-me`"
# nếu bạn muốn override payOS keys, uncomment và sửa ở đây:
# `$env:PAYOS_CLIENT_ID = `"..."`"
# `$env:PAYOS_API_KEY = `"..."`"
# `$env:PAYOS_CHECKSUM_KEY = `"..."`"
python app.py
"@

# Mở cửa sổ PowerShell mới để hiển thị log Flask (không đóng)
Start-Process powershell -ArgumentList "-NoExit","-Command",$psCommand -WindowStyle Normal

Write-Host "Hoàn tất. Ngrok public URL: $pub"