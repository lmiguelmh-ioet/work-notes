# ODS — local inference (Qwen on llama-server)

Running log of setup facts and fixes for the ODS install in `~/ods` (native
`llama-server` on the M4 Pro MacBook, 48 GB unified memory).

## Setup facts

- Install dir: `~/ods` · config: `~/ods/.env` · models: `~/ods/data/models/`
- Server log: `~/ods/data/llama-server.log` · PID file: `~/ods/data/.llama-server.pid`
- Endpoint: `http://localhost:8080/v1` (OpenAI-compatible) · LAN: `http://192.168.2.113:8080/v1`
- Key `.env` keys: `GGUF_FILE` (active model), `CTX_SIZE`, `N_GPU_LAYERS`, `BIND_ADDRESS`
- Restart: `cd ~/ods && ./ods-macos.sh restart llama-server` — run it from your own
  terminal. A server started from an agent/IDE shell gets killed when that shell's
  command finishes (process-group reaping).
- Active model: `hf-unsloth-Qwen3.8-27B-GGUF-Qwen3.8-27B-UD-Q8_K_XL-13252cc0.gguf` (29 GB).
  Thinking model — chat responses include `<think>` blocks; budget `max_tokens` accordingly.
- Measured on M4 Pro 48 GB: ~19 tok/s prompt processing, ~7 tok/s generation.

## Fix log

### 2026-11-24 — LAN access: server bound to loopback

- **Signature:** `curl localhost:8080/v1/models` works; `curl 192.168.2.113:8080/...`
  fails instantly with "Couldn't connect to server".
- **Cause:** ODS defaults `BIND_ADDRESS=127.0.0.1`; `ods-macos.sh` passes it to
  `llama-server --host`.
- **Fix:** `BIND_ADDRESS=0.0.0.0` in `~/ods/.env`, restart. Verified `TCP *:8080 (LISTEN)`.
- **Note:** the LLM API has no auth — it is exposed to the whole LAN.

### 2026-11-24 — LAN access: router AP isolation

- **Signature:** other PCs cannot even ping the Mac; `arp -a` on the Mac shows
  `(incomplete)` for the PC's IP. Both devices reach the gateway and internet.
- **Cause:** ARP `(incomplete)` for a same-subnet host means the L2 fabric drops
  client-to-client frames — router AP/client isolation, not a host firewall.
- **Fix:** disabled AP isolation in the router admin. Ping + inference from the PC
  (192.168.2.77) worked immediately after.

### 2026-11-25 — New model failed to load: llama.cpp too old

- **Sequence:** swapping models is normally config-only (`GGUF_FILE` + restart).
  That alone failed here — b8210 crashed on load. Upgrading only the binary
  (config untouched) then loaded the same GGUF. Config selects the model;
  the binary was the blocker.
- **Signature:** restart prints "llama-server may still be loading model...", then
  the log shows `missing tensor 'blk.64.ssm_conv1d.weight'` and
  `main: exiting due to model loading error`. Nothing listens on 8080.
- **Cause:** Qwen3.8 is a hybrid SSM architecture; the bundled September build
  (b8210) predates it. ODS never refreshes the native binary after install.
- **Fix:** upgraded `~/ods/bin` llama.cpp b8210 → b12359 (current nightly via the
  `v1.0.0` release's `nightly-tag.txt`). Old files backed up at `~/ods/bin.bak-b8210/`.
  Only the llama-owned files were swapped (`llama-server` + `libggml*`/`libllama*`/
  `libmtmd*` dylibs); ODS's own tools in `~/ods/bin` were left untouched.
- **Revert:** the Qwen3.5 model file was never deleted — flip `GGUF_FILE` back to
  `Qwen3.5-27B-Q4_K_M.gguf` and restart (it runs fine on b12359). The full binary
  rollback — `rm -rf ~/ods/bin && mv ~/ods/bin.bak-b8210 ~/ods/bin` — is only
  needed if b12359 itself misbehaves.
- **Memory knob:** 29 GB model + ~5 GB KV cache (CTX_SIZE=65536) is near the edge
  of 48 GB. If Metal allocation fails or the system swaps, set `CTX_SIZE=32768`.

### 2026-11-25 — API model name alias

- **Signature:** chat responses report `"model": "/Users/luis.mamani/ods/data/models/..."`
  (the full path) instead of a clean name.
- **Fix:** `LLAMA_ARG_ALIAS=qwen3.8-27b` in `.env`, passed to llama-server as
  `--alias`. `/v1/models` and all responses then show `qwen3.8-27b`; clients must
  send that name in requests.
- **Local patch:** `ods-macos.sh` had no alias passthrough, so one line was added
  after the other `LLAMA_ARG_*` extras in `start_native_llama`:
  `[[ -n "${ENV_LLAMA_ARG_ALIAS:-}" ]] && llama_args+=(--alias "$ENV_LLAMA_ARG_ALIAS")`.
  An `ods-update.sh` run may overwrite `ods-macos.sh` — if the alias disappears
  after an update, re-add that line.
