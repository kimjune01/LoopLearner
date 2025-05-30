# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Loop Learner is a production-ready human-in-the-loop machine learning system for adaptive prompt optimization. The system consists of a Django REST API backend and a React/TypeScript frontend with session-based learning workflows.

**Key Architecture**: The system implements session-isolated prompt evolution where each learning session maintains independent state, prompt history, and optimization metrics. Users can create multiple sessions, each with their own prompt optimization journey.

## Development Commands

### Backend (Django + uv)

```bash
cd backend

# Environment setup
uv sync                                    # Install dependencies
uv run python manage.py migrate          # Run database migrations
uv run python manage.py runserver        # Start development server (port 8000)

# Testing
uv run pytest                            # Run all tests (200+ comprehensive tests)
uv run pytest tests/test_session_endpoints.py  # Test specific functionality
uv run pytest tests/test_feedback_real_functions.py  # Real business logic tests
uv run pytest tests/test_reward_real_functions.py    # Mathematical validation tests

# Development utilities
uv run python manage.py shell            # Django shell
uv run python manage.py makemigrations   # Create new migrations
```

### Frontend (React + TypeScript + pnpm)

```bash
cd frontend

# Development
pnpm install                              # Install dependencies
pnpm dev                                  # Start dev server (port 5173)
pnpm build                                # Build for production
pnpm preview                              # Preview production build

# Testing
pnpm test                                 # Run tests in watch mode
pnpm test:run                             # Run tests once
pnpm test:ui                              # Run tests with UI

# Code quality
pnpm lint                                 # Run ESLint
```

## Core Architecture

### Session-Based Learning System

The application is built around **learning sessions** - isolated environments where users can:

- Create independent prompt optimization experiments
- Track evolution of system prompts through feedback cycles
- Export/import session data for sharing or backup
- View session-specific analytics and metrics

Key models: `Session` � `SystemPrompt` � `Email` � `Draft` � `UserFeedback`

### Dual Repository Structure

- **`/backend`**: Django REST API with comprehensive business logic
- **`/frontend`**: React TypeScript SPA with modern Tailwind UI
- **Standalone Frontend**: Additional `/frontend` at root level (separate deployment)

### LLM Provider Architecture

The system supports multiple LLM providers through a unified interface:

- **OpenAI API**: Production integration with logprobs for perplexity calculations
- **Ollama**: Local LLM support for development/privacy
- **Mock Provider**: Testing and development without API costs

Located in: `backend/app/services/unified_llm_provider.py`

### Background Processing

Automated optimization runs via Django background scheduler:

- Configurable batch triggers based on feedback accumulation
- Statistical validation before prompt deployment
- Rate limiting to prevent over-optimization
- Rollback capability for failed optimizations

Located in: `backend/app/services/background_scheduler.py`

## Key Components

### Backend Services (`backend/app/services/`)

- **`optimization_orchestrator.py`**: Core batch-based optimization engine
- **`dual_llm_coordinator.py`**: Manages rewriter and task LLM coordination
- **`evaluation_engine.py`**: A/B testing and statistical validation
- **`human_feedback_integrator.py`**: Processes user feedback into learning signals
- **`reward_aggregator.py`**: Combines F1, perplexity, and human feedback rewards

### Frontend Components (`frontend/src/components/`)

- **`SessionCollection.tsx`**: Main homepage with session grid and management
- **`SessionCard.tsx`**: Individual session display with stats and actions
- **`SessionCreator.tsx`**: Modal for creating new learning sessions
- **`Dashboard.tsx`**: Real-time system monitoring and analytics
- **`DemoWorkflow.tsx`**: Guided demonstration workflows

### API Structure (`backend/app/api/`)

- **Session Management**: Full CRUD for learning sessions with export/import
- **Email & Draft Generation**: Session-scoped email creation and response drafts
- **Feedback Collection**: Captures user decisions (accept/reject/edit/ignore)
- **Optimization Control**: Triggers and monitors optimization runs
- **Dashboard APIs**: Real-time metrics and system status

## Database Schema

**Core Entities**:

- `Session`: Top-level container for isolated learning experiments
- `SystemPrompt`: Session-scoped prompt versions with performance tracking
- `Email`: Session-scoped test emails (synthetic or real)
- `Draft`: AI-generated responses with reasoning factors
- `UserFeedback`: Human decisions with rationale and reason ratings

**Key Relationships**: All major entities are session-scoped to ensure complete isolation between learning experiments.

## Testing Philosophy

The project emphasizes **real function testing** over mocks:

- **Business Logic Tests**: Validate actual algorithms without mocking core functions
- **Mathematical Validation**: Test real F1 calculations, perplexity, and reward aggregation
- **End-to-End Scenarios**: Complete learning cycles from feedback to optimization
- **Performance Tracking**: Real trend analysis and threshold decision logic

Critical test files:

- `tests/test_feedback_real_functions.py`: Real business logic validation
- `tests/test_reward_real_functions.py`: Mathematical accuracy verification
- `tests/test_session_endpoints.py`: Session management API coverage

## Development Workflow

### Adding Session-Scoped Features

1. **Model Changes**: Update `core/models.py` with session foreign keys
2. **API Updates**: Modify controllers to accept `session_id` parameters
3. **Frontend Integration**: Update services and components for session context
4. **Testing**: Add both unit tests and session isolation tests

### LLM Provider Integration

1. **Service Layer**: Implement provider in `services/` following unified interface
2. **Configuration**: Add provider settings to Django settings
3. **Testing**: Create provider-specific test suite
4. **Documentation**: Update LLM_PROVIDER_GUIDE.md

## Configuration

### Environment Variables

```bash
# Backend (.env in backend/)
OPENAI_API_KEY=your_openai_key          # For production LLM integration
OLLAMA_BASE_URL=http://localhost:11434  # For local LLM development
DEBUG=True                              # Development mode

# Frontend (.env.local in frontend/)
VITE_API_BASE_URL=http://localhost:8000 # Backend API endpoint
```

### Database

- **Development**: SQLite (auto-created)
- **Production**: Configurable via Django settings
- **Migrations**: Auto-managed through Django ORM

## Tailwind CSS Usage

The frontend uses Tailwind CSS v4 with:

- **Custom Components**: `.btn-primary`, `.card-elevated` for consistency
- **Design System**: Purple/indigo gradients, professional spacing
- **Responsive**: Mobile-first grid layouts and navigation
- **Modern UI**: Glass-morphism effects, smooth animations

Configuration (v4 approach):
- `frontend/vite.config.ts` - Tailwind v4 Vite plugin integration  
- `frontend/src/index.css` - CSS-based configuration with `@theme` block and CSS custom properties
- **No separate config files** - Configuration uses CSS custom properties (`--color-*`, `--animate-*`)

## API Authentication

Currently **development-friendly** (no authentication required). For production deployment, implement:

- Session-based authentication for user sessions
- API key authentication for external integrations
- CORS configuration for cross-origin requests

## Performance Considerations

- **Batch Processing**: Optimization runs are triggered by thresholds, not individual feedback
- **Caching**: LLM responses cached to reduce API costs during development
- **Database**: Optimized queries with select_related/prefetch_related for sessions
- **Frontend**: React optimization with proper key props and memoization
