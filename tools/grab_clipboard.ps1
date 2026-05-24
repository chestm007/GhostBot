# Extrai imagem do clipboard (apos Win+Shift+S) e salva como PNG.
# Uso: powershell -ExecutionPolicy Bypass -File tools\grab_clipboard.ps1
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$img = [System.Windows.Forms.Clipboard]::GetImage()
if ($null -eq $img) {
    Write-Host "ERRO: clipboard nao contem imagem. Use Win+Shift+S primeiro."
    exit 1
}
$path = "C:\Bot\BotTO\tmp_clipboard.png"
$img.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
$img.Dispose()
$kb = [math]::Round((Get-Item $path).Length / 1KB, 1)
Write-Host "OK -- imagem salva em $path ($kb KB)"
