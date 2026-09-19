# Python/FastAPI backend, TypeScript/React frontend

The backend is Python with FastAPI; the frontend is TypeScript with React. The CAMS parsing and financial-maths ecosystem is strongest in Python, and FastAPI's typed request and response models let the API contract be expressed as code. The frontend is a separate single-page application rather than server-rendered, because there is no server-side personalisation or SEO to gain from rendering on the server.

## Consequences

- Two toolchains and two test suites must be maintained; strong coverage is a project standard for both.
- The API is the contract between them, so its shape is a real design decision rather than an implementation detail.
