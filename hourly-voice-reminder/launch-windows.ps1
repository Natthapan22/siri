# Hourly Voice Reminder — Windows one-click launcher
# UTF-8 BOM recommended. Finds Python+tkinter, installs if missing, then opens UI.

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

$LogPath = Join-Path $Root "launch-error.txt"
$PythonVersion = "3.12.7"
$InstallerName = "python-$PythonVersion-amd64.exe"
$InstallerUrl = "https://www.python.org/ftp/python/$PythonVersion/$InstallerName"

function Write-Log([string]$Msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

function Show-Error([string]$Msg) {
    Write-Log $Msg
    try {
        Add-Type -AssemblyName PresentationFramework -ErrorAction SilentlyContinue
        [System.Windows.MessageBox]::Show($Msg, "Hourly Voice Reminder", "OK", "Error") | Out-Null
    } catch {
        Write-Host $Msg
    }
}

function Show-Info([string]$Msg) {
    try {
        Add-Type -AssemblyName PresentationFramework -ErrorAction SilentlyContinue
        [System.Windows.MessageBox]::Show($Msg, "Hourly Voice Reminder", "OK", "Information") | Out-Null
    } catch {
        Write-Host $Msg
    }
}

function Test-PythonTk {
    param([string]$Exe)
    if (-not $Exe) { return $false }
    if (-not (Test-Path -LiteralPath $Exe)) { return $false }
    # Skip Microsoft Store stub
    if ($Exe -like "*\WindowsApps\*") { return $false }
    try {
        $p = Start-Process -FilePath $Exe -ArgumentList @("-c", "import tkinter") `
            -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput "$env:TEMP\hvr-out.txt" `
            -RedirectStandardError "$env:TEMP\hvr-err.txt"
        return ($p.ExitCode -eq 0)
    } catch {
        return $false
    }
}

function Get-PythonCandidates {
    $list = New-Object System.Collections.Generic.List[string]
    $versions = @("Python312", "Python313", "Python311", "Python310", "Python39")
    $bases = @(
        "$env:LocalAppData\Programs\Python",
        "${env:ProgramFiles}\Python",
        "${env:ProgramFiles(x86)}\Python"
    )
    foreach ($base in $bases) {
        foreach ($v in $versions) {
            $list.Add("$base\$v\pythonw.exe")
            $list.Add("$base\$v\python.exe")
        }
    }
    # Also scan LocalAppData\Programs\Python\* for any version folder
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
    foreach ($p in Get-PythonCandidates) {
        if (Test-PythonTk $p) { return $p }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py -and $py.Source -and ($py.Source -notlike "*\WindowsApps\*")) {
        try {
            $resolved = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($resolved) {
                $exe = ($resolved | Select-Object -First 1).ToString().Trim()
                if ($exe -and ($exe -notlike "*\WindowsApps\*")) {
                    $dir = [IO.Path]::GetDirectoryName($exe)
                    $w = Join-Path $dir "pythonw.exe"
                    if (Test-PythonTk $w) { return $w }
                    if (Test-PythonTk $exe) { return $exe }
                }
            }
        } catch {}
    }
    return $null
}

function Install-Python {
    Show-Info "ไม่พบ Python — จะติดตั้ง Python $PythonVersion ให้อัตโนมัติ`nครั้งแรกใช้เวลาประมาณ 1-3 นาที ต้องมีอินเทอร์เน็ต"

    $tmp = Join-Path $env:TEMP $InstallerName
    Write-Log "Downloading $InstallerUrl"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $InstallerUrl -OutFile $tmp -UseBasicParsing
    } catch {
        Show-Error "ดาวน์โหลด Python ไม่สำเร็จ:`n$($_.Exception.Message)`n`nติดตั้งเองได้ที่ https://www.python.org/downloads/`nติ๊ก Add python.exe to PATH และ tcl/tk"
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
        $code = if ($p) { $p.ExitCode } else { "unknown" }
        Show-Error "ติดตั้ง Python ไม่สำเร็จ (exit $code)`n`nติดตั้งเองที่ https://www.python.org/downloads/`nติ๊ก Add python.exe to PATH และ tcl/tk"
        exit 1
    }

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

try {
    if (Test-Path -LiteralPath $LogPath) {
        Remove-Item -LiteralPath $LogPath -Force -ErrorAction SilentlyContinue
    }

    $main = Join-Path $Root "main.py"
    if (-not (Test-Path -LiteralPath $main)) {
        Show-Error "ไม่พบไฟล์ main.py ในโฟลเดอร์:`n$Root`n`nต้องคัดลอกทั้งโฟลเดอร์ hourly-voice-reminder มาด้วย"
        exit 1
    }

    $python = Find-Python
    if (-not $python) {
        Install-Python
        Start-Sleep -Seconds 3
        $python = Find-Python
    }

    if (-not $python) {
        Show-Error "ยังหา Python + tkinter ไม่เจอ`nลองปิดแล้วเปิดใหม่ หรือรีสตาร์ทเครื่อง แล้วดับเบิลคลิก เปิดแอป.bat อีกครั้ง`n`nหรือติดตั้งเอง: https://www.python.org/downloads/"
        exit 1
    }

    # Prefer pythonw for GUI without console — do NOT use -WindowStyle Hidden
    # (Hidden can hide the tkinter window on Windows)
    $dir = [IO.Path]::GetDirectoryName($python)
    $pythonw = Join-Path $dir "pythonw.exe"
    if ((Test-Path -LiteralPath $pythonw) -and (Test-PythonTk $pythonw)) {
        $python = $pythonw
    } else {
        $pythonExe = Join-Path $dir "python.exe"
        if ((Test-Path -LiteralPath $pythonExe) -and (Test-PythonTk $pythonExe)) {
            $python = $pythonExe
        }
    }

    Write-Log "Launching: $python $main"
    $proc = Start-Process -FilePath $python `
        -ArgumentList @($main) `
        -WorkingDirectory $Root `
        -PassThru
    if (-not $proc) {
        Show-Error "เปิดโปรแกรมไม่สำเร็จ`nPython: $python`nดูรายละเอียดใน launch-error.txt"
        exit 1
    }

    $booted = $false
    for ($i = 0; $i -lt 25; $i++) {
        Start-Sleep -Milliseconds 400
        if (Test-Path -LiteralPath $LogPath) {
            $txt = Get-Content -LiteralPath $LogPath -Raw -ErrorAction SilentlyContinue
            if ($txt -and ($txt -match "UI mainloop running")) {
                $booted = $true
                break
            }
            if ($txt -and ($txt -match "Traceback|Exception")) {
                Show-Error "เปิด UI ไม่สำเร็จ`n$txt"
                exit 1
            }
        }
        if ($proc.HasExited) {
            $detail = ""
            if (Test-Path -LiteralPath $LogPath) {
                $detail = Get-Content -LiteralPath $LogPath -Raw
            }
            Show-Error "โปรแกรมปิดทันที (exit $($proc.ExitCode))`n$detail`n`nลองรันใน Command Prompt:`ncd /d `"$Root`"`npython main.py"
            exit 1
        }
    }
    if (-not $booted) {
        Write-Log "warning: no boot confirmation yet; running=$(-not $proc.HasExited)"
    }
} catch {
    Show-Error "เกิดข้อผิดพลาด:`n$($_.Exception.Message)`n`nรายละเอียดบันทึกใน launch-error.txt"
    exit 1
}
