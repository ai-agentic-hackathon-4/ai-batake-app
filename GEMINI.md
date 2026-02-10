# AI Context Rules

## 1. Project Overview
AI Batake App は、AIを活用したスマート農業プラットフォームです。センサーデータのリアルタイム監視、種袋画像からの栽培情報の自動抽出、およびAIエージェントによる栽培ガイドの生成を行います。

This is an AI-powered smart farming platform that provides:
- Real-time environmental monitoring (temperature, humidity, soil moisture)
- AI-driven seed packet analysis and deep research for optimal growing conditions
- **Manual instruction selection** to apply specific research results to the edge agent
- Step-by-step planting guide generation using async AI jobs
- AI character generation from seed packet images
- Unified seed feature (one-click Research + Guide + Character)
- Automated daily growing diary generation (via Cloud Scheduler)
- Illustrated diary image generation with AI characters

## 2. Tech Stack & Versions

### Frontend
- **Language**: TypeScript 5.x
- **Framework**: Next.js 16 (App Router)
- **UI Library**: React 19
- **Styling**: Tailwind CSS 4.x with tw-animate-css
- **Component Library**: Radix UI primitives (@radix-ui/react-*)
- **Form Handling**: React Hook Form with Zod validation
- **Charts**: Recharts

### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Database**: Google Cloud Firestore
- **Storage**: Google Cloud Storage
- **AI Services**: Google Vertex AI, Gemini API
- **Key Libraries**:
  - google-cloud-aiplatform
  - google-cloud-firestore
  - google-cloud-storage
  - python-dotenv

### Infrastructure
- **Container**: Docker
- **Deployment**: Google Cloud Run
- **Scheduler**: Google Cloud Scheduler (daily diary generation)
- **Analytics**: Vercel Analytics

## 3. Coding Guidelines

### Naming Conventions
- **TypeScript/React**:
  - Components: PascalCase (e.g., `MetricCard`, `WeatherCard`)
  - Files: kebab-case for components (e.g., `metric-card.tsx`), or matching component name
  - Variables/Functions: camelCase (e.g., `fetchSensorData`, `sensorData`)
  - Interfaces/Types: PascalCase (e.g., `MetricCardProps`)
- **Python**:
  - Functions: snake_case (e.g., `get_weather_from_agent`, `analyze_seed_packet`)
  - Variables: snake_case (e.g., `vegetable_name`, `image_bytes`)
  - Classes: PascalCase (e.g., `WeatherRequest`)
  - Constants: UPPER_SNAKE_CASE (e.g., `COLLECTION_NAME`)

### Type Definitions
- **TypeScript**: Use strict mode; define explicit interfaces for props and API responses
- **Python**: Use Pydantic models for API request/response validation

### File Organization
- **Frontend Components**: Place reusable components in `frontend/components/`
- **UI Primitives**: Place base UI components in `frontend/components/ui/`
- **Pages**: Use Next.js App Router structure in `frontend/app/`
- **Backend Modules**: Keep related functionality in separate Python modules in `backend/`

### Testing
- **Backend**:
  - **Framework**: pytest with pytest-asyncio (473 tests, 96% coverage)
  - **Test Files**: Files should be prefixed with `test_` and placed in `backend/tests/`
  - **Running Tests**:
    ```bash
    cd backend
    pytest                                    # Run all tests
    pytest --cov=. --cov-report=html          # With coverage
    ```
  - **Verification Scripts** (in `backend/`):
    - `verify_unified_api.py` - Tests unified seed feature flow
    - `verify_character_gen.py` - Tests character generation
    - `verify_save_logic.py` - Tests persistence logic
    - `verify_proxy.py` - Tests image proxy endpoints
- **Frontend**: Jest (42 tests) + ESLint
  - Run tests with `npm test` in the `frontend/` directory
  - Run lint with `npm run lint` in the `frontend/` directory

### Formatting
- **Frontend**: Use consistent indentation (4 spaces for TypeScript)
- **Python**: Follow PEP 8 style guidelines
- Use import aliasing with `@/*` for frontend imports (configured in tsconfig.json)

## 4. Anti-patterns (Do NOT do this)
- ❌ Do not hardcode environment variables or API keys in source code
- ❌ Do not use `any` type in TypeScript; always define proper types
- ❌ Do not mix business logic in view components; keep data fetching in hooks or server components
- ❌ Do not commit `.env` files or credentials to version control
- ❌ Do not use synchronous database operations in FastAPI async endpoints
- ❌ Do not bypass CORS configuration; use proper middleware settings
- ❌ Do not use inline styles; prefer Tailwind CSS utility classes
- ❌ Do not ignore error handling; always use try-catch blocks and proper logging
- ❌ Do not write commit messages in Japanese (use English only for git commits)
- ❌ Do not skip type hints in Python function signatures

## 5. Architecture

### Directory Structure
```
/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # FastAPI app entry point, API routes
│   ├── db.py               # Firestore database operations
│   ├── agent.py            # Vertex AI Agent Engine integration
│   ├── research_agent.py   # Gemini API for seed analysis & research
│   ├── seed_service.py     # Async seed guide generation service
│   ├── diary_service.py    # Automated growing diary generation
│   ├── image_service.py    # Illustrated diary image generation
│   ├── character_service.py # AI character generation
│   ├── logger.py           # Structured logging (JSON formatter)
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # Test files (473 tests)
│
├── frontend/               # Next.js frontend
│   ├── app/               # Next.js App Router pages
│   │   ├── layout.tsx     # Root layout
│   │   ├── page.tsx       # Landing page
│   │   ├── dashboard/     # Dashboard page
│   │   ├── research_agent/# Research agent page
│   │   ├── seed_guide/    # Seed guide page
│   │   ├── unified/       # Unified seed feature page
│   │   ├── diary/         # Growing diary page
│   │   └── character/     # Character management page
│   ├── components/        # React components
│   │   ├── ui/           # Radix UI-based primitives
│   │   └── *.tsx         # Feature components
│   ├── lib/              # Utility functions
│   └── public/           # Static assets
│
├── docs/                  # Documentation
├── Dockerfile            # Container build definition
├── start.sh             # Startup script for backend & frontend
└── package-lock.json    # Root lock file
```

### Design Patterns
- **Frontend**:
  - Component-based architecture with React functional components
  - Server Components by default, Client Components (`"use client"`) where needed
  - Composition pattern for UI components (Card, CardHeader, CardContent, etc.)
  - Custom hooks for data fetching and state management
  
- **Backend**:
  - RESTful API design with FastAPI
  - Background tasks for long-running operations (async job processing)
  - Repository pattern for database operations (db.py)
  - Service layer for AI integrations (agent.py, research_agent.py, diary_service.py, image_service.py, character_service.py)
  - Structured logging with JSON formatter (logger.py)

### API Design
- Base path: `/api/`
- Endpoints follow RESTful conventions
- Use Pydantic models for request/response validation
- Background tasks for heavy processing (seed analysis, deep research, diary generation)
- SSE (Server-Sent Events) for real-time progress streaming (diary generation)

## 6. External Documentation & Resources
- **Next.js Documentation**: https://nextjs.org/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Radix UI Components**: https://www.radix-ui.com/docs/primitives/overview/introduction
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Google Cloud Firestore**: https://cloud.google.com/firestore/docs
- **Vertex AI Agent Engine**: https://cloud.google.com/vertex-ai/docs

## 7. Development Commands
```bash
# Frontend development
cd frontend
npm install
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run ESLint

# Backend development
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8081 --reload

# Full application (Docker)
docker build -t ai-batake-app .
docker run -p 8080:8080 ai-batake-app
```
