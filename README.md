# Dokploy Voice Stack CPU

Stack Docker Compose per Dokploy con:

- Kokoro TTS CPU: API/OpenAI-compatible e UI docs sulla porta interna `8880`.
- KokoClone CPU: UI/API Gradio sulla porta interna `7860`.
- Ultravox CPU quantizzato: `llama.cpp` server con modello GGUF `Q4_K_M` sulla porta interna `8080`.

## Deploy rapido su Dokploy

1. Crea un nuovo progetto/app Docker Compose in Dokploy.
2. Carica/incolla `docker-compose.yml`.
3. Copia `.env.example` nelle variabili Dokploy, poi modifica domini, thread CPU e password.
4. Crea tre domini nel tab **Domains** di Dokploy:
   - `kokoro.example.com` -> servizio `kokoro`, porta `8880`
   - `kokoclone.example.com` -> servizio `kokoclone`, porta `7860`
   - `ultravox.example.com` -> servizio `ultravox`, porta `8080`
5. Abilita HTTPS/SSL dai Domains di Dokploy.
6. Proteggi i domini con Basic Auth / middleware / protection layer di Dokploy o del proxy davanti.

> Importante: non mappare porte pubbliche nel compose. I servizi usano solo `expose`, quindi non sono pubblicati direttamente su internet.

## Protezione

Questo pacchetto include una variante opzionale con label Traefik in `docker-compose.traefik-labels.yml`, ma in Dokploy è consigliato usare il tab **Domains** per associare dominio e porta.

Per password Basic Auth con Traefik labels:

```bash
sudo apt-get install apache2-utils -y
htpasswd -nbB admin 'PASSWORD_FORTE'
```

Copia l'hash dopo `admin:` in `BASIC_AUTH_PASSWORD_HASH`.

Per esposizione pubblica reale, consigliato anche uno tra:

- Cloudflare Access / Zero Trust
- VPN o Tailscale
- allowlist IP sul firewall
- WAF/rate limit a monte

## Test API

### Kokoro

```bash
curl -u admin:PASSWORD_FORTE \
  https://kokoro.example.com/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"kokoro","input":"Ciao, questo è un test.","voice":"af_heart"}' \
  --output kokoro.wav
```

### Ultravox / llama.cpp

```bash
curl -u admin:PASSWORD_FORTE \
  https://ultravox.example.com/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"ultravox","messages":[{"role":"user","content":"Rispondi in italiano: cosa sai fare?"}],"temperature":0.4}'
```

## CPU tuning

- `ULTRAVOX_THREADS`: mettilo uguale o leggermente inferiore ai core fisici.
- `OMP_NUM_THREADS`: 2-8 di solito va bene.
- Ultravox usa il modello 1B `Q4_K_M`, più adatto a CPU rispetto a modelli 8B.
- Se la macchina è piccola, lascia `ULTRAVOX_CTX=2048`.

## Note

- Dokploy salva le variabili definite nel suo editor in un file `.env` accanto al compose; il compose deve comunque referenziarle con `${VAR}`.
- Se usi il file opzionale `docker-compose.traefik-labels.yml`, verifica che la tua installazione Dokploy/Traefik legga le label Docker e che il certresolver si chiami davvero `letsencrypt`.
