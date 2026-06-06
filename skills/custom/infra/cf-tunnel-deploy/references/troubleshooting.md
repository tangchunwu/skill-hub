# Troubleshooting Guide

## DNS Pollution (198.18.x.x)

**Symptom**: `nslookup <domain>` returns `198.18.0.x` instead of real Cloudflare IPs.

**Solution**: Add DNS servers to Docker container:

```yaml
dns:
  - 1.1.1.1
  - 8.8.8.8
```

**Verify**: Real Cloudflare IPs are `104.x.x.x` or `172.67.x.x`.

```bash
nslookup <domain> 1.1.1.1
```

## TLS Handshake Error

**Symptom**:
```
ERR Unable to establish connection with Cloudflare edge error="TLS handshake with edge error: EOF"
```

**Cause**: DNS pollution returning fake IPs.

**Solution**: Add clean DNS to container (see above).

## 404 from Cloudflare

**Symptom**: HTTP 404 with `server: cloudflare` header, tunnel logs show no requests.

**Possible Causes**:

1. **Wrong DNS route**: Check tunnel ID matches
   ```bash
   cloudflared tunnel route dns <tunnel-name> <hostname>
   ```
   If shows wrong tunnel ID, force update:
   ```bash
   cloudflared tunnel route dns -f <correct-tunnel-id> <hostname>
   ```

2. **DNS not propagated**: Wait 1-2 minutes after adding CNAME.

3. **SSL mode wrong**: Set Cloudflare SSL to **Flexible**.

## host.docker.internal Not Accessible

**Symptom**: Tunnel connects but requests fail to reach backend.

**Solution**: Add to Docker run/compose:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

## Tunnel Routes to Wrong Service

**Symptom**: `cloudflared tunnel route dns` shows different tunnel ID.

**Solution**: Use `-f` flag with explicit tunnel UUID:

```bash
cloudflared tunnel route dns -f <tunnel-uuid> <hostname>
```
