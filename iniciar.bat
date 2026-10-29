@echo off
REM Sobe os dois servicos simulados (cada um em uma janela). Rode dentro da pasta do projeto.
start "conta-corrente :8001" cmd /k "set SERVICO=conta-corrente&& py -3.12 -m uvicorn app:app --host 127.0.0.1 --port 8001"
start "clientes :8002" cmd /k "set SERVICO=clientes&& set CONTA_URL=http://127.0.0.1:8001&& py -3.12 -m uvicorn app:app --host 127.0.0.1 --port 8002"
