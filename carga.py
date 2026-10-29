"""
Gerador de carga (somente biblioteca padrão).
Mantém a PROPORÇÃO da volumetria do desafio (104 mil req/dia no total).

Uso:  python carga.py [rps_total] [duracao_segundos]
      python carga.py 10 600     -> 10 req/s por 10 min (padrão)

Equivalência: o desafio tem ~1,2 req/s em média (104.000 / 86.400).
Com 10 req/s o tempo é comprimido ~8x: 10 min de teste ~ 83 min de tráfego real.
"""
import random
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

RPS = float(sys.argv[1]) if len(sys.argv) > 1 else 10
DURACAO = int(sys.argv[2]) if len(sys.argv) > 2 else 600
CONTA, CLI = "http://127.0.0.1:8001", "http://127.0.0.1:8002"

MIX = [  # (volumetria/dia, endpoint)
    (50000, CONTA + "/movimentacao?tipo=credito"),
    (50000, CONTA + "/movimentacao?tipo=debito"),   # movimentação: 100 mil/dia
    (1000, CONTA + "/contas"),                      # cadastro
    (200, CONTA + "/contas/cancelamento"),          # cancelamento
    (700, CONTA + "/fraude/bloqueio"),              # bloqueio por fraude
    (2000, CLI + "/clientes"),                      # inclusão de clientes
    (100, CLI + "/clientes/inativacao"),            # inativação de clientes
]
URLS = [u for _, u in MIX]
PESOS = [p for p, _ in MIX]


def chamar(url):
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="POST"), timeout=6).read()
    except Exception:
        pass  # erros já aparecem nas métricas do serviço


fim = time.time() + DURACAO
enviadas = 0
print(f"Carga: {RPS} req/s por {DURACAO}s. Ctrl+C para parar.")
with ThreadPoolExecutor(max_workers=32) as ex:
    while time.time() < fim:
        ex.submit(chamar, random.choices(URLS, PESOS)[0])
        enviadas += 1
        time.sleep(random.expovariate(RPS))
print(f"Fim. Requisições enviadas: {enviadas}")
