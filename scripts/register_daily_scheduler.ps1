# ==============================================================================
# 큐에이플러스(QA+) 윈도우 작업 스케줄러 매일 자동 실행 등록 스크립트
# - 매일 오전 06:00 정기 자동 실행
# ==============================================================================

$taskName = "QAPlus_Daily_Video_Autopilot"
$scriptPath = Join-Path $PSScriptRoot "daily_qa_autopilot.py"
$pythonPath = (Get-Command python).Source

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  [큐에이플러스] 윈도우 일일 자동화 스케줄러 등록" -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "• 파이썬 경로: $pythonPath"
Write-Host "• 실행 스크립트: $scriptPath"
Write-Host "• 매일 실행 시간: 오전 06:00 (원할 시 수정 가능)"

# Action & Trigger
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`"" -WorkingDirectory (Split-Path $scriptPath)
$trigger = New-ScheduledTaskTrigger -Daily -At 06:00am
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register or update task
try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force
    Write-Host "`n[성공] 작업 스케줄러에 '$taskName' 작업이 성공적으로 등록되었습니다!" -ForegroundColor Green
    Write-Host "이제 컴퓨터가 켜져 있으면 매일 오전 6시에 자동으로 새 주제로 쇼츠 MP4 영상이 생성됩니다." -ForegroundColor Green
} catch {
    Write-Host "`n[오류] 관리자 권한으로 PowerShell을 실행하여 다시 시도해주세요." -ForegroundColor Red
}
