# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** the definitions of 1NF, 2NF, 3NF, and BCNF and state the anomaly each form eliminates.
2. **Understand** why update, insertion, and deletion anomalies arise from poor schema design and how functional dependencies capture the root cause.
3. **Apply** the step-by-step decomposition algorithm to a given relation, using its functional dependencies and candidate keys, to produce schemas in 3NF or BCNF.
4. **Analyze** a real-world schema to identify which normal form it satisfies and pinpoint exactly which functional dependency violates the next higher form.
5. **Evaluate** when to stop normalizing (3NF vs. BCNF) and when deliberate denormalization is a defensible performance trade-off.

---

## 1. Why Normalize? The Problem in One Table

**Opening hook:** Imagine you're the database administrator for a company, and a VP storms into your office demanding to know why the quarterly report says the Sales department occupies *two different buildings simultaneously*. You check the data — it's not a typo. It's a design flaw. The schema you inherited allowed a single truth (Sales is in Building B) to be contradicted by a single stale row. No constraint caught it, because the constraint was never encoded — it was scattered across hundreds of rows, maintained by hope.

That's not a bug. That's an **anomaly** — and normalization exists to make it structurally impossible.

**Pause and predict:** Before reading further, take 30 seconds to sketch what you think caused this. How would *you* design a table to store employees, departments, and buildings so that a single department could accidentally end up in two buildings? What would the table look like?

Now let's see if your intuition matches reality.

Imagine you're building a company directory. You've got employees, departments, and buildings. The obvious first instinct is to put everything in one table — after all, each employee *has* a department, and each department *occupies* a building. So you write:

```
EMP_DEPT_BUILDING(EmpID, EmpName, DeptID, DeptName, Building)
```

Assume these real-world constraints:

- Each employee has a unique `EmpID`.
- Each employee belongs to exactly one department, identified by `DeptID`.
- Each department has one name (`DeptName`) and is housed in one building (`Building`).

Now try three everyday operations against this schema:

- **Update anomaly:** The Sales department moves from Building A to Building B. You must change `Building` in *every* row for every Sales employee. Miss one row, and your database now asserts that Sales occupies two buildings simultaneously — a logical contradiction that no constraint can catch because the constraint isn't expressed in the schema itself.

- **Insertion anomaly:** You want to record a brand-new department, Engineering, before any employees are hired into it. You cannot insert that row because `EmpID` is part of the primary key and cannot be null. The database forces you to invent a fake employee just to record a real department.

- **Deletion anomaly:** The last employee in Marketing resigns. Deleting her row removes *all* record that Marketing ever existed, including its name and building. A single personnel action accidentally erases organizational structure.

These three anomalies share a single root cause: one table attempts to represent multiple independent facts — facts about employees, facts about departments, facts about buildings — and the schema has no mechanism to enforce their independence. The table is a physical container that conflates three separate logical truths.

**The hidden thread connecting all three anomalies:** In each case, the database is forcing you to express one fact as a side effect of expressing another. You can't update a building without touching employee rows. You can't insert a department without an employee. You can't delete an employee without destroying a department. The schema has entangled independent truths, and normalization is the systematic method for disentangling them.

**Cross-domain insight — the compiler construction parallel:** This entanglement is structurally identical to a problem in compiler design called *phase coupling*. In a naive compiler, the parser, type checker, and code generator operate on a single shared data structure. Changing how types are represented forces you to modify the code generator — even though type checking and code generation are logically independent phases. The solution in compiler design is an intermediate representation (IR) with well-defined interfaces between phases. Normalization is the database equivalent: each normal form decomposition introduces an "interface" (a foreign key) between independent facts, so that changing one fact doesn't ripple through representations of unrelated facts. The decomposition into `Employees(EmpID, EmpName, DeptID)` and `Departments(DeptID, DeptName, Building)` is exactly analogous to separating the abstract syntax tree (AST) from the symbol table — each can evolve independently as long as the linking key (`DeptID`, or a symbol pointer) remains consistent.

**Try this yourself:** Open a spreadsheet and create this exact table with 5 employees across 2 departments. Now simulate the update anomaly: change the building for one department but deliberately leave one employee's building unchanged. Your spreadsheet now contains a logical contradiction — and no formula or validation rule will catch it unless you explicitly programmed one. This is the feeling of an anomaly: the tool lets you do something that makes no sense, because the tool doesn't understand what the data *means*.

**Industry Practice — The Cost of Anomalies at Scale:** In modern e-commerce platforms, a single denormalized `Orders` table might store `CustomerName`, `CustomerEmail`, and `ShippingAddress` alongside every order line. When a customer updates their email address, an `UPDATE` must touch every historical order row for that customer — potentially millions of rows in a high-volume retailer like Amazon or Shopify. This isn't merely slow; it creates a window where concurrent queries see inconsistent data: some orders show the new email, others the old. In payment processing systems (e.g., Stripe, Adyen), such inconsistency during a transaction can trigger compliance violations under regulations like PCI-DSS, where audit trails must reflect a single, consistent customer identity. The normalization principles you learn here are not academic exercises — they are the structural guarantees that prevent these production incidents.

**Industry Practice — Healthcare and HIPAA Compliance:** Electronic Health Record (EHR) systems like Epic or Cerner face a related but distinct pressure: auditability. Under HIPAA, every access to a patient record must be logged with the identity of the accessing clinician, the timestamp, and the specific data viewed. If a denormalized `PatientVisits` table stores `AttendingPhysician` and `PhysicianSpecialty` alongside each visit, then a physician changing specialties (e.g., from "General Surgery" to "Cardiothoracic Surgery" after a fellowship) forces an update across all historical visits. An auditor reviewing a visit from three years ago would see the physician's *current* specialty, not the specialty they held at the time of treatment — a misrepresentation that can fail a compliance audit. Normalizing into `Physician(PhysicianID, Name)` and `PhysicianSpecialty(PhysicianID, Specialty, EffectiveDate)` — a slowly changing dimension — preserves the historical truth and satisfies regulatory requirements. The anomaly here is not just a performance problem; it is a legal liability.

**Industry Practice — Logistics and Supply Chain:** Consider a global shipping company like FedEx or Maersk tracking containers. A denormalized `Shipments` table might store `ContainerID`, `CurrentLocation`, `VesselName`, `VesselFlag`, and `DestinationPort` in one row per container. The FD `VesselName → VesselFlag` holds (a vessel is registered in exactly one country). If a vessel is reflagged (e.g., from Panama to Liberia for regulatory reasons), every container currently on that vessel must be updated. In a system processing millions of container movements daily, this update can lock the `Shipments` table for minutes, delaying tracking queries for customers worldwide. Normalizing into `Vessels(VesselID, VesselName, VesselFlag)` and `Shipments(ContainerID, VesselID, ...)` isolates the reflagging update to a single row in `Vessels`, leaving the `Shipments` table untouched. The practical consequence: a schema design decision directly impacts whether a routine maritime regulatory operation causes a global tracking outage.

> **Quick Check 1:** In the table above, which of the three anomalies would occur if we changed an employee's name? (Hint: is an employee's name a fact about the employee alone or about a combination of entities?)

---

## 2. The Tool That Finds the Problem: Functional Dependencies

Normalization does not rely on intuition. It uses a precise, mechanical tool: the **functional dependency (FD)**. This is the diagnostic instrument that tells you *exactly* which facts are tangled together.

Let $R$ be a relation schema with attribute set $U$. An FD $X \rightarrow Y$ (read "$X$ determines $Y$") means: in any valid instance of $R$, whenever two tuples agree on all attributes in $X$, they *must* agree on all attributes in $Y$.

**Analogy — the GPS coordinate principle:** Think of $X \rightarrow Y$ as analogous to how GPS coordinates determine elevation. Given a specific latitude and longitude, there is exactly one elevation at that point on Earth's surface. You can't have two different elevations at the same coordinates — that would violate the fundamental mapping from location to height. An FD enforces the same kind of deterministic mapping in your database: for each value of $X$, there is exactly one allowed value of $Y$. The database is enforcing that the mapping from $X$ to $Y$ is a function, not a relation that could branch.

**Intuition rephrased:** "If I know $X$, I can look up exactly one value for $Y$." In the employee example:

- $\text{EmpID} \rightarrow \text{EmpName}$ — given an employee's ID, there is exactly one name.
- $\text{DeptID} \rightarrow \text{DeptName}, \text{Building}$ — given a department ID, there is exactly one department name and exactly one building.

**Why this matters more than you think:** FDs are not just abstract notation. They are the *enforceable contracts* your schema makes with reality. If $\text{DeptID} \rightarrow \text{Building}$ holds, then your database can physically prevent the two-buildings contradiction from the opening hook — a simple `UNIQUE` constraint on `DeptID` in a properly normalized table makes the anomaly structurally impossible. The FD tells you what constraint to write.

**Formal definition:** For any two tuples $t_1, t_2$ in $r(R)$, if $t_1[X] = t_2[X]$ then $t_1[Y] = t_2[Y]$. An FD is *nontrivial* when $Y \not\subseteq X$; otherwise it conveys no useful constraint (saying "knowing X determines X" is tautologically true but tells you nothing about structure).

**Keys via FDs — the critical bridge:** A **superkey** is any set of attributes $SK$ such that $SK \rightarrow U$ — knowing $SK$ determines the entire tuple. A **candidate key** $K$ is a *minimal* superkey: no attribute can be removed from $K$ while preserving the property $K \rightarrow U$. An attribute is **prime** if it belongs to at least one candidate key; otherwise it is **nonprime**.

These definitions form the lens through which every normal form is judged. The distinction between prime and nonprime is the fault line that separates 2NF from 3NF, and 3NF from BCNF.

**The detective work of finding FDs:** Here's a practical technique. For any pair of attributes, ask: "Can two different values of Y exist for the same value of X, in a *valid* state of the world?" If the answer is no — if the business rules forbid it — then $X \rightarrow Y$ holds. For example: "Can one department ID have two different buildings?" No — the company assigns exactly one building per department. Therefore $\text{DeptID} \rightarrow \text{Building}$. But: "Can one building house two different departments?" Yes — that's common. Therefore $\text{Building} \rightarrow \text{DeptID}$ does *not* hold. This question-based approach turns FD discovery from a mechanical exercise into a conversation with domain experts.

**Cross-domain insight — FDs as conservation laws:** Functional dependencies play the same logical role in database design that conservation laws play in physics. In physics, conservation of energy says: "given an isolated system at time $t_1$ and time $t_2$, the total energy must be identical." It's a constraint that holds across all valid states of the system, not just the ones you've observed. Similarly, an FD says: "given any two tuples with the same $X$, the $Y$ values must be identical." Both are invariants — statements about what the system *cannot* do — and both are discovered by asking "what must remain constant across all valid configurations?" Just as you can't derive conservation of energy from watching a single experiment, you can't derive an FD from a single database snapshot. You must identify the underlying rule that governs all possible states.

**Industry Practice — Discovering FDs from Legacy Systems:** In practice, you rarely inherit a clean set of FDs with a schema. At companies like Netflix or Uber, database migrations often begin with profiling scripts that scan existing tables for FD violations: a query groups by a suspected determinant $X$ and counts distinct values of $Y$. If the count is always 1, the FD holds in the current instance — but this is only a snapshot. The real FD must reflect business rules. For example, a healthcare startup building a patient-portal schema might observe that `ZipCode → City` holds in their U.S. data, but this is not a logical necessity (zip codes can span multiple cities). Embedding it as an FD would cause anomalies if they expand internationally. The discipline of distinguishing *observed* co-occurrence from *logical* determination is what separates robust schema design from brittle assumptions.

**Industry Practice — FDs in Financial Trading Systems:** In algorithmic trading platforms (e.g., those used by Goldman Sachs or Jane Street), FDs are not merely discovered — they are actively enforced as part of trade reconciliation. A `Trades` table might have the FD `TradeID → SettlementDate, Counterparty, NotionalAmount`. If a trade is amended (e.g., the settlement date changes from T+2 to T+3 due to a market holiday), the system must guarantee that all downstream tables reflecting that trade — risk calculations, P&L reports, regulatory filings — propagate the change consistently. Trading systems often implement this not through normalization alone, but through event sourcing: the `TradeID` is the key to an immutable event log, and all derived projections are rebuilt from that log. The FD is the logical invariant that the event log preserves, even as physical tables are denormalized for query speed. This illustrates a deeper point: normalization defines the *logical* truth; physical design (denormalization, caching, materialized views) is an optimization layered on top, and the FD is the contract that the optimization must not violate.

> **Quick Check 2:** In the relation `EMP(EmpID, Name, SSN)`, suppose both `EmpID` and `SSN` are unique per employee. What are the candidate keys? Which attributes are prime, which are nonprime?

---

## 3. First Normal Form (1NF): The Flat-Table Foundation

**Definition.** A relation is in 1NF if every attribute domain contains only atomic (indivisible) values. No attribute may be relation-valued, set-valued, or contain repeating groups within a single cell.

**Why it matters.** The relational algebra operates on flat tables. A cell containing a list `{101, 102, 103}` breaks operators like selection and join because they expect a single value per column per row. It's not a cosmetic preference — it's a requirement for the algebraic machinery to function.

**Analogy — the pixel principle in digital images:** Think of a digital image. A pixel holds exactly one color value at exactly one coordinate. If a single pixel could hold multiple colors simultaneously, every image processing algorithm — blur, edge detection, compression — would break, because they all assume the fundamental contract: one location, one color. 1NF is the same contract for databases: one row-column intersection, one value. Without it, every query becomes an image processing problem where you first have to "segment" the cell contents before you can operate on them.

**The hidden cost of non-atomic values:** Imagine writing `SELECT * FROM Employees WHERE Skill = 'Python'` when `Skills` is a comma-separated string `'Python,SQL,Java'`. You can't use `=` — you need `LIKE '%Python%'`, which also matches `'PythonScript'` or `'NotPython'` if you're not careful. You can't index this column effectively. You can't enforce that skills come from a controlled vocabulary. Every query becomes a parsing problem. 1NF eliminates an entire class of fragile workarounds by refusing to let you store lists where single values belong.

**Worked example.**

Start with this non-1NF table:

```
DEPARTMENT(DeptID, DeptName, Employees)
```

Here `Employees` is a set of employee IDs, e.g., `{E1, E2}`. A single cell contains multiple values.

To reach 1NF, we have two choices:

1. **Flatten:** Expand each set element into its own row:
   ```
   DEPARTMENT(DeptID, DeptName, EmployeeID)
   ```
   Now `D01, Sales, E1` and `D01, Sales, E2` are two separate tuples. The department name is repeated, but every cell holds exactly one atomic value.

2. **Decompose:** Split into two relations:
   ```
   DEPARTMENT(DeptID, DeptName)
   DEPT_EMP(DeptID, EmployeeID)
   ```
   This eliminates the repetition entirely by separating the facts.

In both results, every cell holds exactly one atomic value. The choice between flattening and decomposing is not neutral — decomposition often anticipates further normalization, while flattening can introduce the very redundancy that higher normal forms aim to eliminate.

**Misconception alert:** 1NF does *not* mean "no duplicate rows." Duplicate rows are a separate issue handled by the relational model's set semantics (a relation is a set of tuples, so duplicates are impossible by definition). 1NF only prohibits non-atomic cell contents.

**Limitation:** A schema in 1NF can still suffer from all three anomalies. 1NF is a starting point, not a destination. It clears the ground so that functional dependencies can operate on flat attributes, but it does nothing to untangle the dependencies themselves.

**Cross-domain insight — 1NF and the Unix philosophy:** The 1NF requirement echoes the Unix design principle: "do one thing and do it well." In Unix, each program operates on a simple text stream — one line, one record. You don't embed a database inside a line of text and expect `grep` to understand its structure. Similarly, 1NF says each cell should hold one value, so that relational operators — like Unix pipes — can compose cleanly. When you violate 1NF by storing JSON arrays in a column, you're essentially embedding a sub-program inside your data that every query must first interpret. The composition breaks because the interface is no longer uniform.

**Try this yourself:** Take the `EMP_DEPT_BUILDING` table from Section 1. Is it in 1NF? Check each cell — does any cell contain a list, a set, or a nested table? The answer is yes, it is in 1NF. Yet it still suffers from all three anomalies. This demonstrates that 1NF is necessary but utterly insufficient — a table can be perfectly flat and still be a disaster.

**Industry Practice — JSON Columns and the 1NF Tension:** Modern SQL databases (PostgreSQL, MySQL 8+, SQL Server) support native JSON column types. A column storing `{"skills": ["Python", "SQL", "Docker"]}` technically violates 1NF — the cell contains a set. Yet this pattern is pervasive in practice: job-board platforms like Indeed or LinkedIn store semi-structured resume data in JSON columns for flexibility. The trade-off is real: you gain schema flexibility (no need to predefine all possible skills as columns or rows) but lose relational operators — indexing a JSON array for efficient "find all candidates with Python" queries requires specialized GIN indexes and containment operators (`@>` in PostgreSQL), which are slower and more complex than a simple join on a normalized `CandidateSkills` table. The practical rule is: if an attribute will be queried independently, used in joins, or constrained by foreign keys, normalize it out of JSON. If it is opaque, rarely queried payload data (e.g., an API response