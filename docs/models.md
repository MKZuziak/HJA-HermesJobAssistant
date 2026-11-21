# Changing the model

Hermes talks to one model at a time, chosen with `hermes model`:

```sh
docker exec -it -u hermes hermes hermes model
make restart
```

Scheduled jobs use the same model, so a change applies to every run.

| Option | How | Billing |
|---|---|---|
| Claude subscription (default) | `make login`, then *Claude Subscription DirectSDK (Experimental)* → `sonnet`, `opus` or `haiku` | Your Pro/Max plan |
| Anthropic API key | `hermes model` → Anthropic → paste the key | Per token |
| Nous Portal | `hermes model` → Nous Portal | Nous plan or credits |
| OpenAI, OpenRouter, others | `hermes model` → provider → paste the key | Per token |
| Self-hosted (vLLM, Ollama, …) | `model:` block in `~/.hermes/config.yaml`, below | Your hardware |

Self-hosted, OpenAI-compatible endpoint:

```yaml
model:
  provider: custom
  model: my-model
  base_url: http://vllm:8000/v1   # container or host name, not localhost
  api_key: "none"
```

A single job can also use its own model: `hermes cron edit scout --model <model> --provider <provider>`.

## Notes

- Provider names in the `hermes model` menu may differ slightly from this table.
- Sonnet is enough for scouting; Opus writes better cover letters but uses your limits faster.
- Skills, memory and history are plain files, so they carry over to any model.
- Weaker models are more likely to ignore rules such as "never guess deadlines". After switching, run `make run` and review the report.
- The subscription plugin is experimental, and Anthropic's rules for third-party agents have changed several times. Check the current terms in the Claude Help Center (*"Use the Claude Agent SDK with your Claude plan"*).
- Remove keys you no longer use from `~/.hermes/.env`.
