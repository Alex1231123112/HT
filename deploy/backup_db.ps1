param(
  [string]$ContainerName = "ht-db-1",
  [string]$OutputFile = "backup.sql"
)

docker exec $ContainerName pg_dump -U postgres botdb > $OutputFile
Write-Output "Backup written to $OutputFile"
