
import concurrent.futures
import requests
import time
import json
 
URL = "http://localhost:3000/getRemoteTask2"
PAYLOAD = {
    "image": "juanbrero/servicio-tarea:1.0",
    "task": "suma",
    "params": {"a": 1, "b": 2},
    "timestamp": 0
}
TOTAL_TASKS = 8          # tareas por experimento
WORKER_CONFIGS = [1, 2, 4, 8]  # valores de MAX_WORKERS a probar
 
 
def send_task(task_id):
    """Envía una sola tarea al servidor y retorna el tiempo que tardó."""
    start = time.time()
    try:
        resp = requests.post(URL, json=PAYLOAD, timeout=120)
        elapsed = time.time() - start
        ok = resp.status_code == 200
        return {"id": task_id, "ok": ok, "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        return {"id": task_id, "ok": False, "elapsed": elapsed, "error": str(e)}
 
 
def medir(n_workers_servidor: int) -> dict:
    """
    Envía TOTAL_TASKS solicitudes en paralelo (usando n_workers_servidor threads
    del lado del cliente para saturar el servidor) y calcula throughput.
 
    IMPORTANTE: antes de correr cada bloque, el servidor debe estar
    levantado con MAX_WORKERS = n_workers_servidor.
    """
    print(f"\n{'='*50}")
    print(f"  Midiendo con MAX_WORKERS = {n_workers_servidor}")
    print(f"  Enviando {TOTAL_TASKS} tareas concurrentes...")
    print(f"{'='*50}")
 
    input(f"  >> Configurá MAX_WORKERS={n_workers_servidor} en server.py y reiniciá el servidor. Luego presioná ENTER...")
 
    wall_start = time.time()
 
    with concurrent.futures.ThreadPoolExecutor(max_workers=TOTAL_TASKS) as executor:
        futures = [executor.submit(send_task, i) for i in range(TOTAL_TASKS)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
 
    wall_end = time.time()
    total_time_s = wall_end - wall_start
 
    completadas = sum(1 for r in results if r["ok"])
    throughput_por_min = (completadas / total_time_s) * 60
    latencia_promedio = sum(r["elapsed"] for r in results) / len(results)
 
    print(f"  Completadas:        {completadas}/{TOTAL_TASKS}")
    print(f"  Tiempo total:       {total_time_s:.2f}s")
    print(f"  Latencia promedio:  {latencia_promedio:.2f}s")
    print(f"  Throughput:         {throughput_por_min:.1f} tareas/min")
 
    return {
        "max_workers": n_workers_servidor,
        "total_tasks": TOTAL_TASKS,
        "completadas": completadas,
        "total_time_s": round(total_time_s, 2),
        "latencia_promedio_s": round(latencia_promedio, 2),
        "throughput_tareas_por_min": round(throughput_por_min, 1),
    }
 
 
if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════╗")
    print("║   MEDICIÓN DE THROUGHPUT - HIT2          ║")
    print("║   Variando MAX_WORKERS: 1, 2, 4, 8       ║")
    print("╚══════════════════════════════════════════╝")
 
    all_results = []
    for w in WORKER_CONFIGS:
        result = medir(w)
        all_results.append(result)
 
    # Guardar JSON
    with open("throughput_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
 
    # Tabla resumen
    print("\n\n╔══════════════════════════════════════════════════════════════════╗")
    print("║                     TABLA DE RESULTADOS                         ║")
    print("╠══════════════╦══════════════╦═══════════════╦════════════════════╣")
    print("║  MAX_WORKERS ║ Tiempo total ║ Lat. promedio ║ Throughput (t/min) ║")
    print("╠══════════════╬══════════════╬═══════════════╬════════════════════╣")
    for r in all_results:
        print(f"║      {r['max_workers']:<7} ║    {r['total_time_s']:<9.2f} ║     {r['latencia_promedio_s']:<9.2f} ║       {r['throughput_tareas_por_min']:<12.1f} ║")
    print("╚══════════════╩══════════════╩═══════════════╩════════════════════╝")
    print("\nResultados guardados en throughput_results.json")