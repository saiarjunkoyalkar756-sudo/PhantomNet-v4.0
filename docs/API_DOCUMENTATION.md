# PhantomNet API Documentation

This document explains how to access the API documentation for the PhantomNet backend services.

## API Endpoints (Overview)

Here's a quick overview of some key API endpoints:

**Authentication**
- `POST /auth/login`
- `POST /auth/register`
- `POST /auth/2fa/verify`

**Analytics**
- `POST /analyzer/ingest`
- `GET  /analyzer/results`

**Blockchain**
- `GET /blockchain/logs`
- `POST /blockchain/append`

**Admin**
- `GET /admin/health`
- `GET /admin/agents`

More detailed API reference available below and through the interactive OpenAPI documentation.

---

## OpenAPI (Swagger) Documentation

The PhantomNet backend is built using the FastAPI framework, which automatically generates interactive API documentation using the OpenAPI standard (formerly Swagger).

To access the API documentation, you need to have the PhantomNet backend running. Follow the instructions in the [Deployment Guide](./DEPLOYMENT_GUIDE.md) to start the backend services.

Once the backend is running, the interactive OpenAPI documentation is available at the following URL:

[http://localhost:8001/docs](http://localhost:8001/docs)

This documentation provides a full, interactive overview of all available endpoints, including:

-   Request and response models
-   Path and query parameters
-   Authentication requirements
-   Example requests and responses

You can also access the raw OpenAPI 3.0 specification in JSON format at the following URL:

[http://localhost:8001/openapi.json](http://localhost:8001/openapi.json)

## API Versioning

The PhantomNet API is versioned to ensure backward compatibility. The current version of the API is v1. All API endpoints are prefixed with `/api/v1`.
