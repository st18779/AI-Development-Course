# 🧪 Testing Guide — Order Management Microservices

A step-by-step script to demonstrate that the whole distributed system works. Follow it top to
bottom during the defense. Every command is copy-paste ready.

---

## 0. Start the system

From the project root:

```bash
docker compose up --build
```

Wait until it settles (first run pulls/builds images). The databases **auto-seed** demo products +
stock, so you can start testing immediately.

**Pre-seeded product ids** (already in the catalog with stock):

| Product | Product ID | Price | Stock |
|---|---|---|---|
| Demo Mug | `6a43dd44026dfff7e9bc6382` | 15.00 | 100 |
| Wireless Mouse | `6a43dd44026dfff7e9bc6383` | 49.90 | 50 |
| Cotton T-Shirt | `6a43dd44026dfff7e9bc6384` | 29.90 | 200 |

**Key URLs**

| What | URL |
|---|---|
| API Gateway (single entry) | http://localhost:8080 |
| Order Swagger | http://localhost:8083/swagger |
| Catalog (via load balancer) | http://localhost:8081 |
| **Seq** logs dashboard | http://localhost:5341 |
| **RabbitMQ** UI (`guest`/`guest`) | http://localhost:15672 |

---

## 1. Health checks (Phase 5) — everything is up

```bash
docker compose ps
```
✅ Show that services report **`(healthy)`** (order, inventory, notification, catalog replicas, bff).

Then hit a health endpoint directly:
```bash
curl http://localhost:8083/health      # -> Healthy
```
✅ Talking point: *"Each service exposes `/health`, and docker-compose polls it — this is how an
orchestrator like Kubernetes knows a service is alive."*

---

## 2. Browse the catalog + Load Balancing (Phase 3)

Open in a browser: **http://localhost:8080/api/products** → shows the seeded products (through the
gateway).

**Prove load balancing** — the catalog runs as 2 replicas behind nginx. Each response says which
replica answered (`X-Instance` header):
```bash
curl -s -D - http://localhost:8081/api/products -o /dev/null | findstr /i x-instance
```
Run it a few times → the instance alternates (`catalog-1`, `catalog-2`).
✅ Talking point: *"Horizontal scaling — nginx spreads requests across replicas."*

---

## 3. Redis cache-aside (Phase 4)

Read one product a few times, then look at the logs:
```bash
curl -s http://localhost:8080/api/products/6a43dd44026dfff7e9bc6382 -o nul
curl -s http://localhost:8080/api/products/6a43dd44026dfff7e9bc6382 -o nul
docker compose logs productcatalog1 productcatalog2 | findstr /i "cache"
```
✅ First read = **MISS** (from MongoDB), the rest = **HIT** (from Redis) — even across replicas
(they share one Redis).

---

## 4. ⭐ The Order Saga — Happy Path (Phase 4) + Correlation ID (Phase 5)

This is the centerpiece. Place an order with a **custom correlation id** so we can trace it.

**Option A — curl:**
```bash
curl -X POST http://localhost:8080/api/orders ^
  -H "Content-Type: application/json" ^
  -H "X-Correlation-ID: DEMO-1" ^
  -d "{\"items\":[{\"productId\":\"6a43dd44026dfff7e9bc6382\",\"quantity\":2}]}"
```

**Option B — Swagger** (http://localhost:8083/swagger → `POST /api/orders`), body:
```json
{ "items": [ { "productId": "6a43dd44026dfff7e9bc6382", "quantity": 2 } ] }
```

The order returns immediately as **`"status": 0` (Pending)**. A second later it is auto-confirmed by
the saga. Read it back (use the id from the response):
```bash
curl http://localhost:8080/api/orders/<ORDER_ID>
```
✅ Now **`"status": 1` (Approved)** — nobody approved it manually; the saga did.

### 🔎 Trace the whole journey in Seq (the "wow" moment)
1. Open **http://localhost:5341**
2. In the search bar type: **`CorrelationId = 'DEMO-1'`** → Enter.
3. You'll see the full journey, in order, across **all services and through RabbitMQ**:
   - `order`: created Pending → published **OrderPlaced**
   - `inventory`: 📥 OrderPlaced → reserved stock → published **InventoryReserved**
   - `order`: 📥 InventoryReserved → **CONFIRMED** → published **OrderConfirmed**
   - `notification`: 📥 OrderConfirmed → **customer notified**

✅ Talking point: *"One correlation id follows the order across every service **and survives the
message broker** — that's distributed tracing."*

Confirm the notification was sent:
```bash
curl http://localhost:8080/api/notifications
```

---

## 5. ⭐ The Order Saga — Compensation / Failure Path (Phase 4)

Order **more than the available stock** to trigger the failure path:
```bash
curl -X POST http://localhost:8080/api/orders ^
  -H "Content-Type: application/json" ^
  -H "X-Correlation-ID: DEMO-FAIL" ^
  -d "{\"items\":[{\"productId\":\"6a43dd44026dfff7e9bc6382\",\"quantity\":100000}]}"
```
Read it back → **`"status": 2` (Rejected)**, with the reason in `notes`.

In Seq, filter **`CorrelationId = 'DEMO-FAIL'`**:
- `inventory`: ❌ reservation rejected → published **InventoryRejected**
- `order`: 🚫 order **CANCELLED** (compensation) → published **OrderCancelled**
- `notification`: customer notified of the rejection

✅ Talking point: *"The saga self-heals — no stock is leaked, and the customer is informed. This is
eventual consistency with compensation, not a distributed ACID transaction."*

---

## 6. BFF aggregation (Phase 3)

One clean call that merges data from two services (order + catalog):
```bash
curl http://localhost:8080/api/order-details/<ORDER_ID>
```
✅ Response has the order **plus product names** and a readable status — the frontend makes **one**
call instead of several.

---

## 7. RabbitMQ dashboard (Phase 4)

Open **http://localhost:15672** (`guest` / `guest`):
- **Exchanges** → `order_events` (the topic exchange).
- **Queues** → `inventory.order-placed`, `order.inventory-reserved`, `notification.order-confirmed`, …
- Place another order and watch the message-rate graphs spike.

---

## ✅ Demo checklist (what each step proves)

| Step | Proves | Phase |
|---|---|---|
| 1 | Health checks / readiness | 5 |
| 2 | Gateway + load balancing | 3 |
| 3 | Redis cache-aside | 4 |
| 4 | Async saga (happy path) + correlation tracing | 4 + 5 |
| 5 | Saga compensation (failure path) | 4 |
| 6 | BFF aggregation | 3 |
| 7 | Message broker internals | 4 |

> Tip: keep **Seq (5341)** open in one tab and **RabbitMQ (15672)** in another during the demo — the
> visuals make the async architecture obvious.
