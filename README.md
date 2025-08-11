
# Fusion Stock Analyst API

A comprehensive stock analysis platform with AI-powered insights, options strategies, and real-time market data.

## 🚀 Features

- **Fusion Dashboard**: Aggregated KPIs and market insights across timeframes
- **Equities Analysis**: Stock screening, portfolio tracking, and performance metrics
- **Options Strategies**: Short strangle analysis, position tracking, and Greeks calculation
- **Commodities**: Signal generation and correlation analysis
- **Performance Metrics**: Real-time KPI calculation and monitoring
- **AI Agents**: Intelligent analysis and recommendations
- **Risk Management**: Pins and locks for position and risk control

## 📊 API Surface

| Category | Endpoint | Method | Description | Status |
|----------|----------|---------|-------------|--------|
| **Health** | `/health` | GET | Health check | ✅ |
| | `/api/test` | GET | API test | ✅ |
| **Fusion** | `/api/fusion/dashboard` | GET | Main dashboard data | ✅ |
| | `/api/fusion/test` | GET | Test endpoint | ✅ |
| **Equities** | `/list` | GET | Paginated equities list | ✅ |
| | `/positions` | GET | Equity positions | ✅ |
| | `/kpis` | GET | Equity KPIs | ✅ |
| | `/analytics` | GET | Equity analytics | ✅ |
| **Options** | `/strangle/candidates` | GET | Short strangle candidates | ✅ |
| | `/strangle/plan` | POST | Create execution plan | ✅ |
| | `/positions` | GET | Options positions | ✅ |
| | `/positions/<id>` | GET | Position details | ✅ |
| | `/strategies` | GET | Options strategies | ✅ |
| | `/analytics` | GET | Options analytics | ✅ |
| | `/calculators` | GET | Pricing calculators | ✅ |
| **Commodities** | `/signals` | GET | Commodity signals | ✅ |
| | `/correlations` | GET | Correlation analysis | ✅ |
| | `/positions` | GET | Commodity positions | ✅ |
| | `/analytics` | GET | Commodity analytics | ✅ |
| | `/api/commodities` | GET | Commodities data | ✅ |
| **KPI** | `/api/kpi/metrics` | GET | KPI metrics by timeframe | ✅ |
| | `/api/kpi/recompute` | POST | Force KPI recalculation | ✅ |
| | `/api/kpi/all-timeframes` | GET | All timeframe KPIs | ✅ |
| | `/api/kpi/status` | GET | KPI system status | ✅ |
| **Pins & Locks** | `/api/pins` | GET, POST | User pins management | ✅ |
| | `/api/locks` | GET, POST | Risk locks management | ✅ |
| | `/api/status` | GET | System status | ✅ |
| **Agents** | `/` | GET | List agents | ✅ |
| **Documentation** | `/api` | GET | OpenAPI specification | ✅ |
| **Metrics** | `/metrics` | GET | System metrics | ✅ |

## 🔧 Quick Start

### Development Server

```bash
# Start the development server
python -u src/run_server.py

# Server will start on http://0.0.0.0:5000
```

### Key Endpoints

- **Dashboard**: `http://0.0.0.0:5000/api/fusion/dashboard`
- **Health Check**: `http://0.0.0.0:5000/health`
- **API Documentation**: `http://0.0.0.0:5000/api`
- **Metrics**: `http://0.0.0.0:5000/metrics`

## 📋 Definition of Done

### Backend Implementation Checklist

- [x] **Fusion Dashboard API** - Main aggregation endpoint with all KPI groups
- [x] **Equities API** - List, positions, analytics with filtering and pagination
- [x] **Options API** - Strangle candidates, plan creation, position tracking
- [x] **Commodities API** - Signals, correlations, analytics
- [x] **KPI Calculator** - Real-time metrics calculation across timeframes
- [x] **Pins & Locks** - User preference and risk management system
- [x] **Performance Guardrails** - Auto-degradation on budget violations
- [x] **Agents Framework** - AI-powered analysis and recommendations
- [x] **Caching Layer** - TTL cache for performance optimization
- [x] **Error Handling** - Comprehensive error responses and degraded mode
- [x] **Logging & Metrics** - Request tracking and performance monitoring

### Frontend Contract Enforcement

- [x] **Dashboard Layout** - 6 KPI cards, timeframe chips, top signals table
- [x] **Navigation** - 4 pages (Dashboard, Equities, Options, Commodities)
- [x] **Table Headers** - Consistent column naming across all views
- [x] **Verdict Normalization** - Standardized AI verdict display
- [x] **Responsive Design** - Mobile-friendly layouts

### Testing & Quality Assurance

- [x] **Backend Tests** - Contract enforcement for all API endpoints
- [x] **Frontend Tests** - Playwright tests for UI components and navigation
- [x] **Integration Tests** - End-to-end workflow validation
- [x] **Performance Tests** - Load testing and guardrails validation
- [x] **Regression Suite** - Automated testing pipeline

### Documentation & Contracts

- [x] **OpenAPI Specification** - Complete API documentation with examples
- [x] **README Documentation** - Setup, usage, and API surface
- [x] **Type Safety** - Schema validation for requests and responses
- [x] **Error Handling** - Standardized error responses
- [x] **Deployment Guide** - Production deployment instructions

### Performance & Reliability

- [x] **Caching Strategy** - Multi-level caching for optimal performance
- [x] **Circuit Breakers** - Auto-disable heavy features on resource constraints
- [x] **Monitoring** - Real-time performance metrics and alerting
- [x] **Graceful Degradation** - Fallback responses during service issues
- [x] **Load Testing** - Validated performance under expected load

## 🧪 Testing & Validation

### Running Regression Tests

```bash
# Run complete regression suite
python run_regression.py

# Run backend tests only
python -m pytest tests/backend/ -v

# Run frontend tests only  
python -m pytest tests/frontend/ -v

# Run specific test modules
python -m pytest tests/backend/test_fusion_api.py -v
```

### Test Coverage Areas

1. **API Contract Tests** - Validate response schemas and status codes
2. **Frontend Layout Tests** - Ensure UI components render correctly
3. **Integration Tests** - End-to-end workflow validation
4. **Performance Tests** - Response time and resource usage validation
5. **Error Handling Tests** - Graceful failure and recovery scenarios

### Viewing Metrics & Results

- **Test Results**: Console output during test execution
- **Performance Metrics**: `http://0.0.0.0:5000/metrics`
- **Guardrails Status**: `http://0.0.0.0:5000/api/performance/status`
- **System Health**: `http://0.0.0.0:5000/health`
- **KPI Status**: `http://0.0.0.0:5000/api/kpi/status`

### Continuous Integration

The regression suite runs:
- All backend API contract tests
- Frontend component and navigation tests
- Performance guardrails validation
- Data integrity checks
- Error handling scenarios

Tests are designed to catch:
- API contract violations
- UI component regressions
- Performance degradation
- Data inconsistencies
- Configuration drift

## 🚀 Deployment on Replit

### Development Deployment

1. Fork this Repl or use the template
2. Click the "Run" button to start the development server
3. Access the application at the provided URL

### Production Deployment

1. In the Workspace header, click **Deploy**
2. Choose **Autoscale** deployment type
3. Configure deployment settings:
   - **Build command**: (leave blank)
   - **Run command**: `python -u src/run_server.py`
   - **Port**: 5000 (default)
4. Click **Deploy** to publish your application

### Environment Configuration

The application uses these environment variables:
- `PORT`: Server port (default: 5000)
- `PYTHONPATH`: Set automatically to include src directory
- `DEBUG`: Set to false in production

### Scaling Configuration

For production workloads:
- **Machine configuration**: 1vCPU, 2 GiB RAM (minimum)
- **Max machines**: 3 (for high availability)
- **Auto-scaling**: Enabled based on traffic

## 📚 API Documentation

Full API documentation is available at `/api` endpoint, which serves the OpenAPI 3.0 specification.

### Key Features

- **Complete Schema Definitions** - All request/response models documented
- **Interactive Examples** - Sample requests and responses for each endpoint
- **Error Handling** - Comprehensive error response documentation
- **Authentication** - Security requirements and token handling
- **Rate Limiting** - Request throttling and quota information

### Integration Examples

```javascript
// Fetch dashboard data
const response = await fetch('/api/fusion/dashboard');
const dashboard = await response.json();

// Get KPI metrics for specific timeframe
const kpis = await fetch('/api/kpi/metrics?timeframe=10D');
const metrics = await kpis.json();

// Create options strangle plan
const plan = await fetch('/strangle/plan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    underlying: 'TCS',
    strikes: { call: 4400, put: 4200 },
    expiry: '2024-02-29'
  })
});
```

## 🎯 Architecture Overview

The application follows a modular architecture:

- **Core Layer**: Application bootstrapping, caching, guardrails
- **API Layer**: REST endpoints organized by business domain
- **Service Layer**: Business logic and data processing
- **Data Layer**: File-based storage with JSON fixtures
- **Agents Layer**: AI-powered analysis and recommendations

### Key Design Principles

1. **Contract-First**: OpenAPI specification drives implementation
2. **Performance-Aware**: Built-in guardrails and degraded mode handling
3. **Testable**: Comprehensive test coverage with automated regression
4. **Scalable**: Modular design supports horizontal scaling
5. **Observable**: Extensive logging and metrics collection

## 🔧 Development Guide

### Project Structure

```
src/
├── core/           # Application core (app, caching, guardrails)
├── api/            # API endpoints and routing
├── kpi/            # KPI calculation and storage
├── equities/       # Equity analysis modules
├── options/        # Options strategies and analytics
├── commodities/    # Commodity signals and correlations
├── agents/         # AI agents and orchestration
└── utils/          # Shared utilities and helpers

tests/
├── backend/        # API contract and integration tests
├── frontend/       # UI component and layout tests
└── utils/          # Test utilities and helpers

data/
├── fixtures/       # Sample data for development and testing
├── persistent/     # User preferences and system state
└── cache/          # Temporary data and performance cache
```

### Adding New Features

1. **Define API Contract** - Update `openapi.yaml` with new endpoints
2. **Implement Backend** - Add business logic in appropriate module
3. **Add Tests** - Create comprehensive test coverage
4. **Update Documentation** - Keep README and API docs current
5. **Validate Performance** - Ensure guardrails handle new features

## 📈 Performance Monitoring

The application includes built-in performance monitoring:

- **Request Metrics**: Latency, throughput, error rates
- **Resource Monitoring**: Memory usage, CPU utilization
- **Business Metrics**: KPI calculation times, cache hit rates
- **Guardrails**: Automatic feature disabling on resource constraints

Monitor these endpoints:
- `/metrics` - System performance metrics
- `/api/performance/status` - Guardrails and budget status
- `/health` - Overall system health

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Run regression suite: `python run_regression.py`
5. Update documentation as needed
6. Submit pull request

### Code Quality Standards

- All API changes must update OpenAPI specification
- New features require comprehensive test coverage
- Performance impact must be measured and documented
- Error handling must follow established patterns
- Documentation must be updated for user-facing changes

## 📄 License

MIT License - see LICENSE file for details.
