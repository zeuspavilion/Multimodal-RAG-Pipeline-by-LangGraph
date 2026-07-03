# Ongoing Deployment Errors

The following CORS preflight error is currently occurring when the Vercel frontend attempts to communicate with the Railway backend:

## Error Log

```text
Access to XMLHttpRequest at 'https://multimodal-rag-pipeline-by-langgraph-production.up.railway.app/api/v1/auth/signup' from origin 'https://multimodal-rag-pipeline-by-lang-gra.vercel.app' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.

POST https://multimodal-rag-pipeline-by-langgraph-production.up.railway.app/api/v1/auth/signup net::ERR_FAILED
```

## Diagnostics

- **Cause**: The preflight `OPTIONS` request is returning `400 Bad Request` from the backend service.
- **Troubleshooting Steps**:
  1. Verify if the Railway environment variable `CORS_ORIGINS` is set and matches `https://multimodal-rag-pipeline-by-lang-gra.vercel.app` exactly (with no trailing slashes or quotes).
  2. Verify that the latest deployment containing the CORS parsing fixes has built and is active on Railway.
