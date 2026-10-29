"""
Simulador leve de dois serviços instrumentados (mesmo código, variável SERVICO):

  SERVICO=conta-corrente  -> movimentação, cadastro, cancelamento, bloqueio por fraude
  SERVICO=clientes        -> inclusão e inativação (a inativação aciona o cancelamento na conta-corrente)

Pilares:
  - Métricas : Prometheus (/metrics) com golden signals + métricas de negócio
  - Logs     : JSON estruturado em stdout e em logs/<servico>.log, com trace_id
  - Traces   : trace_id propagado via header X-Trace-Id entre os serviços ("tracing lite")
"""
import contextvars
import json
import logging
import os
import random
import threading
import time
import urllib.request
import uuid

import psutil
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge, Histogram,
                               generate_latest)

SERVICO = os.getenv("SERVICO", "conta-corrente")
CONTA_URL = os.getenv("CONTA_URL", "http://localhost:8001")
POOL_TAMANHO = int(os.getenv("POOL", "10"))  # simula o pool de conexões do banco

# ----------------------------------------------------------------- LOGS (JSON)
trace_ctx = contextvars.ContextVar("trace_id", default="-")
os.makedirs("logs", exist_ok=True)


class JsonFmt(logging.Formatter):
    def format(self, r):
        d = {
            "ts": self.formatTime(r, "%Y-%m-%dT%H:%M:%S"),
            "level": r.levelname,
            "service": SERVICO,
            "trace_id": trace_ctx.get(),
            "msg": r.getMessage(),
        }
        d.update(getattr(r, "campos", {}))
        return json.dumps(d, ensure_ascii=False)


log = logging.getLogger("app")
log.setLevel(logging.INFO)
for h in (logging.StreamHandler(), logging.FileHandler(f"logs/{SERVICO}.log", encoding="utf-8")):
    h.setFormatter(JsonFmt())
    log.addHandler(h)


def evt(nivel, msg, **campos):
    log.log(nivel, msg, extra={"campos": campos})


# ------------------------------------------------------- MÉTRICAS: GOLDEN SIGNALS
REQS = Counter("http_requests_total", "Requisições HTTP (tráfego e erros)",
               ["servico", "operacao", "status"])
LAT = Histogram("http_request_duration_seconds", "Latência das requisições",
                ["servico", "operacao"],
                buckets=(.05, .1, .2, .3, .5, .8, 1, 2, 5, 10, 30))
INFLIGHT = Gauge("http_requests_in_progress", "Requisições em andamento (saturação)", ["servico"])
POOL_USO = Gauge("db_pool_em_uso", "Conexões simuladas em uso (saturação)", ["servico"])
POOL_MAX = Gauge("db_pool_capacidade", "Capacidade do pool simulado", ["servico"])
CPU = Gauge("processo_cpu_percent", "CPU do processo (saturação)", ["servico"])
MEM = Gauge("processo_memoria_mb", "Memória do processo em MB (saturação)", ["servico"])

_proc = psutil.Process()
CPU.labels(SERVICO).set_function(lambda: _proc.cpu_percent(interval=None))
MEM.labels(SERVICO).set_function(lambda: _proc.memory_info().rss / 1024 / 1024)
POOL_MAX.labels(SERVICO).set(POOL_TAMANHO)

# ------------------------------------------------------------ MÉTRICAS DE NEGÓCIO
MOV = Counter("movimentacoes_total", "Movimentações de saldo", ["tipo", "resultado"])
MOV_VALOR = Counter("movimentacao_valor_reais_total", "Valor movimentado em R$", ["tipo"])
CONTAS_ABERTAS = Counter("contas_abertas_total", "Contas abertas")
CONTAS_CANCELADAS = Counter("contas_canceladas_total", "Contas canceladas")
FRAUDE = Counter("bloqueios_fraude_total", "Bloqueios por fraude", ["motivo"])
FRAUDE_LAT = Histogram("bloqueio_fraude_efetivacao_seconds", "Tempo até efetivar o bloqueio",
                       buckets=(.1, .25, .5, 1, 2, 5, 10, 30))
CLI_INCLUIDOS = Counter("clientes_incluidos_total", "Clientes incluídos")
CLI_INATIVADOS = Counter("clientes_inativados_total", "Clientes inativados")
INCONSISTENCIAS = Counter("inconsistencias_cliente_conta_total",
                          "Clientes inativados cujas contas NÃO foram canceladas")

# ------------------------------------------------------------- SIMULAÇÃO / FALHAS
FALHA = {"erro": 0.0, "latencia": 0.0}  # ajustável em /admin/falha
POOL = threading.BoundedSemaphore(POOL_TAMANHO)
BASE = {  # (latência mín, latência máx) em segundos
    "movimentacao": (0.02, 0.20),
    "cadastro": (0.05, 0.30),
    "cancelamento": (0.05, 0.30),
    "bloqueio_fraude": (0.05, 0.40),
    "inclusao_cliente": (0.03, 0.25),
    "inativacao_cliente": (0.03, 0.20),
}
OPERACOES = {
    "/movimentacao": "movimentacao",
    "/contas": "cadastro",
    "/contas/cancelamento": "cancelamento",
    "/fraude/bloqueio": "bloqueio_fraude",
    "/clientes": "inclusao_cliente",
    "/clientes/inativacao": "inativacao_cliente",
}


def processar(operacao):
    """Simula trabalho com banco: usa uma conexão do pool, demora e pode falhar."""
    if not POOL.acquire(timeout=2):
        raise HTTPException(503, "pool de conexões esgotado")
    POOL_USO.labels(SERVICO).inc()
    try:
        lo, hi = BASE[operacao]
        time.sleep(random.uniform(lo, hi) + FALHA["latencia"])
        if random.random() < 0.0005 + FALHA["erro"]:  # 0,05% de erro de base
            raise HTTPException(500, "erro interno simulado")
    finally:
        POOL_USO.labels(SERVICO).dec()
        POOL.release()


# ------------------------------------------------------------------------- APP
app = FastAPI(title=f"Simulador - {SERVICO}")


@app.middleware("http")
async def telemetria(request: Request, call_next):
    caminho = request.url.path
    if caminho.startswith("/metrics") or caminho.startswith("/admin"):
        return await call_next(request)
    operacao = OPERACOES.get(caminho, "outros")
    trace_ctx.set(request.headers.get("x-trace-id") or uuid.uuid4().hex[:16])
    INFLIGHT.labels(SERVICO).inc()
    inicio = time.perf_counter()
    status = 500
    try:
        resp = await call_next(request)
        status = resp.status_code
        return resp
    finally:
        dur = time.perf_counter() - inicio
        INFLIGHT.labels(SERVICO).dec()
        LAT.labels(SERVICO, operacao).observe(dur)
        REQS.labels(SERVICO, operacao, str(status)).inc()
        nivel = logging.INFO if status < 400 else (logging.WARNING if status < 500 else logging.ERROR)
        evt(nivel, "request", operacao=operacao, status=status, duracao_ms=round(dur * 1000))


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/admin/falha")
def falha(erro: float = 0.0, latencia: float = 0.0):
    """Injeção de falha: erro = probabilidade extra de 5xx (0 a 1); latencia = segundos extras."""
    FALHA["erro"], FALHA["latencia"] = erro, latencia
    evt(logging.WARNING, "falha_injetada", erro=erro, latencia=latencia)
    return FALHA


if SERVICO == "conta-corrente":

    @app.post("/movimentacao")
    def movimentacao(tipo: str = "credito"):
        if tipo not in ("credito", "debito"):
            raise HTTPException(400, "tipo inválido")
        processar("movimentacao")
        if tipo == "debito" and random.random() < 0.05:  # erro de NEGÓCIO (não é falha técnica)
            MOV.labels(tipo, "saldo_insuficiente").inc()
            raise HTTPException(422, "saldo insuficiente")
        MOV.labels(tipo, "sucesso").inc()
        MOV_VALOR.labels(tipo).inc(round(random.uniform(10, 2000), 2))
        return {"ok": True}

    @app.post("/contas")
    def cadastro():
        processar("cadastro")
        CONTAS_ABERTAS.inc()
        return {"conta": uuid.uuid4().hex[:8]}

    @app.post("/contas/cancelamento")
    def cancelamento():
        processar("cancelamento")
        CONTAS_CANCELADAS.inc()
        return {"ok": True}

    @app.post("/fraude/bloqueio")
    def bloqueio_fraude():
        inicio = time.perf_counter()
        processar("bloqueio_fraude")
        motivo = random.choice(["padrao_suspeito", "dispositivo_novo", "valor_atipico", "denuncia_cliente"])
        FRAUDE.labels(motivo).inc()
        FRAUDE_LAT.observe(time.perf_counter() - inicio)
        return {"bloqueada": True, "motivo": motivo}

else:  # clientes

    def chamar_conta(caminho):
        req = urllib.request.Request(CONTA_URL + caminho, method="POST",
                                     headers={"X-Trace-Id": trace_ctx.get()})
        urllib.request.urlopen(req, timeout=3).read()

    @app.post("/clientes")
    def inclusao_cliente():
        processar("inclusao_cliente")
        CLI_INCLUIDOS.inc()
        return {"cliente": uuid.uuid4().hex[:8]}

    @app.post("/clientes/inativacao")
    def inativacao_cliente():
        processar("inativacao_cliente")
        CLI_INATIVADOS.inc()
        try:  # cascata: cliente inativo => cancelar contas (outro serviço, mesmo trace_id)
            chamar_conta("/contas/cancelamento")
        except Exception as e:
            INCONSISTENCIAS.inc()
            evt(logging.ERROR, "cascata_falhou", destino="conta-corrente", erro=str(e)[:80])
            raise HTTPException(502, "cliente inativado, mas falhou ao cancelar as contas")
        return {"ok": True}
