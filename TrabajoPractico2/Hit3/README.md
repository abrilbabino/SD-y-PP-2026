para ejecutar by april
cd TrabajoPractico2/Hit3
docker-compose up -d --build
Start-Sleep -Seconds 10 (yo pongo 10 pero quizas anda con menos pq el hearbeat esta en 5)

## Fase 1: Todos los workers corriendo
iwr http://localhost:8001/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:8002/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:9000/status -UseBasicParsing | Select-Object -ExpandProperty Content

### Salida esperada
{"worker_id":1,"leader_id":3,"is_busy":false}
{"worker_id":2,"leader_id":3,"is_busy":false}
{"worker_id":3,"leader_id":3,"is_busy":false}

# Fase 2: Simular petisuis worker3
docker-compose stop worker3
Start-Sleep -Seconds 6
iwr http://localhost:8001/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:8002/status -UseBasicParsing | Select-Object -ExpandProperty Content

### Salida esperada
{"worker_id":1,"leader_id":2,"is_busy":false}
{"worker_id":2,"leader_id":2,"is_busy":false}

## Fase 3: Resucita worker3
docker-compose start worker3
Start-Sleep -Seconds 8
iwr http://localhost:8001/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:8002/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:9000/status -UseBasicParsing | Select-Object -ExpandProperty Content

### Salida esperada 
{"worker_id":1,"leader_id":3,"is_busy":false}
{"worker_id":2,"leader_id":3,"is_busy":false}
{"worker_id":3,"leader_id":3,"is_busy":false}

## Para probar ejecutar tarea
entras al navegador
http://localhost:8080/test3
bancale unos 10 segundillos mas 
y tocas ejecutar