@echo off

if not exist databases mkdir databases

powershell -Command "Invoke-WebRequest 'http://www.leidenuniv.nl/cml/ssp/databases/cmlia/cmlia.zip' -OutFile 'databases\cmlia.zip'"
powershell -Command "Invoke-WebRequest 'https://www.epa.gov/system/files/documents/2024-01/traci_2_2.xlsx' -OutFile 'databases\https://www.epa.gov/system/files/documents/2024-01/traci_2_2.xlsx'"
powershell -Command "Expand-Archive 'databases\cmlia.zip' -DestinationPath 'databases' -Force"

echo Done!
pause
