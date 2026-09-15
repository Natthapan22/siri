on run
	try
		set appPath to POSIX path of (path to me)
		set rootPath to do shell script "dirname " & quoted form of appPath
		set logFile to rootPath & "/launch-error.txt"
		set mainPy to rootPath & "/main.py"
		
		do shell script "printf '%s\n' \"[$(date '+%Y-%m-%d %H:%M:%S')] applescript launch\" > " & quoted form of logFile
		
		if (do shell script "test -f " & quoted form of mainPy & " && echo yes || echo no") is "no" then
			display alert "ไม่พบ main.py" message rootPath
			return
		end if
		
		set py to ""
		set candidates to {¬
			"/Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python", ¬
			"/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python", ¬
			"/Library/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python", ¬
			"/Library/Frameworks/Python.framework/Versions/Current/Resources/Python.app/Contents/MacOS/Python", ¬
			"/Library/Frameworks/Python.framework/Versions/3.11/bin/python3", ¬
			"/opt/homebrew/bin/python3", ¬
			"/usr/local/bin/python3", ¬
			"/usr/bin/python3"}
		
		repeat with c in candidates
			try
				do shell script "test -x " & quoted form of (c as text) & " && " & quoted form of (c as text) & " -c 'import tkinter'"
				set py to (c as text)
				exit repeat
			end try
		end repeat
		
		if py is "" then
			display alert "ไม่พบ Python 3 + tkinter" message "ติดตั้งจาก python.org แล้วติ๊ก Tcl/Tk"
			return
		end if
		
		do shell script "printf '%s\n' \"using " & py & "\" >> " & quoted form of logFile
		
		-- Detach WITHOUT redirecting Python stdio (redirect can hang Tk on macOS)
		set cmd to "cd " & quoted form of rootPath & " && " & quoted form of py & " " & quoted form of mainPy & " &>/dev/null & echo $!"
		set pid to do shell script cmd
		do shell script "printf '%s\n' \"pid=" & pid & "\" >> " & quoted form of logFile
		
		delay 2.0
		try
			tell application "System Events"
				set frontmost of first process whose unix id is (pid as integer) to true
			end tell
		end try
	on error errMsg number errNum
		display alert "เปิดไม่สำเร็จ (" & errNum & ")" message errMsg
	end try
end run
