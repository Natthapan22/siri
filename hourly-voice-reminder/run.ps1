# Auto-find or install Python, then run main.py (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root
$Log = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $Log | Out-Null
$LogFile = Join-Path $Log "launch.log"

function Write-Log([string]$Msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

function Show-Msg([string]$Msg, [string]$Icon = "Information") {
    try {
        Add-Type -AssemblyName PresentationFramework -ErrorAction SilentlyContinue
        [System.Windows.MessageBox]::Show($Msg, "Hourly Voice Reminder", "OK", $Icon) | Out-Null
    } catch {
        Write-Host $Msg
    }
}

function Test-PythonTk([string]$Exe) {
    if (-not $Exe -or -not (Test-Path -LiteralPath $Exe)) { return $false }
    if ($Exe -like "*\WindowsApps\*") { return $false }
    try {
        $p = Start-Process -FilePath $Exe -ArgumentList @("-c", "import sys") `
            -Wait -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput "$env:TEMP\hvr-out.txt" `
            -RedirectStandardError "$env:TEMP\hvr-err.txt"
        return ($p.ExitCode -eq 0)
    } catch {
        return $false
    }
}

function Find-Python {
    $candidates = New-Object System.Collections.Generic.List[string]
    $prog = "$env:LocalAppData\Programs\Python"
    if (Test-Path -LiteralPath $prog) {
        Get-ChildItem -LiteralPath $prog -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $candidates.Add((Join-Path $_.FullName "pythonw.exe"))
            $candidates.Add((Join-Path $_.FullName "python.exe"))
        }
    }
    foreach ($v in @("Python313", "Python312", "Python311", "Python310")) {
        $candidates.Add("$env:LocalAppData\Programs\Python\$v\pythonw.exe")
        $candidates.Add("$env:LocalAppData\Programs\Python\$v\python.exe")
        $candidates.Add("${env:ProgramFiles}\Python\$v\python.exe")
    }
    foreach ($cmd in @("pythonw", "python")) {
        $c = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($c -and $c.Source -and ($c.Source -notlike "*\WindowsApps\*")) {
            $candidates.Add($c.Source)
        }
    }
    foreach ($p in $candidates) {
        if (Test-PythonTk $p) { return $p }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            $resolved = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($resolved) {
                $exe = ($resolved | Select-Object -First 1).ToString().Trim()
                if ($exe -and (Test-PythonTk $exe)) { return $exe }
            }
        } catch {}
    }
    return $null
}

function Install-Python {
    $ver = "3.12.7"
    $name = "python-$ver-amd64.exe"
    $url = "https://www.python.org/ftp/python/$ver/$name"
    $tmp = Join-Path $env:TEMP $name

    Show-Msg "ไม่พบ Python — จะติดตั้งให้อัตโนมัติ (ครั้งแรก 1-3 นาที ต้องมีเน็ต)"

    Write-Log "Downloading $url"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
    } catch {
        Show-Msg "ดาวน์โหลด Python ไม่สำเร็จ:`n$($_.Exception.Message)" "Error"
        exit 1
    }

    Write-Log "Installing silently"
    $args = @(
        "/quiet", "InstallAllUsers=0", "PrependPath=1",
        "Include_tcltk=1", "Include_pip=1", "Include_test=0",
        "Include_doc=0", "Include_launcher=1", "AssociateFiles=0", "Shortcuts=0"
    )
    $p = Start-Process -FilePath $tmp -ArgumentList $args -Wait -PassThru
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue

    if ($null -eq $p -or $p.ExitCode -ne 0) {
        $code = if ($p) { $p.ExitCode } else { "?" }
        Show-Msg "ติดตั้ง Python ไม่สำเร็จ (exit $code)`nลองติดตั้งเองจาก python.org แล้วติ๊ก Add to PATH" "Error"
        exit 1
    }

    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
    Start-Sleep -Seconds 2
}

# --- main ---
try {
    $main = Join-Path $Root "main.py"
    if (-not (Test-Path -LiteralPath $main)) {
        Show-Msg "ไม่พบ main.py ในโฟลเดอร์นี้" "Error"
        exit 1
    }

    # Prefer ready-made exe
    foreach ($exeName in @("HourlyVoiceReminder.exe", "dist\HourlyVoiceReminder.exe")) {
        $exePath = Join-Path $Root $exeName
        if (Test-Path -LiteralPath $exePath) {
            Write-Log "Starting exe $exePath"
            Start-Process -FilePath $exePath -WorkingDirectory $Root
            exit 0
        }
    }

    $python = Find-Python
    if (-not $python) {
        Install-Python
        $python = Find-Python
    }
    if (-not $python) {
        Show-Msg "ติดตั้งแล้วแต่ยังหา Python ไม่เจอ — ลองปิดแล้วเปิด เปิดแอป.bat ใหม่ หรือรีสตาร์ทเครื่อง" "Warning"
        exit 1
    }

    $dir = [IO.Path]::GetDirectoryName($python)
    $pythonw = Join-Path $dir "pythonw.exe"
    if ((Test-Path -LiteralPath $pythonw) -and (Test-PythonTk $pythonw)) {
        $python = $pythonw
    }

    Write-Log "Starting $python $main"
    Start-Process -FilePath $python -ArgumentList @($main) -WorkingDirectory $Root
    exit 0
} catch {
    Write-Log $_.Exception.Message
    Show-Msg "เกิดข้อผิดพลาด:`n$($_.Exception.Message)" "Error"
    exit 1
}
