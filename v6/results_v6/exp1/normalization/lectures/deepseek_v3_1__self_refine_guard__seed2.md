# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** — State the definitions of 1NF, 2NF, 3NF, and BCNF, and identify what each normal form prohibits.
2. **Understand** — Explain why partial and transitive dependencies cause update, insertion, and deletion anomalies, and distinguish between a candidate key and a superkey.
3. **Apply** — Given an unnormalized relation, carry out the step-by-step normalization process to decompose it into 1NF, 2NF, 3NF, and BCNF, correctly identifying all functional dependencies and candidate keys.
4. **Analyze** — Given a relational schema, determine its current normal form and pinpoint the specific functional dependency responsible for any violation.
5. **Evaluate** — Compare the trade-offs between full normalization and intentional denormalization, and justify when lossless-join or dependency-preservation properties might be prioritized in a real-world design.

---

## Prerequisites — What We Assume You Already Know

Before we begin, we assume you are comfortable with:

- The basic structure of a relational table: attributes (columns), tuples (rows), and domains (data types).
- The concept of a **primary key** and the uniqueness constraint it enforces.
- The idea of a **functional dependency** (FD), written as \(X \rightarrow Y\), meaning: if two tuples agree on the attributes in \(X\), they must also agree on the attributes in \(Y\).
- The terms **superkey** (any set of attributes that uniquely identifies a tuple) and **candidate key** (a minimal superkey — no attribute can be removed without losing the uniqueness property).

**Quick warm-up:** Consider a table with attributes \(\{A, B, C, D\}\). If \(\{A, B\} \rightarrow C\) and \(\{A, B\} \rightarrow D\) both hold, and no proper subset of \(\{A, B\}\) uniquely identifies a row, what is the candidate key? *(Answer: \(\{A, B\}\))* If these ideas feel rusty, pause and review them now. We will build directly on these concepts.

---

## 1. Why Normalize? The Problem We Are Solving

### 1.0 Opening Hook: The Database That Forgets

Imagine you are building a database for a small company that tracks employees, the projects they work on, and the locations of those projects. A naive first attempt might put everything into one big table. It works — until it doesn't.

Here is the unsettling reality: your single-table design will silently corrupt data through ordinary operations — renaming a project, hiring an employee before assigning them, or deleting a departing employee. Each is a routine business event, yet each will leave your database in an inconsistent state that no error message will catch. The table *looks* correct, but it now contains lies: duplicate names, missing projects, or phantom relationships.

This is not a bug in your application code. It is a structural defect in your schema. The only way to fix it permanently is to understand exactly *why* the structure permits these anomalies — which is what normalization reveals.

**Cross-Domain Connection: Why This Is a Physics Problem in Disguise**

Before we dive into database theory, consider something from thermodynamics: the concept of *redundancy as a source of instability*. In physical systems, storing the same energy in multiple coupled reservoirs creates paths to irreversible entropy generation — one reservoir changes, the others lag, and the system drifts into inconsistency. A database table with repeated facts is precisely such a system. Every duplicated value is a coupled reservoir; every partial update is a temperature differential; and every resulting inconsistency is entropy — information degraded, unrecoverable without external correction. Normalization is, in this sense, the database equivalent of isolating thermal reservoirs: it eliminates the coupling that makes inconsistency energetically favorable. This is not a metaphor — it is an isomorphism. Both systems fail because redundant coupling creates degrees of freedom for error that no local constraint can close.

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

At first glance this looks like a normal table. However, three specific anomalies arise from this design:

- **Update anomaly:** If the project named "Alpha" gets renamed to "AlphaPlus," we must update *every single row* that contains `ProjName = 'Alpha'`. If we miss one, we have inconsistent data — two rows now silently disagree on the name of project P1. In healthcare databases, this exact pattern causes patient records to show conflicting medication names after a drug rebranding, potentially leading to dangerous prescription errors.
- **Insertion anomaly:** We want to add a new project `P4` with name `Delta` and no employees assigned yet. We cannot insert it because there is no `EMP_ID` value to complete the row — `EMP_ID` is part of the key and cannot be null. The database forces us to invent a fake employee just to record a project's existence. In financial systems, this manifests when a bank cannot record a new financial product until at least one customer purchases it — an absurd business constraint imposed purely by schema design.
- **Deletion anomaly:** If employee `E02` leaves and we delete their only row, we lose all information about project `P3` and its name `Gamma` entirely, even though the project still exists. Deleting a person deletes a project — a fact we never intended to couple. In e-commerce platforms, this surfaces when deleting the last order from a supplier also erases the supplier's contact information, severing the relationship entirely.

These anomalies are not merely theoretical. They cause data corruption, wasted storage, and application bugs. Normalization is the systematic technique that eliminates these anomalies by *decomposing* one badly designed table into several well-designed tables.

---

**Test Yourself 1.1:** Suppose we update the `ProjName` for `P1` to "AlphaPlus" in only the first row of the table above. What inconsistency now exists in the data? Write down the two conflicting facts that now coexist in the table.

<details>
<summary>Click for answer</summary>
Row 1 says `ProjName = 'AlphaPlus'` for P1, while row 2 still says `ProjName = 'Alpha'` for the same P1. The database now contains two different names for project P1 — a contradiction that no constraint in this schema prevents.
</details>

---

### 1.2 The Core Idea: One Fact in One Place

The guiding principle of normalization is:

> Every attribute should describe the key, the whole key, and nothing but the key.

This is a mnemonic, but it encodes a precise technical condition. When we violate this principle — for example, by storing an employee's name in a table where the key is a combination of employee, project, and location — the employee name depends on only part of the key (`EMP_ID` alone). So it gets repeated unnecessarily, and every repetition is an opportunity for inconsistency — an update anomaly waiting to happen. Normalization identifies these violations and splits the table so that each fact (employee name, project name, hours worked) lives in exactly one place.

**Pause and Predict:** Before reading further, look at the table above and ask: which attributes depend on the whole key `{EMP_ID, ProjID, Location}`, and which depend on only part of it? Your answer will anticipate exactly where we decompose next.

---

### 1.3 The Two Non-Negotiable Properties of Decomposition

When we split a table, we must ensure two properties remain true:

1. **Lossless-join property:** We must be able to reconstruct the original table exactly by joining the decomposed tables. No extra, "spurious" tuples should appear. Formally, a decomposition of relation \(R\) into \(R_1\) and \(R_2\) is lossless-join if and only if the common attributes of \(R_1\) and \(R_2\) form a superkey for at least one of the decomposed relations. Think of this as the database equivalent of reversing a chemical reaction — you must recover the original substance, not a different mixture.

2. **Dependency preservation property:** All original functional dependencies should be enforceable directly on the decomposed tables, without needing to join them together to check a constraint. Formally, let \(\mathcal{F}\) be the set of FDs on \(R\), and let \(\mathcal{F}_1, \mathcal{F}_2, \ldots, \mathcal{F}_k\) be the FDs that hold on the decomposed relations \(R_1, R_2, \ldots, R_k\). The decomposition is dependency-preserving if the closure of the union of the projections equals the closure of \(\mathcal{F}\):

   \[
   \left(\bigcup_{i=1}^{k} \pi_{R_i}(\mathcal{F})\right)^+ = \mathcal{F}^+
   \]

   This matters because joins are expensive, and a constraint that requires a join on every insert is a performance disaster waiting to happen.

**Try This Yourself 1.3:** Take the single table from Section 1.1 and manually split it into two tables — one for employees and one for projects with locations. Now try to reconstruct the original rows by joining them. Do you get exactly the original rows, or do extra rows appear? What does this tell you about whether your split was lossless?

We will verify these properties as we proceed. For now, remember: a decomposition that loses information or loses constraints is not a valid normalization.

---

## 2. First Normal Form (1NF) — The Foundation

### 2.1 Intuition Before Formalism

The relational model is built on the idea of a flat, two-dimensional grid. At every row-column intersection, we expect exactly one atomic value — a single number, a single string, a single date. If a column contains a list, a set, or a nested table inside it, then we cannot uniformly use relational operators like `SELECT`, `JOIN`, or `GROUP BY` on that column. 1NF is the rule that says: "Flatten everything. No lists inside cells."

**Analogy:** Think of a spreadsheet. Every cell holds one value. If you put a whole mini-spreadsheet inside a cell, you can no longer sort, filter, or formula-reference that inner data uniformly with the outer data. 1NF forces every cell to be a single data point, so the entire table is a uniform grid that all relational operators can traverse.

**Cross-Domain Connection: Matrices and Linear Algebra**

This flat-grid requirement has a precise mathematical analogue. In linear algebra, a matrix is defined as a rectangular array where every entry is a scalar — a single element from the underlying field. You cannot put a vector inside a single matrix cell and still expect matrix multiplication, row reduction, or eigenvalue computation to behave meaningfully. The operators are defined over scalars, not over nested structures. The relational algebra is exactly the same: `SELECT`, `PROJECT`, and `JOIN` are operators over atomic values. Nesting breaks the closure property of the algebra — the output of one operation can no longer serve as the input to the next. 1NF is therefore not an arbitrary rule; it is the condition that keeps the relational algebra closed under its own operations, exactly as scalar entries keep linear algebra closed.

### 2.2 Formal Definition

A relation schema is in **First Normal Form (1NF)** if the domain of every attribute includes only atomic (indivisible) values, and every tuple contains exactly one value from that domain for each attribute. In other words, 1NF disallows:

- Multivalued attributes (e.g., a column `PhoneNumbers` storing a set of numbers).
- Composite attributes (e.g., a column `Address` that itself is composed of `Street`, `City`, `Zip`).
- Nested relations (a table inside a table).

The definition of "atomic" is context-dependent. A value is atomic if the application does not need to decompose it further for its operations. For example, a `DATE` value is atomic in most applications, even though it contains year, month, and day components, because relational operators treat it as a single value. However, if the application frequently queries by month alone, then storing `DATE` as a single atomic value may be insufficient, and 1NF would require decomposing it into separate `YEAR`, `MONTH`, `DAY` attributes.

**Try This Yourself 2.2:** Consider a `PHONE_NUMBER` attribute stored as a single string like "+1-555-123-4567". Is this atomic? It depends. List two application scenarios: one where this string is atomic enough, and one where it is not. For the second scenario, what would a 1NF-compliant decomposition look like?

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

---

**Test Yourself 2.1:** Consider this table:

```
StudentID | Name   | Courses
----------|--------|--------------------------
S01       | Alice  | Math, Physics, Chemistry
S02       | Bob    | Biology
```

Is it in 1NF? If not, what must change?

<details>
<summary>Click for answer</summary>
No. The `Courses` column contains a comma-separated list — a multivalued attribute. To reach 1NF, each course must appear in its own row:

```
StudentID | Name   | Course
----------|--------|---------
S01       | Alice  | Math
S01       | Alice  | Physics
S01       | Alice  | Chemistry
S02       | Bob    | Biology
```
</details>

---

### 2.4 Misconception Alert

A common misconception is: "If I split `Address` into `Street`, `City`, `Zip`, I am normalizing to 1NF." That is true only if `Address` was a composite attribute. Splitting an already-atomic attribute into smaller pieces is not 1NF normalization — it is a design choice about granularity. 1NF is about removing non-atomic domains, not about arbitrarily breaking strings apart.

---

## 3. Second Normal Form (2NF) — Eliminating Partial Dependencies

### 3.1 The Problem 2NF Solves

Consider again our 1NF table from Section 2.3. It is flat and atomic — so it satisfies 1NF. But the anomalies from Section 1.1 are still present. Why? Because 1NF only guaranteed atomic cells; it said nothing about which attributes depend on which parts of the key.

Here is the tension: the table is in 1NF, yet it still corrupts data on updates, blocks inserts, and destroys information on deletes. This is the intellectual tension that motivates 2NF — 1NF was necessary but not sufficient. We need a stronger condition that examines the functional dependencies *inside* the key.

**Analogy: Library Catalog Cards**

1NF is like ensuring every card in a library catalog drawer has exactly one entry per field — no scribbled lists in the margin. But 2NF addresses a deeper problem: if the same author name appears on fifty catalog cards for fifty different books, and the author changes their name, you must update all fifty cards by hand. The author's name doesn't depend on which book card it appears on — it depends only on the author's identity. 2NF says: pull the author information onto its own card, keyed by author ID, and reference it from the book cards. One fact, one card — one place to update.

### 3.2 Formal Definition

A relation schema is in **Second Normal Form (2NF)** if:

1. It is in 1NF, and
2. Every non-prime attribute (an attribute that is not part of any candidate key) is **fully functionally dependent** on every candidate key — not just on a proper subset of a candidate key.

Formally, an attribute \(A\) is fully functionally dependent on a set of attributes \(X\) if \(X \rightarrow A\) holds and there is no proper subset \(Y \subset X\) such that \(Y \rightarrow A\) also holds. In simpler terms: no non-key attribute depends on only part of a candidate key. If the key is composite, every non-key attribute must depend on the entire key, not just a piece of it.

### 3.3 Worked Example: Spotting Partial Dependencies

Let us examine our 1NF table with candidate key \(\{\text{EMP_ID}, \text{ProjID}, \text{Location}\}\):

\[
\text{EMP_ID} \rightarrow \text{EmpName} \quad \text{(EmpName depends on EMP_ID alone — partial dependency)}
\]
\[
\text{ProjID} \rightarrow \text{ProjName} \quad \text{(ProjName depends on ProjID alone — partial dependency)}
\]
\[
\{\text{EMP_ID}, \text{ProjID}\} \rightarrow \text{Hours} \quad \text{(Hours depends on employee and project, but not location)}
\]

Here is the crucial observation: `EmpName` depends only on `EMP_ID`, which is a proper subset of the candidate key. `ProjName` depends only on `ProjID`, another proper subset. `Hours` depends on `{EMP_ID, ProjID}`, also a proper subset (it does not need `Location`). These are all **partial dependencies** — non-prime attributes that depend on part of a candidate key rather than the whole key. This is exactly what 2NF prohibits.

**Decomposition to 2NF:** We split the table so that each partial dependency gets its own relation where its determinant is the full key:

- **EMPLOYEE(EMP_ID, EmpName)** — key: `{EMP_ID}`, and `EmpName` now depends on the whole key.
- **PROJECT(ProjID, ProjName)** — key: `{ProjID}`, and `ProjName` depends on the whole key.
- **WORKS_ON(EMP_ID, ProjID, Location, Hours)** — key: `{EMP_ID, ProjID, Location}`. `Hours` still depends on `{EMP_ID, ProjID}`, which is a subset of this key. This is a partial dependency — so this table is *not yet* in 2NF. We will address this in a moment.

Wait — why is `Hours` still a problem? Because in `WORKS_ON`, the candidate key includes `Location`, but `Hours` does not functionally depend on `Location`. It depends only on `{EMP_ID, ProjID}`. So `Hours` is a non-prime attribute that depends on a proper subset of the candidate key — a textbook partial dependency.

**Pause and Predict:** Before reading the fix, ask: what should