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

**Opening hook:** Imagine you’re building a company directory. You’ve got employees, departments, and buildings. The obvious first instinct is to put everything in one table — after all, each employee *has* a department, and each department *occupies* a building. So you write:

```
EMP_DEPT_BUILDING(EmpID, EmpName, DeptID, DeptName, Building)
```

Assume these real-world constraints:

- Each employee has a unique `EmpID`.
- Each employee belongs to exactly one department, identified by `DeptID`.
- Each department has one name (`DeptName`) and is housed in one building (`Building`).

**The moment of tension:** This single table seems perfectly reasonable. Every row answers the question: "Which employee, in which department, in which building?" But what happens when reality shifts — when a department moves, when a new department forms with zero employees, when the last person in Marketing resigns? The table doesn't just store data; it *entangles* facts about employees, departments, and buildings into one physical structure. When those facts change independently, the entanglement punishes you.

**Cross-domain insight — the entanglement pattern beyond databases:** This same structural entanglement appears in software configuration management. Consider a monolithic YAML configuration file where each microservice's deployment settings repeat the entire cluster topology, network policies, and monitoring endpoints. When the monitoring endpoint changes, every service block must be updated. This is identical to the update anomaly: one real-world fact (the monitoring URL) is stored in *n* places, and consistency depends on perfect discipline in a manual update process. The solution in configuration management — parameterized templates with variable substitution — is structurally identical to normalization: extract the repeated fact into one canonical location and reference it by key. The intellectual pattern of "one fact, one place" transcends databases.

Now try three everyday operations against this schema:

- **Update anomaly:** The Sales department moves from Building A to Building B. You must change `Building` in *every* row for every Sales employee. Miss one row, and your database now asserts that Sales occupies two buildings simultaneously — a logical contradiction that no constraint can catch because the constraint isn’t expressed in the schema itself. In an organization with 500 Sales employees, this is 500 individual updates for one real-world event. On a production PostgreSQL instance at a mid-size enterprise, a developer who writes `UPDATE emp_dept_building SET building = 'B' WHERE dept_id = 3` will execute this correctly in a single transaction, but the schema still stores the same fact 500 times — every one of those copies is an opportunity for inconsistency if application code bypasses the WHERE clause or if an ETL job performs partial updates.

- **Insertion anomaly:** You want to record a brand-new department, Engineering, before any employees are hired into it. You cannot insert that row because `EmpID` is part of the primary key and cannot be null. The database forces you to invent a fake employee just to record a real department. This scenario plays out routinely in SaaS multi-tenant architectures: a new customer organization is created during a trial signup flow, but no users have been provisioned yet. If the schema conflates organization metadata with user records, the signup transaction must insert a placeholder user row — a hack that later requires cleanup logic, distorts user-count metrics, and complicates downstream analytics queries that must filter out "sentinel" rows.

- **Deletion anomaly:** The last employee in Marketing resigns. Deleting her row removes *all* record that Marketing ever existed, including its name and building. A single personnel action accidentally erases organizational structure. In financial systems, this pattern is particularly dangerous: if invoice line items and invoice headers share a single table, deleting the last line item of a paid invoice can destroy the invoice header — including payment status, tax totals, and audit trail information that must be retained for regulatory compliance (e.g., Sarbanes-Oxley or GDPR record-keeping requirements).

**The root cause, stated sharply:** These three anomalies share a single root cause: one table attempts to represent multiple independent facts — facts about employees, facts about departments, facts about buildings — and the schema has no mechanism to enforce their independence. The table is a physical container that conflates three separate logical truths.

**Industry practice — normalization in modern ORM-based development.** The anomalies above are not relics of 1970s database theory; they manifest daily in production systems built with object-relational mappers (ORMs) like Django's ORM, Rails' ActiveRecord, or Hibernate. A common anti-pattern in Django applications is defining a single model that mixes user profile fields with subscription plan fields and billing address fields, then using `select_related` to eagerly load everything. When the billing address changes, the ORM's `save()` method updates only the single user row — but if a reporting ETL pipeline has denormalized billing addresses into a separate analytics table via a materialized view or a batch `INSERT ... ON CONFLICT` pattern, the update anomaly resurfaces across the boundary between the operational database and the analytics store. The normalization discipline in the OLTP schema prevents the anomaly at its source; downstream denormalization for analytics is then a conscious, documented trade-off rather than an accidental inconsistency generator.

> **Quick Check 1:** In the table above, which of the three anomalies would occur if we changed an employee’s name? (Hint: is an employee’s name a fact about the employee alone or about a combination of entities?)

---

## 2. The Tool That Finds the Problem: Functional Dependencies

Normalization does not rely on intuition. It uses a precise, mechanical tool: the **functional dependency (FD)**. This is the diagnostic instrument that tells you *exactly* which facts are tangled together.

Let $R$ be a relation schema with attribute set $U$. An FD $X \rightarrow Y$ (read “$X$ determines $Y$”) means: in any valid instance of $R$, whenever two tuples agree on all attributes in $X$, they *must* agree on all attributes in $Y$.

**Analogy:** Think of $X \rightarrow Y$ as a mathematical function from $X$ to $Y$. Just as $f(x) = \sin(x)$ gives you exactly one output for each input, an FD says that for each value of $X$, there is exactly one corresponding value of $Y$ in the database. The database is enforcing that the mapping from $X$ to $Y$ is a function, not a relation that could branch.

**Intuition rephrased:** “If I know $X$, I can look up exactly one value for $Y$.” In the employee example:

- $\text{EmpID} \rightarrow \text{EmpName}$ — given an employee’s ID, there is exactly one name.
- $\text{DeptID} \rightarrow \text{DeptName}, \text{Building}$ — given a department ID, there is exactly one department name and exactly one building.

**Formal definition:** For any two tuples $t_1, t_2$ in $r(R)$, if $t_1[X] = t_2[X]$ then $t_1[Y] = t_2[Y]$. An FD is *nontrivial* when $Y \not\subseteq X$; otherwise it conveys no useful constraint (saying “knowing X determines X” is tautologically true but tells you nothing about structure).

**Keys via FDs — the critical bridge:** A **superkey** is any set of attributes $SK$ such that $SK \rightarrow U$ — knowing $SK$ determines the entire tuple. A **candidate key** $K$ is a *minimal* superkey: no attribute can be removed from $K$ while preserving the property $K \rightarrow U$. An attribute is **prime** if it belongs to at least one candidate key; otherwise it is **nonprime**.

These definitions form the lens through which every normal form is judged. The distinction between prime and nonprime is the fault line that separates 2NF from 3NF, and 3NF from BCNF.

**Cross-domain connection — functional dependencies as information theory:** The concept of a functional dependency mirrors the information-theoretic notion of *mutual information* and *conditional entropy*. If $X \rightarrow Y$ holds, then the conditional entropy $H(Y \mid X) = 0$ — knowing $X$ eliminates all uncertainty about $Y$. Normalization can be reframed as minimizing redundant mutual information in a schema: when a non-key attribute depends on part of a key, the schema encodes the same mutual information between that key-part and the attribute in every row. Decomposition removes this redundancy by storing each deterministic relationship exactly once. This lens connects database design to broader principles of data compression and signal processing — normalization is, in essence, lossless compression of the schema's logical structure.

**Industry practice — discovering FDs from production data.** In legacy system migrations, the target schema's FDs are often not documented. A common practice at companies like Stripe and Shopify during database modernization projects is to run FD discovery algorithms (such as TANE, FUN, or HyFD) against production data snapshots to infer candidate FDs. These algorithms scan the data and test for violations of $X \rightarrow Y$ by checking whether any two rows with the same $X$ values have different $Y$ values. The output is a set of FDs that *hold on the current data*, which a data architect then validates against business rules to distinguish accidental holds (e.g., "every employee currently happens to have a unique last name") from genuine constraints (e.g., "EmployeeID determines last name by business policy"). Tools like Metanome and the FD discovery module in Apache Griffin operationalize this workflow. This practice connects the theoretical FD formalism directly to the messy reality of reverse-engineering schemas from live databases.

> **Quick Check 2:** In the relation `EMP(EmpID, Name, SSN)`, suppose both `EmpID` and `SSN` are unique per employee. What are the candidate keys? Which attributes are prime, which are nonprime?

---

## 3. First Normal Form (1NF): The Flat-Table Foundation

**Definition.** A relation is in 1NF if every attribute domain contains only atomic (indivisible) values. No attribute may be relation-valued, set-valued, or contain repeating groups within a single cell.

**Why it matters — a concrete analogy:** Imagine trying to alphabetize a library where some books are shelved singly and others are stacked in boxes labeled "Miscellaneous: 12 books." The sorting algorithm that works on individual books breaks on the boxes. 1NF is the rule that says: "Every shelf slot holds exactly one book." The relational algebra operates on flat tables. A cell containing a list `{101, 102, 103}` breaks operators like selection and join because they expect a single value per column per row. It’s not a cosmetic preference — it’s a requirement for the algebraic machinery to function.

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

**Misconception alert:** 1NF does *not* mean “no duplicate rows.” Duplicate rows are a separate issue handled by the relational model’s set semantics (a relation is a set of tuples, so duplicates are impossible by definition). 1NF only prohibits non-atomic cell contents.

**Limitation:** A schema in 1NF can still suffer from all three anomalies. 1NF is a starting point, not a destination. It clears the ground so that functional dependencies can operate on flat attributes, but it does nothing to untangle the dependencies themselves.

**Industry practice — 1NF violations in modern systems.** While classical SQL databases enforce 1NF at the schema level (a column is typed as `INTEGER` or `VARCHAR`, not as an array), two contemporary patterns routinely challenge 1NF in production:

- **JSON/JSONB columns in PostgreSQL and MySQL.** A column of type `JSONB` can store `{"emails": ["a@x.com", "b@x.com"]}` — a set-valued attribute inside a single cell. This is deliberately non-1NF. Development teams choose this design for schema flexibility (avoiding migrations when the set of email addresses is a new requirement) or for read-performance (fetching the entire user profile including all emails in one row access rather than a join). The trade-off is real: indexing individual array elements requires GIN indexes and containment operators (`@>`), which are more complex and slower than standard B-tree indexes on a normalized `user_emails` table. The query `SELECT * FROM users WHERE 'b@x.com' = ANY(emails)` is valid but cannot use a simple equality index. Teams accept this complexity when the access pattern is "always fetch the whole user object" and the nested data is never queried independently.

- **Nested repeated records in Google BigQuery and Apache Parquet.** BigQuery's native schema model permits `RECORD` (struct) types and `REPEATED` modes, allowing a single row to contain an array of sub-objects. For example, an `orders` row might contain a repeated field `line_items` where each element is a struct `{sku, quantity, price}`. This violates 1NF by design, and it is the *recommended* schema pattern for OLAP (online analytical processing) workloads because it eliminates the need for a shuffle-join between `orders` and `line_items` when running aggregation queries over terabytes of data. The normalization trade-off is inverted: in OLTP, normalization reduces write anomalies; in OLAP, denormalization (including 1NF violation) reduces query latency and data shuffling. The practitioner must recognize that 1NF is a design choice, not an absolute law — its utility depends on the workload's read/write ratio and query patterns.

**Industry practice — 1NF compliance in event sourcing and CQRS.** In systems built on the Command Query Responsibility Segregation (CQRS) pattern with event sourcing (e.g., using Axon Framework, EventStoreDB, or Kafka with KSQLDB), the *write-side* event store deliberately violates 1NF: an event record often stores a JSON or Protobuf payload containing the entire state delta as a nested structure. This is because the event store's contract is "store the event exactly as it occurred," and decomposing the event into 1NF tables would break the immutability and ordering guarantees. The *read-side* projections, however, are typically fully normalized (often to 3NF or BCNF) to support efficient querying. This split demonstrates that 1NF is not a universal requirement — it is a property of a specific data model within a specific bounded context. A team designing a CQRS system must consciously decide which side of the architecture respects 1NF and which side optimizes for append-only immutability.

**Innovative framing — 1NF as a data structure invariant:** First normal form can be understood as enforcing an invariant analogous to the *array-of-structs vs. struct-of-arrays* layout decision in high-performance computing. In a columnar database, storing `{E1, E2}` as an array in a single cell is a struct-of-arrays pattern: the department struct contains an array of employee IDs. Flattening to 1NF is converting to array-of-structs: each (department, employee) pair is a separate struct. The choice between these layouts in HPC is governed by memory access patterns — struct-of-arrays enables vectorized operations on a single attribute across many entities. The same principle governs the 1NF decision in databases: if queries predominantly filter and aggregate on employee attributes independently of departments, the 1NF (array-of-structs) layout enables efficient indexing and joins. If queries always fetch all employees of a department together, the non-1NF (struct-of-arrays) layout reduces I/O. The normal form is not merely a rule — it is an optimization choice with predictable performance consequences.

> **Quick Check 3:** Why would a column storing comma-separated values like `'Math,Physics'` violate 1NF? (Consider: what would a query asking “find all employees enrolled in Physics” have to do to that column?)

---

## 4. Second Normal Form (2NF): Eliminating Partial Dependencies

### 4.1 Motivation

2NF targets a specific situation that 1NF leaves untouched: the primary key is composite (made of multiple attributes), yet some non-key attribute depends on only *part* of that key. When that happens, the attribute is really describing one of the key parts, not the whole combination. The attribute is, in a sense, in the wrong table — it belongs with its determining subset, not with the full composite.

### 4.2 Definition

A relation $R$ is in 2NF if:

1. $R$ is in 1NF, and
2. Every nonprime attribute is *fully* functionally dependent on every candidate key. That means no nonprime attribute $A$ satisfies $K' \rightarrow A$ where $K'$ is a proper subset of a candidate key $K$.

**Tension:** Notice what this definition *doesn’t* say. It doesn’t say “no nonprime attribute depends on part of the primary key.” It says “every candidate key.” If a relation has multiple candidate keys, 2NF checks all of them. A schema can satisfy 2NF with respect to one key and still fail with respect to another — but the definition requires satisfaction for every candidate key.

### 4.3 Worked Example: The Classic EMP_PROJ

Consider a schema that tracks which employees work on which projects and for how many hours:

```
EMP_PROJ(EmpID, ProjID, EmpName, ProjLocation, Hours)
```

We identify the FDs from the real-world rules:

- $\text{EmpID} \rightarrow \text{EmpName}$ (an employee’s ID determines their name)
- $\text{ProjID} \rightarrow \text{ProjLocation}$ (a project’s ID determines its location)
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$ (the combination determines hours worked)

Candidate key: $\{\text{EmpID}, \text{ProjID}\}$. Prime attributes: `EmpID`, `ProjID`. Nonprime: `EmpName`, `ProjLocation`, `Hours`.

Now inspect the nonprime attributes against the key. This is where the tension resolves — we’ve identified the FDs, now we check each one:

- `EmpName` depends on `EmpID` alone — a proper subset of the key. This is a partial dependency. **Violation.**
- `ProjLocation` depends on `ProjID` alone — another partial dependency. **Violation.**
- `Hours` depends on the full key $\{\text{EmpID}, \text{ProjID}\}$ — no violation. `Hours` is the only attribute that genuinely describes the *intersection* of an employee and a project.

**Anomalies caused:**

- Update: Changing an employee’s name requires updating every row for that employee across all projects. If they’re on 20 projects, that