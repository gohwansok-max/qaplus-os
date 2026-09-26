# Jarvis PC 에이전트 설치(재실행 가능). 토큰은 화면에 출력하지 않는다.
param(
  [Parameter(Mandatory = $true)][string]$WorkerUrl,
  [string]$NodePath = '',
  # 새 PC를 기존 Jarvis에 안전하게 연결한다. 그 PC에서 만든 토큰의 해시만 Worker에 보내고, 텔레그램 승인을 기다린다.
  [switch]$PairDevice,
  [string]$DeviceName = $env:COMPUTERNAME
)
$ErrorActionPreference = 'Stop'
# 일부 실행 환경에서는 $env:USERNAME 이 비어 있으므로 Windows 계정 정보에서 직접 가져온다.
$user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
if (-not $user) { throw 'Windows 계정을 확인할 수 없습니다.' }
if (-not $WorkerUrl.StartsWith('https://')) { throw 'WorkerUrl은 https 주소여야 합니다.' }
if (-not $NodePath) {
  $nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
  if ($nodeCommand) { $NodePath = $nodeCommand.Source } else { $NodePath = 'C:\Program Files\nodejs\node.exe' }
}
if (-not (Test-Path $NodePath)) { throw "Node.js를 찾을 수 없습니다. Node.js LTS를 설치한 뒤 다시 실행하세요: $NodePath" }
if (-not $DeviceName -or $DeviceName.Length -gt 40 -or $DeviceName -notmatch '^[\w가-힣 .()-]+$') { throw 'DeviceName에는 한글, 영문, 숫자, 공백, .()- 만 사용할 수 있습니다.' }

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

if ($PairDevice) {
  # 토큰 원문은 이 PC의 ACL 보호 config.json 밖으로 나가지 않는다. Worker에는 SHA-256 해시만 보낸다.
  $tokenBytes = [Text.Encoding]::UTF8.GetBytes([string]$config.agentToken)
  $hash = -join ([Security.Cryptography.SHA256]::HashData($tokenBytes) | ForEach-Object { $_.ToString('x2') })
  $pairUri = "$($config.workerUrl)/agent/pair"
  try {
    $pair = Invoke-RestMethod -Method Post -Uri $pairUri -ContentType 'application/json' -Body (@{token_hash=$hash; name=$DeviceName} | ConvertTo-Json -Compress) -TimeoutSec 20
  } catch { throw "연결 요청 전송에 실패했습니다: $($_.Exception.Message)" }
  Write-Output "텔레그램에 표시된 연결 승인 코드: $($pair.code)"
  Write-Output '텔레그램에서 코드가 같은지 확인하고 [승인]을 누르세요. 10분 안에 승인되지 않으면 다시 실행하세요.'
  $approved = $false
  for ($i = 0; $i -lt 120; $i++) {
    Start-Sleep -Seconds 5
    try {
      $status = Invoke-RestMethod -Method Post -Uri "$pairUri/status" -ContentType 'application/json' -Body (@{token_hash=$hash} | ConvertTo-Json -Compress) -TimeoutSec 15
      if ($status.approved) { $approved = $true; break }
    } catch { }
  }
  if (-not $approved) { throw '텔레그램 승인이 확인되지 않았습니다. 에이전트는 시작하지 않았습니다.' }
  Write-Output '텔레그램 승인 확인 완료. 이 PC 에이전트를 시작합니다.'
}

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
if (-not $PairDevice) { Write-Output '기존 기본 PC 설치용입니다. 새 PC는 -PairDevice 옵션으로 텔레그램 승인 연결을 사용하세요.' }
