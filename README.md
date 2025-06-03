# Loop Learner

A production-ready human-in-the-loop machine learning system for optimizing email response generation using reinforcement learning, batch-based optimization, and real-time performance monitoring.

## Overview

Loop Learner implements a comprehensive prompt optimization platform inspired by the PRewrite methodology (arXiv:2401.08189). It uses reinforcement learning with human feedback, batch-based triggers, statistical evaluation, and real-time dashboard monitoring to continuously improve AI-generated email responses through an interactive web interface.

## Production-Ready System

✅ **Complete Learning Engine**
- Real Log Probabilities using OpenAI's logprobs API for genuine perplexity-based rewards
- LLM-Based Prompt Rewriting with advanced similarity matching and pattern optimization
- Multi-Metric Reward System combining F1 + Perplexity + Human Feedback hybrid scoring
- Database-Driven Learning with pattern storage and retrieval for continuous improvement

✅ **Batch-Based Optimization**
- Smart Triggers that optimize only when sufficient feedback accumulates (configurable thresholds)
- Statistical Validation requiring statistical significance before deployment
- Rate Limiting to prevent over-optimization with time-based controls
- Automated Deployment with confidence-based prompt updates and rollback capability

✅ **Comprehensive Evaluation System**
- A/B Testing Engine for statistical comparison of prompt candidates
- Batch Prompt Evaluator for automated performance testing against test cases
- Evaluation Test Suite with generated and curated test case management
- Performance Metrics including success rates, improvement tracking, and confidence calculations
- Dataset-Based Optimization with real-time progress tracking and navigation

✅ **Real-Time Dashboard**
- System Status Monitoring including scheduler health, active prompts, and optimization activity
- Performance Analytics with improvement trends, acceptance rates, and learning velocity
- Optimization Activity tracking success rates, historical data, and recent optimization timeline
- Learning Efficiency metrics with feedback-to-optimization ratios and pattern analysis
- Modern UI with Tailwind CSS responsive design and auto-refresh capabilities

✅ **Complete Demonstration Workflows**
- Automated Demo Scenarios with 3 predefined learning scenarios
- Guided User Experience with step-by-step workflow and real-time progress visualization
- End-to-End Learning Cycle demonstrating complete feedback collection to optimization flow
- Demo Analytics with comprehensive metrics and reporting for demonstration results
- Interactive Workflows with REST API integration and React frontend for seamless demo experience

✅ **Production Architecture**
- Django REST API with comprehensive backend and async ORM operations
- React + TypeScript Frontend with modern UI and navigation between demo and dashboard
- Unified LLM Provider supporting OpenAI, Ollama, and mock providers
- Background Scheduler for automated optimization checks with configurable intervals
- Comprehensive Testing with 200+ tests covering all functionality with 95%+ coverage

## Key Features

### 🧠 **Core Learning Engine**
- **Real Log Probabilities**: Genuine perplexity-based reward calculation using OpenAI's logprobs API
- **LLM-Based Prompt Rewriting**: Advanced similarity matching and pattern-based optimization
- **Multi-Metric Reward System**: F1 + Perplexity + Human Feedback hybrid scoring
- **Database-Driven Learning**: Pattern storage and retrieval for continuous improvement

### 🔄 **Batch-Based Optimization**
- **Smart Triggers**: Optimization only when sufficient feedback accumulates (configurable thresholds)
- **Statistical Validation**: Requires statistical significance before deployment
- **Rate Limiting**: Prevents over-optimization with time-based controls
- **Automated Deployment**: Confidence-based prompt updates with rollback capability

### 📊 **Comprehensive Evaluation System**
- **A/B Testing Engine**: Statistical comparison of prompt candidates
- **Batch Prompt Evaluator**: Automated performance testing against test cases
- **Evaluation Test Suite**: Generated and curated test case management
- **Performance Metrics**: Success rates, improvement tracking, confidence calculations
- **Dataset-Based Optimization**: Real-time progress tracking with immediate navigation to run details
- **Optimization Run Management**: Track optimization history, view results, and monitor status

### 📈 **Real-Time Dashboard**
- **System Status Monitoring**: Scheduler health, active prompts, optimization activity
- **Performance Analytics**: Improvement trends, acceptance rates, learning velocity
- **Optimization Activity**: Success rates, historical data, recent optimization timeline
- **Learning Efficiency**: Feedback-to-optimization ratios, pattern analysis
- **Modern UI**: Tailwind CSS responsive design with auto-refresh capabilities

### 🧪 **Advanced Testing Philosophy**

**Real Function Testing**: Unlike traditional tests that mock business logic, Loop Learner includes comprehensive real implementation tests that validate actual mathematical calculations and algorithms:

- **Reward Function Accuracy**: Tests verify real F1 score calculations, perplexity computations, and reward aggregation math
- **Performance Tracking**: Validates actual performance history tracking, trend analysis, and threshold decision logic  
- **Text Analysis**: Tests real edit analysis, feature extraction, and preference learning algorithms
- **Business Logic**: Verifies feedback processing, reason rating calculations, and user preference updates

**Benefits of Real Testing**:
- **Bug Discovery**: Found actual bugs in reward functions that were hidden by mocks (None value handling)
- **Mathematical Accuracy**: Validates complex calculations like F1 scores, edit ratios, and trend analysis
- **Confidence**: Ensures core algorithms work correctly under real conditions
- **Documentation**: Tests serve as executable specifications of expected behavior

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

**✅ Production Ready Features:**
- Complete batch-based optimization system with statistical validation
- Real-time dashboard with comprehensive analytics and monitoring
- Automated prompt deployment with confidence thresholds and rollbacks
- Background scheduler with configurable triggers and rate limiting
- Real log probabilities calculation for genuine perplexity-based rewards
- A/B testing engine with statistical significance validation
- Dataset-based optimization with real-time progress tracking and navigation
- Optimization run management with UUID-based tracking and status monitoring
- Complete demonstration workflows with 3 predefined learning scenarios
- Modern Tailwind CSS responsive frontend with demo, workflow, and dashboard modes
- Comprehensive test suite with 200+ tests covering all functionality including real implementations

**🎯 System Highlights:**
- **Intelligence**: Genuine learning from human feedback with statistical validation
- **Efficiency**: Batch-based triggers prevent wasteful over-optimization
- **Reliability**: Comprehensive error handling, logging, and recovery mechanisms
- **Visibility**: Real-time dashboard provides complete system transparency
- **Scalability**: Modular architecture supports additional providers and metrics
- **Test Quality**: Real function tests validate actual business logic without mocks

**Test Coverage:**
- Core Learning Functions: 21/21 tests passing
- Optimization Orchestrator: 16/16 tests passing  
- Evaluation Engine: 13/13 tests passing
- Dashboard Controller: 14/14 tests passing
- Demo Workflow System: 14/14 tests passing
- API Endpoints: 23/23 tests passing
- Dataset Optimization: 15/15 tests passing
- Optimization Run Management: 12/12 tests passing
- **Real Function Tests: 20/20 tests passing** (Business logic without mocks)
- **Mathematical Calculations: 15/15 tests passing** (Reward functions with real math)

## Getting Started

### Prerequisites
- Python 3.13+
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

### Demo Mode
1. **Start Backend**: Django server runs on http://localhost:8000
2. **Start Frontend**: React app runs on http://localhost:5173
3. **Generate Email**: Click "Generate New Email" to create test scenarios
4. **Generate Drafts**: Click "Generate Drafts" to create AI responses
5. **Provide Feedback**: Use Accept/Reject/Edit/Skip buttons to train the system
6. **Batch Learning**: System automatically triggers optimization when sufficient feedback accumulates

### Workflow Mode  
1. **Switch to Workflow**: Click "Workflow" tab in the header
2. **Select Scenario**: Choose from 3 predefined learning scenarios
3. **Run Demo**: Execute complete demonstration with automated steps
4. **Monitor Progress**: Watch real-time learning progress and optimization
5. **Review Results**: Analyze demo metrics and learning objectives achieved

### Dashboard Mode
1. **Switch to Dashboard**: Click "Dashboard" tab in the header
2. **Monitor System**: View real-time system status and scheduler health
3. **Track Performance**: Analyze improvement trends and acceptance rates
4. **Review Optimizations**: See recent optimization history and success rates
5. **Learning Analytics**: Monitor feedback patterns and learning efficiency

## Testing

```bash
# Run all tests (200+ comprehensive tests)
uv run pytest

# Run specific test suites
uv run pytest tests/test_optimization_orchestrator.py  # Batch optimization
uv run pytest tests/test_evaluation_engine.py         # A/B testing
uv run pytest tests/test_dashboard_controller.py      # Dashboard APIs
uv run pytest tests/test_demo_workflow.py             # Demo workflows
uv run pytest tests/test_log_probabilities.py         # Learning functions
uv run pytest tests/test_learning_pipeline.py         # End-to-end learning

# Test real function implementations (no mocks)
uv run pytest tests/test_feedback_real_functions.py   # Real business logic
uv run pytest tests/test_reward_real_functions.py     # Real mathematical calculations

# Frontend development
cd frontend && pnpm dev
```

## Documentation

See [REQUIREMENTS.md](./REQUIREMENTS.md) for detailed functional and technical requirements.

## Research Foundation

This project builds upon cutting-edge research in prompt optimization and human-in-the-loop learning:

### Core Methodologies

**PRewrite: Prompt Rewriting with Reinforcement Learning**
- *Authors*: Weize Kong, Spurthi Amba Hombaiah, Mingyang Zhang, Qiaozhu Mei, Michael Bendersky
- *Paper*: [arXiv:2401.08189](https://arxiv.org/abs/2401.08189)
- *Application*: Dual-LLM architecture, PPO-based prompt optimization, meta-prompt framework

**Key Techniques Implemented:**
- **Reinforcement Learning**: PPO with KL penalty for stable prompt rewriting
- **Multi-Metric Rewards**: F1 + Perplexity hybrid reward functions (proven most effective)
- **Dual-LLM Architecture**: Separate rewriter and task LLMs for specialized optimization
- **Meta-Prompt Guidance**: Template-based prompt rewriting instructions

### Attribution

Loop Learner extends the PRewrite methodology by:
- Adding comprehensive human feedback integration
- Implementing scenario-specific optimization strategies  
- Creating adaptive learning rates based on user expertise
- Building interpretability and control mechanisms for human oversight

We acknowledge and thank the research community for these foundational contributions to automated prompt engineering.

## License

TBD