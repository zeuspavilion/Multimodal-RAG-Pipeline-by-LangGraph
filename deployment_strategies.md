# Deployment Strategies — Zeus Multimodal RAG Pipeline

This document outlines the hosting platforms, architectural blueprints, configuration files, and steps required to deploy the **Zeus Multimodal RAG Pipeline** in production environments.

---

## 1. Production Architecture Overview

In a production environment, we separate client-side assets from the dynamic, CPU-heavy API nodes. This ensures cost-effectiveness, scalability, and robust security.

```mermaid
graph TB
    subgraph "Clients"
        Browser["User Web Browser"]
    end

    subgraph "Edge / Static Hosting"
        CDN["Vercel / Cloudflare CDN"]
        FE["React Frontend (SPA)<br/>Static Assets"]
    end

    subgraph "Application Layer (FastAPI Backend)"
        LB["Application Load Balancer / Nginx"]
        BE1["Uvicorn Backend Instance 1"]
        BE2["Uvicorn Backend Instance 2"]
    end

    subgraph "Data & Caching Layer"
        PG["Neon Serverless PostgreSQL<br/>(pgvector enabled)"]
        RD["Upstash Serverless Redis<br/>(Cache layer)"]
        FS["Persistent File Volumes<br/>(Local VPS / S3 Storage)"]
    end

    subgraph "External AI Interfaces"
        Groq["Groq Cloud API<br/>(Inference)"]
        Tavily["Tavily Search API<br/>(Web Search)"]
    end

    Browser --> CDN
    CDN --> FE
    Browser -->|"HTTP SSE /chat/stream"| LB
    LB --> BE1 & BE2
    BE1 & BE2 -->|"Save State & Vectors"| PG
    BE1 & BE2 -->|"Caching Map-Reduce"| RD
    BE1 & BE2 -->|"Temporary Uploads"| FS
    BE1 & BE2 --> Groq & Tavily
```

---

## 2. Infrastructure Setup & Prerequisites

Before deploying the application, provision the following managed cloud services:

1. **PostgreSQL Database with `pgvector`**:
   - Create a free serverless database on [Neon PostgreSQL](https://neon.tech/).
   - Copy the database connection URL (e.g., `postgresql://neondb_owner:password@host/neondb?sslmode=require`).
   - Neon enables `pgvector` by default; Zeus automatically executes database migrations to create the required tables (`users`, `conversations`, `messages`, `document_chunks`) on startup.

2. **Redis Cache (Optional but Recommended)**:
   - Create a serverless Redis database on [Upstash Redis](https://upstash.com/).
   - Copy the `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`.
   - Caching handles Map-Reduce operations and semantic search indices to cut down API latencies and token usage.

3. **External API Keys**:
   - **Groq API Key**: For low-latency inference (Llama, Whisper, Qwen-Vision models).
   - **Tavily API Key**: For web search retrievals.
   - **Hugging Face Token** (`HF_TOKEN`): Required if you need to download embedding models or fetch Hugging Face assets.

---

## 3. Strategy A: Split PaaS Deployment (Recommended)

This strategy splits compute and hosting resources. It uses Vercel for fast, edge-cached static distribution of the frontend, and a managed container platform (Railway or Render) for the API nodes.

### Step 1: Deploying the React Frontend to Vercel
1. Create a repository on GitHub and commit the project.
2. Log in to [Vercel](https://vercel.com/) and click **Add New Project**.
3. Select your GitHub repository.
4. Set the **Root Directory** option to `frontend/`.
5. Set the **Build Command** to: `npm run build`
6. Set the **Output Directory** to: `dist`
7. Set the **Environment Variables**:
   - `VITE_API_URL`: `https://your-backend-url.railway.app` (The public domain of your backend API).
8. Click **Deploy**. Vercel will bundle the SPA and serve it over a secure HTTPS edge network.

### Step 2: Deploying the FastAPI Backend to Railway
1. Log in to [Railway.app](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select the repository.
4. Railway will automatically detect the root `Dockerfile` and build it.
5. Under **Variables**, add the following production variables:
   ```env
   # API Configuration
   PORT=8000
   ENVIRONMENT=production
   CORS_ORIGINS=https://your-frontend-domain.vercel.app

   # Database & Redis Caching
   NEON_DATABASE_URL=postgresql://user:password@host/neondb?sslmode=require
   UPSTASH_REDIS_REST_URL=https://your-redis-url.upstash.io
   UPSTASH_REDIS_REST_TOKEN=your_token_here

   # AI Credentials
   GROQ_API_KEY=gsk_your_actual_key
   TAVILY_API_KEY=tvly-your_actual_key
   HF_TOKEN=hf_your_actual_key

   # Authentication Configuration
   JWT_SECRET_KEY=generate_using_openssl_rand_hex_32
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=10080
   ```
6. In **Settings**, generate a public domain (Railway TCP/HTTP domain).
7. Under **Deployments**, wait for the build to finish. The backend is automatically configured to run database migrations, verify Upstash connection states, and bind to port `8000`.

---

## 4. Strategy B: Single-Node VPS Deployment (Docker Compose)

For private servers (DigitalOcean, Linode, AWS EC2, etc.), you can run the entire stack on a single Virtual Private Server (VPS) via Docker Compose. We route incoming requests through an **Nginx** reverse proxy that manages Let's Encrypt SSL certificates.

### Step 1: Nginx Configuration
Place the following inside `/etc/nginx/sites-available/zeus` on the server host:

```nginx
server {
    listen 80;
    server_name zeus.yourdomain.com;

    # Redirect all HTTP requests to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name zeus.yourdomain.com;

    # SSL Certificates (managed via Certbot / Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/zeus.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zeus.yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ─── Route Backend API (including SSE Support) ────────────
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        
        # SSE Streaming requirements
        proxy_set_header Connection '';
        proxy_set_header Cache-Control 'no-cache';
        proxy_set_header X-Accel-Buffering 'no';
        proxy_buffering off;
        proxy_read_timeout 24h;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ─── Route Frontend Static Assets ──────────────────────────
    location / {
        proxy_pass http://localhost:5173; # Routes traffic to static container or node port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Step 2: Production Docker Compose File
Use the following `docker-compose.prod.yml` configuration:

```yaml
version: '3.8'

services:
  # ─── Backend Service ────────────────────────────────────────
  backend:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        HF_TOKEN: ${HF_TOKEN}
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      ENVIRONMENT: production
      NEON_DATABASE_URL: ${NEON_DATABASE_URL}
      GROQ_API_KEY: ${GROQ_API_KEY}
      TAVILY_API_KEY: ${TAVILY_API_KEY}
      UPSTASH_REDIS_REST_URL: ${UPSTASH_REDIS_REST_URL}
      UPSTASH_REDIS_REST_TOKEN: ${UPSTASH_REDIS_REST_TOKEN}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    volumes:
      # Upload volume structure to persist uploads
      - backend_uploads:/app/backend/data/uploads
    restart: unless-stopped

  # ─── Frontend Static Container ──────────────────────────────
  frontend:
    image: node:20-slim
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=https://zeus.yourdomain.com/api
    command: sh -c "npm install && npm run build && npm install -g serve && serve -s dist -l 5173"
    restart: unless-stopped

volumes:
  backend_uploads:
```

### Step 3: Run the Stack
Deploy the stack on the VPS using the following commands:
```bash
# Pull and build the containers
docker compose -f docker-compose.prod.yml up -d --build

# Reload Nginx to activate changes
sudo systemctl restart nginx
```

---

## 5. Strategy C: AWS Enterprise Deployment (Production Grade)

For critical enterprise production, scale horizontally across multiple Availability Zones using AWS services.

```
                  ┌─────────────────────────────────────┐
                  │          AWS CloudFront CDN         │
                  └──────────────────┬──────────────────┘
                                     │
                  ┌──────────────────▼──────────────────┐
                  │       Application Load Balancer     │
                  └──────────────────┬──────────────────┘
                                     │
             ┌───────────────────────┴───────────────────────┐
             │                                               │
┌────────────▼─────────────┐                    ┌────────────▼─────────────┐
│    ECS Task (Fargate)    │                    │    ECS Task (Fargate)    │
│      [AZ1 Backend]       │                    │      [AZ2 Backend]       │
└────────────┬─────────────┘                    └────────────┬─────────────┘
             │                                               │
             └───────────────────────┬───────────────────────┘
                                     │
                  ┌──────────────────▼──────────────────┐
                  │    AWS EFS (Shared File Storage)    │
                  └──────────────────┬──────────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           │                                                   │
┌──────────▼──────────┐                             ┌──────────▼──────────┐
│   Aurora Postgres   │                             │ Amazon ElastiCache  │
│   (pgvector, multi-AZ)│                           │ (Serverless Redis)  │
└─────────────────────┘                             └─────────────────────┘
```

1. **Storage Routing**: Mount a shared **Amazon EFS (Elastic File System)** as a directory path (`/app/backend/data/uploads`) to ECS tasks so file attachments are persistent and shared across all active backend nodes.
2. **Container Host**: Deploy the backend container inside AWS **ECS (with Fargate)**. Define tasks with minimum 1 vCPU and 2GB RAM to support Hugging Face embedding generation, text chunk retrieval, and thread-pool audio transcriptions.
3. **Database Layer**: Host the database on **Amazon Aurora Serverless v2 for PostgreSQL** with multi-AZ replication. Set instance setups to automatically scale capacity units (ACUs) during query spikes.

---

## 6. Deployment Verification & Testing

Once deployment completes, check the following endpoints to verify system health:

| Metric | Target | Verification Method |
|---|---|---|
| **CORS Verification** | Status 200 | Verify request `OPTIONS /api/v1/chat/stream` from frontend return CORS headers. |
| **SSE Streaming Stability**| Event source stream | Send query to `/api/v1/chat/stream`, inspect network logs to ensure chunks stream token-by-token. |
| **Upload Pipeline Storage**| HTTP 200 | Upload a sample PDF. Check `/app/backend/data/uploads` to confirm the file is registered. |
| **Migrations Integrity** | Active schema | Run `SELECT * FROM conversations;` in database console to verify schema tables exist. |

---

## 7. Operational Troubleshooting

> [!WARNING]
> **Server-Sent Events (SSE) Timeout / Buffering Issues**
> If your streaming answers fail to render incrementally (getting dumped all at once at the end), Nginx is buffering the output. Make sure `proxy_buffering off;` and `proxy_set_header X-Accel-Buffering 'no';` are configured correctly in your proxy files.

> [!IMPORTANT]
> **Model pre-downloading and Memory limits**
> The `all-MiniLM-L6-v2` embedding model takes approximately 120MB memory when loaded. If backend containers keep crashing on startup with exit codes `137` (OOM), your hosting instance lacks memory. Ensure container provisioning allocates at least **512MB RAM** (recommended: **1GB RAM**).
