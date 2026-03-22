"""Framework-specific agent context templates for agentkit frameworks --generate."""
from __future__ import annotations

from typing import Optional

_TEMPLATES: dict[str, str] = {
    "Next.js": """\
## Next.js Notes

### Setup
Run `npm install` then `npm run dev` to start the development server.
The app runs on http://localhost:3000 by default.
Use the App Router (`app/`) for new pages; avoid mixing App and Pages routers.

### Common Patterns
- Server Components are the default; opt into Client Components with `"use client"`.
- Fetch data in Server Components using `async/await` directly.
- Use `next/image` for optimized images and `next/link` for client-side navigation.
- API routes live in `app/api/` (App Router) or `pages/api/` (Pages Router).

### Known Gotchas
- Server Components cannot use React hooks or browser APIs.
- Environment variables must be prefixed with `NEXT_PUBLIC_` to be exposed to the client.
- `cookies()` and `headers()` are async in Next.js 15+.
""",

    "FastAPI": """\
## FastAPI Notes

### Setup
Install dependencies: `pip install -r requirements.txt`
Run the server: `uvicorn main:app --reload`
Interactive docs available at http://localhost:8000/docs

### Common Patterns
- Use Pydantic models for request/response validation.
- Dependency injection via `Depends()` for shared logic (DB sessions, auth).
- Use `async def` for async endpoints; `def` for synchronous ones.
- Router prefixes keep endpoints organized: `APIRouter(prefix="/api/v1")`.

### Known Gotchas
- Do not block the event loop with synchronous I/O in async endpoints.
- Pydantic v2 has breaking changes from v1 (model config, validators).
- Background tasks run after the response; avoid relying on their completion.
""",

    "Django": """\
## Django Notes

### Setup
Install: `pip install -r requirements.txt`
Run migrations: `python manage.py migrate`
Start server: `python manage.py runserver`

### Common Patterns
- Use class-based views (CBVs) for CRUD operations; function-based views for simple logic.
- Django ORM: prefer `select_related` / `prefetch_related` to avoid N+1 queries.
- Settings split: `settings/base.py`, `settings/local.py`, `settings/production.py`.
- Use `django.contrib.auth` for authentication; extend `AbstractUser` for custom fields.

### Known Gotchas
- `DEBUG = True` must never be set in production.
- CSRF protection is on by default; use `@csrf_exempt` only when absolutely necessary.
- Migrations must be committed to version control.
""",

    "Rails": """\
## Rails Notes

### Setup
Install gems: `bundle install`
Setup database: `bin/rails db:create db:migrate`
Start server: `bin/rails server`

### Common Patterns
- Follow Rails conventions: fat models, skinny controllers.
- Use Active Record scopes for reusable query logic.
- Service objects for complex business logic outside models.
- Use `bin/rails generate` for scaffolding models, controllers, and migrations.

### Known Gotchas
- `before_action` callbacks can hide implicit side effects — keep them explicit.
- Avoid `N+1` queries: use `includes`, `preload`, or `eager_load`.
- Rails credentials: use `bin/rails credentials:edit` for secrets, never plain env files in source.
""",

    "React": """\
## React Notes

### Setup
Install: `npm install`
Start dev server: `npm start` or `npm run dev`

### Common Patterns
- Prefer functional components with hooks over class components.
- `useState` for local state; `useContext` or external stores (Zustand, Redux) for shared state.
- `useEffect` cleanup: always return a cleanup function for subscriptions/timers.
- Lift state up to the nearest common ancestor when siblings need shared data.

### Known Gotchas
- Stale closures in `useEffect`: include all dependencies in the dependency array.
- Keys in lists must be stable and unique (not array index for dynamic lists).
- Avoid prop drilling more than 2-3 levels deep — use context or state libraries.
""",

    "Vue": """\
## Vue Notes

### Setup
Install: `npm install`
Run dev server: `npm run dev`

### Common Patterns
- Use Composition API (`<script setup>`) for new components; Options API for legacy code.
- `ref()` for primitives, `reactive()` for objects.
- Pinia is the recommended state management library (replaces Vuex).
- Use `v-model` for two-way binding; `:prop` + `@event` pattern for component communication.

### Known Gotchas
- Vue 3 is not fully backward compatible with Vue 2 — check the migration guide.
- Reactivity is lost when destructuring reactive objects directly; use `toRefs()`.
- `<Suspense>` for async components is still experimental.
""",

    "Nuxt": """\
## Nuxt Notes

### Setup
Install: `npm install`
Start dev: `npm run dev`
Nuxt auto-imports composables and components from `composables/` and `components/`.

### Common Patterns
- File-based routing: files in `pages/` become routes automatically.
- `useFetch` / `useAsyncData` for SSR-aware data fetching.
- Server routes in `server/api/` are auto-registered as API endpoints.
- Use `useState` for SSR-safe shared state (avoids hydration mismatches).

### Known Gotchas
- Nuxt 3 requires Vue 3; do not mix Nuxt 2 modules.
- Environment variables: use `NUXT_` prefix for runtime config, not `VITE_`.
- Hydration mismatches occur when server and client render differently — avoid `Math.random()` or `Date.now()` in templates.
""",

    "Flask": """\
## Flask Notes

### Setup
Install: `pip install -r requirements.txt`
Run: `flask run` or `python app.py`
Set `FLASK_ENV=development` for debug mode.

### Common Patterns
- Use Application Factory pattern (`create_app()`) for testability.
- Blueprints for organizing routes into modules.
- Flask-SQLAlchemy for ORM; Flask-Migrate for database migrations.
- Use `current_app` and `g` for application and request context access.

### Known Gotchas
- The development server is not suitable for production — use gunicorn/uWSGI.
- `before_request` / `after_request` hooks apply to all routes in the blueprint.
- Secret key must be set and kept truly secret in production.
""",

    "Laravel": """\
## Laravel Notes

### Setup
Install dependencies: `composer install`
Copy env: `cp .env.example .env && php artisan key:generate`
Run migrations: `php artisan migrate`
Start server: `php artisan serve`

### Common Patterns
- Eloquent ORM for database interaction; use relationships (`hasMany`, `belongsTo`).
- Route model binding auto-injects models from route parameters.
- Use form requests (`php artisan make:request`) for validation logic.
- Queues for deferred processing: `php artisan queue:work`.

### Known Gotchas
- N+1 queries: use `with()` for eager loading relationships.
- `.env` must never be committed to version control.
- `APP_DEBUG=true` must be false in production.
""",

    "Express": """\
## Express Notes

### Setup
Install: `npm install`
Start: `node index.js` or `npm start`
Use `nodemon` during development for auto-restart.

### Common Patterns
- Middleware chain: `app.use(middleware)` applies globally; `router.use()` applies to a route group.
- Error handling middleware has 4 parameters: `(err, req, res, next)`.
- Use `express.json()` and `express.urlencoded()` for body parsing.
- Router modules keep route definitions organized: `express.Router()`.

### Known Gotchas
- Express does not handle async errors automatically — wrap async handlers or use a library like `express-async-errors`.
- Always call `next(err)` instead of throwing in middleware.
- Do not serve static files from the project root in production.
""",
}


def get_template(framework_name: str) -> Optional[str]:
    """Return the markdown template for a framework, or None if not found."""
    return _TEMPLATES.get(framework_name)


def list_templates() -> list[str]:
    """Return names of all frameworks with templates."""
    return list(_TEMPLATES.keys())
