# Loop Learner

A human-in-the-loop (HITL) machine learning system that demonstrates adaptive agent learning through iterative prompt evolution.

## Overview

Loop Learner implements a multi-layered feedback system where AI agents learn from human feedback to continuously improve their performance. The system uses email response generation as a demonstration vehicle, but the architecture is designed to be generalizable to other natural language generation tasks.

## Architecture

- **Frontend**: TypeScript/React with Vite (separate repository)
- **Backend**: Python with FastAPI/Flask using uv (separate repository)
- **Version Control**: Git with separate repositories for frontend and backend

## Key Features

- Dynamic prompt evolution based on human feedback
- Multi-draft response generation with reasoning
- Real-time learning and adaptation
- Cold start problem solving with synthetic data
- State persistence and export functionality

## Documentation

See [REQUIREMENTS.md](./REQUIREMENTS.md) for detailed functional and technical requirements.

## Development Setup

This is the main repository containing documentation and requirements. The actual implementation will be split into:

- Frontend repository: TypeScript/React with Vite
- Backend repository: Python with uv dependency management

## Getting Started

1. Review the requirements document
2. Set up separate repositories for frontend and backend
3. Follow the development phases outlined in REQUIREMENTS.md

## License

TBD