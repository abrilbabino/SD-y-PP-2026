levantar la api main --> uvicorn api.main:app --host 0.0.0.0 --port 3000

para probar multiples request (concurrencia) --> 1..8 | ForEach-Object {
>>   Start-Job {
>>     Invoke-RestMethod -Uri "http://localhost:3000/getRemoteTask2" `
>>     -Method POST `
>>     -ContentType "application/json" `
>>     -Body '{"image":"juanbrero/servicio-tarea:1.0","task":"suma","params":{"a":1,"b":2},"timestamp":0}'
>>   }
>> }

esperar a que terminen los jobs y de los jobs --> Get-Job | Wait-Job

ver resultados --> Get-Job | Receive-Job

