# Hourly Voice Reminder — Windows one-click launcher
# Finds Python+tkinter, or silently installs Python for current user, then opens UI.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$PythonVersion = "3.12.7"
$InstallerName = "python-$PythonVersion-amd64.exe"
$InstallerUrl = "https://www.python.org/ftp/python/$PythonVersion/$InstallerName"

function Test-PythonTk {
    param([string]$Exe)
    if (-not $Exe -or -not (Test-Path -LiteralPath $Exe)) { return $false }
    try {
        & $Exe -c "import tkinter" 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Get-PythonCandidates {
    $list = New-Object System.Collections.Generic.List[string]
    $versions = @("Python312", "Python311", "Python313", "Python310")
    foreach ($v in $versions) {
        $list.Add("$env:LocalAppData\Programs\Python\$v\pythonw.exe")
        $list.Add("$env:LocalAppData\Programs\Python\$v\python.exe")
        $list.Add("${env:ProgramFiles}\Python\$v\pythonw.exe")
        $list.Add("${env:ProgramFiles}\Python\$v\python.exe")
    }
    foreach ($cmd in @("pythonw", "python", "py")) {
        $c = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($c -and $c.Source) { $list.Add($c.Source) }
    }
    # py launcher: try -3
    return $list
}

function Find-Python {
    foreach ($p in Get-PythonCandidates) {
        if (Test-PythonTk $p) { return $p }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            $resolved = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($resolved) {
                $exe = $resolved.Trim()
                $w = [IO.Path]::Combine([IO.Path]::GetDirectoryName($exe), "pythonw.exe")
                if (Test-PythonTk $w) { return $w }
                if (Test-PythonTk $exe) { return $exe }
            }
        } catch {}
    }
    return $null
}

function Install-Python {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "ไม่พบ Python — จะติดตั้ง Python $PythonVersion ให้อัตโนมัติ (ครั้งแรกอาจใช้เวลา 1–3 นาที)`nต้องมีอินเทอร์เน็ต",
        "Hourly Voice Reminder",
        "OK",
        "Information"
    ) | Out-Null

    $tmp = Join-Path $env:TEMP $InstallerName
    Write-Host "Downloading Python $PythonVersion ..."
    try {
        Invoke-WebRequest -Uri $InstallerUrl -OutFile $tmp -UseBasicParsing
    } catch {
        [System.Windows.MessageBox]::Show(
            "ดาวน์โหลด Python ไม่สำเร็จ:`n$($_.Exception.Message)",
            "Hourly Voice Reminder",
            "OK",
            "Error"
        ) | Out-Null
        exit 1
    }

    Write-Host "Installing Python (silent, current user) ..."
    $args = @(
        "/quiet",
        "InstallAllUsers=0",
        "PrependPath=1",
        "Include_tcltk=1",
        "Include_pip=1",
        "Include_test=0",
        "Include_doc=0",
        "Include_launcher=1",
        "AssociateFiles=0",
        "Shortcuts=0",
        "SimpleInstall=1"
    )
    $p = Start-Process -FilePath $tmp -ArgumentList $args -Wait -PassThru
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue

    if ($p.ExitCode -ne 0) {
        [System.Windows.MessageBox]::Show(
            "ติดตั้ง Python ไม่สำเร็จ (exit $($p.ExitCode))`nลองติดตั้งเองจาก https://www.python.org/downloads/ แล้วติ๊ก Add to PATH + tcl/tk",
            "Hourly Voice Reminder",
            "OK",
            "Error"
        ) | Out-Null
        exit 1
    }

    # refresh PATH for this process
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

$python = Find-Python
if (-not $python) {
    Install-Python
    Start-Sleep -Seconds 2
    $python = Find-Python
}

if (-not $python) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "ติดตั้งแล้วแต่ยังหา Python+tkinter ไม่เจอ`nลองปิดแล้วเปิดใหม่ หรือรีสตาร์ทเครื่อง แล้วดับเบิลคลิกอีกครั้ง",
        "Hourly Voice Reminder",
        "OK",
        "Warning"
    ) | Out-Null
    exit 1
}

# Prefer pythonw (no console) when available
$dir = [IO.Path]::GetDirectoryName($python)
$pythonw = Join-Path $dir "pythonw.exe"
if ((Test-Path -LiteralPath $pythonw) -and (Test-PythonTk $pythonw)) {
    $python = $pythonw
}

$main = Join-Path $Root "main.py"
Start-Process -FilePath $python -ArgumentList "`"$main`"" -WorkingDirectory $Root
