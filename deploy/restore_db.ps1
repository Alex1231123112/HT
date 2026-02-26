param(
  [string]$ContainerName = "ht-db-1",
  [string]$InputFile = "backup.sql"
)

if (-Not (Test-Path $InputFile)) {
  Write-Error "Backup file not found: $InputFile"
  exit 1
}

Get-Content $InputFile | docker exec -i $ContainerName psql -U postgres -d botdb
Write-Output "Database restored from $InputFile"
