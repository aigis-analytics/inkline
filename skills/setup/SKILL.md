---
name: setup
description: >
  Inkline environment health check. Use when the user asks how to set up
  Inkline, reports the bridge is not running, wants to install inkline,
  encounters an inkline error, needs to configure inkline, or wants to
  verify the installation before generating output. Keyword triggers:
  inkline not working, bridge not running, setup inkline, install inkline,
  inkline error, configure inkline, inkline bridge.
user-invocable: true
allowed-tools:
  - Bash(curl *)
  - Bash(python3 *)
  - Bash(pip *)
  - Bash(which *)
  - Bash(inkline *)
---

# Inkline Setup — Health Check Procedure

Run the following five checks in order. Print the result of each check before moving to the next. Stop at the first blocking failure and give the user a specific fix before proceeding.

## Check 1 — inkline installed

```bash
python3 -c "import inkline; print(inkline.__version__)"
```

- Pass: print the version and continue.
- Fail (ModuleNotFoundError): run `pip install inkline` and retry the check. If it still fails after install, stop and tell the user to check their Python environment (virtual env, PATH, etc.).

## Check 2 — typst available

```bash
python3 -c "import typst; print('ok')"
```

- Pass: continue.
- Fail: run `pip install --upgrade typst` and retry. If still failing, note it but do not block — typst may be installed system-wide.

## Check 3 — bridge health (primary path)

```bash
curl -s --max-time 3 http://localhost:8082/ | head -1
```

- Pass (any content returned): print "Bridge OK on port 8082" and continue.
- Fail (no response or connection refused): the bridge is not running. Attempt to start it:

```bash
inkline serve &
```

Wait 3 seconds, then re-check:

```bash
curl -s --max-time 3 http://localhost:8082/ | head -1
```

If the bridge is now responding: print "Bridge started successfully on port 8082" and continue.

If the bridge is still not responding after the start attempt: print the following message and stop further checks. This is a blocking failure.

```
Bridge not running. Start it:

    inkline serve

Keep that terminal open. Once you see "Inkline bridge running on port 8082",
re-run /inkline:setup or proceed with /inkline:deck <file>.
```

Do not attempt any further workarounds. The bridge must be running before generation is possible.

## Check 4 — API key fallback (only if bridge cannot be started)

This check applies only when Check 3 has failed and the bridge could not be started. It describes a degraded fallback mode.

```bash
python3 -c "import os; print('SET' if os.environ.get('ANTHROPIC_API_KEY') else 'MISSING')"
```

- Set: note that `mode="rules"` (deterministic, no LLM design) will work without the bridge as a last resort, but this bypasses the Archon pipeline and visual audit. Output quality will be significantly lower. The bridge is the correct path — this is only a fallback.
- Missing: note that without both the bridge and an API key, LLM-assisted generation is not possible. `mode="rules"` also requires the key when the bridge is not mediating the call. Tell the user to set `ANTHROPIC_API_KEY` in their shell environment if they need keyless-bridge operation.

Do not suggest storing the key in a file or embedding it in code. Shell environment or `.env` file only.

Note: if the user is running Claude Code via the Claude Max bridge on port 8082, the key may not appear in the shell environment even though generation works fine — the bridge handles auth transparently. Do not treat a missing key as a hard failure if the bridge itself is running.

## Check 5 — available brands

```bash
python3 -c "from inkline.brands import list_brands; print(list_brands())"
```

Print the list. If only `minimal` appears, note that private brands (aigis, tvf, aria, statler, exmachina, sparkdcs) can be added by cloning the private brands repo to `~/.config/inkline/`. This is optional — `minimal` is fully functional for all generation tasks.

## Summary output

After all checks (or after identifying a blocking failure), print a one-line status table:

```
inkline: X.X.X | typst: ok | bridge: OK (or MANUAL START REQUIRED) | brands: [list]
```

Then print the next step:

- If everything passed: "Ready — run /inkline:deck <file> to generate a slide deck, or /inkline:doc <file> for a PDF document."
- If bridge requires manual start: give the `inkline serve` instruction from Check 3 above.
- If inkline is not installed: give the `pip install inkline` instruction.
