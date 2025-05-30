# Loop Learner Requirements Document

## Executive Summary

Loop Learner is a human-in-the-loop (HITL) machine learning system that demonstrates adaptive agent learning through iterative prompt evolution. Unlike traditional systems with fixed prompts, Loop Learner continuously evolves its system prompt based on qualitative human feedback, incorporating principles from reinforcement learning from human feedback (RLHF) and constitutional AI approaches.

## 1. System Overview

### 1.1 Core Concept

Loop Learner implements a multi-layered feedback system where:

- **Inner Loop**: Draft generation for email responses using an evolving system prompt
- **Middle Loop**: Prompt optimization based on human feedback and evaluation snapshots
- **Outer Loop**: Continuous probing and confidence building through synthetic data generation

### 1.2 Primary Use Case

The system generates draft email responses as a technical demonstration vehicle. This is primarily a research prototype - actual email integration is not required. The architecture is designed to be generalizable to other natural language generation tasks.

## 2. Functional Requirements

### 2.1 Draft Generation System

#### 2.1.1 Core Functionality

- **FR-001**: System SHALL generate 2+ draft email responses for each incoming email
- **FR-002**: Each draft MUST include a concise list of reasoning factors that influenced the suggestion
- **FR-003**: Draft generation MUST use a dynamic system prompt that includes user preferences in natural language
- **FR-004**: System prompt MUST be updatable based on feedback without code changes

#### 2.1.2 Output Requirements

- **FR-005**: Drafts SHALL be presented in a desktop-optimized web interface
- **FR-006**: Each suggestion MUST display associated reasoning clearly
- **FR-007**: Reasoning items MUST be individually rateable (like/dislike)

### 2.2 Human Feedback Interface

#### 2.2.1 Decision Options

- **FR-008**: Users SHALL be able to accept suggestions in whole
- **FR-009**: Users SHALL be able to reject suggestions with textual reasoning
- **FR-010**: Users SHALL be able to edit suggestions with textual reasoning
- **FR-011**: Users SHALL be able to ignore emails without providing feedback
- **FR-012**: Users SHALL be able to rate individual reasoning factors

#### 2.2.2 Feedback Collection

- **FR-013**: System MUST capture all user decisions made through the UI
- **FR-014**: Feedback MUST include context about the original email being responded to
- **FR-015**: System MUST preserve user preference statements in natural language

### 2.3 Prompt Optimization Engine

#### 2.3.1 Optimization Process

- **FR-016**: Optimizer MUST accept arrays of suggestions with associated feedback
- **FR-017**: Optimizer MUST reference historical snapshots for evaluation
- **FR-018**: Optimizer MUST call SOTA LLM providers for prompt improvement
- **FR-019**: System MUST evaluate new prompts against historical performance snapshots
- **FR-020**: Optimization MUST continue until no meaningful improvements are detected

#### 2.3.2 Evaluation Framework

- **FR-021**: System MUST maintain a curated set of evaluation snapshots
- **FR-022**: Eval set MUST remain lean for runtime performance optimization
- **FR-023**: System MUST implement algorithm for selecting which snapshots to preserve, balancing quality and performance

### 2.4 Cold Start Solution

#### 2.4.1 Synthetic Data Generation

- **FR-024**: System MUST provide button to generate fake email scenarios on demand
- **FR-025**: System MUST generate fake email scenarios to solicit initial feedback during cold start
- **FR-026**: Synthetic data MUST be realistic enough to elicit meaningful user preferences
- **FR-027**: Cold start process MUST continue until user or system confidence threshold is met

### 2.5 State Management and Persistence

#### 2.5.1 State Representation

- **FR-028**: Complete system state MUST be representable in structured JSON format
- **FR-029**: State MUST persist between sessions
- **FR-030**: State MUST exclude UI-specific data, but UI should be able to ingest state

#### 2.5.2 Export Functionality

- **FR-031**: System MUST support exporting complete state data
- **FR-032**: Exported data MUST include current system prompt
- **FR-033**: Exported data MUST include user preferences
- **FR-034**: Exported data MUST include evaluation snapshots

### 2.6 Session Management and Frontend Interface

#### 2.6.1 Session Creation and Management

- **FR-035**: Users SHALL be able to create new learning sessions
- **FR-036**: Each session MUST be associated with a specific system prompt and its evolution history
- **FR-037**: Sessions MUST persist across browser sessions and device changes
- **FR-038**: Users SHALL be able to name and describe sessions for easy identification
- **FR-039**: System MUST track session creation date, last activity, and optimization iterations

#### 2.6.2 Session Collection View

- **FR-040**: Frontend MUST provide a collection view displaying all user sessions
- **FR-041**: Session collection MUST show session name, description, creation date, and last activity
- **FR-042**: Session collection MUST indicate current optimization status (active, paused, completed)
- **FR-043**: Users SHALL be able to filter and search sessions by name, date, or status
- **FR-044**: Users SHALL be able to sort sessions by creation date, last activity, or name
- **FR-045**: Session collection MUST provide quick actions (delete, duplicate, export)

#### 2.6.3 Session Detail View

- **FR-046**: Clicking on a session MUST navigate to a dedicated session overview page
- **FR-047**: Session overview MUST contain all functionality currently shown on the homepage
- **FR-048**: Session overview MUST display current system prompt and its evolution history
- **FR-049**: Session overview MUST show session-specific learning metrics and progress
- **FR-050**: Session overview MUST provide session-scoped email generation and feedback collection
- **FR-051**: Users SHALL be able to export individual session data
- **FR-052**: Users SHALL be able to switch between sessions without losing current work

#### 2.6.4 Session State Isolation

- **FR-053**: Each session MUST maintain independent system state and prompt evolution
- **FR-054**: Feedback provided in one session MUST NOT affect other sessions
- **FR-055**: Session data MUST be isolated to prevent cross-contamination
- **FR-056**: Users SHALL be able to work on multiple sessions simultaneously in different browser tabs

## 3. Non-Functional Requirements

### 3.1 Performance Requirements

- **NFR-001**: Draft generation MUST complete within 10 seconds
- **NFR-002**: Prompt optimization MUST complete within 5 minutes
- **NFR-003**: System MUST support concurrent user sessions, so that feedback can be solicited during optimization

### 3.2 Usability Requirements

- **NFR-004**: Web interface MUST be fit for desktop usage
- **NFR-005**: User feedback collection MUST be intuitive and require minimal training
- **NFR-006**: System MUST provide clear indicators of learning progress

### 3.3 Reliability Requirements

- **NFR-007**: System MUST gracefully handle LLM provider API failures
- **NFR-008**: State persistence MUST be atomic to prevent corruption
- **NFR-009**: System MUST maintain audit trail of all optimization iterations

## 4. Technical Architecture

### 4.1 System Components

- **Draft Generator**: Core LLM integration for response generation
- **Feedback Collector**: Web interface for human input capture
- **Prompt Optimizer**: Meta-learning system for prompt evolution
- **Evaluation Engine**: Performance assessment against historical snapshots
- **State Manager**: Persistence and export functionality
- **Synthetic Data Generator**: Cold start problem solver

### 4.2 Data Flow

1. User triggers fake email generation via button click
2. System generates synthetic incoming email
3. Multiple drafts with reasoning presented to user
4. User feedback collected and structured (accept/reject/edit/ignore)
5. Feedback triggers prompt optimization cycle
6. New prompt evaluated against historical performance
7. Improved prompt deployed for next iteration

## 5. Work Plan

### 5.1 Development Phases

#### Phase 1: Core Infrastructure

- Set up Python backend framework (FastAPI/Flask) using uv for dependency management
- Set up TypeScript/React frontend framework using Vite
- Initialize Git repositories for version control (separate repos for frontend/backend)
- Implement LLM provider integration
- Create basic draft generation pipeline
- Develop state management system

#### Phase 2: Feedback Collection

- Build desktop-optimized React interface
- Implement feedback capture mechanisms
- Create structured data models for user input
- Develop basic prompt modification logic
- Establish frontend-backend API communication

#### Phase 3: Optimization Engine

- Build prompt optimization algorithm
- Implement evaluation framework
- Create snapshot management system
- Develop performance assessment metrics

#### Phase 4: Cold Start & Polish

- Implement synthetic data generation
- Add export/import functionality
- Performance optimization and testing
- Documentation and deployment preparation

### 5.2 Module Responsibilities

#### 5.2.1 Frontend Repository (`frontend/`)

**Technology Stack:**
- TypeScript
- React
- Vite for build tooling and development server
- Git for version control
- Separate dependency management (package.json)

**Responsibilities:**

- Desktop-optimized React interface
- Real-time feedback collection
- Draft presentation and interaction
- Progress visualization

**Key Components:**

- `SessionCollection`: Display and manage all user sessions with filtering and search
- `SessionOverview`: Session-specific view containing all current homepage functionality
- `EmailGenerator`: Button-triggered fake email generation (session-scoped)
- `DraftViewer`: Display multiple email drafts with reasoning (session-scoped)
- `FeedbackCollector`: Capture user decisions and ratings (session-scoped)
- `ProgressDashboard`: Show learning progress and confidence metrics (session-scoped)
- `StateExporter`: Handle data export functionality (global and session-specific)
- `SessionCreator`: Interface for creating new sessions with name and description
- `PromptEvolutionViewer`: Display system prompt history and evolution within a session

#### 5.2.2 Backend Repository (`backend/`)

**Technology Stack:**
- Python
- FastAPI or Flask
- uv for dependency management and virtual environments
- Git for version control
- pyproject.toml for project configuration

**Responsibilities:**

- RESTful API for frontend communication
- Session management
- Data validation and sanitization
- Integration orchestration

**Key Components:**

- `SessionController`: Create, read, update, delete session management
- `EmailController`: Handle fake email generation and draft requests (session-scoped)
- `FeedbackController`: Process user feedback (session-scoped, including ignore actions)
- `StateController`: Manage state persistence and export (global and session-specific)
- `OptimizationController`: Trigger and monitor optimization cycles (session-scoped)

#### 5.2.3 Draft Generation Module (Backend: `drafters/`)

**Responsibilities:**

- LLM provider integration (OpenAI, Anthropic APIs)
- Prompt template management
- Response generation with reasoning
- Provider failover handling

**Key Components:**

- `LLMProvider`: Abstract interface for different LLM services
- `PromptBuilder`: Dynamic prompt construction from templates and preferences
- `DraftGenerator`: Core response generation logic
- `ReasoningExtractor`: Parse and structure reasoning from LLM outputs

#### 5.2.4 Optimization Engine Module (Backend: `optimizer/`)

**Responsibilities:**

- Prompt evolution algorithms
- Performance evaluation
- Snapshot management
- Convergence detection

**Key Components:**

- `PromptOptimizer`: Main optimization algorithm implementation
- `EvaluationEngine`: Assess prompt performance against snapshots
- `SnapshotManager`: Curate and maintain evaluation dataset
- `ConvergenceDetector`: Determine when optimization should stop

#### 5.2.5 State Management Module (Backend: `state/`)

**Responsibilities:**

- Data persistence (SQLite/PostgreSQL)
- State serialization/deserialization
- Export/import functionality
- Migration handling

**Key Components:**

- `StateSerializer`: Convert application state to/from JSON
- `PersistenceLayer`: Handle database operations
- `ExportManager`: Generate exportable data packages
- `MigrationManager`: Handle state schema evolution

#### 5.2.6 Synthetic Data Module (Backend: `synthetic/`)

**Responsibilities:**

- Generate realistic email scenarios
- Create diverse feedback situations
- Cold start orchestration
- Confidence assessment

**Key Components:**

- `EmailGenerator`: Create synthetic incoming emails
- `ScenarioBuilder`: Construct realistic email contexts
- `ConfidenceTracker`: Monitor system and user confidence levels
- `ColdStartOrchestrator`: Manage initial learning phase

## 6. Testing Strategy

### 6.1 Testing Philosophy

- **Module-Level Focus**: Testing strategy should be implemented at the module level, with each module responsible for its own test suite
- **Test-Driven Development (TDD)**: Use TDD approach - write failing tests first, then implement code to make them pass
- **Modularity Enforcement**: TDD process should encourage clean module interfaces and loose coupling

### 6.2 Unit Testing

- **Minimal Unit Tests**: Unit tests should be kept minimal, primarily used to establish and validate module interfaces
- **Interface Definition**: Focus on testing public APIs and contracts between modules rather than implementation details
- **Frontend Framework**: Jest for TypeScript/React components
- **Backend Framework**: pytest for Python components
- **TDD Workflow**: 
  1. Write failing test that defines expected interface behavior
  2. Implement minimal code to make test pass
  3. Refactor while keeping tests green
- **Focus Areas**:
  - Module interface contracts
  - Data transformation boundaries
  - API endpoint contracts
  - LLM provider integration interfaces

### 6.3 Integration Testing

- **API Testing**: Comprehensive REST API testing between TypeScript frontend and Python backend
- **LLM Integration**: Test with actual LLM providers using test accounts
- **Database Integration**: Test state persistence under various scenarios
- **End-to-End Workflows**: Complete user journey testing across both repositories

### 6.4 Performance Testing

- **Load Testing**: Simulate multiple concurrent users
- **Stress Testing**: Test system behavior under resource constraints
- **Optimization Performance**: Measure prompt optimization cycle times
- **Memory Usage**: Monitor state growth and memory consumption

### 6.5 User Acceptance Testing

- **Usability Testing**: Desktop interface optimization validation
- **Feedback Quality**: Assess quality of collected user feedback
- **Learning Effectiveness**: Measure actual prompt improvement over iterations
- **Cold Start Effectiveness**: Validate synthetic data approach

### 6.6 Security Testing

- **Input Validation**: Test against malicious user inputs
- **API Security**: Authentication and authorization testing
- **Data Privacy**: Ensure user feedback data protection
- **LLM Prompt Injection**: Test resilience against prompt injection attacks

### 6.7 Evaluation Metrics

- **System Performance Metrics**:

  - Draft generation latency
  - Optimization cycle completion time
  - User feedback collection rate
  - System uptime and reliability

- **Learning Effectiveness Metrics**:

  - Prompt performance improvement over time
  - User satisfaction scores
  - Acceptance rate of generated drafts
  - Reduction in user edits over time

- **User Experience Metrics**:
  - Time to provide feedback
  - Feedback completion rate
  - User confidence progression
  - Feature adoption rates

## 7. Technical Considerations

### 7.1 LLM Provider Integration

- Support for multiple providers (OpenAI, Anthropic, Google, etc.)
- Graceful fallback mechanisms
- Cost optimization strategies
- Rate limiting and quota management

### 7.2 Data Privacy and Security

- User feedback data encryption
- Secure state persistence
- API authentication and authorization
- Compliance with data protection regulations

### 7.3 Scalability Architecture

- Separate frontend and backend repositories for independent deployment
- Python backend designed for horizontal scaling
- React frontend served via CDN for global distribution
- Asynchronous processing for optimization cycles
- Caching strategies for frequently accessed data
- Database optimization for state queries

## 8. Success Criteria

### 8.1 Technical Success Metrics

- System successfully demonstrates prompt evolution through human feedback
- Measurable improvement in draft quality over time
- Stable performance under normal usage loads
- Successful cold start process for new users

### 8.2 Research Success Metrics

- Clear evidence of learning from human feedback
- Effective transfer of learning across similar email contexts
- Demonstration of preference adaptation without programming
- Reproducible results across different user profiles

### 8.3 User Experience Success Metrics

- Users can effectively provide feedback without technical training
- Clear visualization of system learning progress
- Intuitive interface for complex feedback scenarios
- Successful export and import of learned preferences

## 9. Future Enhancements

### 9.1 Multi-Domain Adaptation

- Extend beyond email to other text generation tasks
- Support for domain-specific prompt optimization
- Cross-domain learning transfer capabilities

### 9.2 Advanced Learning Algorithms

- Implementation of more sophisticated RLHF techniques
- Constitutional AI integration for safety constraints
- Multi-objective optimization for competing preferences

### 9.3 Collaborative Learning

- Multi-user learning environments
- Shared preference models
- Organizational learning capabilities

---

_This requirements document serves as the foundation for implementing Loop Learner and may be iteratively refined based on implementation discoveries and user feedback._
