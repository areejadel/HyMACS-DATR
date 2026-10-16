# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** the definitions of 1NF, 2NF, 3NF, and BCNF, and state what each form prohibits.
2. **Understand** why partial and transitive dependencies cause update anomalies, and explain the difference between a candidate key and a superkey.
3. **Apply** the step-by-step normalization process to decompose a given unnormalized relation into 1NF, 2NF, 3NF, and BCNF, identifying all functional dependencies and candidate keys along the way.
4. **Analyze** a given relational schema to determine its current normal form and diagnose which specific functional dependency causes the violation.
5. **Evaluate** trade-offs between full normalization and denormalization, and explain the role of lossless-join and dependency-preservation properties in schema decomposition.

---

## Prerequisites — What We Assume You Already Know

We assume you are comfortable with:

- The basic structure of a relational table: attributes (columns), tuples (rows), and domains (data types).
- The concept of a **primary key** and the uniqueness constraint it enforces.
- The idea of a **functional dependency** (FD), written as \(X \rightarrow Y\), meaning: if two tuples agree on the attributes in \(X\), they must also agree on the attributes in \(Y\).
- The terms **superkey** (any set of attributes that uniquely identifies a tuple) and **candidate key** (a minimal superkey — no attribute can be removed without losing the uniqueness property).

If any of these feel rusty, take a moment to review them. We will build directly on these ideas.

---

## 1. Why Normalize? The Problem We Are Solving

### 1.0 Opening Hook: The Database That Forgets

Imagine you are building a database for a small company that tracks employees, the projects they work on, and the locations of those projects. A naive first attempt might put everything into one big table. It works — until it doesn’t.

Here is the unsettling reality: your single-table design will silently corrupt data through ordinary operations — renaming a project, hiring an employee before assigning them, or deleting a departing employee. Each is a routine business event, yet each will leave your database in an inconsistent state that no error message will catch. The table *looks* correct, but it now contains lies: duplicate names, missing projects, or phantom relationships.

This is not a bug in your application code. It is a structural defect in your schema. The only way to fix it permanently is to understand exactly *why* the structure permits these anomalies — which is what normalization reveals.

**Pause and predict:** Before we analyze the table below, try to spot the problem yourself. If you had to update the name of project "Alpha" across this table, what could go wrong? Write down your answer — we'll verify it against the formal anomalies in a moment.

**Cross-domain insight — the data science perspective:** Normalization is not merely a database administration concern. It is a structural guarantee against what machine learning practitioners call *data leakage* in the training pipeline. Consider a denormalized table where a customer's credit score is repeated across every transaction row. If you naively split this table into training and test sets by random row sampling, the same customer's credit score appears in both sets — the model has effectively memorized the customer, not learned to generalize from transaction patterns. The result is inflated validation accuracy that collapses in production. Normalization, by isolating each fact in one place, makes the statistical independence of entities explicit in the schema. When you split a normalized database into train/test sets by primary key of the entity table (e.g., by `CustomerID`), you guarantee no entity-level leakage — a property that denormalized schemas cannot provide without careful, error-prone sampling logic. This is why feature stores in production ML platforms (such as Uber's Michelangelo or Airbnb's Zipline) are built on normalized entity tables: they need point-in-time correct joins that do not accidentally leak future information into training data.

### 1.1 A Single-Table Design and Its Anomalies

Suppose we store all information in one table called `EMPLOYEE_PROJECTS`:

```
EMP_ID | EmpName   | ProjID | ProjName | Location | Hours
-------|-----------|--------|----------|----------|------
E01    | Smith     | P1     | Alpha    | NYC      | 20
E01    | Smith     | P1     | Alpha    | BOS      | 20
E01    | Smith     | P2     | Beta     | CHI      | 15
E02    | Jones     | P3     | Gamma    | SFO      | 30
```

**Quick check — what do you notice?** Look at the first two rows. The employee name "Smith" and project name "Alpha" are repeated. Is this repetition necessary, or is it a symptom of a deeper structural problem? Hold your answer — we'll formalize it below.

At first glance this looks like a normal table. However, three specific anomalies arise from this design:

- **Update anomaly:** If the project named "Alpha" gets renamed to "AlphaPlus," we must update *every single row* that contains `ProjName = 'Alpha'`. If we miss one, we have inconsistent data — two rows now silently disagree on the name of project P1.
- **Insertion anomaly:** We want to add a new project `P4` with name `Delta` and no employees assigned yet. We cannot insert it because there is no `EMP_ID` value to complete the row — `EMP_ID` is part of the key and cannot be null. The database forces us to invent a fake employee just to record a project’s existence.
- **Deletion anomaly:** If employee `E02` leaves and we delete their only row, we lose all information about project `P3` and its name `Gamma` entirely, even though the project still exists. Deleting a person deletes a project — a fact we never intended to couple.

These anomalies cause data corruption, wasted storage, and application bugs. Normalization eliminates them by *decomposing* one badly designed table into several well-designed tables.

**Industry example — healthcare systems:** Consider an electronic health record (EHR) system at a hospital network. A poorly designed `PATIENT_VISITS` table might store patient name, primary physician name, physician's office address, and visit details all in one table. When Dr. Chen moves her practice from the downtown clinic to the suburban campus, an update anomaly requires changing her office address in thousands of rows — every past visit for every one of her patients. A missed row means billing statements and follow-up reminders go to the wrong address. The insertion anomaly prevents the hospital from onboarding Dr. Chen before she has seen her first patient, because there is no visit row to hold her information. The deletion anomaly means that when a long-term patient moves away and their records are archived, the system may lose the fact that Dr. Chen is credentialed to practice at the suburban campus entirely. These are real failure modes that have caused HIPAA compliance violations and patient safety incidents in production hospital databases. Normalization to 3NF prevents every one of them by storing physician information, patient information, and visit information in separate relations.

**Industry example — e-commerce inventory:** An online retailer's `ORDER_ITEMS` table that stores `product_name`, `supplier_name`, and `supplier_contact` alongside each line item creates the same class of problems. When a supplier changes their contact email, the update must propagate to every historical order containing their products. A supplier with no current orders cannot be added to the system, blocking procurement workflows. Deleting the last order for a discontinued product may inadvertently delete the supplier record, severing the ability to process warranty returns. These anomalies translate directly to lost revenue, supplier relationship damage, and inventory reconciliation errors.

**Cross-domain connection — graph databases and entity resolution:** The anomalies of denormalized tables are isomorphic to the problem of *entity duplication* in graph databases and knowledge graphs. In a property graph like Neo4j, if you store a person's name as a property on every `WORKS_ON` edge rather than on the `Person` node, you have created the same partial dependency — and updating that person's name requires traversing and rewriting every edge, an O(n) operation instead of O(1). The graph database community arrived at the same solution independently: they call it *node deduplication* or *entity resolution*, and it is the graph equivalent of 2NF decomposition. The underlying principle — one fact, one location — transcends the relational model.

### 1.2 The Core Idea: One Fact in One Place

The guiding principle of normalization is:

> Every attribute should describe the key, the whole key, and nothing but the key.

This mnemonic encodes a precise technical condition. When we violate this principle — for example, by storing an employee’s name in a table where the key is a combination of employee, project, and location — the employee name depends on only part of the key (`EMP_ID` alone). So it gets repeated unnecessarily, and every repetition is an opportunity for inconsistency — an update anomaly waiting to happen. Normalization identifies these violations and splits the table so that each fact (employee name, project name, hours worked) lives in exactly one place.

**Try this yourself:** Before reading further, look at the table above and ask: which attributes depend on the whole key {`EMP_ID`, `ProjID`, `Location`}, and which depend on only part of it? Your answer will anticipate exactly where we decompose next.

### 1.3 The Two Non-Negotiable Properties of Decomposition

When we split a table, we must ensure two properties remain true:

1. **Lossless-join property:** We must be able to reconstruct the original table exactly by joining the decomposed tables. No extra, "spurious" tuples should appear. Think of this as the database equivalent of reversing a chemical reaction — you must recover the original substance, not a different mixture.
2. **Dependency preservation property:** All original functional dependencies should be enforceable directly on the decomposed tables, without needing to join them together to check a constraint. This matters because joins are expensive, and a constraint that requires a join on every insert is a performance disaster waiting to happen.

**Discussion prompt:** Why might a decomposition be lossless but not dependency-preserving? Can you imagine a scenario where you can reconstruct the data perfectly but cannot enforce a business rule without a join? This tension becomes critical when we reach BCNF — keep it in mind.

We will verify these properties as we proceed. A decomposition that loses information or loses constraints is not a valid normalization.

**Cross-domain insight — information theory:** The lossless-join property has a precise analogue in information theory: it is equivalent to the condition that the mutual information between the decomposed relations equals the information content of the original relation. When a join is lossless, no information is created or destroyed — only reorganized. When it is lossy, the join introduces spurious tuples that correspond to *new* information not present in the original data, equivalent to adding noise. This is why lossless-join is non-negotiable: a lossy decomposition is not a reorganization of facts but an invention of false facts. Claude Shannon's insight that information can be measured and preserved applies directly here — normalization is, in essence, a lossless compression algorithm for relational data, where the compression comes from eliminating redundancy while preserving the ability to reconstruct the original relation exactly.

---

## 2. First Normal Form (1NF) — The Foundation

### 2.1 Intuition Before Formalism

The relational model is built on the idea of a flat, two-dimensional grid. At every row-column intersection, we expect exactly one atomic value — a single number, a single string, a single date. If a column contains a list, a set, or a nested table inside it, then we cannot uniformly use relational operators like `SELECT`, `JOIN`, or `GROUP BY` on that column. 1NF is the rule that says: "Flatten everything. No lists inside cells."

**Analogy:** Think of a spreadsheet. Every cell holds one value. If you put a whole mini-spreadsheet inside a cell, you can no longer sort, filter, or formula-reference that inner data uniformly with the outer data. 1NF forces every cell to be a single data point, so the entire table is a uniform grid that all relational operators can traverse.

**Cross-domain connection:** This constraint mirrors the flat array requirement in linear algebra libraries like NumPy. A matrix is defined as a rectangular grid of scalars — you cannot nest a sub-matrix inside a single cell and still expect matrix multiplication to work. The relational model makes the same demand: operators are defined over atomic values, so the structure must be flat. If you have ever tried to vectorize a nested Python list and received a ragged-array warning, you have encountered 1NF thinking in another domain.

**Industry example — logistics and shipping:** A freight company's `SHIPMENTS` table might initially store a `TrackingHistory` column as a JSON array of `{timestamp, location, status}` objects. This is convenient for the application developer — one query retrieves the full history. But it violates 1NF. When a logistics analyst needs to answer "how many shipments passed through the Chicago hub last month?", the query must parse JSON inside every row, defeating indexing and forcing a full table scan. When the operations team needs to enforce that no shipment can have more than one "out for delivery" event, the constraint cannot be expressed declaratively — it requires application-level validation that is easily bypassed. Flattening `TrackingHistory` into a `SHIPMENT_EVENTS` table with one row per event transforms both problems: the Chicago-hub query becomes an indexed join, and the single-delivery-event constraint becomes a simple partial unique index. Logistics platforms built on PostgreSQL routinely face this exact trade-off between developer convenience and operational queryability, and 1NF provides the principled resolution.

**Cross-domain insight — functional programming and monads:** The 1NF requirement that every cell contain exactly one atomic value has a deep structural parallel in functional programming. A list inside a cell is like a nested monad — `List<List<Value>>` — which cannot be operated on by functions designed for `List<Value>` without explicit flattening (the `bind` or `flatMap` operation). The relational algebra's operators are defined over the outer container (the relation), and they expect the inner type to be scalar. 1NF is the database equivalent of the monadic law that requires flattening nested structures before applying transformations — a constraint that falls out naturally from the type system in languages like Haskell, but must be enforced by discipline in SQL.

### 2.2 Formal Definition

A relation schema is in **First Normal Form (1NF)** if the domain of every attribute includes only atomic (indivisible) values, and every tuple contains exactly one value from that domain for each attribute. In other words, 1NF disallows:

- Multivalued attributes (e.g., a column `PhoneNumbers` storing a set of numbers).
- Composite attributes (e.g., a column `Address` that itself is composed of `Street`, `City`, `Zip`).
- Nested relations (a table inside a table).

### 2.3 Worked Example: Breaking a Nested Structure

Let us start with a design that is *not* even in 1NF:

```
EMP_ID | EmpName   | Projects(ProjID, ProjName, Locations(*))
-------|-----------|----------------------------------------------
E01    | Smith     | { (P1, Alpha, {NYC, BOS}), (P2, Beta, {CHI}) }
E02    | Jones     | { (P3, Gamma, {SFO}) }
```

Here, `Projects` is a nested relation — a table inside a cell. Inside it, `Locations` is a multivalued set. This is a clear 1NF violation.

**Step 1: Flatten the nested relation into tuples.** We expand each project entry into its own row and each location into its own row. The result is a flat table:

```
EMP_ID | EmpName | ProjID | ProjName | Location
-------|---------|--------|----------|---------
E01    | Smith   | P1     | Alpha    | NYC
E01    | Smith   | P1     | Alpha    | BOS
E01    | Smith   | P2     | Beta     | CHI
E02    | Jones   | P3     | Gamma    | SFO
```

**Step 2: Identify the new primary key.** In the original design, `EMP_ID` alone might have been the key. Now, because an employee can have multiple projects and a project can have multiple locations, a single `EMP_ID` no longer uniquely identifies a row. We need the combination of all three: `{EMP_ID, ProjID, Location}`. No subset of this combination guarantees uniqueness anymore.

**Check:** Is every cell atomic? Yes — each contains a single string or number. The table is now in 1NF.

**Try this yourself:** What would happen if we stopped here and declared this 1NF table as our final design? Try inserting a new employee with no projects yet. Try deleting the last location for project P3. What breaks? This exercise will directly motivate Section 3.

**Industry example — telecommunications:** A mobile carrier's `CUSTOMER_ACCOUNTS` table might initially store a `LinkedPhoneNumbers` attribute as a comma-separated list (e.g., "555-0101, 555-0102, 555-0103") for family plans. This 1NF violation creates exactly the problem described above. When the carrier needs to identify which phone numbers are eligible for a port-out (transfer to another carrier) based on contract end dates, the comma-separated list must be parsed with string functions — `LIKE '%555-0102%'` — which cannot use a standard B-tree index. On a table of 50 million subscribers, this query times out. The normalized design — a `PHONE_NUMBERS` table with one row per number, foreign-keyed to `CUSTOMER_ACCOUNTS` — turns the port-out eligibility check into an indexed equality lookup that completes in milliseconds. Major telecommunications billing systems (such as those built on Oracle Communications Billing and Revenue Management) enforce 1NF at the data model level precisely to avoid these query performance cliffs.

### 2.4 Misconception Alert

A common misconception is: "If I split `Address` into `Street`, `City`, `Zip`, I am normalizing to 1NF." That is true only if `Address` was a composite attribute. Splitting an already-atomic attribute into smaller pieces is not 1NF normalization — it is a design choice about granularity. 1NF is about removing non-atomic domains, not about arbitrarily breaking strings apart.

### 2.5 Quick Check — Test Yourself

Is the following table in 1NF?

```
StudentID | Name   | Courses
----------|--------|--------------------------
S01       | Alice  | Math, Physics, Chemistry
S02       | Bob    | Biology
```

**Answer:** No. The `Courses` column contains a comma-separated list — a multivalued attribute. To reach 1NF, each course must appear in its own row.

---

## 3. Second Normal Form (2NF) — Eliminating Partial Dependencies

### 3.1 The Problem 2NF Solves

Consider again our 1NF table from Section 2.3. It is flat and atomic — so it satisfies 1NF. But the anomalies from Section 1.1 are still present. Why? Because 1NF only guaranteed atomic cells; it said nothing about which attributes depend on which parts of the key.

Here is the tension: the table is in 1NF, yet it still corrupts data on updates, blocks inserts, and destroys information on deletes. This is the intellectual tension that motivates 2NF — 1NF was necessary but not sufficient. We need a stronger condition that examines the functional dependencies *inside* the key.

**Analogy:** 1NF is like ensuring every box in a warehouse holds exactly one item. But if you store the item’s label inside a box that also holds a shipping address, and you have multiple boxes for the same item with different addresses, you still have to update the label in every box when it changes. 2NF says: the label belongs with the item, not with the item-and-address combination.

**Cross-domain connection:** This is the database equivalent of the Single Source of Truth principle in software architecture. In a microservice system, if the same piece of data — say, a user's email — is stored in both the billing service and the notification service, any update must propagate to both. Miss one, and the system contains contradictory facts. 2NF formalizes this intuition by requiring that non-key attributes depend on the entire key, not on a fragment of it.