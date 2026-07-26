# 🎤 10-Minute Presentation Script — Order Management Microservices

A timed outline with **what to say**. Keep [TESTING-GUIDE.md](TESTING-GUIDE.md) open for the live demo.

---

## ⏱️ Timing at a glance

| Time | Section |
|---|---|
| 0:00–1:00 | Intro & the problem |
| 1:00–3:00 | Architecture walkthrough (the 5 phases) |
| 3:00–7:00 | **Live demo** (happy saga + compensation + tracing) |
| 7:00–9:00 | **Defending two decisions** (MongoDB + staying with the class stack) |
| 9:00–10:00 | Wrap-up + Q&A |

---

## 1. Intro & the problem (1 min)

> "My project is an **e-commerce Order Management system**. I started with a **monolith** — one .NET 8
> API, one SQL database — and evolved it, in five phases, into a **distributed microservices**
> platform. The goal was to experience *why* each pattern exists by hitting the problem it solves."

Name the core capabilities: **browse products, place an order, reserve inventory, notify the customer**.

---

## 2. Architecture walkthrough (2 min)

Show the diagram in the README. Walk the phases:

- **Phase 1 — Monolith:** everything in one process + one DB. Simple, but one point of failure and
  can't scale parts independently.
- **Phase 2 — Split into 4 services** with **database-per-service** and **polyglot persistence**:
  catalog on **MongoDB**, orders & inventory on **SQL Server**.
- **Phase 3 — Gateway + BFF + Load Balancer:** clients hit **one** Ocelot gateway; a **BFF**
  aggregates data; the catalog runs as **2 replicas behind nginx**.
- **Phase 4 — Async + Saga + Cache:** services talk through **RabbitMQ** events (a **choreography
  saga** with compensation), and the catalog uses a **Redis** cache.
- **Phase 5 — Observability:** **Serilog → Seq** logs, **/health** checks, and a **correlation ID**
  that traces one order across everything.

> One sentence to land: *"Each phase removed a specific weakness of the previous one."*

---

## 3. Live demo (4 min) — the heart of the grade

Follow [TESTING-GUIDE.md](TESTING-GUIDE.md). Do these four things:

1. **Health** — `docker compose ps` shows everything `healthy`.
2. **Happy-path saga** — place an order with `X-Correlation-ID: DEMO-1`; show it goes **Pending →
   Approved** on its own; then in **Seq** filter `CorrelationId = 'DEMO-1'` and show the full journey
   across all services **and through RabbitMQ**.
3. **Compensation** — order 100000 units; show it auto-**Rejected**, no stock leaked, customer notified.
4. **Load balancing / cache** — repeat a catalog read; show `X-Instance` alternating and Redis
   **HIT/MISS** in the logs.

> The Seq correlation-id trace is your strongest moment — pause on it.

---

## 4. Defending two decisions (2 min)

The rubric asks you to defend **one database choice** and **one technology decision**.

### Decision A — MongoDB for the Product Catalog (a database choice)
> "The catalog is **read-heavy** and its products have **different attributes per category** — a shirt
> has size/colour, a laptop has CPU/RAM. In a relational table that's nullable-column sprawl. A
> **document database (MongoDB)** lets each product carry its own attributes with **no schema
> migration**. Consistency-wise the catalog is fine with **BASE** — a product description being a few
> milliseconds stale is harmless — so on **CAP** it leans **Availability + Partition tolerance**."

Contrast with **Orders on SQL Server**:
> "Orders are **money**, so they need **ACID** — the order and its items must commit atomically. There
> I chose **Consistency** over availability. That's *polyglot persistence*: the right database per job."

*(This is all written up in [ADR.md](ADR.md).)*

### Decision B — Staying with the class stack (RabbitMQ, Ocelot, nginx, Redis, Seq)
> "The brief allowed substitutions like **Kafka instead of RabbitMQ**. I chose to **stay with
> RabbitMQ** deliberately: my order saga is **task/command-style messaging** with low volume and needs
> **per-message acknowledgement and easy compensation** — RabbitMQ's routing + acks fit that exactly.
> **Kafka** shines for **high-throughput event streaming and replay**, which my workload doesn't need,
> and it would add operational complexity. So the choice is *fit-for-purpose*, not just familiarity."

> "Similarly I used **Ocelot** (a .NET-native gateway) and **nginx** for load balancing — both are the
> standard, well-documented tools for these jobs in the .NET ecosystem."

---

## 5. Wrap-up + Q&A (1 min)

> "So: a monolith became a **gateway-fronted, load-balanced, event-driven, cached, fully-observable**
> microservices system — and I can trace any order end-to-end with a single id. Every decision was
> driven by a concrete trade-off: ACID vs BASE, sync vs async, consistency vs availability."

### Likely questions — quick answers
- **"What if a consumer gets the same message twice?"** → *Idempotency:* inventory tracks processed
  orders; the order service only acts on a `Pending` order. At-least-once delivery is safe.
- **"How does the saga handle failure?"** → *Compensation:* on `InventoryRejected` the order is
  cancelled and the customer notified — eventual consistency, not a distributed transaction.
- **"Why database-per-service?"** → Independent scaling + failure isolation; no service can couple to
  another's schema. Services share **data via APIs/events, never a shared database**.
- **"Is it production-ready?"** → The patterns are; I'd add auth at the gateway, retries/circuit
  breakers (Polly), and separate DB servers. *(Honest and shows awareness.)*
- **"How do the two catalog replicas stay consistent?"** → They share one MongoDB and one Redis; the
  cache is invalidated on update.

---

### 🎯 One-liners to remember
- *"Right database for the right job — money needs ACID, a catalog is fine with BASE."*
- *"Services share data through events, never a shared database."*
- *"The correlation id survives the message broker — that's real distributed tracing."*
- *"The saga self-heals with compensation instead of a distributed transaction."*
