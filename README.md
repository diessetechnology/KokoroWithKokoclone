# Voice Hub Stack

Stack Compose CPU-only con una UI unica per:

- Kokoro TTS: API TTS semplice
- KokoClone API: voice cloning / TTS
- Ultravox: chat/audio model via llama.cpp server

La UI unica e pubblica e' `voice-hub-ui` sulla porta interna `7860`.
I backend rimangono privati sulla rete Docker per default.

## File inclusi

- `docker-compose.yml`: stack principale con UI unica
- `docker-compose.public-apis.yml`: override opzionale per esporre le API pubblicamente dietro Basic Auth
- `.env.example`: variabili ambiente
- `voice-hub-ui/Dockerfile`: build della UI
- `voice-hub-ui/app.py`: codice Gradio della UI

## Deploy su Coolify

1. Crea una nuova risorsa Docker Compose.
2. Carica/incolla `docker-compose.yml`.
3. Carica anche la cartella `voice-hub-ui`.
4. Copia `.env.example` nelle variabili ambiente e modifica i valori.
5. Assegna dominio solo a:
   - servizio: `voice-hub-ui`
   - porta: `7860`
6. Se usi labels Traefik, imposta `VOICE_UI_HOST=voice.tuodominio.it`.
7. Se Coolify gestisce routing dalla UI, puoi rimuovere le labels router dal servizio `voice-hub-ui` e configurare dominio -> porta 7860 dalla UI.

## Deploy su Dokploy

Per Dokploy, se usi labels Traefik manuali, assicurati che il proxy riesca a raggiungere i container.
Se hai gateway timeout, collega i servizi anche alla rete esterna di Dokploy, spesso `dokploy-network`, e aggiungi:

```yaml
labels:
  - "traefik.docker.network=dokploy-network"
```

## Basic Auth

Genera credenziali:

```bash
docker run --rm httpd:2.4-alpine htpasswd -nbB admin 'PASSWORD_FORTE'
```

Esempio output:

```text
admin:$2y$05$abc...
```

Nel file env/Compose raddoppia i `$`:

```env
BASIC_AUTH_USERS=admin:$$2y$$05$$abc...
```

## Uso come API per una app

### App nello stesso server/rete Docker

Non esporre le API pubblicamente. La tua app chiama:

```text
http://kokoro:8880
http://kokoclone-api:8000
http://ultravox:8080
```

### App esterna

Usa l'override `docker-compose.public-apis.yml` o configura domini dalla UI:

```text
https://kokoro-api.tuodominio.it
https://clone-api.tuodominio.it
https://ultravox-api.tuodominio.it
```

Proteggi sempre con Basic Auth, Cloudflare Access, VPN, IP allowlist o un gateway API.
Non lasciare le API nude su internet.

## Test API

Kokoro:

```bash
curl -u admin:PASSWORD_FORTE \
  https://kokoro-api.tuodominio.it/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"kokoro","input":"Ciao mondo","voice":"af_heart","response_format":"wav"}' \
  --output kokoro.wav
```

Ultravox:

```bash
curl -u admin:PASSWORD_FORTE \
  https://ultravox-api.tuodominio.it/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"ultravox","messages":[{"role":"user","content":"Ciao"}],"temperature":0.4}'
```

## Nota KokoClone

La UI prova l'endpoint OpenAI-compatible `/v1/audio/speech`.
Se l'image KokoClone scelta espone un endpoint diverso, apri la tab `Debug API`, leggi `/openapi.json` e modifica la funzione `kokoclone_tts()` in `voice-hub-ui/app.py`.
