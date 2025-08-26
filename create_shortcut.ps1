$ErrorActionPreference = 'Stop'

# 한글 주석: 현재 폴더의 run_windows.bat을 대상으로, Desktop에 바로가기를 만들고 app_icon.ico를 아이콘으로 설정합니다.
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'PDF Merge Split.lnk'

$target = (Resolve-Path '.\run_windows.bat').Path
$workdir = (Get-Location).Path

# 아이콘 파일이 있으면 사용, 없으면 경고
$iconPath = $null
try { $iconPath = (Resolve-Path '.\app_icon.ico').Path } catch {}

$sc = $shell.CreateShortcut($shortcutPath)
$sc.TargetPath = $target
$sc.WorkingDirectory = $workdir
if ($iconPath) { $sc.IconLocation = $iconPath }
$sc.Save()

Write-Output "CREATED $shortcutPath"

