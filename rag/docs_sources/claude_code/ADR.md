# 📑 Architecture Decision Records (ADRs) — Phase 2 Storage Choices

These ADRs justify the database chosen for each microservice, using the vocabulary from the
Databases lesson (**ACID, BASE, CAP, consistency models**). This is the "polyglot persistence"
required by Phase 2.

> **CAP refresher:** under a network partition a distributed datastore can guarantee at most two of
> Consistency, Availability, Partition-tolerance. Partition-tolerance (P) is non-negotiable in a
> distributed system, so the real choice is **C vs. A**.
> **ACID** (Atomicity, Consistency, Isolation, Durability) = strong, immediate consistency.
> **BASE** (Basically Available, Soft state, Eventually consistent) = relaxed consistency for
> availability and scale.

---

## ADR-001 — ProductCatalogService uses MongoDB (document database)

**Status:** Accepted (implemented in Task 2.2)

**Context.** The catalog must store products whose attributes vary by category (a shirt has
Size/Color; a laptop has CPU/RAM/SSD). It is a read-heavy, browse-oriented workload. Product data
rarely participates in multi-record transactions.

**Decision.** Store products as **documents in MongoDB**, each carrying a flexible `Attributes`
bag, instead of a fixed relational schema.

**Why (ACID/BASE/CAP).**
- **Schema flexibility:** a document holds whatever fields a product needs — no nullable-column
  sprawl, no migration when a new category appears.
- **BASE over ACID:** a product description being a few milliseconds stale is harmless, so we trade
  strict ACID for availability and horizontal read scale.
- **CAP positioning:** the catalog favours **Availability + Partition-tolerance (A + P)** so reads
  stay fast and scalable; strong consistency is not required here.

**Consequences.** Great fit for catalog reads and evolving attributes. Trade-off: no cross-document
ACID transactions and no foreign keys — acceptable, because the catalog owns only product data.

---

## ADR-002 — OrderService stays on SQL Server (relational, ACID)

**Status:** Accepted (implemented in Task 2.3)

**Context.** Orders represent money: totals, line items, prices paid, and a status lifecycle
(Pending → Approved/Rejected). Creating an order must reserve stock and record the order as one
all-or-nothing unit; a half-saved order is unacceptable.

**Decision.** Keep orders in a **relational SQL Server database** (`OrdersDb`) owned solely by
OrderService.

**Why (ACID/BASE/CAP).**
- **Money demands ACID:** Atomicity (the order and its items commit together or not at all),
  Consistency (constraints like unique order numbers), Isolation, and Durability are exactly what a
  financial record needs.
- **CAP positioning:** for orders we favour **Consistency (C + P)** over raw availability — we would
  rather reject an order than record an incorrect one.

**Consequences.** Strong guarantees for the money path. Note: consistency that spans services (e.g.
"order saved" + "stock reserved" in InventoryService) cannot be a single ACID transaction, because
the data lives in different databases. We bridge that gap with a **compensating saga** (reserve over
HTTP; release everything if any step fails) — synchronous now (Phase 2), event-driven in Phase 4.

---

## ADR-003 — InventoryService uses its own relational SQL Server database

**Status:** Accepted (implemented in Task 2.3)

**Context.** Inventory tracks `QuantityAvailable` / `QuantityReserved` per product. Correctness
matters: we must never oversell. Reserve/release are frequent small updates that must not race into
a negative or double-counted state.

**Decision.** Keep inventory **relational on SQL Server**, in a **separate database** (`InventoryDb`)
owned solely by InventoryService — no foreign key to the catalog's products (cross-service FKs are
forbidden); `ProductId` is stored as a loose string reference to the catalog's Mongo id.

**Why (ACID/BASE/CAP).**
- **Consistency over availability** for stock counts — the same C + P lean as orders. Selling
  inventory you don't have is worse than briefly refusing a reservation.
- A relational store gives us straightforward atomic read-modify-write on the stock row.
- The "third NoSQL family" the brief asks for is satisfied later by **Redis** (key-value) used for
  cache-aside in Phase 4 — so inventory does not need to be NoSQL.

**Consequences.** Clean, consistent stock management with database-per-service isolation.

> **Deployment note (honest trade-off):** `OrdersDb` and `InventoryDb` are *separate databases* but
> currently run on the **same SQL Server container** to save memory on a development laptop. The
> service boundary still holds — each service has credentials for only its own database and cannot
> query the other. In production these would be separate database servers; co-locating the engine is
> a local-dev optimization, not a design coupling.

---

## Summary

| Service | Store | Model | Consistency | CAP lean | Why |
|---|---|---|---|---|---|
| ProductCatalog | MongoDB | Document | BASE | A + P | Flexible attributes, read-heavy, staleness OK |
| Order | SQL Server (`OrdersDb`) | Relational | ACID | C + P | Money needs atomic, durable, consistent writes |
| Inventory | SQL Server (`InventoryDb`) | Relational | ACID | C + P | Never oversell; atomic stock updates |
| (Phase 4) Cache | Redis | Key-value | BASE | A + P | Cache-aside for catalog reads — third NoSQL family |
