# Docker Compose Template

## Cloudflared Service Configuration

```yaml
cloudflared:
  image: cloudflare/cloudflared:latest
  container_name: cloudflared-<service-name>
  dns:
    - 1.1.1.1
    - 8.8.8.8
  extra_hosts:
    - "host.docker.internal:host-gateway"
  volumes:
    - ~/.cloudflared:/etc/cloudflared:ro
  command: tunnel --no-autoupdate --config /etc/cloudflared/config-<service>.yml run
  restart: unless-stopped
  depends_on:
    - <backend-service>
```

## Key Configuration Points

| Config | Purpose |
|--------|---------|
| `dns: 1.1.1.1, 8.8.8.8` | Avoid DNS pollution |
| `extra_hosts` | Allow container to access host services |
| `volumes: ~/.cloudflared` | Mount tunnel credentials |
| `depends_on` | Start after backend service |

## Complete Example

```yaml
version: '3.8'

services:
  my-service:
    build: .
    container_name: my-service
    ports:
      - "8000:8000"
    restart: unless-stopped

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared-my-service
    dns:
      - 1.1.1.1
      - 8.8.8.8
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ~/.cloudflared:/etc/cloudflared:ro
    command: tunnel --no-autoupdate --config /etc/cloudflared/config-my-service.yml run
    restart: unless-stopped
    depends_on:
      - my-service
```
