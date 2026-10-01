param(
    [ValidateRange(10, 3600)]
    [int]$IntervalSeconds = 60
)

$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'RDP Keepalive - close this window to stop'
$keyboard = New-Object -ComObject WScript.Shell

Write-Host 'RDP Keepalive is running. Sends F15 once per interval.'
Write-Host "Interval: $IntervalSeconds seconds."
Write-Host 'Close this window or press Ctrl+C to stop.'
Write-Host 'Run inside the remote Windows desktop session.'

try {
    while ($true) {
        $keyboard.SendKeys('{F15}')
        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($keyboard)
}
