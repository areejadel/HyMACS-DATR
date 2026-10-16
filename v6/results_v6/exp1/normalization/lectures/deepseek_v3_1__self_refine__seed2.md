# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Recall** the formal definitions of 1NF, 2NF, 3NF, and BCNF, and state what each normal form prohibits.
2.  **Explain** why partial and transitive dependencies cause update, insertion, and deletion anomalies, and distinguish a candidate key from a superkey.
3.  **Apply** the normalization process to decompose an unnormalized relation through 1NF, 2NF, 3NF, and BCNF, correctly identifying all functional dependencies and candidate keys at each stage.
4.  **Analyze** a given relational schema to determine its current normal form and pinpoint the functional dependency that causes any violation.
5.  **Evaluate** trade-offs between normalization and denormalization in real-world scenarios, and explain the role of lossless-join and dependency-preservation properties in schema decomposition.

---

## Prerequisites

We assume you are comfortable with:

- The structure of a relational table: attributes (columns), tuples (rows), and domains (data types).
- The concept of a **primary key** and the uniqueness constraint it enforces.
- The notion of a **functional dependency** (FD), written \(X \rightarrow Y\), meaning: if two tuples agree on attributes \(X\), they must agree on attributes \(Y\).
- The terms **superkey** (any set of attributes that uniquely identifies a tuple) and **candidate key** (a minimal superkey — no attribute can be removed without destroying uniqueness).
- The **closure** of a set of functional dependencies, denoted \(F^+\), which is the set of all FDs logically implied by a given set \(F\) under Armstrong's axioms (reflexivity, augmentation, transitivity).

If any of these concepts feel rusty, review them now. We build directly on these ideas.

> **Prerequisite check:** Consider a table with attributes \(A, B, C\). Suppose \(A \rightarrow B\) and \(B \rightarrow C\). What is the candidate key?
>
> <details>
> <summary>Click to reveal answer</summary>
>
> **Answer:** \(A\). Because \(A \rightarrow B\) and \(B \rightarrow C\), transitivity yields \(A \rightarrow C\). The closure of \(\{A\}\) is \(\{A, B, C\}\), so \(A\) is a superkey. No proper subset of \(A\) exists, so \(A\) is the candidate key. If this reasoning feels unfamiliar, review functional dependency transitivity and attribute closure before proceeding.
> </details>

---

## 1. Why Normalize? The Problem We Are Solving

### 1.1 Opening Hook: The Database Design That Passes Every Test — Until It Doesn't

A startup launches with a single database table tracking customers, orders, and shipping addresses. For six months, everything works perfectly. Queries return correct results. The application passes every integration test. Then, on a Tuesday, the operations team changes a warehouse address. They update it in the admin panel. The update succeeds. But the next day, half the pending orders ship to the old address while half ship to the new one. No error was thrown. No constraint was violated. The database simply *believed two contradictory things at once*.

What went wrong? The same warehouse address was stored in 847 different rows — once per order — and the update query only touched 423 of them due to a subtle partitioning in the batch process. The schema permitted this inconsistency because it encoded no rule that a warehouse has exactly one address. The application code "knew" this rule, but the database did not. When the code and the data diverged, the data won.

This is the central tension of database design: **the database enforces only what you declare structurally. Everything else is a hope.** Normalization is the process of encoding real-world constraints — functional dependencies — directly into the structure of your tables so that the database management system itself prevents these inconsistencies, regardless of what your application code does or fails to do.

But here is the puzzle: if normalization eliminates redundancy, why do production databases at companies like Amazon, Netflix, and Uber deliberately *denormalize* certain tables? What do they gain by reintroducing the very redundancy normalization removes? Hold this question. We will resolve it when we reach the trade-off analysis in Section 5.

### 1.2 The Single-Table Disaster: A Concrete Starting Point

Imagine building a database for a small company that tracks employees, their projects, and project locations. A naive first attempt puts everything into one table:

```
EMP_ID | EmpName   | ProjID | ProjName | Location | Hours
-------|-----------|--------|----------|----------|------
E01    | Smith     | P1     | Alpha    | NYC      | 20
E01    | Smith     | P1     | Alpha    | BOS      | 20
E01    | Smith     | P2     | Beta     | CHI      | 15
E02    | Jones     | P3     | Gamma    | SFO      | 30
```

It works — until it does not. The table *looks* correct after every operation, but it now contains duplicate names, missing projects, or phantom relationships waiting to surface.

> **Pause and predict:** Before reading the anomaly descriptions below, examine this table and predict which operations will cause problems, and what kind of problems. Specifically:
> - What happens to project "Alpha" if you update its name in only one row?
> - What happens if you try to add a new project "Delta" with no employees assigned yet?
> - What happens if you delete employee E02's row?
>
> Write down your predictions, then read on to verify.
>
> <details>
> <summary>Click to reveal analysis</summary>
>
> - **Update:** If you rename "Alpha" to "AlphaPlus" in only one of the two rows for P1, the database now contains two different names for the same project — a silent inconsistency. No error is raised. No constraint is violated. The database simply now believes P1 is simultaneously named "Alpha" and "AlphaPlus."
> - **Insert:** You cannot add project "Delta" with ProjID P4 because there is no EMP_ID to complete the row (EMP_ID is part of the key and cannot be null). The project's existence is blocked by the absence of an employee — a fact about projects is coupled to a fact about employees.
> - **Delete:** Deleting E02 removes the only row containing project P3 and its name "Gamma." The project vanishes from the database even though it still exists in reality. Deleting a person deletes a project.
> </details>

### 1.3 Three Anomalies That Corrupt Your Data

Each anomaly is a direct consequence of storing the same fact in multiple rows. The schema forces you to repeat information, and every repetition is an opportunity for inconsistency.

**Update anomaly:** When a fact changes, you must update every copy. Miss one, and the database silently contradicts itself. In a modern e-commerce setting, consider a product catalog where `SupplierName` is stored redundantly in an `Inventory` table across thousands of stock-keeping units (SKUs). When a supplier rebrands, an incomplete `UPDATE` causes some SKUs to display the old name while others show the new one, leading to purchase order errors and supplier payment delays. A documented case from the financial sector involves a major bank's trading system that stored counterparty legal names redundantly across millions of trade records. A corporate merger required updating the counterparty name, and the batch update process, running over a weekend, missed approximately 0.3% of rows due to a partitioning error, causing regulatory reporting discrepancies that took weeks to reconcile.

**Insertion anomaly:** You cannot record one fact without simultaneously recording an unrelated fact. In modern microservice architectures, this manifests when a new financial product cannot be recorded in a product catalog service until at least one customer purchases it, because the schema incorrectly couples product metadata with transaction data. A documented instance occurred in a university course registration system: new courses could not be entered into the catalog over the summer unless at least one student pre-registered, forcing administrators to create dummy student records that later caused audit trail anomalies.

**Deletion anomaly:** Deleting one fact inadvertently deletes another. In modern cloud-based SaaS platforms, a documented supply-chain system failure occurred when the last shipment record for a warehouse location was archived, causing the warehouse itself to disappear from the active database, halting all future routing to that facility. This is functionally equivalent to deleting a user's last order causing the product they ordered to vanish from the catalog.

These anomalies cause data corruption, wasted storage, and application bugs. Normalization eliminates them by *decomposing* one badly designed table into several well-designed tables, each responsible for exactly one kind of fact.

> **Cross-domain connection — compiler design:** The normalization process mirrors what optimizing compilers do during *common subexpression elimination*. If a computation `x + y` appears in multiple places in your code, a compiler computes it once, stores the result in a temporary variable, and reuses it. Normalization does the same for data: if a fact (like an employee's name) appears in multiple rows, we store it once in its own table and reference it. Both techniques eliminate redundant storage and the inconsistencies that redundant updates create. The compiler's "single static assignment" form — where each variable is assigned exactly once — is the code analogue of the normalization principle: each fact has one canonical location.

> **Cross-domain connection — software engineering and the DRY principle:** Normalization is the database-level enforcement of "Don't Repeat Yourself." In code, extracting a repeated logic block into a single function eliminates the risk of fixing a bug in one copy while leaving others broken. In databases, extracting a repeated fact into its own table eliminates the risk of updating that fact inconsistently. The same abstraction instinct — identify what varies together and encapsulate it — drives both good schema design and good software architecture. The difference is that a database schema persists for years and accumulates data continuously; a bug in application logic can be fixed with a redeploy, but inconsistent data must be painstakingly repaired row by row.

### 1.4 The Core Idea: One Fact in One Place

The guiding principle of normalization is:

> Every attribute should describe the key, the whole key, and nothing but the key.

This mnemonic, attributed to William Kent, encodes a precise technical condition. When we violate this principle — for example, by storing an employee's name in a table whose key is a combination of employee, project, and location — the employee name depends on only part of the key (`EMP_ID` alone). It gets repeated unnecessarily, and every repetition is an opportunity for inconsistency.

But what does "describe the key" actually mean? It means the attribute's value is determined by the key and only by the key. If you tell me the key value, I can tell you the attribute's value — uniquely, without ambiguity. If the attribute's value can be determined by something *less* than the full key, you have a partial dependency. If it can be determined by something that is *not* the key at all, you have a transitive dependency. Normalization is the systematic process of detecting and eliminating these misplaced dependencies.

> **Try this yourself:** Before reading further, look at the table above and ask: which attributes depend on the whole key `{EMP_ID, ProjID, Location}`, and which depend on only part of it?
>
> <details>
> <summary>Click to reveal analysis</summary>
>
> - `EmpName` depends only on `EMP_ID` — a proper subset of the key. Given EMP_ID = "E01", you know EmpName = "Smith" regardless of project or location.
> - `ProjName` depends only on `ProjID` — a proper subset of the key. Given ProjID = "P1", you know ProjName = "Alpha."
> - `Hours` depends on `{EMP_ID, ProjID}` — a proper subset of the key. An employee's hours on a project do not depend on location.
> - No non-key attribute depends on the full key `{EMP_ID, ProjID, Location}`.
>
> This means every non-key attribute suffers from a partial dependency — a 2NF violation we address in Section 3. The table is fundamentally miskeyed.
> </details>

### 1.5 The Two Non-Negotiable Properties of Decomposition

When we split a table, two properties must hold. Losing either one is unacceptable in most contexts.

**Property 1 — Lossless-join:** We must be able to reconstruct the original table exactly by joining the decomposed tables, with no spurious tuples appearing. Formally, a decomposition of a relation \(R\) into \(R_1\) and \(R_2\) is lossless-join if and only if at least one of the following FDs is in \(F^+\):

\[
R_1 \cap R_2 \rightarrow R_1 \quad \text{or} \quad R_1 \cap R_2 \rightarrow R_2
\]

The common attributes must functionally determine at least one of the decomposed relations. In signal processing terms, a lossless decomposition is like a Fourier transform — the original signal can be perfectly reconstructed from its components because no information is discarded. A decomposition that is not lossless-join is a lossy decomposition, which is unacceptable because it introduces spurious tuples that did not exist in the original relation, effectively fabricating data upon reconstruction. Imagine splitting a table of students and their courses into two tables, joining them back, and discovering that a student who never enrolled in a course now appears to be enrolled — that is what a lossy decomposition does.

**Property 2 — Dependency preservation:** All original functional dependencies should be enforceable directly on the decomposed tables, without requiring a join to check a constraint. Formally, let \(F\) be the set of FDs on \(R\), and let \(F_1, F_2, \ldots, F_k\) be the projections of \(F\) onto the decomposed schemas \(R_1, R_2, \ldots, R_k\). The decomposition is dependency-preserving if:

\[
(F_1 \cup F_2 \cup \cdots \cup F_k)^+ = F^+
\]

This matters because joins are expensive, and a constraint requiring a join on every insert degrades performance. For example, if an FD \(A \rightarrow B\) spans two tables, every insert into either table requires checking the other table to ensure the FD holds. In a high-throughput system processing thousands of inserts per second, this join-per-insert cost can be prohibitive. The tension between lossless-join and dependency preservation becomes acute with BCNF — sometimes you cannot have both, and you must choose. This is the first hint of why real-world databases sometimes stop at 3NF rather than pursuing BCNF.

> **Quick check — test the lossless-join condition:** A relation \(R(A, B, C)\) with FD \(A \rightarrow B\) is decomposed into \(R_1(A, B)\) and \(R_2(A, C)\). Is this lossless?
>
> <details>
> <summary>Click to reveal answer</summary>
>
> **Answer:** Yes. The intersection is \(\{A\}\), and \(A \rightarrow R_1\) holds because \(A \rightarrow B\) and \(R_1\) contains only \(A\) and \(B\). Since \(A\) determines all of \(R_1\), joining on \(A\) reconstructs the original tuples exactly. No spurious tuples can appear because every \(A\) value in \(R_2\) matches at most one tuple in \(R_1\).
> </details>

> **Quick check — test your understanding of trade-offs:** A relation \(R(A, B, C)\) with FDs \(A \rightarrow B\) and \(B \rightarrow C\) is decomposed into \(R_1(A, B)\) and \(R_2(A, C)\). Is this decomposition dependency-preserving? What FD might be lost?
>
> <details>
> <summary>Click to reveal answer</summary>
>
> **Answer:** The FD \(A \rightarrow B\) is preserved in \(R_1\). However, the FD \(B \rightarrow C\) spans both tables — \(B\) is in \(R_1\) and \(C\) is in \(R_2\). To check \(B \rightarrow C\), we would need to join \(R_1\) and \(R_2\) on \(A\) and verify that for every \(B\) value, there is exactly one \(C\) value. This decomposition is not dependency-preserving with respect to \(B \rightarrow C\). This is the classic trade-off we will revisit when we discuss BCNF in Section 4.
> </details>

---

## 2. First Normal Form (1NF) — The Foundation

### 2.1 Intuition Before Formalism: Why the Grid Must Be Flat

The relational model is built on a flat, two-dimensional grid. At every row-column intersection, we expect exactly one atomic value — a single number, a single string, a single date. This is not an arbitrary aesthetic preference. It is a requirement for the relational algebra to work uniformly.

If a column contains a list, a set, or a nested table, the fundamental operations — selection, projection, join — cannot be applied without special-case handling. A `WHERE` clause filtering on a list-valued column becomes ambiguous: do you mean "the list contains this value" or "the list equals this value"? A `JOIN` on a nested table requires unnesting logic that the relational engine cannot optimize generically. 1NF is the rule that says: flatten everything so the algebra applies uniformly.

**Analogy — the spreadsheet:** Think of a spreadsheet. Every cell holds one value. If you put a mini-spreadsheet inside a cell, you can no longer sort, filter, or formula-reference that inner data uniformly with the outer data. 1NF forces every cell to be a single data point, so the entire table forms a uniform grid that all relational operators can traverse identically.

**Analogy — linear algebra:** This is analogous to the first normal form in linear algebra — a matrix must have scalar entries before you can apply matrix operations uniformly. A "matrix of vectors" breaks the algebraic machinery until you flatten it. You cannot multiply two matrices if their entries are themselves matrices without defining a higher-order tensor algebra. The relational model makes the same demand: scalar values in every cell so that the relational operators compose cleanly.

### 2.2 Formal Definition

A relation schema is in **First Normal Form (1NF)** if the domain of every attribute includes only atomic (indivisible) values, and every tuple contains exactly one value from that domain for each attribute. 1NF disallows:

- **Multivalued attributes:** A column storing a set of values (e.g., a `PhoneNumbers` column containing `{555-1234, 555-5678}`).
- **Composite attributes:** A column composed of sub-parts treated as a unit (e.g., an `Address` column that internally contains `Street`, `City`, `Zip`).
- **Nested relations:** A table inside a table cell.

The definition of "atomic" is context-dependent. A string like "New York" is atomic for most purposes, but if an application needs to query by individual words, it may not be atomic *for that application*. Codd's original formulation left "atomic" intentionally relative to the domain of discourse — a value is atomic if the database system never needs to decompose it to enforce constraints or answer queries. The rule of thumb: if you ever need to extract a sub-part of a value using substring operations or application logic to enforce a constraint, the value is not atomic for your purposes and should be split.

### 2.3 Worked Example: Breaking a Nested Structure

Consider a design that is *not* in 1NF:

```
EMP_ID | EmpName   | Projects(ProjID, ProjName, Locations(*))
-------|-----------|----------------------------------------------
E01    | Smith     | { (P1, Alpha, {NYC, BOS}), (P2, Beta, {CHI}) }
E02    | Jones     | { (P3, Gamma, {SFO}) }
```

Here, `Projects` is a nested relation — a table inside a cell. Inside it, `Locations` is a multivalued set. This is a clear 1NF violation. The database cannot index `ProjName` values, cannot join on `ProjID`, and cannot enforce a uniqueness constraint on project names without first extracting them from the nested structure — operations that require custom code rather than declarative SQL.

**Step 1: Flatten the nested relation into tuples.** We expand each project entry into its own row and each location into its own row. Let us walk through this systematically:

- Employee E01 has two projects: P1 (with locations NYC and BOS) and P2 (with location CHI).
- Project P1 for E01 produces two rows: one for NYC, one for BOS.
- Project P2 for E01 produces one row: for CHI.
- Employee