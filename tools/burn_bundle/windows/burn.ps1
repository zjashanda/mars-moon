param(
    [string]$FirmwareBin = "",
    [string]$CtrlPort = "COM15",
    [string]$BurnPort = "COM14",
    [int]$CtrlBaud = 115200,
    [int]$LogBaud = 115200,
    [int]$BurnBaud = 1500000,
    [int]$CmdDelayMs = 300,
    [int]$PreBurnWaitMs = 1500,
    [int]$PostPowerOnReadSeconds = 8,
    [int]$PostLoglevelReadSeconds = 3,
    [int]$MaxRetry = 3,
    [switch]$VerifyOnly,
    [switch]$SkipLoglevel
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($MaxRetry -lt 1) {
    $MaxRetry = 1
}

$script:Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:BurnTool = Join-Path $script:Root "Uart_Burn_Tool.exe"
$script:LogFile = Join-Path $script:Root "burn.log"
$script:ToolLog = Join-Path $script:Root "burn_tool.log"
[System.IO.File]::WriteAllText($script:LogFile, "", [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText($script:ToolLog, "", [System.Text.Encoding]::UTF8)

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    [System.IO.File]::AppendAllText($script:LogFile, $line + [Environment]::NewLine, [System.Text.Encoding]::UTF8)
}

function Append-RawLog {
    param([string]$Text)
    if (-not [string]::IsNullOrEmpty($Text)) {
        [System.IO.File]::AppendAllText($script:LogFile, $Text, [System.Text.Encoding]::UTF8)
    }
}

function Append-LineToFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Line
    )
    [System.IO.File]::AppendAllText($Path, $Line + [Environment]::NewLine, [System.Text.Encoding]::UTF8)
}

function Get-AvailablePorts {
    [System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object
}

function Wait-Port {
    param(
        [Parameter(Mandatory = $true)][string]$PortName,
        [int]$Attempts = 20,
        [int]$DelayMs = 500
    )

    for ($i = 0; $i -lt $Attempts; $i++) {
        if ((Get-AvailablePorts) -contains $PortName) {
            Write-Log "Detected port $PortName"
            return
        }
        Start-Sleep -Milliseconds $DelayMs
    }

    throw "Timeout waiting for port $PortName"
}

function Open-Port {
    param(
        [Parameter(Mandatory = $true)][string]$PortName,
        [Parameter(Mandatory = $true)][int]$BaudRate,
        [int]$ReadTimeout = 200,
        [int]$WriteTimeout = 500
    )

    $port = [System.IO.Ports.SerialPort]::new(
        $PortName,
        $BaudRate,
        [System.IO.Ports.Parity]::None,
        8,
        [System.IO.Ports.StopBits]::One
    )
    $port.Encoding = [System.Text.Encoding]::ASCII
    $port.NewLine = "`r`n"
    $port.ReadTimeout = $ReadTimeout
    $port.WriteTimeout = $WriteTimeout
    $port.Handshake = [System.IO.Ports.Handshake]::None
    $port.DtrEnable = $false
    $port.RtsEnable = $false
    $port.Open()
    return $port
}

function Invoke-CtrlSequence {
    param([Parameter(Mandatory = $true)][string[]]$Commands)

    Wait-Port -PortName $CtrlPort
    $port = $null
    try {
        $port = Open-Port -PortName $CtrlPort -BaudRate $CtrlBaud
        Write-Log "Opened control port $CtrlPort"
        foreach ($cmd in $Commands) {
            Write-Log "Send control command -> $CtrlPort : $cmd"
            $port.WriteLine($cmd)
            $port.BaseStream.Flush()
            Start-Sleep -Milliseconds $CmdDelayMs
        }
    }
    finally {
        if ($port -and $port.IsOpen) {
            $port.Close()
            $port.Dispose()
            Write-Log "Closed control port $CtrlPort"
        }
    }
}

function Resolve-FirmwarePath {
    if ($VerifyOnly) {
        return ""
    }

    if (-not (Test-Path -LiteralPath $script:BurnTool)) {
        throw "Burn tool does not exist: $script:BurnTool"
    }

    if ($FirmwareBin) {
        $resolved = (Resolve-Path -LiteralPath $FirmwareBin).Path
        Write-Log "Use explicit firmware: $resolved"
        return $resolved
    }

    $defaultBin = Get-ChildItem -LiteralPath $script:Root -File -Filter *.bin | Sort-Object Name
    if ($defaultBin.Count -eq 1) {
        Write-Log "Use default firmware: $($defaultBin[0].FullName)"
        return $defaultBin[0].FullName
    }

    if ($defaultBin.Count -eq 0) {
        throw "No firmware bin found in $script:Root. Provide -FirmwareBin."
    }

    $names = ($defaultBin | ForEach-Object { $_.Name }) -join ", "
    throw "Multiple firmware bins found in $script:Root: $names. Provide -FirmwareBin."
}

function Enter-BurnReadyState {
    Write-Log "Prepare device for burn: power off -> boot on -> power on -> boot off"
    Invoke-CtrlSequence -Commands @(
        "uut-switch1.off",
        "uut-switch2.on",
        "uut-switch1.on",
        "uut-switch2.off"
    )
    Start-Sleep -Milliseconds $PreBurnWaitMs
}

function Restore-NormalPower {
    Write-Log "Restore normal boot: power off -> boot off -> power on"
    Invoke-CtrlSequence -Commands @(
        "uut-switch1.off",
        "uut-switch2.off",
        "uut-switch1.on"
    )
}

function Recover-AfterFailure {
    try {
        Write-Log "Recover after failed attempt"
        Invoke-CtrlSequence -Commands @(
            "uut-switch1.off",
            "uut-switch2.off"
        )
    }
    catch {
        Write-Log "Recovery sequence also failed: $($_.Exception.Message)"
    }
}

function Test-BurnSuccess {
    param(
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [int]$ExitCode
    )

    $markers = @(
        "CONNECT ROM AND DOWNLOAD RAM LOADER SUCCESS",
        "SEND MD5 COMMAND WITH RAM SUCCESS",
        "SEND END COMMAND SUCCESS"
    )

    if ($ExitCode -ne 0) {
        Write-Log "Burn tool returned non-zero exit code: $ExitCode"
        return $false
    }

    $content = if (Test-Path -LiteralPath $OutputPath) {
        Get-Content -LiteralPath $OutputPath -Raw -Encoding UTF8
    }
    else {
        ""
    }

    foreach ($marker in $markers) {
        if ($content -notmatch [Regex]::Escape($marker)) {
            Write-Log "Missing success marker: $marker"
            return $false
        }
    }

    return $true
}

function Invoke-BurnTool {
    param([Parameter(Mandatory = $true)][string]$FwPath)

    Wait-Port -PortName $BurnPort
    if (Test-Path -LiteralPath $script:ToolLog) {
        Remove-Item -LiteralPath $script:ToolLog -Force
    }

    $args = @(
        "-b", "$BurnBaud",
        "-p", "$BurnPort",
        "-f", "$FwPath",
        "-m",
        "-d",
        "-a", "0x0",
        "-i", "adaptive-duplex",
        "-s"
    )

    Write-Log ("Run burn tool: {0} {1}" -f $script:BurnTool, ($args -join " "))
    $output = & $script:BurnTool @args 2>&1
    $exitCode = $LASTEXITCODE

    foreach ($item in $output) {
        $line = [string]$item
        if ([string]::IsNullOrEmpty($line)) {
            continue
        }
        Write-Host $line
        Append-LineToFile -Path $script:ToolLog -Line $line
        Append-LineToFile -Path $script:LogFile -Line $line
    }

    if (-not (Test-BurnSuccess -OutputPath $script:ToolLog -ExitCode $exitCode)) {
        throw "Burn tool failed. Check $script:ToolLog and $script:LogFile"
    }

    Write-Log "Burn tool reported success"
}

function Capture-SerialWindow {
    param(
        [Parameter(Mandatory = $true)][System.IO.Ports.SerialPort]$Port,
        [Parameter(Mandatory = $true)][int]$Seconds,
        [Parameter(Mandatory = $true)][System.Text.StringBuilder]$Buffer
    )

    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        $chunk = $Port.ReadExisting()
        if (-not [string]::IsNullOrEmpty($chunk)) {
            $null = $Buffer.Append($chunk)
            Append-RawLog $chunk
        }
        Start-Sleep -Milliseconds 100
    }
}

function Test-BootLogObserved {
    param([Parameter(Mandatory = $true)][string]$SerialText)

    $lines = $SerialText -split "(`r`n|`n|`r)" | ForEach-Object { $_.Trim() } | Where-Object {
        $_ -and $_ -ne "loglevel 4"
    }

    if (-not $lines) {
        return $false
    }

    return $true
}

function Verify-SerialAfterBurn {
    Wait-Port -PortName $BurnPort
    $port = $null
    $buffer = [System.Text.StringBuilder]::new()

    try {
        $port = Open-Port -PortName $BurnPort -BaudRate $LogBaud
        Write-Log "Opened burn/log port $BurnPort for final power-on verification"
        $port.DiscardInBuffer()
        Write-Log "----- device serial capture begin -----"
        Restore-NormalPower
        Capture-SerialWindow -Port $port -Seconds $PostPowerOnReadSeconds -Buffer $buffer

        if (-not $SkipLoglevel) {
            Write-Log "Send loglevel 4 to $BurnPort"
            $port.WriteLine("loglevel 4")
            $port.BaseStream.Flush()
            Capture-SerialWindow -Port $port -Seconds $PostLoglevelReadSeconds -Buffer $buffer
        }

        Write-Log "----- device serial capture end -----"
    }
    finally {
        if ($port -and $port.IsOpen) {
            $port.Close()
            $port.Dispose()
            Write-Log "Closed burn/log port $BurnPort"
        }
    }

    $serialText = $buffer.ToString()
    if (-not (Test-BootLogObserved -SerialText $serialText)) {
        throw "No boot log observed on $BurnPort after final power on"
    }

    $markers = @("VER:", "SDK:", "version", "volume", "work mode", "curtain", "root:/", "reset=")
    $matched = $markers | Where-Object { $serialText.IndexOf($_, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 } | Select-Object -First 1
    if ($matched) {
        Write-Log "Observed boot marker on ${BurnPort}: $matched"
    }
    else {
        Write-Log "Observed serial output on $BurnPort after final power on"
    }
}

$fwPath = Resolve-FirmwarePath
Write-Log "========== burn flow start =========="
Write-Log "CtrlPort=$CtrlPort CtrlBaud=$CtrlBaud BurnPort=$BurnPort LogBaud=$LogBaud BurnBaud=$BurnBaud VerifyOnly=$VerifyOnly"

if ($VerifyOnly) {
    Verify-SerialAfterBurn
    Write-Log "Verification-only flow completed"
    exit 0
}

$attempt = 0
while ($attempt -lt $MaxRetry) {
    $attempt++
    try {
        Write-Log "Burn attempt $attempt/$MaxRetry"
        Enter-BurnReadyState
        Invoke-BurnTool -FwPath $fwPath
        Verify-SerialAfterBurn
        Write-Log "Burn flow completed"
        exit 0
    }
    catch {
        Write-Log "Attempt failed: $($_.Exception.Message)"
        if ($attempt -ge $MaxRetry) {
            Write-Log "Burn flow failed"
            exit 1
        }
        Recover-AfterFailure
        Start-Sleep -Seconds 2
    }
}

Write-Log "Burn flow failed"
exit 1
