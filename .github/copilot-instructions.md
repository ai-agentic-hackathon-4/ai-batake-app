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

**Test Framework**: pytest with comprehensive test coverage

**Test Structure**:
- `backend/tests/test_db.py` - Database operations (Firestore)
- `backend/tests/test_agent.py` - AI agent integration and communication
- `backend/tests/test_main.py` - FastAPI endpoint testing
- `backend/tests/test_seed_service.py` - Seed image analysis service
- `backend/tests/test_utils.py` - Utility functions

**Running Tests**:
```bash
cd backend
pip install -r requirements.txt
pytest
```

**Configuration**:
- `backend/pytest.ini` - pytest configuration file
- Mock external dependencies (Firestore, Google Cloud APIs)
- Test both success and error scenarios
- Always check if `db` is None for offline testing

**Test Coverage**: 42 tests covering:
- Database operations (11 tests) - init, update, query operations
- Agent functionality (10 tests) - authentication, session management, queries
- API endpoints (13 tests) - all REST endpoints with success/error cases
- Seed service (4 tests) - image analysis and guide generation
- Utilities (4 tests) - basic Python operations

### Frontend Testing (TypeScript/Jest)

**Test Framework**: Jest with React Testing Library

**Test Structure**:
- `frontend/__tests__/lib/utils.test.ts` - Utility functions (cn helper)
- `frontend/__tests__/components/metric-card.test.tsx` - MetricCard component
- `frontend/__tests__/components/weather-card.test.tsx` - WeatherCard component
- `frontend/__tests__/components/growth-stage-card.test.tsx` - GrowthStageCard component

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

**Test Coverage**: 30 tests covering:
- Utility functions (7 tests) - class name merging, conditional classes
- UI Components (23 tests) - rendering, props, styling, interactions

### Test Documentation

**Comprehensive Test Matrix**: See `docs/TEST_MATRIX.md` for:
- Complete list of all test cases with IDs
- Test categorization (normal/error scenarios)
- Expected behaviors
- Implementation status

**Test Summary**: See `docs/TEST_README.md` for:
- Quick reference guide
- Test execution instructions
- Overall test statistics (72 total tests, 100% pass rate)

### Testing Best Practices

1. **Always run tests before committing code changes**
2. **Mock external dependencies** (Firestore, Google Cloud APIs)
3. **Test both success and error paths**
4. **Use descriptive test names** that explain what is being tested
5. **Follow existing test patterns** when adding new tests
6. **Maintain 100% test pass rate** - do not commit failing tests
7. **Update TEST_MATRIX.md** when adding new test cases

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
