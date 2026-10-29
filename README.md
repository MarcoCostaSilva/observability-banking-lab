<h1 align="center">Observabilidade: Conta-corrente e Clientes<br>Observability: Checking Account and Customers</h1>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white"></a>
  <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white"></a>
  <a href="https://www.uvicorn.org/"><img alt="Uvicorn" src="https://img.shields.io/badge/Uvicorn-ASGI-499848"></a>
  <a href="https://prometheus.io/"><img alt="Prometheus" src="https://img.shields.io/badge/Prometheus-3.13_LTS-E6522C?logo=prometheus&logoColor=white"></a>
  <a href="https://grafana.com/"><img alt="Grafana" src="https://img.shields.io/badge/Grafana-13.2-F46800?logo=grafana&logoColor=white"></a>
  <a href="https://prometheus.io/docs/prometheus/latest/querying/basics/"><img alt="PromQL" src="https://img.shields.io/badge/PromQL-alert_rules-E6522C"></a>
  <img alt="Logs JSON" src="https://img.shields.io/badge/Logs-JSON-000000?logo=json&logoColor=white">
  <a href="https://github.com/giampaolo/psutil"><img alt="psutil" src="https://img.shields.io/badge/psutil-metrics-3776AB"></a>
  <img alt="Windows" src="https://img.shields.io/badge/Windows-10-0078D6?logo=windows&logoColor=white">
  <img alt="PowerShell" src="https://img.shields.io/badge/PowerShell-5391FE?logo=powershell&logoColor=white">
  <img alt="Git" src="https://img.shields.io/badge/Git-F05032?logo=git&logoColor=white">
  <img alt="GitHub" src="https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white">
</p>

<p align="center"><a href="#português-pt-br">Português</a> | <a href="#english">English</a></p>

---

## Português (PT-BR)

Plano de observabilidade e prova de conceito para duas aplicações bancárias (conta-corrente e clientes), construídos com ferramentas 100% gratuitas e leves o bastante para rodar em um notebook com 8 GB de RAM, sem Docker.

O projeto responde ao **Desafio de Observabilidade do Instituto de Ciência e Tecnologia Itaú**: definir como observar seis serviços com golden signals, os três pilares da observabilidade, métricas de negócio e alarmes, e provar na prática que o plano detecta falhas reais.

### O desafio

| Aplicação | Serviço | Volumetria | Taxa média |
|---|---|---|---|
| Conta-corrente | Movimentação de saldo (crédito e débito) | 100 mil por dia | 1,2 req/s |
| Conta-corrente | Cadastro de novas contas | 1 mil por dia | 42 req/h |
| Conta-corrente | Cancelamento de contas | 200 por dia | 8 req/h |
| Conta-corrente | Bloqueio por fraudes | 700 por dia | 29 req/h |
| Clientes | Inclusão de clientes | 2 mil por dia | 83 req/h |
| Clientes | Inativação de clientes | 100 por dia | 4 req/h |

A soma é de aproximadamente 104 mil requisições por dia (cerca de 1,2 por segundo). Nos serviços de baixo volume uma única falha altera muito a taxa de erro (1 erro em 3 requisições equivale a 33%), então o plano usa janelas longas, volume mínimo e contagem absoluta em vez de taxa em 5 minutos.

### Visão geral da solução

- **Métricas:** Prometheus coleta histogramas de latência, contadores de tráfego e erros, gauges de saturação e métricas de negócio.
- **Logs:** eventos JSON, um por linha, com `trace_id` e sem dados pessoais (LGPD).
- **Traces:** o `trace_id` é propagado entre os serviços pelo cabeçalho `X-Trace-Id` (versão simplificada).
- **Golden signals:** latência (p50, p95 e p99), tráfego, erros e saturação por operação.
- **Alarmes:** 14 regras em três níveis (críticos, avisos e anomalias).
- **Dashboard:** 18 painéis no Grafana.
- **Validação:** gerador de carga proporcional e injeção de falhas em tempo real.

### Arquitetura

```
                  +---------------------+
 carga.py  ---->  | conta-corrente :8001| <----+
 (volumetria)     +---------------------+      |  cascata (X-Trace-Id)
        |                  | /metrics          |
        |         +---------------------+      |
        +------>  |    clientes :8002   | -----+
                  +---------------------+
                           | /metrics
                           v
                  +---------------------+      14 regras de alerta
                  |  Prometheus :9090   | ---> http://localhost:9090/alerts
                  +---------------------+
                           |
                           v
                  +---------------------+
                  |   Grafana :3000     |  dashboard com 18 painéis
                  +---------------------+

 logs/conta-corrente.log e logs/clientes.log (JSON com trace_id)
```

Os dois serviços usam o mesmo código (`app.py`). A variável `SERVICO` define qual API é exposta. Na inativação de um cliente, o serviço de clientes chama o cancelamento de contas na conta-corrente, repassando o mesmo `trace_id`. Se essa chamada falha, o contador de inconsistência é incrementado.

### Estrutura do repositório

```
observabilidade-conta-corrente-clientes/
  app.py                    serviços simulados e instrumentação
  carga.py                  gerador de carga com a volumetria do desafio
  iniciar.bat               sobe os dois serviços no Windows
  requirements.txt          dependências Python
  prometheus/
    prometheus.yml          configuração da coleta
    regras.yml              regras de gravação (SLIs) e 14 alarmes
  grafana/
    dashboard.json          dashboard importável
  logs/                     logs JSON gerados em execução (ignorada pelo Git)
  docs/
    Plano-Observabilidade-Itau.pptx
    Relatorio-Gerencial-Observabilidade-v4.docx
    prints/                 evidências dos experimentos
  README.md
```

### Pré-requisitos

- Windows 10 ou superior (Linux e macOS funcionam com ajustes nos comandos)
- Python 3.12
- Prometheus 3.13 LTS (prometheus.io/download)
- Grafana OSS 13.2, ou versões 11 e 12 (grafana.com/grafana/download, opção Standalone Windows Binaries)
- 8 GB de RAM (o conjunto usa cerca de 600 MB) e cerca de 1 GB de disco

### Instalação

```
git clone https://github.com/SEU-USUARIO/observabilidade-conta-corrente-clientes.git
cd observabilidade-conta-corrente-clientes
py -3.12 -m pip install -r requirements.txt
```

Extraia o Prometheus e o Grafana em qualquer pasta (não há instalador). Se o seu Python não for o 3.12, edite o `iniciar.bat` e troque `py -3.12` pelo comando equivalente.

### Como executar

Mantenha quatro janelas abertas durante os testes.

1. **Serviços simulados.** Dê dois cliques no `iniciar.bat`. Teste em `http://127.0.0.1:8001/metrics`.
2. **Prometheus.** Na pasta do Prometheus (ajuste o caminho do projeto):

```
prometheus.exe --config.file=C:\caminho\do\projeto\prometheus\prometheus.yml --storage.tsdb.retention.time=2d
```

Confira `http://localhost:9090/targets`: os dois alvos devem estar **UP**.

3. **Grafana.** Na pasta do Grafana:

```
bin\grafana.exe server
```

Nas versões recentes o executável se chama `grafana.exe`. Aguarde cerca de 1 minuto e abra `http://localhost:3000` (usuário `admin`, senha `admin`).

4. **Fonte de dados e dashboard.** Connections, Data sources, Add data source, Prometheus, URL `http://localhost:9090`, Save and test. Depois Dashboards, New, Import, envie `grafana/dashboard.json`.
5. **Carga.** Em um terminal na pasta do projeto:

```
py -3.12 carga.py 10 1500
```

Em cerca de 1 minuto os gráficos recebem dados: disponibilidade de 100% e p99 da movimentação perto de 250 ms.

**Endpoints**

| Serviço | Método e rota | Operação |
|---|---|---|
| conta-corrente (8001) | `POST /movimentacao?tipo=credito` ou `debito` | Movimentação de saldo |
| conta-corrente (8001) | `POST /contas` | Cadastro de conta |
| conta-corrente (8001) | `POST /contas/cancelamento` | Cancelamento de conta |
| conta-corrente (8001) | `POST /fraude/bloqueio` | Bloqueio por fraude |
| clientes (8002) | `POST /clientes` | Inclusão de cliente |
| clientes (8002) | `POST /clientes/inativacao` | Inativação (aciona o cancelamento de contas) |
| ambos | `GET /metrics` | Métricas para o Prometheus |
| ambos | `POST /admin/falha?erro=0.5&latencia=0.8` | Injeção de falha |

### Gerador de carga

O `carga.py` mantém a proporção exata da volumetria do desafio.

```
py -3.12 carga.py [requisicoes_por_segundo] [duracao_em_segundos]
```

A média real do desafio é de cerca de 1,2 req/s. Com 10 req/s o tempo é comprimido cerca de 8 vezes: 10 minutos de teste representam cerca de 83 minutos de tráfego real. Se o computador ficar lento, use `py -3.12 carga.py 5 600`.

### Cenários de falha

**Protocolo:** (1) apague a pasta `data` do Prometheus e reinicie-o; (2) rode a carga e espere 5 minutos de linha de base; (3) injete a falha e mantenha por 9 a 10 minutos; (4) registre `http://localhost:9090/alerts` e o dashboard (Last 15 minutes); (5) remova a falha, mantenha a carga e espere cerca de 16 minutos para registrar a recuperação.

| Cenário | Hipótese | Comando |
|---|---|---|
| 1. Erros 5xx | Falhas de aplicação são detectadas pelo burn rate e a cascata gera inconsistência visível | `curl.exe -X POST "http://127.0.0.1:8001/admin/falha?erro=0.5"` |
| 2. Lentidão sem erro | A degradação de latência só é detectada pelo p99 | `curl.exe -X POST "http://127.0.0.1:8001/admin/falha?latencia=0.8"` |
| 3. Serviço fora do ar | A indisponibilidade é detectada por `up` e ausência de tráfego | `Ctrl + C` na janela da conta-corrente (manter a carga) |

Para religar apenas a conta-corrente no cenário 3:

```
set SERVICO=conta-corrente&& py -3.12 -m uvicorn app:app --host 127.0.0.1 --port 8001
```

Para remover as falhas injetadas:

```
curl.exe -X POST "http://127.0.0.1:8001/admin/falha?erro=0&latencia=0"
```

### Catálogo de métricas

| Métrica | Tipo | Rótulos | Uso |
|---|---|---|---|
| `http_requests_total` | counter | servico, operacao, status | Tráfego e erros |
| `http_request_duration_seconds` | histogram | servico, operacao | Latência (p50, p95, p99) |
| `http_requests_in_progress` | gauge | servico | Saturação |
| `db_pool_em_uso` e `db_pool_capacidade` | gauge | servico | Saturação do pool simulado |
| `processo_cpu_percent` e `processo_memoria_mb` | gauge | servico | Saturação |
| `movimentacoes_total` | counter | tipo, resultado | Negócio |
| `movimentacao_valor_reais_total` | counter | tipo | Valor movimentado em R$ |
| `contas_abertas_total` e `contas_canceladas_total` | counter | nenhum | Negócio |
| `bloqueios_fraude_total` | counter | motivo | Fraude |
| `bloqueio_fraude_efetivacao_seconds` | histogram | nenhum | Tempo até efetivar o bloqueio |
| `clientes_incluidos_total` e `clientes_inativados_total` | counter | nenhum | Negócio |
| `inconsistencias_cliente_conta_total` | counter | nenhum | Inativações sem cancelamento de conta |

Regras de gravação (SLIs): `servico:requisicoes:taxa5m`, `servico:erros_5xx:razao5m` e `servico:latencia_p99:5m`. Erro técnico (5xx) e erro de negócio (422) são separados, nenhum rótulo usa identificador de conta ou cliente, e a latência usa histogramas porque a média esconde a cauda.

### SLOs propostos e orçamento de erro

O enunciado não fornece SLAs nem SLOs. As metas abaixo são propostas iniciais, a validar com o negócio e calibrar com dados reais.

| Serviço | Meta (30 dias) |
|---|---|
| Movimentação | 99,9% de disponibilidade e 99% das requisições abaixo de 300 ms |
| Bloqueio por fraude | 99,5% dos bloqueios efetivados em menos de 2 s |
| Demais serviços | 99,5% de disponibilidade |

**Requisições elegíveis.** A disponibilidade considera todas as requisições HTTP da operação. Respostas 5xx são falhas. Respostas 422 (saldo insuficiente) e demais 4xx são tratadas como respostas válidas, por representarem regras de negócio, e não consomem o orçamento.

**Orçamento de erro.** Em um mês de 30 dias e com volume constante de 100 mil requisições por dia, o orçamento da movimentação (0,1%) corresponde a aproximadamente 3.000 falhas, cerca de 100 por dia. O alarme de burn rate segue a abordagem multijanela do SRE Workbook: o limite é 14,4 vezes o consumo sustentável, ou seja, taxa de erro acima de 1,44%. **O alarme exige as duas condições ao mesmo tempo** (janelas de 5 minutos e 1 hora): a longa confirma que o consumo é relevante e a curta garante que o problema ainda está ativo. Exceder o limite em apenas uma janela não dispara o alarme.

### Alarmes

São 14 regras em `prometheus/regras.yml`. O princípio é alertar sobre sintoma, não sobre causa.

| Nível | Alarme | Condição de disparo | Janela e persistência |
|---|---|---|---|
| Crítico | ServicoForaDoAr | Alvo sem resposta ao scrape (`up == 0`) | Persistência de 1 min |
| Crítico | MovimentacaoBurnRateAlto | Taxa de 5xx acima de 1,44% nas duas janelas ao mesmo tempo | 5 min e 1 h; persistência de 2 min |
| Crítico | MovimentacaoErroAlto | Razão de 5xx acima de 2% | 5 min; persistência de 2 min |
| Crítico | MovimentacaoLatenciaP99Alta | p99 acima de 0,8 s | 5 min; persistência de 2 min |
| Crítico | MovimentacaoSemTrafego | Serviço ativo sem requisições (taxa igual a zero) ou métrica ausente (alvo indisponível, redundante com `up == 0`) | 5 min; persistência de 3 min |
| Crítico | FraudeBloqueioLento | Proporção de bloqueios acima de 2 s superior a 5% (10x o orçamento de 0,5%), com pelo menos 20 bloqueios | 1 h; imediato |
| Crítico | FraudeFalhas | 3 ou mais respostas 5xx no bloqueio por fraude | 15 min; imediato |
| Crítico | InconsistenciaClienteConta | Contador de inativações sem cancelamento maior que 0 | 15 min; imediato |
| Aviso | PoolConexoesSaturado | Conexões em uso acima de 80% da capacidade | Persistência de 2 min |
| Aviso | CancelamentoFalhas | 3 ou mais respostas 5xx no cancelamento | 1 h; imediato |
| Aviso | CadastroErrosAltos | 5xx acima de 5%, com pelo menos 20 requisições | 30 min; imediato |
| Aviso | InclusaoClienteErrosAltos | 5xx acima de 5%, com pelo menos 20 requisições | 30 min; imediato |
| Anomalia | QuedaAbruptaMovimentacoes | Taxa abaixo de 50% da taxa de 15 min antes, com base anterior acima de 1 req/s | 5 min; persistência de 5 min |
| Anomalia | PicoBloqueiosFraude | Bloqueios acima de 3 vezes o valor de 1 h antes, com pelo menos 10 bloqueios | 15 min; imediato |

**Observações importantes**

- **FraudeBloqueioLento foi redefinida após os experimentos** para refletir o SLO (proporção acima de 2 s, calculada a partir do histograma). Nos experimentos, a versão original usava o p95 em janela de 15 minutos. A regra atual **não foi exercitada em nenhum cenário** e sua forma de cálculo ainda precisa ser validada. Em horas com menos de 20 bloqueios o alarme não é avaliado, o que é uma limitação do critério.
- Os limites de página (erros acima de 2% e p99 acima de 0,8 s) são mais folgados que as metas (0,1% e 300 ms) por desenho: o burn rate acompanha o orçamento e o limite de página evita acionar o plantão por desvios pequenos.
- A redundância entre `ServicoForaDoAr` e `MovimentacaoSemTrafego` é intencional: o primeiro cobre alvo indisponível, o segundo cobre serviço ativo sem requisições.

O Alertmanager é opcional. Os alertas aparecem em `http://localhost:9090/alerts` e no Grafana. Para notificações, rode o Alertmanager e descomente o bloco `alerting` do `prometheus.yml`.

### Logs e rastreamento

Cada requisição gera um evento JSON em `logs/<servico>.log`:

```json
{"ts": "2026-10-28T04:12:09", "level": "INFO", "service": "conta-corrente",
 "trace_id": "9f3a1c0b7d2e4a55", "msg": "request", "operacao": "movimentacao",
 "status": 200, "duracao_ms": 143}
```

O nível é INFO abaixo de 400, WARNING de 400 a 499 e ERROR a partir de 500. Nenhum dado pessoal é registrado. O `trace_id` é gerado na entrada ou recebido por `X-Trace-Id` e repassado entre serviços. Para investigar no PowerShell:

```
Get-Content logs\clientes.log -Tail 300 | % { $_ | ConvertFrom-Json } | ? msg -eq "cascata_falhou"
Select-String -Path logs\*.log -Pattern "COLE_O_TRACE_ID"
```

### Resultados dos experimentos

Valores lidos nos painéis, um experimento por cenário, carga de 10 req/s.

| Indicador | Linha de base | Cenário 1: erros 5xx | Cenário 2: lentidão | Cenário 3: serviço fora |
|---|---|---|---|---|
| Falha injetada | Nenhuma | 50% de erros 5xx | +0,8 s de latência | Indisponibilidade do serviço de conta-corrente por aproximadamente 9 minutos |
| Disponibilidade (15 min) | 100% | 64,1% | 99,9% | Sem dados |
| p99 da movimentação | cerca de 240 ms | cerca de 250 ms | 1,98 s | Sem dados |
| Alertas em Firing | 0 | 6 | 1 | 3 |
| O que detectou | Nenhum | Burn rate e erro 5xx | Latência p99 | `up == 0` e falta de tráfego |
| Efeito no negócio | Nenhum | Queda de 55% nas movimentações | Sem alteração | Movimentações iguais a zero |
| Inconsistência cliente x conta | 0 | 5 | 0 | 5 (pico de 7 ao religar) |
| Recuperação | n/a | Disponibilidade 100% | p99 261 ms e 0 alertas | Disponibilidade 99,9% e p99 249 ms |

- **Os 64,1% do cenário 1.** A falha foi ativada alguns minutos depois do início da carga e a leitura ocorreu cerca de 10 minutos depois, com a janela de 15 minutos ainda incluindo tráfego sem falha e a taxa de erro subindo de forma gradual. A estimativa fica entre 63% e 67%, a mesma ordem de grandeza do valor medido. É uma aproximação, e não um valor teórico exato, porque o instante da injeção não foi registrado em log.
- **Pool de conexões no cenário 2.** Observado: o pool atingiu picos de 100%, mas oscilou (cerca de 60% a 100%) e o aviso de pool não disparou, pois a regra exige mais de 80% de forma contínua por 2 minutos. Recomendado, não testado: avaliar a média ou o máximo do pool em janela de 2 minutos.
- **Conclusão cautelosa.** Os resultados foram compatíveis com as três hipóteses nos experimentos realizados. Como houve um único experimento por cenário, são evidências iniciais, sem repetição estatística.

### Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| "Python não foi encontrado" e abre a Microsoft Store | Atalho de execução do Windows | Use `py -3.12` ou desative o alias em Configurações, Aplicativos, Aliases de execução |
| `No module named uvicorn` | Pacotes instalados em outro Python | `py -3.12 -m pip install -r requirements.txt` |
| `Connection refused` na porta 8001 | Conta-corrente parada | Rode o `iniciar.bat` ou o comando de religar |
| Porta em uso ou janela duplicada de `clientes` | Serviço iniciado duas vezes | Feche a janela duplicada |
| `grafana-server.exe` não abre ou tem 0 bytes | Nas versões recentes o executável é outro | Use `bin\grafana.exe server` |
| Gráficos vazios | Sem tráfego ou Prometheus sem alvos | Rode a carga e confira `/targets` |
| Inativação com vários segundos de latência | `localhost` tenta IPv6 primeiro no Windows | Use `127.0.0.1`, como no `iniciar.bat` e no `carga.py` |
| Painel de disponibilidade com "No data" | Sem requisições na janela | Esperado quando o tráfego é zero |
| Prometheus não inicia após editar `regras.yml` | Erro de sintaxe na regra | Verifique a indentação e a expressão PromQL |
| Histórico antigo polui os gráficos | Dados anteriores no Prometheus | Feche o Prometheus, apague a pasta `data` e ligue de novo |

### Limitações

- Um experimento por cenário, sem repetição estatística.
- Simulador sem banco de dados real e com estado em memória.
- Traces simplificados: apenas a propagação do `trace_id`.
- SLOs e limiares são propostas iniciais, sem calibração com dados de produção.
- A regra `FraudeBloqueioLento` foi redefinida após os experimentos e não foi exercitada.
- A carga é comprimida cerca de 8 vezes em relação ao tráfego real.
- As medidas protetivas e corretivas da documentação são recomendações e não foram testadas.

### Próximos passos

OpenTelemetry com Tempo, Loki para logs, Alertmanager com Telegram ou e-mail, CloudWatch e X-Ray na AWS, PostgreSQL real com múltiplas réplicas, regra de pool baseada em média ou máximo em janela, detecção sazonal com `offset 1w` e calibração de SLOs com dados reais.

### Documentação complementar

- `docs/Plano-Observabilidade-Itau.pptx`: apresentação de até 10 minutos.
- `docs/Relatorio-Gerencial-Observabilidade-v4.docx`: relatório gerencial.
- `docs/prints/`: evidências dos experimentos.

### Referências

- BEYER, B. et al. (org.). *Site Reliability Engineering: how Google runs production systems*. Sebastopol: O'Reilly Media, 2016.
- BEYER, B. et al. (org.). *The Site Reliability Workbook: practical ways to implement SRE*. Sebastopol: O'Reilly Media, 2018.
- SRIDHARAN, C. *Distributed Systems Observability*. Sebastopol: O'Reilly Media, 2018.
- PROMETHEUS AUTHORS. *Prometheus Documentation*. Disponível em: https://prometheus.io/docs/. Acesso em: 28 out. 2026.

### Autor

Marco Aurélio Costa da Silva. Desenvolvido para o Desafio de Observabilidade do Instituto de Ciência e Tecnologia Itaú.

---

## English

Observability plan and proof of concept for two banking applications (checking account and customers), built with 100% free tools and light enough to run on a laptop with 8 GB of RAM, without Docker.

The project answers the **Observability Challenge of the Itaú Institute of Science and Technology**: define how to observe six services using golden signals, the three pillars of observability, business metrics and alerts, and prove in practice that the plan detects real failures.

### The challenge

| Application | Service | Volume | Average rate |
|---|---|---|---|
| Checking account | Balance movement (credit and debit) | 100 thousand per day | 1.2 req/s |
| Checking account | New account registration | 1 thousand per day | 42 req/h |
| Checking account | Account cancellation | 200 per day | 8 req/h |
| Checking account | Fraud blocking | 700 per day | 29 req/h |
| Customers | Customer registration | 2 thousand per day | 83 req/h |
| Customers | Customer deactivation | 100 per day | 4 req/h |

The total is about 104 thousand requests per day (around 1.2 per second). In low-volume services a single failure changes the error rate a lot (1 error in 3 requests is 33%), so the plan uses long windows, minimum volume and absolute counts instead of a 5-minute rate.

### Solution overview

- **Metrics:** Prometheus collects latency histograms, traffic and error counters, saturation gauges and business metrics.
- **Logs:** one JSON event per line, with `trace_id` and no personal data (LGPD, the Brazilian data protection law).
- **Traces:** the `trace_id` is propagated between services through the `X-Trace-Id` header (simplified version).
- **Golden signals:** latency (p50, p95 and p99), traffic, errors and saturation per operation.
- **Alerts:** 14 rules in three levels (critical, warning and anomaly).
- **Dashboard:** 18 panels in Grafana.
- **Validation:** proportional load generator and real-time fault injection.

### Architecture

```
                  +---------------------+
 carga.py  ---->  | checking acct :8001 | <----+
 (volume)         +---------------------+      |  cascade (X-Trace-Id)
        |                  | /metrics          |
        |         +---------------------+      |
        +------>  |   customers :8002   | -----+
                  +---------------------+
                           | /metrics
                           v
                  +---------------------+      14 alert rules
                  |  Prometheus :9090   | ---> http://localhost:9090/alerts
                  +---------------------+
                           |
                           v
                  +---------------------+
                  |   Grafana :3000     |  dashboard with 18 panels
                  +---------------------+

 logs/conta-corrente.log and logs/clientes.log (JSON with trace_id)
```

Both services run the same code (`app.py`). The `SERVICO` environment variable selects which API is exposed. When a customer is deactivated, the customers service calls account cancellation on the checking account service, passing the same `trace_id`. If that call fails, the inconsistency counter is incremented.

### Repository structure

```
observabilidade-conta-corrente-clientes/
  app.py                    simulated services and instrumentation
  carga.py                  load generator with the challenge volumes
  iniciar.bat               starts both services on Windows
  requirements.txt          Python dependencies
  prometheus/
    prometheus.yml          scrape configuration
    regras.yml              recording rules (SLIs) and 14 alerts
  grafana/
    dashboard.json          importable dashboard
  logs/                     JSON logs created at runtime (ignored by Git)
  docs/
    Plano-Observabilidade-Itau.pptx
    Relatorio-Gerencial-Observabilidade-v4.docx
    prints/                 experiment evidence
  README.md
```

### Requirements

- Windows 10 or later (Linux and macOS work with command adjustments)
- Python 3.12
- Prometheus 3.13 LTS (prometheus.io/download)
- Grafana OSS 13.2, or versions 11 and 12 (grafana.com/grafana/download, Standalone Windows Binaries)
- 8 GB of RAM (the whole stack uses about 600 MB) and about 1 GB of disk

### Installation

```
git clone https://github.com/YOUR-USER/observabilidade-conta-corrente-clientes.git
cd observabilidade-conta-corrente-clientes
py -3.12 -m pip install -r requirements.txt
```

Extract Prometheus and Grafana to any folder (there is no installer). If your Python is not 3.12, edit `iniciar.bat` and replace `py -3.12` with the equivalent command.

### How to run

Keep four windows open during the tests.

1. **Simulated services.** Double-click `iniciar.bat`. Test at `http://127.0.0.1:8001/metrics`.
2. **Prometheus.** In the Prometheus folder (adjust the project path):

```
prometheus.exe --config.file=C:\path\to\project\prometheus\prometheus.yml --storage.tsdb.retention.time=2d
```

Check `http://localhost:9090/targets`: both targets must be **UP**.

3. **Grafana.** In the Grafana folder:

```
bin\grafana.exe server
```

In recent versions the executable is called `grafana.exe`. Wait about 1 minute and open `http://localhost:3000` (user `admin`, password `admin`).

4. **Data source and dashboard.** Connections, Data sources, Add data source, Prometheus, URL `http://localhost:9090`, Save and test. Then Dashboards, New, Import, and upload `grafana/dashboard.json`.
5. **Load.** In a terminal in the project folder:

```
py -3.12 carga.py 10 1500
```

In about 1 minute the charts receive data: 100% availability and a movement p99 near 250 ms.

**Endpoints**

| Service | Method and route | Operation |
|---|---|---|
| checking account (8001) | `POST /movimentacao?tipo=credito` or `debito` | Balance movement |
| checking account (8001) | `POST /contas` | Account registration |
| checking account (8001) | `POST /contas/cancelamento` | Account cancellation |
| checking account (8001) | `POST /fraude/bloqueio` | Fraud blocking |
| customers (8002) | `POST /clientes` | Customer registration |
| customers (8002) | `POST /clientes/inativacao` | Deactivation (triggers account cancellation) |
| both | `GET /metrics` | Metrics for Prometheus |
| both | `POST /admin/falha?erro=0.5&latencia=0.8` | Fault injection |

### Load generator

`carga.py` keeps the exact proportion of the challenge volumes.

```
py -3.12 carga.py [requests_per_second] [duration_in_seconds]
```

The real average of the challenge is about 1.2 req/s. At 10 req/s time is compressed about 8 times: 10 minutes of testing represent about 83 minutes of real traffic. If the computer slows down, use `py -3.12 carga.py 5 600`.

### Failure scenarios

**Protocol:** (1) delete the Prometheus `data` folder and restart it; (2) run the load and wait 5 minutes for the baseline; (3) inject the fault and hold it for 9 to 10 minutes; (4) record `http://localhost:9090/alerts` and the dashboard (Last 15 minutes); (5) remove the fault, keep the load and wait about 16 minutes to record the recovery.

| Scenario | Hypothesis | Command |
|---|---|---|
| 1. 5xx errors | Application failures are detected by burn rate and the cascade creates a visible inconsistency | `curl.exe -X POST "http://127.0.0.1:8001/admin/falha?erro=0.5"` |
| 2. Slowness without errors | Latency degradation is only detected by p99 | `curl.exe -X POST "http://127.0.0.1:8001/admin/falha?latencia=0.8"` |
| 3. Service down | Unavailability is detected by `up` and missing traffic | `Ctrl + C` in the checking account window (keep the load) |

To restart only the checking account service in scenario 3:

```
set SERVICO=conta-corrente&& py -3.12 -m uvicorn app:app --host 127.0.0.1 --port 8001
```

To remove injected faults:

```
curl.exe -X POST "http://127.0.0.1:8001/admin/falha?erro=0&latencia=0"
```

### Metrics catalog

| Metric | Type | Labels | Use |
|---|---|---|---|
| `http_requests_total` | counter | servico, operacao, status | Traffic and errors |
| `http_request_duration_seconds` | histogram | servico, operacao | Latency (p50, p95, p99) |
| `http_requests_in_progress` | gauge | servico | Saturation |
| `db_pool_em_uso` and `db_pool_capacidade` | gauge | servico | Simulated pool saturation |
| `processo_cpu_percent` and `processo_memoria_mb` | gauge | servico | Saturation |
| `movimentacoes_total` | counter | tipo, resultado | Business |
| `movimentacao_valor_reais_total` | counter | tipo | Amount moved in BRL |
| `contas_abertas_total` and `contas_canceladas_total` | counter | none | Business |
| `bloqueios_fraude_total` | counter | motivo | Fraud |
| `bloqueio_fraude_efetivacao_seconds` | histogram | none | Time to enforce a block |
| `clientes_incluidos_total` and `clientes_inativados_total` | counter | none | Business |
| `inconsistencias_cliente_conta_total` | counter | none | Deactivations without account cancellation |

Recording rules (SLIs): `servico:requisicoes:taxa5m`, `servico:erros_5xx:razao5m` and `servico:latencia_p99:5m`. Technical errors (5xx) and business errors (422) are kept apart, no label uses an account or customer identifier, and latency uses histograms because the mean hides the tail.

### Proposed SLOs and error budget

The challenge statement gives no SLAs or SLOs. The targets below are initial proposals, to be validated with the business and calibrated with real data.

| Service | Target (30 days) |
|---|---|
| Movement | 99.9% availability and 99% of requests under 300 ms |
| Fraud blocking | 99.5% of blocks enforced in under 2 s |
| Other services | 99.5% availability |

**Eligible requests.** Availability considers all HTTP requests of the operation. 5xx responses are failures. 422 responses (insufficient balance) and other 4xx are treated as valid responses because they represent business rules, and they do not consume the budget.

**Error budget.** In a 30-day month with a constant volume of 100 thousand requests per day, the movement budget (0.1%) is about 3,000 failures, around 100 per day. The burn rate alert follows the multiwindow approach of the SRE Workbook: the threshold is 14.4 times the sustainable consumption, that is, an error rate above 1.44%. **The alert requires both conditions at the same time** (5-minute and 1-hour windows): the long window confirms the consumption is relevant and the short one confirms the problem is still active. Exceeding the threshold in only one window does not trigger the alert.

### Alerts

There are 14 rules in `prometheus/regras.yml`. The principle is to alert on symptoms, not causes.

| Level | Alert | Trigger condition | Window and persistence |
|---|---|---|---|
| Critical | ServicoForaDoAr | Target not responding to scrape (`up == 0`) | 1 min persistence |
| Critical | MovimentacaoBurnRateAlto | 5xx rate above 1.44% in both windows at once | 5 min and 1 h; 2 min persistence |
| Critical | MovimentacaoErroAlto | 5xx ratio above 2% | 5 min; 2 min persistence |
| Critical | MovimentacaoLatenciaP99Alta | p99 above 0.8 s | 5 min; 2 min persistence |
| Critical | MovimentacaoSemTrafego | Active service with no requests (rate equal to zero) or missing metric (unavailable target, redundant with `up == 0`) | 5 min; 3 min persistence |
| Critical | FraudeBloqueioLento | Share of blocks above 2 s greater than 5% (10x the 0.5% budget), with at least 20 blocks | 1 h; immediate |
| Critical | FraudeFalhas | 3 or more 5xx responses in fraud blocking | 15 min; immediate |
| Critical | InconsistenciaClienteConta | Counter of deactivations without cancellation greater than 0 | 15 min; immediate |
| Warning | PoolConexoesSaturado | Connections in use above 80% of capacity | 2 min persistence |
| Warning | CancelamentoFalhas | 3 or more 5xx responses in cancellation | 1 h; immediate |
| Warning | CadastroErrosAltos | 5xx above 5%, with at least 20 requests | 30 min; immediate |
| Warning | InclusaoClienteErrosAltos | 5xx above 5%, with at least 20 requests | 30 min; immediate |
| Anomaly | QuedaAbruptaMovimentacoes | Rate below 50% of the rate 15 min earlier, with previous base above 1 req/s | 5 min; 5 min persistence |
| Anomaly | PicoBloqueiosFraude | Blocks above 3 times the value 1 h earlier, with at least 10 blocks | 15 min; immediate |

**Important notes**

- **FraudeBloqueioLento was redefined after the experiments** to reflect the SLO (share above 2 s, computed from the histogram). During the experiments the original version used the p95 over a 15-minute window. The current rule **was not exercised in any scenario** and its calculation still needs validation. In hours with fewer than 20 blocks the alert is not evaluated, which is a limitation of the criterion.
- Paging thresholds (errors above 2% and p99 above 0.8 s) are looser than the targets (0.1% and 300 ms) by design: burn rate tracks the budget and the paging threshold avoids waking someone for small deviations.
- The redundancy between `ServicoForaDoAr` and `MovimentacaoSemTrafego` is intentional: the first covers an unavailable target, the second covers an active service receiving no requests.

Alertmanager is optional. Alerts appear at `http://localhost:9090/alerts` and in Grafana. For notifications, run Alertmanager and uncomment the `alerting` block in `prometheus.yml`.

### Logs and tracing

Each request produces a JSON event in `logs/<service>.log`:

```json
{"ts": "2026-10-28T04:12:09", "level": "INFO", "service": "conta-corrente",
 "trace_id": "9f3a1c0b7d2e4a55", "msg": "request", "operacao": "movimentacao",
 "status": 200, "duracao_ms": 143}
```

The level is INFO below 400, WARNING from 400 to 499 and ERROR from 500. No personal data is recorded. The `trace_id` is generated on entry or received through `X-Trace-Id` and passed between services. To investigate in PowerShell:

```
Get-Content logs\clientes.log -Tail 300 | % { $_ | ConvertFrom-Json } | ? msg -eq "cascata_falhou"
Select-String -Path logs\*.log -Pattern "PASTE_THE_TRACE_ID"
```

### Experiment results

Values read from the dashboards, one experiment per scenario, load of 10 req/s.

| Indicator | Baseline | Scenario 1: 5xx errors | Scenario 2: slowness | Scenario 3: service down |
|---|---|---|---|---|
| Injected fault | None | 50% of 5xx errors | +0.8 s of latency | Checking account service unavailable for about 9 minutes |
| Availability (15 min) | 100% | 64.1% | 99.9% | No data |
| Movement p99 | about 240 ms | about 250 ms | 1.98 s | No data |
| Alerts in Firing | 0 | 6 | 1 | 3 |
| What detected it | None | Burn rate and 5xx error | p99 latency | `up == 0` and missing traffic |
| Business effect | None | 55% drop in movements | No change | Movements equal to zero |
| Customer x account inconsistency | 0 | 5 | 0 | 5 (peak of 7 after restart) |
| Recovery | n/a | Availability 100% | p99 261 ms and 0 alerts | Availability 99.9% and p99 249 ms |

- **The 64.1% in scenario 1.** The fault was enabled a few minutes after the load started and the reading happened about 10 minutes later, with the 15-minute window still containing fault-free traffic and the error rate rising gradually. The estimate is between 63% and 67%, the same order of magnitude as the measured value. It is an approximation, not an exact theoretical value, because the injection instant was not logged.
- **Connection pool in scenario 2.** Observed: the pool peaked at 100% but oscillated (about 60% to 100%) and the pool warning did not fire, because the rule requires more than 80% continuously for 2 minutes. Recommended, not tested: evaluate the average or maximum of the pool over a 2-minute window.
- **Cautious conclusion.** The results were compatible with the three hypotheses in the experiments performed. Since there was a single experiment per scenario, they are initial evidence, without statistical repetition.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Python was not found" and the Microsoft Store opens | Windows app execution alias | Use `py -3.12` or disable the alias in Settings, Apps, App execution aliases |
| `No module named uvicorn` | Packages installed in another Python | `py -3.12 -m pip install -r requirements.txt` |
| `Connection refused` on port 8001 | Checking account service stopped | Run `iniciar.bat` or the restart command |
| Port in use or duplicate `clientes` window | Service started twice | Close the duplicate window |
| `grafana-server.exe` does not open or has 0 bytes | Recent versions use another executable | Use `bin\grafana.exe server` |
| Empty charts | No traffic or Prometheus without targets | Run the load and check `/targets` |
| Deactivation with several seconds of latency | `localhost` tries IPv6 first on Windows | Use `127.0.0.1`, as in `iniciar.bat` and `carga.py` |
| Availability panel shows "No data" | No requests in the window | Expected when traffic is zero |
| Prometheus fails to start after editing `regras.yml` | Rule syntax error | Check indentation and the PromQL expression |
| Old history pollutes the charts | Previous data in Prometheus | Close Prometheus, delete its `data` folder and start again |

### Limitations

- One experiment per scenario, without statistical repetition.
- Simulator without a real database and with in-memory state.
- Simplified traces: only `trace_id` propagation.
- SLOs and thresholds are initial proposals, not calibrated with production data.
- The `FraudeBloqueioLento` rule was redefined after the experiments and was not exercised.
- The load is compressed about 8 times relative to real traffic.
- The protective and corrective measures in the documentation are recommendations and were not tested.

### Next steps

OpenTelemetry with Tempo, Loki for logs, Alertmanager with Telegram or e-mail, CloudWatch and X-Ray on AWS, a real PostgreSQL with multiple replicas, a pool rule based on average or maximum over a window, seasonal detection with `offset 1w`, and SLO calibration with real data.

### Additional documentation

- `docs/Plano-Observabilidade-Itau.pptx`: presentation of up to 10 minutes (in Portuguese).
- `docs/Relatorio-Gerencial-Observabilidade-v4.docx`: management report (in Portuguese).
- `docs/prints/`: experiment evidence.

### References

- BEYER, B. et al. (ed.). *Site Reliability Engineering: how Google runs production systems*. Sebastopol: O'Reilly Media, 2016.
- BEYER, B. et al. (ed.). *The Site Reliability Workbook: practical ways to implement SRE*. Sebastopol: O'Reilly Media, 2018.
- SRIDHARAN, C. *Distributed Systems Observability*. Sebastopol: O'Reilly Media, 2018.
- PROMETHEUS AUTHORS. *Prometheus Documentation*. Available at: https://prometheus.io/docs/. Accessed on: Oct 28, 2026.

### Author

Marco Aurélio Costa da Silva. Developed for the Observability Challenge of the Itaú Institute of Science and Technology.
