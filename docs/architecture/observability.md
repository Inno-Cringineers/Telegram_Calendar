## Risks

We identify the following technical risks for our MVP:

1. **Reminders are late or not sent**
Reminder Scheduler fails, is stopped, or sends with big delay.
2. **Daily plan job fails or sends at wrong time**
Daily plan is not generated or sent at wrong hour from Settings.
3. **Events from external calendars are not imported**
4. **Bot process crash or stop**
Docker container or process stops.

From these we choose two most critical risks:

- Reminders are late or not sent;
- Events from external calendars are not imported

---

## Objectives and SLOs

### SLO 1:

Risk: reminders are late or not sent.

Metric:

- on time reminder rate = share of reminders sent in small delay window ( ±1 minute from planned send time).

SLO:

- To monitor r**eminders late or not sent**, we will track **on time reminder rate**. It must remain **at or above 99%** over the **last 7 days**.

### SLO 2:

Risk: Events from external calendars are not imported

Metrics:

- Calendar Sync Success Rate is the percentage of successful calendar sync attempts relative to all attempts over a given period

SLO:

- To monitor **calendar sync availability**, we will track **calendar sync success rate**. It must remain **above 95%** for **99% of sync attempts over any 7 day period.**

## Plan instrumentation

### **Calculating Metrics**

On-time Reminder Rate = (Number of on-time reminders / Total scheduled reminders) × 100%

Calendar Sync Success Rate = (Number of successful syncs / Total sync attempts) × 100%

Number of on-time reminders is how many reminders sent in ±1 minute delay.

We can see this metrics in logs and database.

### **Context Required When SLO is Violated**

we can see logs and get more information.

### How will you technically collect and process all this information (metrics, traces,logs, etc.)? Explain and provide a diagram of the pipeline.

Process Details:

1. Bot generates data:
    - Logs via Python logging (processed by OpenTelemetry's LoggingHandler)
    - Metrics automatically collected via opentelemetry-instrument (asyncio, database, etc.)
2. OpenTelemetry SDK processes:
    - Logs: BatchLogRecordProcessor → OTLPLogExporter
    - Metrics: automatic collection → OTLP export
3. Transmission to Grafana Cloud:
    - Protocol: OTLP (HTTP/Protobuf)
    - Endpoint: OTEL_EXPORTER_OTLP_ENDPOINT
    - Headers: OTEL_EXPORTER_OTLP_HEADERS (authorization)
4. Grafana Cloud stores:
    - Logs in Loki (LogQL)
    - Metrics in Prometheus (PromQL)
5. Dashboard queries data:
    - Prometheus datasource (DS_PROMETHEUS)
    - Loki datasource (DS_LOKI)
    - Refresh interval: every 30 seconds


![Pipeline diagram](/images/pipeline_diagram.png)


## Plan alerts

### **Alert Thresholds**

On-time reminder rate < 98%

Calendar sync success rate < 95%

### **Alert Delivery**

In logs we can see information about that.

## Plan response

Person who host the bot get allerts.

if an alert is received, you need to open the logs, view the system logs, and check the system's actions. if the docker has crashed, restart docker and double-check everything.

## Visualize data

[Grafana](https://cringineers.grafana.net/dashboard/snapshot/xbQ6YJo9NVBmeF99jloIMMdq7waAjdCL)

![Grafana DashBoard](/images/grafana_dashboard.png)

