!macro NSIS_HOOK_PREINSTALL
  ExecWait '"$SYSDIR\\taskkill.exe" /F /IM "ragkit-backend.exe" /T'
  ExecWait '"$SYSDIR\\taskkill.exe" /F /IM "ragkit-desktop.exe" /T'
  ExecWait '"$SYSDIR\\taskkill.exe" /F /IM "RAGKIT Desktop.exe" /T'
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  ExecWait '"$SYSDIR\\taskkill.exe" /F /IM "ragkit-backend.exe" /T'
  ExecWait '"$SYSDIR\\taskkill.exe" /F /IM "ragkit-desktop.exe" /T'
  ExecWait '"$SYSDIR\\taskkill.exe" /F /IM "RAGKIT Desktop.exe" /T'
!macroend
