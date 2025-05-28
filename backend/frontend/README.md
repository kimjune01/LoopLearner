# Loop Learner Frontend

Modern React + TypeScript frontend for the Loop Learner human-in-the-loop machine learning system.

## Overview

The Loop Learner frontend provides an interactive web interface for demonstrating adaptive learning through human feedback. Built with React 19 + TypeScript + Vite, it offers three main modes: Demo, Workflow, and Dashboard.

## Features

### 🎭 **Demo Mode**
- **Email Generation**: Create synthetic test emails across 4 scenario types
- **Draft Generation**: Generate AI response drafts with reasoning factors
- **Interactive Feedback**: Accept/Reject/Edit/Skip buttons for training the system
- **Real-time Updates**: Watch the system learn from your feedback

### 🔄 **Workflow Mode**
- **Guided Scenarios**: 3 predefined learning demonstrations
- **Step-by-step Progress**: Visual workflow with real-time progress tracking
- **Automated Learning**: Complete end-to-end demonstration cycles
- **Results Analytics**: Comprehensive metrics and learning objectives achieved

### 📊 **Dashboard Mode**
- **System Monitoring**: Real-time scheduler health and optimization activity
- **Performance Analytics**: Improvement trends, acceptance rates, learning velocity
- **Optimization History**: Success rates, statistical validation, recent optimizations
- **Learning Efficiency**: Feedback patterns, optimization ratios, system metrics
- **Auto-refresh**: 30-second intervals for live data updates

## Tech Stack

- **React 19** - Latest React with concurrent features
- **TypeScript** - Type-safe development
- **Vite** - Fast build tooling with HMR
- **Tailwind CSS** - Modern responsive design
- **Axios** - API communication with Django backend
- **React Router** - Client-side routing between modes
- **Error Boundaries** - Comprehensive error handling

## Getting Started

### Prerequisites
- Node.js 18+
- pnpm

### Development Setup
```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview
```

### Environment Configuration
Create a `.env` file for local development:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Architecture

### Component Structure
```
src/
├── components/
│   ├── Demo/          # Demo mode components
│   ├── Workflow/      # Workflow mode components
│   ├── Dashboard/     # Dashboard mode components
│   └── common/        # Shared components
├── hooks/             # Custom React hooks
├── services/          # API service layer
├── types/             # TypeScript type definitions
└── utils/             # Utility functions
```

### Key Components

**Demo Mode:**
- `EmailGenerator` - Synthetic email creation interface
- `DraftGenerator` - AI response generation with reasoning
- `FeedbackCollector` - Interactive feedback buttons
- `LearningProgress` - Real-time learning visualization

**Workflow Mode:**
- `ScenarioSelector` - Choose from predefined learning scenarios
- `WorkflowProgress` - Step-by-step progress visualization
- `DemoRunner` - Automated demonstration execution
- `ResultsAnalyzer` - Demo metrics and analytics

**Dashboard Mode:**
- `SystemStatus` - Scheduler health and optimization activity
- `PerformanceCharts` - Improvement trends and analytics
- `OptimizationHistory` - Recent optimization timeline
- `LearningMetrics` - Efficiency ratios and pattern analysis

## API Integration

The frontend communicates with the Django backend through a comprehensive REST API:

### Core Demo APIs
- `POST /api/generate-synthetic-email/` - Create test scenarios
- `POST /api/emails/{email_id}/generate-drafts/` - Generate responses
- `POST /api/drafts/{draft_id}/submit-feedback/` - Submit feedback
- `GET /api/system/state/` - Export system state

### Dashboard APIs
- `GET /api/dashboard/overview/` - Complete dashboard data
- `GET /api/dashboard/metrics/` - Learning analytics
- `GET /api/optimization/history/` - Optimization history

### Workflow APIs
- `POST /api/demo/workflow/` - Run demonstration scenarios
- `GET /api/demo/status/` - Monitor workflow progress

## Responsive Design

Built with Tailwind CSS for modern, responsive design:
- **Mobile-first**: Optimized for all screen sizes
- **Dark/Light Mode**: Automatic theme adaptation
- **Accessibility**: WCAG compliant with proper ARIA labels
- **Performance**: Optimized loading and rendering

## Error Handling

Comprehensive error handling with:
- **Error Boundaries**: Catch and display React errors gracefully
- **API Error States**: User-friendly error messages for API failures
- **Retry Mechanisms**: Automatic retry for transient failures
- **Loading States**: Clear feedback during async operations

## Development Scripts

```bash
# Development
pnpm dev              # Start development server with HMR
pnpm build            # Build for production
pnpm preview          # Preview production build locally

# Code Quality
pnpm lint             # Run ESLint
pnpm lint:fix         # Fix ESLint issues automatically
pnpm type-check       # Run TypeScript type checking

# Testing (when implemented)
pnpm test             # Run test suite
pnpm test:watch       # Run tests in watch mode
pnpm test:coverage    # Generate coverage report
```

## Configuration

### Vite Configuration
- **Fast Refresh**: Instant updates during development
- **TypeScript Support**: Built-in TypeScript compilation
- **Path Aliases**: Clean import paths with @ aliases
- **Environment Variables**: VITE_ prefixed variables

### ESLint & TypeScript
- **Strict TypeScript**: Type-aware lint rules enabled
- **React Best Practices**: React-specific linting rules
- **Code Formatting**: Consistent code style enforcement

## Performance Optimization

- **Code Splitting**: Automatic route-based code splitting
- **Tree Shaking**: Eliminate unused code
- **Asset Optimization**: Optimized images and fonts
- **Caching**: Efficient browser caching strategies

## Production Deployment

The frontend builds to static files that can be served by any web server:

```bash
# Build production bundle
pnpm build

# Output directory: dist/
# Deploy dist/ contents to your web server
```

**Deployment Notes:**
- Configure your web server to serve `index.html` for all routes (SPA routing)
- Set appropriate cache headers for static assets
- Configure CORS if backend is on different domain

## Contributing

1. Follow the established component patterns
2. Use TypeScript for all new code
3. Follow the existing code style (ESLint + Prettier)
4. Write tests for new components (when test suite is implemented)
5. Update this README for significant changes

## Integration with Backend

The frontend is designed to work seamlessly with the Loop Learner Django backend:
- **Real-time Communication**: WebSocket support for live updates
- **State Management**: Efficient state synchronization with backend
- **Error Handling**: Graceful degradation when backend is unavailable
- **Development Mode**: Proxy configuration for local development

---

**Loop Learner Frontend** provides a modern, responsive interface for demonstrating and monitoring human-in-the-loop machine learning with real-time feedback visualization and comprehensive system analytics.

> Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>