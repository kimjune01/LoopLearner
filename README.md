# Loop Learner

A human-in-the-loop (HITL) machine learning system that demonstrates adaptive agent learning through iterative prompt evolution.

## Overview

Loop Learner implements a multi-layered feedback system where AI agents learn from human feedback to continuously improve their performance. The system uses email response generation as a demonstration vehicle, but the architecture is designed to be generalizable to other natural language generation tasks.

## Current State (Phase 1 Complete)

✅ **Core Infrastructure Setup**
- Django backend with SQLite database for data persistence
- React/TypeScript frontend with Vite build system
- Pytest configuration with Django integration working
- Async/sync compatibility resolved for Django ORM

✅ **Database Schema Implemented**
- Email generation and storage (synthetic emails with 4 scenario types)
- Draft response tracking with reasoning factors
- User feedback collection (accept/reject/edit/ignore actions)
- System prompt versioning and evolution tracking
- Performance evaluation snapshots for optimization
- Complete relational data model for the learning loop

✅ **Core Services Implemented**
- **EmailGenerator**: Creates realistic synthetic emails with 4 scenario types
- **LLMProvider**: OpenAI integration for draft generation with reasoning factors
- **PromptOptimizer**: Framework for evolving prompts based on feedback
- Django REST API views for core functionality
- Async database operations properly configured

## Architecture

- **Frontend**: TypeScript/React with Vite and pnpm
- **Backend**: Python with Django + Django REST Framework + FastAPI hybrid
- **Database**: SQLite with Django ORM
- **LLM Integration**: OpenAI GPT-4 for draft generation and prompt optimization
- **Version Control**: Single Git repository with frontend/backend separation

## Key Features

- **Dynamic Prompt Evolution**: System prompts improve based on human feedback patterns
- **Multi-Draft Generation**: Each email generates 2+ response options with reasoning
- **Comprehensive Feedback Loop**: Track user preferences, actions, and reasoning ratings
- **Synthetic Data Generation**: 4 email scenario types (professional, casual, complaint, inquiry)
- **Database Persistence**: Complete audit trail of learning iterations
- **TDD Architecture**: Clean interfaces defined through failing tests

## Technology Stack

**Backend:**
- Django 5.2 + Django REST Framework
- SQLite database with full relationship modeling
- OpenAI API integration
- uv for dependency management
- pytest for testing

**Frontend:**
- React 19 + TypeScript
- Vite for build tooling
- Axios for API communication
- Vitest for testing
- pnpm for package management

## Development Status

**Completed:**
- ✅ Complete database schema and models
- ✅ Synthetic email generation with realistic templates
- ✅ OpenAI integration for draft generation with reasoning
- ✅ Django REST API endpoints for core functionality
- ✅ React component structure
- ✅ TDD test framework with passing email generator tests
- ✅ Async database operations properly configured
- ✅ Django settings configured for pytest execution

**In Progress:**
- 🔄 Complete test suite implementation (9 tests need setup fixes)
- 🔄 Frontend-backend API integration
- 🔄 Full end-to-end workflow testing

**Next Steps (Phase 2):**
- Complete remaining test implementations
- Add user interface for feedback collection
- Implement basic prompt optimization cycle
- Add error handling and logging

## Getting Started

1. **Backend Setup:**
   ```bash
   cd backend
   uv install
   uv run python manage.py migrate
   uv run python manage.py runserver
   ```

2. **Frontend Setup:**
   ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```

3. **Run Tests:**
   ```bash
   # Backend
   cd backend && uv run pytest
   
   # Frontend  
   cd frontend && pnpm test
   ```

## Documentation

See [REQUIREMENTS.md](./REQUIREMENTS.md) for detailed functional and technical requirements.

## License

TBD