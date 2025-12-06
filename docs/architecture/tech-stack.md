# Tech Stack

## Backend

### Language

**Technology:** Python

**Reason:** Most popular for telegram bots and simple language syntax

### Framework

**Technology:** aioram

**Reason:** most popular framevork for tg bot API

### Database

**Technology:** SQLite

**Reason:** Lightweight and simple. Docker friendly.

## Integration

### Calendar Sync

**Technology:** icalendar / ics

**Reason:** RFC 5545 standard, widely used in calendar applications

## Deployment

### Containerization

**Technology:** Docker

**Reason:** Most popular containerization tool

## Testing

### Testing Framework

**Technology:** pytest

**Reason:** Most popular testing framework for Python

## Static Analysis

### Formatting Framework

**Technology:** ruff

**Reason:** Good for linting and formatting. Also popular in the community.

### Type Checking Framework

**Technology:** mypy

**Reason:** Best for type checking. Also popular in the community.

### Link Checker Framework

**Technology:** lychee

**Reason:** Works well with Jekyll and GitHub Pages.

## Analytics

### Instrumentation Framework

**Technology:** OpenTelemetry

**Reason:** Industry-standard observability framework that provides vendor-neutral instrumentation. Enables automatic collection of metrics, logs, and traces without vendor lock-in. Supports multiple exporters and integrates seamlessly with various observability platforms.

### Visualization Platform

**Technology:** Grafana Cloud

**Reason:** Unified platform for metrics and logs visualization. Integrates with Prometheus and Loki, providing a single dashboard for all analytics data. Offers real-time monitoring, alerting capabilities, and supports custom dashboards for business metrics.

### Metrics Storage

**Technology:** Prometheus

**Reason:** Industry-standard metrics storage and time-series database. Provides PromQL query language for flexible metric queries. Reliable, scalable, and widely adopted in the observability ecosystem. Stores metrics collected via OpenTelemetry instrumentation.

### Data Collection

**Technology:** Database queries

**Reason:** Direct access to application data for custom analytics metrics. Allows collection of business-specific metrics like user language distribution and event source tracking (external calendars vs manually created events). Provides real-time data from the application database.

## Observability

### Instrumentation Framework

**Technology:** OpenTelemetry

**Reason:** Provides unified instrumentation for logs, metrics, and traces. Automatic collection via `opentelemetry-instrument` wrapper enables zero-code instrumentation for asyncio, database operations, and system metrics. Vendor-neutral standard ensures flexibility in choosing observability backends.

### Monitoring Platform

**Technology:** Grafana Cloud

**Reason:** Centralized monitoring and diagnostics dashboard that supports multiple data sources. Enables real-time system health monitoring, SLO tracking, and alerting. Provides unified view of logs (Loki) and metrics (Prometheus) for comprehensive system observability.

### Log Storage

**Technology:** Loki

**Reason:** Efficient log aggregation and storage system designed for high-volume log ingestion. Provides LogQL query language for log analysis. Integrates seamlessly with Grafana for log visualization and correlation with metrics. Optimized for cloud-native applications.

### Metrics Storage

**Technology:** Prometheus

**Reason:** Time-series metrics database that supports alerting and flexible querying. Widely adopted standard for metrics storage. Handles high-cardinality metrics and provides reliable storage for monitoring data. Used by Grafana Cloud for metrics persistence.

### Logging Framework

**Technology:** Python logging

**Reason:** Standard library logging framework with flexible configuration. Supports multiple handlers (console, file, OpenTelemetry). Provides structured logging with different log levels. Enables application-level logging that integrates with OpenTelemetry for centralized log collection.