# Telemetry Data Collection

This document describes what telemetry data is collected, how to enable or disable collection, and which modules are responsible for telemetry.

## Which Data is Collected

### Custom Metrics

Custom metrics are collected by the `MetricsService` and exported via OpenTelemetry:

- **User language distribution** (`user_language_count`)
  - Metric name: `user_language_count`
  - Description: Number of users by language
  - Labels: `language` (e.g., "en", "ru")
  - Source: `Settings` table in database

- **Events with URL count** (`events_with_url_count`)
  - Metric name: `events_with_url_count`
  - Description: Total number of events from external calendars (with URL)
  - Source: Events joined with calendars that have a URL

- **Events without URL count** (`events_without_url_count`)
  - Metric name: `events_without_url_count`
  - Description: Total number of manually created events (without URL)
  - Source: Events joined with calendars that have no URL

These metrics are collected periodically based on the `metrics_interval` configuration (default: 300 seconds).

### Application Logs

Application logs are collected via logging middleware and Python logging:

- **Message events** (from `MessageLoggingMiddleware`):
  - User ID
  - User name
  - Message text or content type
  - Handler execution time

- **Callback query events** (from `CallbackQueryLoggingMiddleware`):
  - User ID
  - User name
  - Callback data
  - Handler execution time

- **General application logs** (via Python logging):
  - Timestamps
  - Log levels (DEBUG, INFO, WARNING, ERROR)
  - Log messages
  - Stack traces for errors
  - File and line numbers (in DEBUG mode)

### Automatic Metrics

Automatic metrics are collected via `opentelemetry-instrument` wrapper:

- **Asyncio metrics**: Performance metrics for async operations
- **Database operation metrics**: SQLAlchemy query performance and connection metrics
- **System metrics**: CPU, memory, and other system-level metrics

These metrics are automatically instrumented when the application runs with `opentelemetry-instrument`.

## How to Enable/Disable Telemetry Data Collection

### Enable Telemetry Collection

To enable telemetry data collection, set the following environment variables:

- **`OTEL_EXPORTER_OTLP_ENDPOINT`**: Set to your Grafana Cloud OTLP endpoint URL
  - Example: `https://otlp-gateway-prod-us-central-0.grafana.net/otlp`
- **`OTEL_EXPORTER_OTLP_HEADERS`**: Set to include authorization headers
  - Example: `Authorization=Basic <base64-encoded-credentials>`
- **`OTEL_EXPORTER_OTLP_PROTOCOL`**: Protocol to use (default: `http/protobuf`)
- **`OTEL_RESOURCE_ATTRIBUTES`**: Resource attributes to attach to telemetry data
  - Example: `service.name=telegram-calendar-bot,service.version=1.0.0`

These environment variables can be set in `docker-compose.yml` or passed directly to the container.

When `OTEL_EXPORTER_OTLP_ENDPOINT` is configured:
- OpenTelemetry logging handler is automatically set up (see `logger/logger.py`)
- Logs are exported to Grafana Cloud via OTLP
- Metrics collected by `MetricsService` are exported via OpenTelemetry
- Automatic metrics from `opentelemetry-instrument` are exported

### Disable Telemetry Collection

To disable telemetry data collection:

1. **Unset or omit** the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable
2. When this variable is not set:
   - OpenTelemetry logging handler setup is skipped (see `logger/logger.py:87-90`)
   - No logs are exported to Grafana Cloud
   - Metrics service still runs and collects data, but metrics are not exported
   - Automatic instrumentation still runs but data is not exported

Note: The application will continue to function normally with telemetry disabled. Logs will still be written to console and file (if configured), but will not be sent to Grafana Cloud.

### Configuration in docker-compose.yml

Telemetry configuration is managed via environment variables in `app/docker-compose.yml`:

```yaml
environment:
  - OTEL_RESOURCE_ATTRIBUTES=${OTEL_RESOURCE_ATTRIBUTES}
  - OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT}
  - OTEL_EXPORTER_OTLP_HEADERS=${OTEL_EXPORTER_OTLP_HEADERS}
  - OTEL_EXPORTER_OTLP_PROTOCOL=${OTEL_EXPORTER_OTLP_PROTOCOL}
```

Set these variables in your `.env` file or export them before running docker-compose.

## Main Modules Responsible for Telemetry Data Collection

### `logger/logger.py`

**Functions:**
- `setup_logger()`: Configures Python logging with console, file, and OpenTelemetry handlers
- `_setup_otel_logging()`: Sets up OpenTelemetry logging handler for Grafana Cloud

**Responsibilities:**
- Configures logging infrastructure
- Adds OpenTelemetry handler when `OTEL_EXPORTER_OTLP_ENDPOINT` is set
- Formats log messages with timestamps and metadata
- Exports logs to Grafana Cloud via OTLP protocol

### `services/metrics_service.py`

**Class:** `MetricsService`

**Responsibilities:**
- Collects custom metrics from database periodically
- Creates OpenTelemetry observable gauges for metrics
- Collects user language distribution from `Settings` table
- Collects event counts (with/without URL) from `Event` and `Calendar` tables
- Updates OpenTelemetry metrics via callback functions

**Key methods:**
- `start_metrics_service()`: Starts periodic metric collection
- `collect_metrics()`: Collects all metrics from database
- `_collect_user_languages()`: Collects user language distribution
- `_collect_events_counts()`: Collects event counts by source type

### `middlewares/logging_middleware.py`

**Classes:**
- `MessageLoggingMiddleware`: Logs message events with timing information
- `CallbackQueryLoggingMiddleware`: Logs callback query events with timing information

**Responsibilities:**
- Intercepts incoming messages and callback queries
- Logs user information, event data, and execution time
- Measures handler execution time for performance monitoring
- Logs errors with full stack traces

### `main.py`

**Function:** `main()`

**Responsibilities:**
- Initializes `MetricsService` with configured update interval
- Starts metrics collection service as background task
- Configures logger via `setup_logger()`
- Ensures metrics service runs throughout application lifecycle

### `Dockerfile`

**Responsibilities:**
- Installs OpenTelemetry instrumentation via `opentelemetry-bootstrap --action=install`
- Runs application with `opentelemetry-instrument` wrapper
- Enables automatic instrumentation for asyncio, database, and system metrics

The `opentelemetry-instrument` wrapper automatically instruments:
- Python asyncio operations
- SQLAlchemy database operations
- HTTP requests (if applicable)
- System-level metrics

