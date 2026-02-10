# AI Batake App - Copilot Instructions

## Project Overview
AI Batake App is a smart gardening application that uses AI agents to analyze seed packets and provide growing instructions. The application is deployed on Google Cloud Run and uses Google Cloud Platform services.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: Google Cloud Firestore
- **Storage**: Google Cloud Storage
- **AI**: Google Cloud Vertex AI (Reasoning Engines)
- **Key Dependencies**: uvicorn, google-cloud-aiplatform, google-cloud-firestore, python-dotenv

### Frontend
- **Framework**: Next.js 16 (React 19)
- **TypeScript**: Version 5
- **UI Components**: Radix UI
- **Styling**: Tailwind CSS 4
- **Form Management**: React Hook Form with Zod validation
- **Key Features**: Server-side rendering, Firebase integration

## Project Structure
```
/backend              - FastAPI backend application
  main.py            - Main FastAPI application and API endpoints
  db.py              - Firestore database operations
  agent.py           - Google Cloud AI agent integration
  research_agent.py  - Seed packet analysis logic
  seed_service.py    - Asynchronous seed analysis service
  requirements.txt   - Python dependencies

/frontend            - Next.js frontend application
  /app               - Next.js App Router pages and layouts
  /components        - React components
  /lib               - Utility functions and helpers
  package.json       - Node.js dependencies
  tsconfig.json      - TypeScript configuration
```

## Development Guidelines

### Code Style and Conventions
- **Python**: Follow PEP 8 style guide
- **TypeScript**: Use strict mode, avoid `any` type
- **Imports**: Use relative imports within the same module (e.g., `from .db import ...`)
- **Error Handling**: Always include proper error handling with logging
- **Logging**: Use Python's `logging` module for backend, structured logging preferred

### Environment Variables
- Never commit `.env` files or credentials
- Required environment variables:
  - `AGENT_ENDPOINT`: Google Cloud Reasoning Engine endpoint
  - `GOOGLE_CLOUD_PROJECT`: GCP project ID
  - `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account key (local dev)

### Database Conventions
- Use Firestore for all persistent data
- Collections:
  - `vegetables`: Stores seed analysis results and growing instructions
- Always check if `db` is None before database operations (handles offline/dev mode)

### API Design
- RESTful endpoints following FastAPI conventions
- Use Pydantic models for request/response validation
- Enable CORS for all origins (configured in `main.py`)
- Background tasks for long-running operations (e.g., seed analysis)

### Frontend Patterns
- Use Server Components by default in Next.js App Router
- Client components only when needed (use `"use client"` directive)
- Use TypeScript path aliases (`@/*`) for imports
- Component composition with Radix UI primitives

## Build and Test Commands

### Backend
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run locally
uvicorn backend.main:app --host 0.0.0.0 --port 8081 --reload

# Test API (if test file exists)
python backend/test_api.py
```

### Frontend
```bash
# Install dependencies
cd frontend
npm install

# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

### Full Application
```bash
# Build Docker image
docker build -t ai-batake-app .

# Run with start script (both backend and frontend)
./start.sh
```

## Deployment
- **Platform**: Google Cloud Run
- **Container**: Docker (multi-stage with Python 3.11 and Node.js)
- **Ports**: 
  - Backend: 8081
  - Frontend: PORT environment variable (default 8080 for Cloud Run)
- **Build Process**: Docker builds frontend first, then starts both services via `start.sh`

## Testing

### Backend Testing (Python/pytest)

**Test Framework**: pytest with pytest-asyncio and pytest-cov

**Test Structure** (15 test files, 473 tests, 96% code coverage):
- `backend/tests/test_main.py` - FastAPI endpoints, middleware, background tasks (131 tests)
- `backend/tests/test_db.py` - Firestore database operations (75 tests)
- `backend/tests/test_diary_service.py` - Diary service: data collection, AI generation, persistence (71 tests)
- `backend/tests/test_seed_service.py` - Seed image analysis and guide image generation (38 tests)
- `backend/tests/test_research_agent.py` - Seed packet analysis, Deep Research, Web Grounding (37 tests)
- `backend/tests/test_logger.py` - Structured logging, JSON Formatter, decorators (34 tests)
- `backend/tests/test_image_service.py` - Picture diary image generation (27 tests)
- `backend/tests/test_agent.py` - AI agent: sessions, queries, SSE streaming (24 tests)
- `backend/tests/test_character_service.py` - Character generation service (10 tests)
- `backend/tests/test_select_feature.py` - Instruction selection (5 tests)
- `backend/tests/test_seed_guide_persistence.py` - Seed guide CRUD (4 tests)
- `backend/tests/test_character_api.py` - Character API endpoints (4 tests)
- `backend/tests/test_vegetable_config.py` - Vegetable config and diary priority (4 tests)
- `backend/tests/test_utils.py` - Utility functions (4 tests)
- `backend/tests/test_async_flow.py` - Async generation flow (3 tests)

**Running Tests**:
```bash
cd backend
pip install -r requirements.txt
pytest
```

**Running with Coverage**:
```bash
cd /path/to/project
venv/bin/python -m pytest backend/tests/ --cov=backend --cov-config=backend/pytest.ini --cov-report=term-missing
```

**Configuration**:
- `backend/pytest.ini` - pytest configuration file (asyncio_mode=strict)
- Mock external dependencies (Firestore, Google Cloud APIs, Gemini API)
- Test both success and error scenarios
- Always check if `db` is None for offline testing

**Code Coverage** (96% overall):
- `logger.py` - 100%
- `research_agent.py` - 99%
- `character_service.py`, `db.py`, `diary_service.py`, `image_service.py`, `seed_service.py` - 97%
- `agent.py` - 96%
- `main.py` - 94%

### Frontend Testing (TypeScript/Jest)

**Test Framework**: Jest with React Testing Library

**Test Structure** (6 test suites, 42 tests):
- `frontend/__tests__/lib/utils.test.ts` - Utility functions (cn helper)
- `frontend/__tests__/components/metric-card.test.tsx` - MetricCard component
- `frontend/__tests__/components/weather-card.test.tsx` - WeatherCard component
- `frontend/__tests__/components/growth-stage-card.test.tsx` - GrowthStageCard component
- `frontend/__tests__/components/plant-camera.test.tsx` - PlantCamera component
- `frontend/__tests__/components/environment-chart.test.tsx` - EnvironmentChart component

**Running Tests**:
```bash
cd frontend
npm install --legacy-peer-deps
npm test
```

**Watch Mode**:
```bash
npm run test:watch
```

**Configuration**:
- `frontend/jest.config.js` - Jest configuration
- `frontend/jest.setup.js` - Test setup file
- Use `@testing-library/react` for component testing
- Use `@testing-library/jest-dom` for DOM assertions

### Test Documentation

**Comprehensive Test Matrix**: See `docs/TEST_MATRIX.md` for:
- Complete list of all test cases organized by module
- Test categorization (normal/error scenarios)
- Coverage breakdown per file

**Test Summary**: See `docs/TEST_README.md` for:
- Quick reference guide with per-file test counts
- Code coverage table
- Test execution instructions
- Overall test statistics (515 total tests, 100% pass rate, 96% backend coverage)

### Testing Best Practices

1. **Always run tests before committing code changes**
2. **Mock external dependencies** (Firestore, Google Cloud APIs, Gemini API)
3. **Test both success and error paths**
4. **Use descriptive test names** that explain what is being tested
5. **Follow existing test patterns** when adding new tests
6. **Maintain 100% test pass rate** - do not commit failing tests
7. **Maintain 95%+ code coverage** - run coverage reports to verify
8. **Update TEST_MATRIX.md** when adding new test cases

## Important Notes
- The application requires Google Cloud credentials to function properly
- Firestore client gracefully handles missing credentials for local development
- Background tasks are used for long-running AI operations
- Frontend communicates with backend on port 8081 in production

## Security Considerations
- Never expose API keys or service account credentials in code
- All GCP authentication uses Application Default Credentials (ADC)
- Use environment variables for all sensitive configuration
- Validate all user inputs with Pydantic/Zod schemas
