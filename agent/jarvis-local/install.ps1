# Jarvis PC 에이전트 설치(재실행 가능). 토큰은 화면에 출력하지 않는다.
param(
  [Parameter(Mandatory = $true)][string]$WorkerUrl,
  [string]$NodePath = "C:\Program Files\nodejs\node.exe"
)
$ErrorActionPreference = 'Stop'
# 일부 실행 환경에서는 $env:USERNAME 이 비어 있으므로 Windows 계정 정보에서 직접 가져온다.
$user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
if (-not $user) { throw 'Windows 계정을 확인할 수 없습니다.' }
if (-not $WorkerUrl.StartsWith('https://')) { throw 'WorkerUrl은 https 주소여야 합니다.' }
if (-not (Test-Path $NodePath)) { throw "Node를 찾을 수 없습니다: $NodePath" }

$agentHome = Join-Path $env:LOCALAPPDATA 'JarvisAgent'
$app = Join-Path $agentHome 'app'
New-Item -ItemType Directory -Force $app, (Join-Path $agentHome 'work') | Out-Null
Copy-Item (Join-Path $PSScriptRoot '*.mjs') $app -Force

$configPath = Join-Path $agentHome 'config.json'
$config = if (Test-Path $configPath) { Get-Content $configPath -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
if (-not $config.agentToken) {
  $bytes = New-Object byte[] 36; [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
  $token = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
  $config | Add-Member -Force agentToken $token
}
$config | Add-Member -Force workerUrl $WorkerUrl.TrimEnd('/')
foreach ($pair in @(@('claudeModel', 'sonnet'), @('learnModel', 'haiku'), @('codexEffort', 'low'), @('pollMs', 3000))) {
  if (-not $config.($pair[0])) { $config | Add-Member -Force $pair[0] $pair[1] }
}
$config | ConvertTo-Json | Set-Content -Encoding utf8 $configPath
icacls $configPath /inheritance:r /grant:r "$($user):F" | Out-Null   # 본인 계정만 읽기

# 콘솔 창 없이 실행하는 런처(종료 코드를 작업 스케줄러에 전달해 실패 시 재시작되게 한다)
$launcher = Join-Path $agentHome 'launch.vbs'
@"
Set sh = CreateObject("WScript.Shell")
code = sh.Run("""$NodePath"" ""$app\agent.mjs""", 0, True)
WScript.Quit code
"@ | Set-Content -Encoding ascii $launcher

$action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument "`"$launcher`"" -WorkingDirectory $agentHome
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
  -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'JarvisAgent' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Stop-ScheduledTask -TaskName 'JarvisAgent' -ErrorAction SilentlyContinue
# 작업을 멈춰도 런처의 자식 node는 남는다. 이전 버전이 질문을 가로채지 않도록 모두 종료한다.
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -and $_.CommandLine.Contains((Join-Path $app 'agent.mjs')) } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1
Start-ScheduledTask -TaskName 'JarvisAgent'
Write-Output "설치 완료: $agentHome (작업 스케줄러 'JarvisAgent')"
Write-Output "Cloudflare에 같은 토큰 등록 필요: config.json의 agentToken -> wrangler secret put JARVIS_AGENT_TOKEN"
