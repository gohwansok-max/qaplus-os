$ErrorActionPreference = 'Stop'
$TaskName = 'QAPlus_Blog_GDrive_Archive'
$Python = (Get-Command python -ErrorAction Stop).Source
$SyncScript = Join-Path $PSScriptRoot 'sync_blog_archive_to_gdrive.py'

if (-not (Test-Path -LiteralPath $SyncScript)) {
    throw "동기화 스크립트를 찾을 수 없습니다: $SyncScript"
}

$Arguments = '"{0}"' -f $SyncScript
$Action = New-ScheduledTaskAction -Execute $Python -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 30)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Description 'QA+ 블로그 산출물을 Google Drive에 30분마다 보관' -Force | Out-Null

Write-Host "등록 완료: $TaskName"
Write-Host '보관 위치: sync_blog_archive_to_gdrive.py 기본 Google Drive 폴더'
