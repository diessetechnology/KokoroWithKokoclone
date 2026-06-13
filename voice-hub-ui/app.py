import os
import json
import tempfile

import gradio as gr
import requests


KOKORO_API_BASE = os.getenv("KOKORO_API_BASE", "http://kokoro:8880").rstrip("/")
KOKOCLONE_API_BASE = os.getenv("KOKOCLONE_API_BASE", "http://kokoclone-api:8000").rstrip("/")
ULTRAVOX_API_BASE = os.getenv("ULTRAVOX_API_BASE", "http://ultravox:8080").rstrip("/")


def api_status():
    rows = []
    for name, base in [
        ("Kokoro", KOKORO_API_BASE),
        ("KokoClone", KOKOCLONE_API_BASE),
        ("Ultravox", ULTRAVOX_API_BASE),
    ]:
        ok = False
        detail = ""
        for path in ["/health", "/v1/models", "/docs", "/"]:
            try:
                r = requests.get(f"{base}{path}", timeout=8)
                if r.status_code < 500:
                    ok = True
                    detail = f"{path} -> HTTP {r.status_code}"
                    break
                detail = f"{path} -> HTTP {r.status_code}"
            except Exception as exc:
                detail = str(exc)
        rows.append([name, "online" if ok else "offline", base, detail])
    return rows


def save_audio_response(response, suffix=".wav"):
    if not response.ok:
        raise gr.Error(f"API error {response.status_code}: {response.text[:1200]}")
    output = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    output.write(response.content)
    output.close()
    return output.name


def kokoro_tts(text, voice, speed, response_format):
    if not text or not text.strip():
        raise gr.Error("Inserisci un testo.")

    payload = {
        "model": "kokoro",
        "input": text,
        "voice": voice,
        "speed": float(speed),
        "response_format": response_format,
    }
    r = requests.post(
        f"{KOKORO_API_BASE}/v1/audio/speech",
        json=payload,
        timeout=300,
    )
    return save_audio_response(r, suffix=f".{response_format}")


def kokoclone_tts(text, voice_sample, language, speed):
    if not text or not text.strip():
        raise gr.Error("Inserisci un testo.")

    data = {
        "input": text,
        "language": language,
        "speed": str(speed),
    }
    files = {}
    if voice_sample:
        files["voice_sample"] = open(voice_sample, "rb")

    try:
        # Default endpoint for OpenAI-compatible speech APIs.
        # If your KokoClone image exposes a different route, open the Debug API tab
        # and inspect /openapi.json, then change this route.
        r = requests.post(
            f"{KOKOCLONE_API_BASE}/v1/audio/speech",
            data=data,
            files=files,
            timeout=600,
        )
        return save_audio_response(r, suffix=".wav")
    finally:
        for file_obj in files.values():
            file_obj.close()


def ultravox_chat(message, temperature, max_tokens):
    if not message or not message.strip():
        raise gr.Error("Scrivi un messaggio.")

    payload = {
        "model": "ultravox",
        "messages": [{"role": "user", "content": message}],
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
    }
    r = requests.post(
        f"{ULTRAVOX_API_BASE}/v1/chat/completions",
        json=payload,
        timeout=600,
    )
    if not r.ok:
        raise gr.Error(f"Ultravox error {r.status_code}: {r.text[:1200]}")

    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(data, ensure_ascii=False, indent=2)


def get_openapi(service):
    base = {
        "Kokoro": KOKORO_API_BASE,
        "KokoClone": KOKOCLONE_API_BASE,
        "Ultravox": ULTRAVOX_API_BASE,
    }[service]
    try:
        r = requests.get(f"{base}/openapi.json", timeout=10)
        if r.ok:
            return json.dumps(r.json(), ensure_ascii=False, indent=2)[:15000]
        return f"HTTP {r.status_code}\n{r.text[:4000]}"
    except Exception as exc:
        return str(exc)


def raw_post(service, path, body):
    base = {
        "Kokoro": KOKORO_API_BASE,
        "KokoClone": KOKOCLONE_API_BASE,
        "Ultravox": ULTRAVOX_API_BASE,
    }[service]
    try:
        payload = json.loads(body or "{}")
    except Exception as exc:
        raise gr.Error(f"JSON non valido: {exc}")
    r = requests.post(f"{base}{path}", json=payload, timeout=600)
    content_type = r.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return json.dumps(r.json(), ensure_ascii=False, indent=2)
        except Exception:
            pass
    return f"HTTP {r.status_code}\n{r.text[:12000]}"


with gr.Blocks(title="Voice Hub") as demo:
    gr.Markdown("# Voice Hub")
    gr.Markdown("UI unica per Kokoro, KokoClone e Ultravox. Le API backend restano interne alla rete Docker, salvo override pubblico.")

    with gr.Tab("Status"):
        refresh = gr.Button("Aggiorna stato")
        status_table = gr.Dataframe(
            headers=["Servizio", "Stato", "Base URL", "Dettaglio"],
            datatype=["str", "str", "str", "str"],
            value=api_status,
            interactive=False,
        )
        refresh.click(fn=api_status, outputs=status_table)

    with gr.Tab("Kokoro TTS"):
        kokoro_text = gr.Textbox(label="Testo", lines=6, placeholder="Scrivi il testo da sintetizzare...")
        with gr.Row():
            kokoro_voice = gr.Textbox(label="Voce", value="af_heart")
            kokoro_speed = gr.Slider(label="Velocita", minimum=0.5, maximum=1.5, value=1.0, step=0.05)
            kokoro_format = gr.Dropdown(label="Formato", choices=["wav", "mp3", "opus", "flac"], value="wav")
        kokoro_btn = gr.Button("Genera con Kokoro")
        kokoro_output = gr.Audio(label="Audio generato", type="filepath")
        kokoro_btn.click(fn=kokoro_tts, inputs=[kokoro_text, kokoro_voice, kokoro_speed, kokoro_format], outputs=kokoro_output)

    with gr.Tab("KokoClone"):
        clone_text = gr.Textbox(label="Testo", lines=6, placeholder="Scrivi il testo da generare con la voce clonata...")
        clone_sample = gr.Audio(label="Sample voce", type="filepath")
        with gr.Row():
            clone_lang = gr.Dropdown(label="Lingua", choices=["it", "en", "fr", "es", "pt", "ja", "zh", "hi"], value="it")
            clone_speed = gr.Slider(label="Velocita", minimum=0.5, maximum=1.5, value=1.0, step=0.05)
        clone_btn = gr.Button("Genera con KokoClone")
        clone_output = gr.Audio(label="Audio generato", type="filepath")
        clone_btn.click(fn=kokoclone_tts, inputs=[clone_text, clone_sample, clone_lang, clone_speed], outputs=clone_output)

    with gr.Tab("Ultravox Chat"):
        uv_message = gr.Textbox(label="Messaggio", lines=5, placeholder="Chiedi qualcosa a Ultravox...")
        with gr.Row():
            uv_temp = gr.Slider(label="Temperature", minimum=0.0, maximum=1.5, value=0.4, step=0.05)
            uv_tokens = gr.Slider(label="Max token", minimum=32, maximum=2048, value=512, step=32)
        uv_btn = gr.Button("Invia a Ultravox")
        uv_output = gr.Textbox(label="Risposta", lines=12)
        uv_btn.click(fn=ultravox_chat, inputs=[uv_message, uv_temp, uv_tokens], outputs=uv_output)

    with gr.Tab("Debug API"):
        gr.Markdown("Usa questa tab per verificare gli endpoint reali, soprattutto KokoClone.")
        service = gr.Dropdown(label="Servizio", choices=["Kokoro", "KokoClone", "Ultravox"], value="Kokoro")
        openapi_btn = gr.Button("Leggi /openapi.json")
        openapi_output = gr.Code(label="OpenAPI", language="json")
        openapi_btn.click(fn=get_openapi, inputs=service, outputs=openapi_output)

        gr.Markdown("## Raw POST")
        raw_path = gr.Textbox(label="Path", value="/v1/chat/completions")
        raw_body = gr.Code(label="JSON body", language="json", value='{"model":"ultravox","messages":[{"role":"user","content":"Ciao"}]}')
        raw_btn = gr.Button("Invia POST")
        raw_output = gr.Code(label="Risposta", language="json")
        raw_btn.click(fn=raw_post, inputs=[service, raw_path, raw_body], outputs=raw_output)


demo.queue().launch(
    server_name=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
    server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
)
