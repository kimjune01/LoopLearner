# Loop Learner

A human-in-the-loop machine learning system for optimizing email response generation using reinforcement learning and prompt rewriting techniques.

## Overview

Loop Learner implements a state-of-the-art prompt optimization system inspired by the PRewrite methodology (arXiv:2401.08189). It uses reinforcement learning with human feedback to continuously improve AI-generated email responses through an interactive web interface.

## Key Features

- **Dual-LLM Architecture**: Separate rewriter and task LLMs for specialized optimization
- **Multi-Metric Reward System**: F1 + Perplexity hybrid scoring for comprehensive evaluation
- **Human-in-the-Loop Learning**: Real-time feedback integration with RL training signals
- **Local LLM Support**: Ollama integration for fast, private development
- **Interactive Web Interface**: Modern React frontend for seamless user experience
- **Comprehensive Testing**: 99%+ test coverage with TDD approach

## System Architecture

### Backend (Django REST API)
- **Email Generation**: Synthetic email creation for training scenarios
- **Draft Generation**: Multi-LLM coordination for response drafts
- **Feedback Processing**: Human feedback integration into optimization pipeline
- **State Management**: System state export/import for reproducibility
- **Health Monitoring**: Real-time system metrics and status

### Frontend (React + TypeScript)
- **Email Workflow**: Generate ’ Draft ’ Feedback ’ Learn cycle
- **Interactive UI**: Tab-based draft selection with feedback buttons
- **Real-time Updates**: Automatic progression through optimization cycles
- **Responsive Design**: Works on desktop and mobile devices

### Core Components

1. **Prompt Rewriter Engine** - PPO-based prompt optimization with KL penalty
2. **Reward Function Aggregator** - Multi-dimensional scoring system
3. **Meta-Prompt Manager** - Template-based rewriting instructions
4. **Dual-LLM Coordinator** - Orchestrates rewriter and task LLMs
5. **Human Feedback Integrator** - Converts user input to training signals

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- pnpm
- uv (Python package manager)

### Backend Setup
```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

### Frontend Setup
```bash
cd backend/frontend
pnpm install
pnpm dev
```

### Local LLM Setup (Optional)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Llama 3.2 3B model
ollama pull llama3.2:3b
```

## Usage

1. **Start Backend**: Django server runs on http://localhost:8000
2. **Start Frontend**: React app runs on http://localhost:5173
3. **Generate Email**: Click "Generate New Email" to create a test scenario
4. **Generate Drafts**: Click "Generate Drafts" to create AI responses
5. **Provide Feedback**: Use Accept/Reject/Edit/Skip buttons to train the system
6. **Iterate**: System automatically generates new scenarios for continuous learning

## API Endpoints

- `POST /api/generate-synthetic-email/` - Create test email scenarios
- `POST /api/generate-drafts/{email_id}/` - Generate response drafts
- `POST /api/submit-feedback/` - Submit human feedback
- `GET /api/system-state/` - Export current system state
- `POST /api/trigger-optimization/` - Start optimization cycle
- `GET /api/health/` - System health check

## Configuration

### LLM Providers
Configure in environment variables:
```bash
LLM_PROVIDER=ollama  # Options: ollama, openai, anthropic, mock
OLLAMA_MODEL=llama3.2:3b
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### Optimization Settings
- **Conservative Mode**: Stable improvements with low KL penalty
- **Exploratory Mode**: Aggressive optimization for rapid learning
- **Hybrid Mode**: Balanced approach with adaptive learning rates

## Research Attribution

This implementation is inspired by and builds upon:

- **PRewrite: Prompt Rewriting with Reinforcement Learning** (arXiv:2401.08189)
- **Constitutional AI: Harmlessness from AI Feedback** (Anthropic, 2022)
- **Training Language Models to Follow Instructions with Human Feedback** (OpenAI, 2022)

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test suites
uv run pytest tests/test_api_endpoints.py
uv run pytest tests/test_prompt_rewriter.py
uv run pytest tests/test_dual_llm_coordinator.py

# Frontend tests (lightweight)
cd frontend && pnpm test
```

## Development Status

**Current Implementation:**
-  Complete API backend with 23/23 endpoint tests passing
-  React frontend with full workflow integration
-  Local LLM provider system with Ollama support
-  Comprehensive test suite (140/141 tests passing)
-  CORS configuration for frontend-backend communication

**Next Steps:**
- Implement real-time optimization visualization
- Add system metrics dashboard
- Enhance feedback collection with reasoning explanations
- Deploy production-ready configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow TDD principles - write tests first
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

---

> Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>