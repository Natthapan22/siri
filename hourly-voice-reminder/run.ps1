# Hourly Voice Reminder — Windows one-click: install Python if needed → open UI
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

$PythonVersion = "3.12.7"
$InstallerName = "python-$PythonVersion-amd64.exe"
$InstallerUrl = "https://www.python.org/ftp/python/$PythonVersion/$InstallerName"
$ExpectedPython = "$env:LocalAppData\Programs\Python\Python312\pythonw.exe"

$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir "launch.log"
$BootFile = Join-Path $LogDir "ui-boot.txt"

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
        $p = Start-Process -FilePath $Exe -ArgumentList @(
            "-c", "import tkinter; tkinter.Tk().destroy()"
        ) -Wait -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput "$env:TEMP\hvr-out.txt" `
            -RedirectStandardError "$env:TEMP\hvr-err.txt"
        return ($p.ExitCode -eq 0)
    } catch {
        return $false
    }
}

function Get-PythonCandidates {
    $list = New-Object System.Collections.Generic.List[string]
    $list.Add($ExpectedPython)
    $list.Add("$env:LocalAppData\Programs\Python\Python312\python.exe")
    $list.Add("$env:LocalAppData\Programs\Python\Python313\pythonw.exe")
    $list.Add("$env:LocalAppData\Programs\Python\Python313\python.exe")
    $list.Add("$env:LocalAppData\Programs\Python\Python311\pythonw.exe")
    $list.Add("$env:LocalAppData\Programs\Python\Python311\python.exe")
    $prog = "$env:LocalAppData\Programs\Python"
    if (Test-Path -LiteralPath $prog) {
        Get-ChildItem -LiteralPath $prog -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $list.Add((Join-Path $_.FullName "pythonw.exe"))
            $list.Add((Join-Path $_.FullName "python.exe"))
        }
    }
    foreach ($cmd in @("pythonw", "python")) {
        $c = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($c -and $c.Source -and ($c.Source -notlike "*\WindowsApps\*")) {
            $list.Add($c.Source)
        }
    }
    return $list
}

function Find-Python {
    foreach ($p in (Get-PythonCandidates)) {
        if (Test-PythonTk $p) { return $p }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            $resolved = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($resolved) {
                $exe = ($resolved | Select-Object -First 1).ToString().Trim()
                $dir = [IO.Path]::GetDirectoryName($exe)
                foreach ($name in @("pythonw.exe", "python.exe")) {
                    $candidate = Join-Path $dir $name
                    if (Test-PythonTk $candidate) { return $candidate }
                }
            }
        } catch {}
    }
    return $null
}

function Install-Python {
    Write-Log "Step 2: Installing Python $PythonVersion"
    Show-Msg @"
ขั้นที่ 1/2 — ติดตั้ง Python $PythonVersion

เครื่องนี้ยังไม่มี Python สำหรับเปิดหน้าต่าง UI
จะดาวน์โหลดและติดตั้งให้อัตโนมัติ

• ใช้เวลาประมาณ 1–3 นาที
• ต้องมีอินเทอร์เน็ต
• กด OK แล้วรอจนเสร็จ
"@

    $tmp = Join-Path $env:TEMP $InstallerName
    Write-Log "Downloading $InstallerUrl"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $InstallerUrl -OutFile $tmp -UseBasicParsing
    } catch {
        Show-Msg "ดาวน์โหลด Python ไม่สำเร็จ:`n$($_.Exception.Message)`n`nติดตั้งเอง:`n$InstallerUrl" "Error"
        exit 1
    }

    Write-Log "Running installer silently"
    $argList = @(
        "/quiet",
        "InstallAllUsers=0",
        "PrependPath=1",
        "Include_tcltk=1",
        "Include_pip=1",
        "Include_test=0",
        "Include_doc=0",
        "Include_launcher=1",
        "AssociateFiles=0",
        "Shortcuts=0"
    )
    $p = Start-Process -FilePath $tmp -ArgumentList $argList -Wait -PassThru
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue

    if ($null -eq $p -or $p.ExitCode -ne 0) {
        $code = if ($p) { $p.ExitCode } else { "?" }
        Show-Msg "ติดตั้ง Python ไม่สำเร็จ (exit $code)`n`nติดตั้งเอง:`n$InstallerUrl`nติ๊ก Add to PATH + tcl/tk" "Error"
        exit 1
    }

    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
    Start-Sleep -Seconds 4
    Write-Log "Python install finished"
}

function Start-Ui([string]$PythonExe) {
    $main = Join-Path $Root "main.py"
    Remove-Item -LiteralPath $BootFile -Force -ErrorAction SilentlyContinue
    Write-Log "Step 3: Starting UI with $PythonExe"
    $proc = Start-Process -FilePath $PythonExe -ArgumentList @($main) -WorkingDirectory $Root -PassThru
    if (-not $proc) {
        Show-Msg "เปิด UI ไม่สำเร็จ" "Error"
        exit 1
    }

    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 400
        if (Test-Path -LiteralPath $BootFile) {
            $txt = Get-Content -LiteralPath $BootFile -Raw -ErrorAction SilentlyContinue
            if ($txt -match "UI mainloop running") {
                Write-Log "UI confirmed running pid=$($proc.Id)"
                return
            }
            if ($txt -match "Tk failed") {
                Show-Msg "เปิด UI ไม่สำเร็จ:`n$txt" "Error"
                exit 1
            }
        }
        if ($proc.HasExited) {
            $detail = ""
            if (Test-Path -LiteralPath $BootFile) {
                $detail = Get-Content -LiteralPath $BootFile -Raw
            }
            Show-Msg "โปรแกรมปิดทันที (exit $($proc.ExitCode))`n$detail`nดู logs\launch.log" "Error"
            exit 1
        }
    }
    Write-Log "UI started (no boot file yet) pid=$($proc.Id)"
}

try {
    Write-Log "=== One-click launch start ==="
    $main = Join-Path $Root "main.py"
    if (-not (Test-Path -LiteralPath $main)) {
        Show-Msg "ไม่พบ main.py ในโฟลเดอร์นี้" "Error"
        exit 1
    }

    # Optional pre-built exe
    foreach ($exeName in @("HourlyVoiceReminder.exe", "dist\HourlyVoiceReminder.exe")) {
        $exePath = Join-Path $Root $exeName
        if (Test-Path -LiteralPath $exePath) {
            Write-Log "Starting bundled exe $exePath"
            Start-Process -FilePath $exePath -WorkingDirectory $Root
            exit 0
        }
    }

    Write-Log "Step 1: Checking Python + tkinter"
    $python = Find-Python
    if (-not $python) {
        Install-Python
        $python = Find-Python
    }
    if (-not $python) {
        Show-Msg "ยังหา Python + tkinter ไม่เจอ`n`nลอง:`n1) ปิดแล้วเปิด เปิดแอป.bat อีกครั้ง`n2) รีสตาร์ทเครื่อง`n3) ติดตั้งเองจาก python.org (Python 3.12 + tcl/tk)" "Warning"
        exit 1
    }

    # Prefer pythonw (no black console) — UI เหมือน Mac
    $dir = [IO.Path]::GetDirectoryName($python)
    $pythonw = Join-Path $dir "pythonw.exe"
    if ((Test-Path -LiteralPath $pythonw) -and (Test-PythonTk $pythonw)) {
        $python = $pythonw
    }

    Show-Msg "ขั้นที่ 2/2 — เปิดหน้าต่างตั้งค่า`n`nกด OK แล้วรอสักครู่" "Information"
    Start-Ui $python
    Write-Log "=== Launch complete ==="
    exit 0
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    Show-Msg "เกิดข้อผิดพลาด:`n$($_.Exception.Message)`n`nดู logs\launch.log" "Error"
    exit 1
}
