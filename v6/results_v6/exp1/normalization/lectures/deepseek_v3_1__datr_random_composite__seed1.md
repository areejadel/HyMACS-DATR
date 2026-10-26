# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember** – State the definitions of 1NF, 2NF, 3NF, and BCNF in your own words.
2.  **Understand** – Explain why each normal form addresses a specific type of redundancy anomaly.
3.  **Apply** – Given a relation and a set of functional dependencies, determine which normal form the relation satisfies.
4.  **Analyze** – Identify the precise functional dependency that violates a normal form and trace the resulting insertion, update, or deletion anomaly.
5.  **Create** – Perform a lossless decomposition to bring a schema into 3NF or BCNF using the standard algorithms.

---

## 0. Prerequisites

We build on three concepts from earlier lectures. If any feel unclear, pause and review them now.

- **Relation schema** – A named set of attributes (columns). A *relation instance* is a table of tuples conforming to that schema.
- **Superkey** – A set of attributes whose values uniquely identify each tuple. Formally, if $SK$ is a superkey of $R$, then $SK \rightarrow R$ holds.
- **Candidate key** – A minimal superkey. Removing any attribute from it destroys uniqueness.

---

## 1. The Engine of Normalization: Functional Dependencies

### 1.1 Why This Matters: The Hidden Cost of "Just One More Column"

Imagine you run a small online bookstore. Every time an order ships, you record the `OrderID`, `CustomerID`, `CustomerName`, `ShippingAddress`, and `BookTitle`. It works fine—until a loyal customer moves. Now you must hunt through every order they ever placed and update their address. Miss one row, and the next shipment goes to the wrong house. Worse, when a new customer registers but hasn't ordered yet, you have nowhere to put their name. The database refuses to store facts you know are true.

These are not bugs in your application code. They are structural defects in your table design—defects that normalization systematically erases. The tool that reveals them is the functional dependency.

### 1.2 A Cross-Domain Lens: FDs as Compiler Type Inference Rules

Before diving into formal definitions, let's borrow an insight from programming language theory. In a statically typed language, the compiler performs type inference: it deduces that if `x` has type `int`, then `x + 1` must also have type `int`. This is a deterministic rule—given the type of `x`, the type of the expression is uniquely determined. Functional dependencies operate identically: given a value for $X$, the value for $Y$ is uniquely determined. Just as a type checker rejects programs where an expression's type cannot be inferred, normalization rejects schemas where an attribute's value cannot be uniquely determined by a key. The FD is your schema's type inference rule, and normalization is the type-checking pass that catches design bugs before they corrupt your data.

### 1.3 Another Cross-Domain Connection: FDs as Cryptographic Hash Functions

Here is a second analogy that illuminates the asymmetry at the heart of functional dependencies. A cryptographic hash function like SHA-256 maps an arbitrary input to a fixed-size output. Given the same input, you always get the same hash—that's determinism, exactly like an FD. But the reverse is computationally infeasible: given a hash, you cannot recover the original input. Similarly, an FD $X \rightarrow Y$ guarantees that $X$ determines $Y$, but says nothing about whether $Y$ determines $X$. This asymmetry is why $\{\text{CourseID}\} \rightarrow \{\text{Grade}\}$ fails in our enrollment example—multiple students can earn different grades in the same course, just as multiple inputs can produce the same hash (a collision, in cryptographic terms). The FD arrow is a one-way function: it promises forward determinism, not reversibility. Recognizing this asymmetry is the key to spotting normalization violations.

### 1.4 An Unconventional Framing: FDs as Causal Graphs with Missing Arrows

Here is a perspective you won't find in standard textbooks: think of a relation schema as a causal graph where attributes are nodes and functional dependencies are directed edges. When we assert $\{\text{StudentID}\} \rightarrow \{\text{StudentEmail}\}$, we are claiming a causal mechanism in the domain: a student's identity *causes* them to have a specific email. But here's the twist—the FD formalism deliberately omits the reverse arrow even when it might exist in a particular instance. This is not a bug; it's a feature. By encoding only the dependencies guaranteed by the domain rules, we create a schema that is robust to *counterfactual* scenarios: what if two different students happened to share an email? The schema must not collapse under that possibility. Normalization, then, is the discipline of designing causal graphs where every non-key effect has exactly one key cause—no confounding, no chains of intermediaries. This framing will pay dividends when we reach transitive dependencies in 3NF.

### 1.5 Intuition

Consider a university database. We know that a given `StudentID` always belongs to exactly one `StudentName`. Whenever two rows share the same `StudentID`, they must share the same `StudentName`. This is not a coincidence—it is a rule enforced by the real world. We capture such rules as **functional dependencies (FDs)**.

### 1.6 Formal Definition

Let $X$ and $Y$ be sets of attributes in a relation schema $R$. A **functional dependency** $X \rightarrow Y$ holds if, for every possible instance of $R$, whenever two tuples agree on all attributes in $X$, they also agree on all attributes in $Y$.

Think of $X \rightarrow Y$ as: "Given a value for $X$, you can look up exactly one value for $Y$."

### 1.7 Worked Example: Spotting an FD

Consider this `ENROLLMENT` table:

| StudentID | CourseID | Grade | StudentEmail     |
|-----------|----------|-------|------------------|
| S1        | C101     | A     | s1@univ.edu      |
| S1        | C102     | B     | s1@univ.edu      |
| S2        | C101     | A     | s2@univ.edu      |

- **FD1:** $\{\text{StudentID}\} \rightarrow \{\text{StudentEmail}\}$ holds. Every time S1 appears, the email is identical. S2 confirms it.
- **FD2:** $\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Grade}\}$ holds. The combination determines exactly one grade.
- **Does** $\{\text{CourseID}\} \rightarrow \{\text{Grade}\}$ hold? No—C101 appears with both A and B.

**Try this yourself:** Before reading on, scan the table and ask: does $\{\text{StudentEmail}\} \rightarrow \{\text{StudentID}\}$ hold? If two rows share the same email, must they share the same StudentID? (In this tiny instance, yes—but can you imagine a realistic scenario where it fails? That's the difference between an FD that holds in this instance and one that holds by the rules of the domain.)

### 1.8 Keys Revisited Through the Lens of FDs

- A **superkey** $SK$ satisfies $SK \rightarrow R$ (all attributes).
- A **candidate key** $K$ is a superkey such that no proper subset $K' \subset K$ satisfies $K' \rightarrow R$.

A **prime attribute** belongs to at least one candidate key. A **nonprime attribute** belongs to no candidate key.

> **Quick Check 1:** In `ENROLLMENT`, what is a candidate key? Which attributes are prime, which are nonprime?
>
> *(Answer: $\{\text{StudentID}, \text{CourseID}\}$ is the only minimal superkey. Both are prime. `Grade` and `StudentEmail` are nonprime.)*

---

## 2. First Normal Form (1NF): The Starting Line

### 2.1 Why It Matters

The relational model assumes that every cell holds exactly one atomic value—no lists, no nested tables. If a column contains a set of values, we cannot write a simple FD about it, and we cannot index it or join on it reliably. 1NF is the baseline that makes all further normalization possible.

Think of it this way: a table not in 1NF is like a book where some "words" are actually whole paragraphs stuffed into a single character slot. You can't alphabetize it, you can't search it, and you certainly can't reason about what determines what.

### 2.2 An Unexpected Analogy: Normalization as Data Compression

Here is a perspective a standard textbook will not give you: normalization is lossless data compression applied to logical schemas. In signal processing, we compress by removing redundancy—storing each distinct waveform once and referencing it. In database design, we compress by removing redundancy—storing each distinct fact once and referencing it via foreign keys. 1NF is the sampling step: before you can compress a signal, you must digitize it into discrete samples. Before you can normalize a schema, you must atomize it into discrete cells. The higher normal forms are the compression algorithms: 2NF removes partial redundancies (like run-length encoding), 3NF removes transitive redundancies (like dictionary coding), and BCNF removes the last remaining inter-key redundancies (like predictive coding that exploits correlations between keys). The losslessness guarantee—that we can reconstruct the original table exactly through joins—is the database equivalent of a perfect reconstruction filter.

### 2.3 A Biological Lens: 1NF as Cellular Organization

Consider another cross-domain insight: the jump from non-1NF to 1NF mirrors the evolutionary transition from prokaryotic to eukaryotic cells. A prokaryotic cell packs multiple functions into a single, undifferentiated compartment—metabolic pathways intermingle, genetic material floats freely, and one "cell" does everything. This works, but it creates dependencies that are impossible to disentangle. The eukaryotic cell, by contrast, compartmentalizes: the nucleus holds DNA, mitochondria handle energy production, the endoplasmic reticulum manages protein synthesis. Each compartment has one atomic responsibility. 1NF performs exactly this compartmentalization on your data: it insists that each attribute holds one atomic value, separating concerns so that higher normal forms can then assign each fact to its proper "organelle" relation. A non-1NF table with nested lists is the prokaryote of database design—functional, but impossible to reason about modularly.

### 2.4 A Fresh Cross-Domain Perspective: 1NF as Quantum State Collapse

Here is an innovation that connects database theory to quantum mechanics. A non-1NF attribute containing a set of values—like `Projects: {P1, P2}`—exists in a superposition of states. From the perspective of relational operators, that cell simultaneously "is" P1 and "is" P2, yet you cannot query it as either without first collapsing the superposition. Writing `WHERE Projects = 'P1'` fails because the cell doesn't equal 'P1'; it equals the set {P1, P2}. The act of normalization to 1NF is measurement: it forces each tuple to commit to exactly one project, collapsing the multivalued attribute into a series of definite, queryable states. Just as you cannot extract information from a quantum system without collapsing its wavefunction, you cannot query a non-atomic attribute without first flattening it. 1NF is the measurement postulate of database theory—it transforms potential into actual, making the data accessible to all downstream operators.

### 2.5 Definition

A relation schema $R$ is in **First Normal Form (1NF)** if the domain of every attribute is atomic, and each tuple contains exactly one value from that domain per attribute.

### 2.6 Worked Example: Flattening a Multivalued Attribute

**Before (not 1NF):**

| EmpID | Name  | Projects    |
|-------|-------|-------------|
| 101   | Alice | {P1, P2}   |
| 102   | Bob   | {P3}        |

`Projects` is a set—not atomic.

**After (1NF, one row per project):**

| EmpID | Name  | Project |
|-------|-------|---------|
| 101   | Alice | P1      |
| 101   | Alice | P2      |
| 102   | Bob   | P3      |

Now every cell is single-valued. We have introduced redundancy (`Name` repeats for Alice), but that is exactly what higher normal forms will eliminate.

### 2.7 Common Misconception

"1NF means no duplicate rows." That is false. 1NF concerns the atomicity of attribute values, not uniqueness of tuples. Uniqueness is guaranteed by keys, not by 1NF.

> **Quick Check 2:** Is a table with a JSON blob in a text column in 1NF?
>
> *(Answer: Technically the column holds a single string, so the relational model may consider it atomic. But the values inside are not accessible to standard relational operators without parsing—this is a design smell, not a 1NF violation per se.)*

---

## 3. Second Normal Form (2NF): Eliminating Partial Dependencies

### 3.1 The Problem 2NF Solves

Imagine a table tracking which employee works on which project, and for how many hours. The key is composite: $\{\text{EmpID}, \text{ProjectID}\}$. But suppose we also store `EmpName` and `ProjectBudget`. `EmpName` depends only on `EmpID`—a part of the key. `ProjectBudget` depends only on `ProjectID`—another part. These are **partial dependencies**.

**Consequence:** If Alice changes her name, we must update every row where she appears. If we delete the last row linking an employee to a project, we lose the employee's name entirely. These are update and deletion anomalies.

Here is the tension: the table is trying to do two jobs at once. It records both "who is this employee?" and "who works on what project?" The composite key is perfect for the second job, but the first job only needs half the key. 2NF resolves this by splitting those responsibilities into separate relations.

### 3.2 A Cross-Domain Connection: Partial Dependencies as Overfitting in Machine Learning

Let's draw an insight from machine learning. When you train a model on high-dimensional data, you risk overfitting: the model learns patterns that are true only for specific feature combinations in the training set, rather than generalizable rules. A partial dependency is the database equivalent of an overfit model. The attribute `EmpName` is "learned" from the full composite key $\{\text{EmpID}, \text{ProjectID}\}$, but it actually only needs the simpler feature $\{\text{EmpID}\}$. Storing `EmpName` in a table keyed by both attributes is like training a classifier that memorizes every training example instead of extracting the underlying decision boundary—it works on the data you have, but it fails catastrophically when anything changes. 2NF decomposition is regularization: it forces each non-key attribute to depend on the simplest possible key, preventing the schema from "memorizing" spurious associations.

### 3.3 An Innovation: Partial Dependencies as Music Sampling Without Attribution

Here is a cross-domain connection that makes partial dependencies visceral. In music production, sampling is the practice of taking a portion of an existing recording and incorporating it into a new track. When done properly—with attribution and clearance—the sample's origin is tracked, and royalties flow back to the original artist. When done improperly, the sample's origin is obscured; if the original recording is later remastered or corrected, the derivative track retains the old, flawed version. A partial dependency is exactly an uncleared sample: `EmpName` is sampled from the `EmpID` dimension, but it's stored in a table whose primary key includes `ProjectID`—a dimension that has nothing to do with employee identity. The original "artist" (the `EMPLOYEE` relation) loses control over its own data. 2NF decomposition is proper sample clearance: it extracts `EmpName` back into the `EMPLOYEE` relation where it belongs, leaving only a foreign key reference in the `WORKS_ON` relation. Now when the employee's name changes, the correction propagates automatically—no stale samples remain.

### 3.4 Full Functional Dependency (Prerequisite Concept)

An FD $X \rightarrow Y$ is **full** if no proper subset $X' \subset X$ satisfies $X' \rightarrow Y$. Otherwise, it is **partial**.

### 3.5 Definition of 2NF

A relation schema $R$ is in **Second Normal Form (2NF)** if:
1.  It is in 1NF, and
2.  Every nonprime attribute is fully functionally dependent on every candidate key.

### 3.6 Worked Example: Decomposing to 2NF

Consider `EMP_PROJ` with attributes $\{\text{EmpID}, \text{ProjectID}, \text{EmpName}, \text{ProjectBudget}, \text{HoursWorked}\}$ and candidate key $\{\text{EmpID}, \text{ProjectID}\}$.

Given FDs:
- $\{\text{EmpID}\} \rightarrow \{\text{EmpName}\}$
- $\{\text{ProjectID}\} \rightarrow \{\text{ProjectBudget}\}$
- $\{\text{EmpID}, \text{ProjectID}\} \rightarrow \{\text{HoursWorked}\}$

**Step 1: Identify violations.** `EmpName` is nonprime and depends on $\{\text{EmpID}\}$ alone—a proper subset of the key. `ProjectBudget` is nonprime and depends on $\{\text{ProjectID}\}$ alone. Both are partial dependencies.

**Step 2: Decompose.** Create a new relation for each partial dependency, plus a relation for the fully dependent remainder:

- $R_1(\text{EmpID}, \text{EmpName})$ with candidate key $\{\text{EmpID}\}$
- $R_2(\text{ProjectID}, \text{ProjectBudget})$ with candidate key $\{\text{ProjectID}\}$
- $R_3(\text{EmpID}, \text{ProjectID}, \text{HoursWorked})$ with candidate key $\{\text{EmpID}, \text{ProjectID}\}$

Now every nonprime attribute in each relation depends on the whole key. Update Alice's name once in $R_1$; all references stay consistent.

**Try this yourself:** Before moving to 3NF, ask: in $R_2$, does `ProjectBudget` depend on `ProjectID` alone? Yes—that's the key. But what if each project has a `DepartmentID`, and each department has a fixed budget allocation? Then `ProjectBudget` might depend on `ProjectID` only transitively, through `DepartmentID`. That's exactly the 3NF violation we tackle next.

### 3.7 Common Misconception

"If a table has a single-attribute primary key, it is automatically in 2NF." This is true only because a single-attribute key has no proper subsets to cause partial dependencies. But 2NF is not automatic—you must still verify that no nonprime attribute depends on a subset of a different candidate key when multiple candidate keys exist.

> **Quick Check 3:** In $R_3$ above, is `HoursWorked` fully dependent on the key?
>
> *(Answer: Yes—no FD tells us `HoursWorked` from `EmpID` alone or `ProjectID` alone. It requires the pair.)*

---

## 4. Third Normal Form (3NF): Eliminating Transitive Dependencies

### 4.1 The Problem 3NF Solves

Even after 2NF, a nonprime attribute can still hold a hidden dependency chain. Consider a table `EMPLOYEE_DEPT` with attributes $\{\text{EmpID}, \text{EmpName}, \text{DeptID}, \text{DeptName}, \text{DeptBuilding}\}$. The candidate key is $\{\text{EmpID}\}$. We have:

- $\{\text{EmpID}\} \rightarrow \{\text{EmpName}, \text{DeptID}\}$ — full on the key, so 2NF is satisfied.
- $\{\text{DeptID}\} \rightarrow \{\text{DeptName}, \text{DeptBuilding}\}$ — a dependency between nonprime attributes.

Now `DeptName` and `DeptBuilding` depend on `EmpID` only because `EmpID` determines `DeptID`, and `DeptID` determines them. This is a **transitive dependency**: the key determines a nonprime attribute