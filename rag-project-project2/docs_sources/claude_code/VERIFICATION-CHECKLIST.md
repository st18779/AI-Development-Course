# ✅ Requirements Verification Checklist

Every mandatory task mapped to **(1) status**, **(2) where it lives in the repo**, and **(3) a one-line
defense explanation**. Paths are clickable/relative from the repo root.

**Legend:** ✅ = fully implemented · ⚠️ = implemented with a noted nuance

---

## 🧩 Core capabilities (the "must support" list)

| Capability | Status | Where | How (defense line) |
|---|---|---|---|
| Browse products | ✅ | `ProductCatalogService/Controllers/ProductsController.cs` | `GET /api/products` reads the Mongo catalog (through the cache). |
| Place an order | ✅ | `OrderService/Services/OrderService.cs` | `POST /api/orders` creates a Pending order and starts the saga. |
| Reserve inventory | ✅ | `InventoryService/Messaging/OrderEventsConsumer.cs` | The saga reserves stock atomically when it consumes `OrderPlaced`. |
| Notify on confirm/reject | ✅ | `NotificationService/Messaging/NotificationEventsConsumer.cs` | It consumes `OrderConfirmed`/`OrderCancelled` and notifies the customer. |

---

## 📌 Phase 1 — Monolith Baseline (10%)

**Task 1.1 — Single .NET 8 Web API (Orders + Products + Inventory) on one relational DB** — ✅
- **Where:** `OrderManagementAPI/` (Controllers, Services, Models, `Data/OrderManagementDbContext.cs`)
- **Defense:** One ASP.NET Core 8 API with all three domains backed by a single SQL Server database via EF Core.

**Task 1.2 — docker-compose runs API + DB in one command** — ✅
- **Where:** `OrderManagementAPI/Dockerfile` + the root `docker-compose.yml`
- **Defense:** The monolith and its SQL Server started together with `docker compose up`. *(Note: the monolith was later retired via the Strangler-Fig migration, but the project + Dockerfile are preserved as the baseline.)*

**Task 1.3 — Document the monolith (diagram + endpoints + 3 scale problems)** — ✅
- **Where:** `OrderManagementAPI/PHASE1-ARCHITECTURE.md`
- **Defense:** A Mermaid diagram, all 13 endpoints, and 3 bottlenecks (shared DB, synchronous coupling, no caching).

**✔ Checkpoint** (create product, place order, inventory changes) — ✅ demonstrated live (inventory *reserves* stock rather than decrementing available — a deliberate reserve/release model).

---

## 📌 Phase 2 — Microservices + Polyglot Persistence (25%)

**Task 2.1 — Split into ≥4 services** — ✅
- **Where:** `OrderService/`, `ProductCatalogService/`, `InventoryService/`, `NotificationService/`
- **Defense:** Four independently-deployable services, each its own .NET 8 project and container.

**Task 2.2 — Database-per-service (no shared DB)** — ✅
- **Where:** connection strings in `docker-compose.yml` → `OrdersDb`, `InventoryDb`, `ProductCatalogDb`
- **Defense:** Each service owns its own database and only ever reaches another service's data through its API/events, never its database.

**Task 2.3 — Polyglot persistence (document + relational + one more NoSQL)** — ✅
- **Where:** `ProductCatalogService/Data/` (MongoDB), `OrderService/Data/OrderDbContext.cs` & `InventoryService/Data/InventoryDbContext.cs` (SQL Server), `ProductCatalogService/Data/ProductCache.cs` (Redis key-value)
- **Defense:** Catalog = MongoDB (document, flexible attributes), Orders/Inventory = SQL Server (ACID for money/stock), and Redis is the third NoSQL family (key-value cache).

**Task 2.4 — ADR per database choice (ACID/BASE/CAP)** — ✅
- **Where:** `ADR.md`
- **Defense:** Three ADRs justify each store using ACID, BASE, CAP and consistency-model vocabulary.

**✔ Checkpoint** (all services in compose, own data store, order end-to-end) — ✅

---

## 📌 Phase 3 — Gateway, BFF & Load Balancing (15%)

**Task 3.1 — API Gateway; services not exposed directly** — ✅
- **Where:** `ApiGateway/` (`Program.cs`, `ocelot.json`)
- **Defense:** An **Ocelot** gateway on port 8080 is the single public entry point that routes to each service by path.

**Task 3.2 — BFF aggregating ≥2 services** — ✅
- **Where:** `BffService/Controllers/OrderDetailsController.cs` + `BffService/Services/OrderDetailsService.cs`
- **Defense:** `GET /api/order-details/{id}` merges order data (OrderService) with product names (Catalog) into one response.

**Task 3.3 — 2+ replicas behind a load balancer, proven** — ✅
- **Where:** `docker-compose.yml` (`productcatalog1`, `productcatalog2`, `productcatalog` = nginx) + `nginx/catalog-lb.conf` + `X-Instance` header in `ProductCatalogService/Program.cs`
- **Defense:** Two catalog replicas sit behind nginx; each response's `X-Instance` header shows the rotation between them.

**✔ Checkpoint** (client talks only to gateway; killing a replica survives) — ✅ (stop one replica → nginx serves from the other).

---

## 📌 Phase 4 — Async Messaging, Saga & Caching (25%)

**Task 4.1 — Replace sync flow with async messaging (RabbitMQ)** — ✅
- **Where:** `*/Messaging/EventBus.cs` (a lightweight RabbitMQ.Client wrapper) + `rabbitmq` service in `docker-compose.yml`
- **Defense:** Services no longer call each other over HTTP for the order flow — they publish/consume events on a RabbitMQ topic exchange.

**Task 4.2 — Choreography Order Saga (happy path) + idempotency** — ✅
- **Where:** `OrderService/Messaging/OrderSagaConsumer.cs`, `InventoryService/Messaging/OrderEventsConsumer.cs`, `NotificationService/Messaging/NotificationEventsConsumer.cs`
- **Defense:** OrderPlaced → InventoryReserved → OrderConfirmed → notify, with idempotent consumers (inventory tracks processed orders; the order service only acts on a `Pending` order).

**Task 4.3 — Compensation (failure path)** — ✅
- **Where:** `OrderSagaConsumer.HandleInventoryRejectedAsync` (+ the reject branch in `InventoryService/Messaging/OrderEventsConsumer.cs`)
- **Defense:** On `InventoryRejected` the order is cancelled and the customer notified; because reservation is all-or-nothing, no stock is leaked.

**Task 4.4 — Redis cache-aside on catalog reads + invalidation** — ✅
- **Where:** `ProductCatalogService/Data/ProductCache.cs` + `ProductCatalogService/Services/ProductService.cs` + `redis` service in `docker-compose.yml`
- **Defense:** Reads check Redis first (HIT/MISS logged); a miss loads Mongo and caches it; updates/deletes invalidate the entry.

**✔ Checkpoint** (happy + compensation through broker; cache hits) — ✅

---

## 📌 Phase 5 — Monitoring & Observability (10%)

**Task 5.1 — Structured logging in every service, aggregated** — ✅
- **Where:** `builder.Host.UseSerilog(...)` in each service `Program.cs` + `seq` service in `docker-compose.yml`
- **Defense:** Every service logs with **Serilog** and ships to a central **Seq** dashboard (http://localhost:5341), tagged by `Service`.

**Task 5.2 — /health endpoint per service, wired into compose healthchecks** — ✅
- **Where:** `app.MapHealthChecks("/health")` in each service `Program.cs` + `healthcheck:` blocks in `docker-compose.yml`
- **Defense:** Each service exposes `/health`; docker-compose polls it and `docker compose ps` shows services as `healthy`.

**Task 5.3 — Correlation ID across all services AND the broker** — ✅
- **Where:** `*/Messaging/Correlation.cs` (context + Serilog enricher), correlation middleware in `Program.cs`, `EventBus.cs` (stamps `props.CorrelationId` on publish, restores it on consume)
- **Defense:** One `X-Correlation-ID` is created per order and rides through HTTP **and RabbitMQ messages**, so one Seq filter shows the whole saga.

**✔ Checkpoint** (trace one order's full story in the aggregator) — ✅ (`CorrelationId = '...'` in Seq).

---

## 📦 Deliverables

| Deliverable | Status | Where |
|---|---|---|
| Git repo + root README with one-command startup | ✅ | `README.md` (`docker compose up --build`) |
| Architecture document (diagram + ADRs + tech comparison) | ✅ | `ADR.md`, `PHASE1-ARCHITECTURE.md`, `PHASE2-MICROSERVICES-PLAN.md`, `PRESENTATION.md` |
| Demo evidence (saga happy/compensation, cache hit/miss, traced correlation id) | ⚠️ scripted | `TESTING-GUIDE.md` — **capture screenshots while running it** |
| 10-minute presentation defending 2 decisions | ✅ | `PRESENTATION.md` (MongoDB choice + staying with RabbitMQ/the class stack) |

---

## 🌟 Bonus (optional extra credit) — honest status

| Bonus | Status |
|---|---|
| CI/CD pipeline (GitHub Actions) | ❌ not implemented |
| Unit tests (xUnit) | ❌ not implemented |
| Push images to a registry (part of the CI/CD B.4 stretch) | ⚠️ tooling ready — `push-images.sh` + `docker-compose.registry.yml` (manual, not in a pipeline) |
| Kafka / Orchestration saga / Elasticsearch / Neo4j / Polly / Grafana | ❌ not implemented |

> **Biggest easy win if you want bonus marks:** a **GitHub Actions** workflow that builds the services (and runs a couple of xUnit tests) — up to +5%.

---

## ⚠️ Small honesty notes (good to mention proactively)

1. **Gateway** is not health-checked or correlation-enriched (the 4 business services are) — it's a thin Ocelot router; easy to add if asked.
2. **Inventory "decrease"** is modeled as **reserve/release** (`QuantityReserved`), not a raw decrement of `QuantityAvailable` — a deliberate, more realistic design.
3. The **"third NoSQL family"** is **Redis (key-value)**, exactly as the brief's hint suggested — not a separate database for Inventory.

---

### Rubric coverage summary
| Component | Weight | Status |
|---|---|---|
| Phase 1 | 10% | ✅ |
| Phase 2 | 25% | ✅ |
| Phase 3 | 15% | ✅ |
| Phase 4 | 25% | ✅ |
| Phase 5 | 10% | ✅ |
| Architecture doc & presentation | 15% | ✅ (capture demo screenshots) |
| Bonus | +10% | ❌ (optional) |
| CI/CD bonus | +5% | ⚠️ registry tooling only |

**All 5 mandatory phases (85%) + the docs/presentation (15%) are covered.**
