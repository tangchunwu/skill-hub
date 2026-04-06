---
name: openclaw-cloudpc-bridge
description: Build and troubleshoot a "OpenClaw on overseas host + cloud desktop as execution node" setup using reverse SSH. Use when user asks to control a cloud desktop from OpenClaw, configure reverse tunnels, persist auto-reconnect, or migrate this architecture to new servers/cloud PCs (Windows/macOS/Linux).
---

# OpenClaw Cloud PC Bridge

Use this workflow to keep an overseas OpenClaw gateway while delegating execution work to a cloud desktop through reverse SSH.

## Architecture

- Gateway node: overseas Linux server, runs OpenClaw and model/IM connectivity.
- Execution node: cloud desktop (Windows/macOS/Linux), runs user workloads.
- Tunnel direction: execution node initiates SSH to overseas host with `-R`.
- Control path: OpenClaw shell command on overseas host -> reverse port -> execution node.

## Standard Workflow

1. Ensure overseas host SSH access works with key auth.
2. Enable SSH server on cloud desktop.
3. Generate cloud-desktop outbound key and add its public key to overseas host `authorized_keys`.
4. Generate overseas-to-desktop key and add its public key to desktop `authorized_keys`.
5. Start reverse tunnel from desktop to overseas host.
6. Verify from overseas host that desktop commands run.
7. Create wrapper commands (`cloudpc-ps`, `cloudpc-run`) on overseas host.
8. Persist tunnel with auto-reconnect (scheduled task, launchd, or systemd user service).

## Command Patterns

### A) Desktop -> Overseas reverse tunnel

Windows PowerShell example:

```powershell
ssh -i $env:USERPROFILE\.ssh\cloudpc_to_do -NT -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -R 2222:127.0.0.1:22 root@<OVERSEAS_IP>
```

macOS/Linux desktop example:

```bash
ssh -i ~/.ssh/cloudpc_to_do -NT -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -R 2222:127.0.0.1:22 root@<OVERSEAS_IP>
```

### B) Overseas host test execution

```bash
ssh -i /root/.ssh/openclaw_to_cloudpc -p 2222 Administrator@127.0.0.1 "whoami && hostname"
```

### C) Wrapper commands on overseas host

- `cloudpc-ps "<PowerShell command>"`: run PowerShell on Windows desktop.
- `cloudpc-run "<command string>"`: run generic remote command.

Prefer wrapper calls in OpenClaw prompts to avoid instance-ID confusion.

## Troubleshooting Decision Tree

1. Error: `Permission denied (publickey)`
   - Check key path and key permissions.
   - Confirm public key exists in target `authorized_keys`.

2. Error: `remote port forwarding failed for listen port <PORT>`
   - Remote port occupied by stale tunnel.
   - Kill stale SSH session on overseas host or choose new port (e.g., `2233`).

3. Reverse port listens but login closes immediately
   - Desktop SSH service not running or misconfigured.
   - Start/reinstall `sshd`, check host keys and file permissions.

4. Works once, breaks after reboot
   - Add persistent auto-reconnect job on desktop.
   - Keep tunnel command under user context with key access.

## Migration Checklist (New Infra)

For future server/cloud-desktop replacement, change only endpoints and keys:

- Replace overseas host IP/domain.
- Replace desktop username/path format (`Administrator`, `ubuntu`, etc.).
- Regenerate and re-register both key pairs.
- Recreate reverse-tunnel persistence job.
- Re-run verification (`whoami`, `hostname`, test file write).
- Update OpenClaw prompt memory/instructions so agent uses wrappers by default.

## Safety Rules

- Never expose raw `ws://` on public internet for sensitive traffic.
- Prefer SSH tunnel or TLS (`wss://`) for remote dashboard/control.
- Keep private keys out of chat logs and shared channels.
- Restrict `authorized_keys` and rotate keys during infra migration.
