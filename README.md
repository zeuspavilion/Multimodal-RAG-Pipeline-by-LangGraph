# 🚀 Deployment Overview & Cloud Migration Techniques

This `README.md` is specific to the **`deployment`** branch and documents the active production hosting configuration and the technical adjustments made to migrate the codebase from a localhost-only setup to a cloud-ready production state.

> **Note:** For the full application features, architecture diagrams, and system design specifications, refer to the [main branch README](https://github.com/zeuspavilion/Multimodal-RAG-Pipeline-by-LangGraph/blob/main/README.md).

---

## 🌐 Active Hosting Status

The system is deployed using a split-hosting architecture:

* **Frontend**: Hosted on **Vercel**
  - **URL**: [https://multimodal-rag-pipeline-by-lang-gra.vercel.app](https://multimodal-rag-pipeline-by-lang-gra.vercel.app)
  - **Build Target**: React SPA (Vite)
* **Backend API**: Hosted on **Railway**
  - **Endpoint**: `https://multimodal-rag-pipeline-by-langgraph-production.up.railway.app`
  - **Runtime**: FastAPI in a Docker container (exposed on port `8000`)
* **Vector Store**: Neon Serverless PostgreSQL (`pgvector`)
* **Cache Layer**: Upstash Redis

---

## 🛠️ Local-to-Cloud Migration Techniques

To successfully deploy the codebase to cloud platforms, several architectural and configuration changes were introduced to solve common deployment bottlenecks:

### 1. Decoupling Local Docker Compose from Cloud Builds
* **Local Issue**: Railway automatically detects `docker-compose.yml` in the repository root and attempts to orchestrate builds using it. This bypassed Railway's dashboard environment variables and loaded local-only database links, causing Pydantic validation crashes on startup.
* **Resolution**: Renamed `docker-compose.yml` to `docker-compose.local.yml`. This restricts docker-compose orchestration to local machines, forcing Railway to build directly using the production `Dockerfile` and successfully inject active environment variables.

### 2. Defending Against Pydantic Settings Validation Crashes
* **Local Issue**: `pydantic_settings` raised immediate `ValidationError` exceptions at startup if keys (`GROQ_API_KEY`, etc.) were missing from the environment, printing verbose traceback outputs.
* **Resolution**: Assigned safe empty-string defaults (`= ""`) to required configuration keys in `backend/config.py`. This defers checks to a custom `@model_validator` which logs clean, developer-friendly warnings on missing keys instead of breaking startup.

### 3. Vercel Single-Page Application (SPA) Routing Rewrite
* **Local Issue**: Direct navigation or browser refreshes on routes other than root (like `/login` or `/signup`) threw Vercel 404 errors because the platform is optimized for static file resolution.
* **Resolution**: Configured a `vercel.json` rewrite file in the `frontend/` directory to redirect all client-side routes back to `index.html`, allowing React Router to handle page rendering seamlessly:
  ```json
  {
    "rewrites": [
      { "source": "/(.*)", "destination": "/index.html" }
    ]
  }
  ```

### 4. Quote-Stripping for Configured CORS Origins
* **Local Issue**: When copying credentials or domains from env files, users frequently write them with quotes (e.g. `CORS_ORIGINS="https://..."`). On Railway, this causes the values to be parsed with literal quotes, leading to preflight CORS failures.
* **Resolution**: Added a robust quote-stripping parser in the settings loader:
  ```python
  CORS_ORIGINS: list[str] = [o.strip().strip("'\"") for o in settings.CORS_ORIGINS.split(",") if o.strip()]
  ```
  This ensures origins match perfectly regardless of surrounding quotes.

### 5. Wildcard-Safe CORS Credentials Management
* **Local Issue**: Setting `CORS_ORIGINS=*` while having `allow_credentials=True` enabled causes FastAPI to crash with a configuration exception on startup.
* **Resolution**: Updated `backend/api/main.py` to dynamically disable credentials transmission only when a wildcard is present, preventing crashes:
  ```python
  allow_credentials=False if "*" in app_config.CORS_ORIGINS else True
  ```

### 6. Git Secret Exclusion & Rules
* **Action**: Configured ignore patterns in root and subfolder `.gitignore` files to guarantee that local `.env` files, temporary audio/PDF files in `backend/data/uploads`, database checkpoints, and system variables are never staged, keeping your active production credentials secure while pushing updates.

### 7. Multi-Cloud Persistent Storage (AWS S3 Integration)
* **Local Issue**: Railway containers run on ephemeral filesystems. If the container restarts or scales, all user-uploaded files are wiped out. Any subsequent user query attempting to reference these files will fail.
* **Resolution**: Integrated an optional AWS S3 persistent object storage layer via `boto3` in [storage.py](file:///c:/Users/Ronit/Downloads/Multimodal-RAG-Pipeline-by-LangGraph/Multimodal-RAG-Pipeline-by-LangGraph/backend/utils/storage.py):
  - **Uploads**: Files are saved locally for execution speed and uploaded to S3. 
  - **Downloads**: If local cache misses (e.g. after container restart), worker nodes automatically download the file from S3 before processing.
  - **Zero-Config Local Fallback**: Local development automatically falls back to local disk storage if AWS keys are not configured, maintaining zero-setup offline capability.
  - **Configuration**: Expose `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, and `AWS_S3_REGION` in Railway dashboard variables.
