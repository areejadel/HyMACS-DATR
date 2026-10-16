# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** – State the definitions of 1NF, 2NF, 3NF, and BCNF.
2. **Understand** – Explain the type of redundancy anomaly each normal form prevents, and trace how an insertion, update, or deletion anomaly arises from a specific functional dependency violation.
3. **Apply** – Given a relation and a set of functional dependencies, determine the highest normal form the relation satisfies.
4. **Analyze** – Identify the precise functional dependency that violates a normal form and predict the resulting data anomalies.
5. **Create** – Perform a lossless decomposition to bring a schema into 3NF or BCNF using the standard synthesis and decomposition algorithms.

---

## 0. Prerequisites

We build on three concepts from earlier lectures. If any feel unclear, pause and review them now.

- **Relation schema** – A named set of attributes. A *relation instance* is a table of tuples conforming to that schema.
- **Superkey** – A set of attributes whose values uniquely identify each tuple in every possible instance of the relation. Formally, if $SK$ is a superkey of $R$, then the functional dependency $SK \rightarrow R$ holds.
- **Candidate key** – A minimal superkey: no proper subset of a candidate key is itself a superkey.

We also use two classifications of attributes:

- **Prime attribute:** An attribute that belongs to at least one candidate key of $R$.
- **Nonprime attribute:** An attribute that belongs to no candidate key of $R$.

---

## 1. The Engine of Normalization: Functional Dependencies

### 1.1 Why This Matters

Here is a puzzle that has cost real organizations millions of dollars in data corruption: you design a database that works perfectly for months. Then one day, a routine update—changing a single phone number—requires modifying ten thousand rows. The update takes so long it locks the table, your application goes down, and when it recovers, half the rows have the new number and half have the old one. The database is now lying to you.

What went wrong? The schema stored the same fact—"this department has this phone number"—in thousands of places. When a fact lives in multiple places, updates create contradictions. When a fact can only be stored if some other fact also exists, you cannot record it independently. These are not bugs in your application code. They are structural defects in your schema design.

**Example 1 — Healthcare.** A table `PATIENT_VISIT` stores `VisitID`, `PatientID`, `PatientName`, `WardID`, and `WardPhone`. When a ward's phone number changes, staff must update every row for every patient ever admitted to that ward. If a new ward is built but has not yet admitted patients, there is nowhere to store its phone number. The schema has confused "a patient visit" with "a ward's properties."

**Example 2 — Logistics.** A shipping table tracks `ShipmentID`, `TruckID`, `DriverName`, and `TruckCapacity`. The driver's name depends only on the truck (each truck has a dedicated driver), not on the shipment. Deleting the last shipment for a truck loses the driver assignment entirely. The schema has confused "a shipment" with "a truck's crew assignment."

**Example 3 — Education.** A table `COURSE_REGISTRATION` stores `StudentID`, `CourseID`, `InstructorName`, and `InstructorOffice`. The instructor's office depends only on the instructor, not on the student-course pair. If an instructor moves offices, we must update every row for every student in every course that instructor teaches. If the instructor takes a sabbatical and teaches no courses, we lose their office assignment. The schema has confused "a registration" with "an instructor's location."

In every case, the schema conflates distinct real-world entities into a single table. The tool that exposes these conflation errors with mathematical precision is the **functional dependency**.

### 1.2 Intuition

Think of a functional dependency as a deterministic function in code: given an input $X$, the function returns exactly one output $Y$. If you call `getStudentName("S1")` twice, you expect the same answer both times—not because the current data happens to agree, but because the domain rule says a student has one name.

This is why functional dependencies are not discovered by inspecting data; they are discovered by understanding the domain. A snapshot of your database might show every employee with a unique last name today, but that does not make `LastName → EmployeeID` a functional dependency. Tomorrow you could hire a second Smith.

**Analogy — Hash Functions vs. Domain Rules.** A hash function maps arbitrarily many inputs to one output deterministically. A functional dependency $X \rightarrow Y$ is similar: many different $X$ values could map to the same $Y$, but each $X$ maps to at most one $Y$. The critical difference is that a hash function's mapping is algorithmic; a functional dependency's mapping is a constraint imposed by the real world. You cannot change a hash function's output without changing its code. You cannot change a functional dependency without changing the business rules of the organization.

### 1.3 Formal Definition

Let $X$ and $Y$ be sets of attributes in a relation schema $R$. A **functional dependency (FD)** $X \rightarrow Y$ holds if, for every possible legal instance of $R$, whenever two tuples agree on all attributes in $X$, they must also agree on all attributes in $Y$.

The phrase "every possible legal instance" is critical. An FD is a constraint on the schema, not a statement about the current data. We cannot infer an FD merely by inspecting a snapshot; we must know the business rules of the domain.

**Cross-domain insight — FDs as type signatures.** In programming language theory, a function type `X → Y` declares that given an argument of type `X`, the function returns a value of type `Y`. A functional dependency `X → Y` in a database makes the same declaration: given a value for `X`, you can determine at most one value for `Y`. The difference is that the database does not implement this as executable code; it enforces it as an integrity constraint that the DBMS can check and use for optimization. This is why normalization is, in a deep sense, type-checking your schema against the domain rules.

### 1.4 Worked Example: Spotting an FD

Consider this `ENROLLMENT` instance:

| StudentID | CourseID | Grade | StudentEmail     |
|-----------|----------|-------|------------------|
| S1        | C101     | A     | s1@univ.edu      |
| S1        | C102     | B     | s1@univ.edu      |
| S2        | C101     | A     | s2@univ.edu      |

We examine each candidate FD:

- **FD1:** $\{\text{StudentID}\} \rightarrow \{\text{StudentEmail}\}$. In this instance, S1 always maps to `s1@univ.edu`, S2 to `s2@univ.edu`. As a domain rule, a student has exactly one university email. **This FD holds.**

- **FD2:** $\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Grade}\}$. A student receives one grade per course. **This FD holds.**

- **FD3:** $\{\text{CourseID}\} \rightarrow \{\text{Grade}\}$. C101 appears with both A and B. **This FD does not hold.**

- **FD4:** $\{\text{StudentEmail}\} \rightarrow \{\text{StudentID}\}$. In this instance, each email maps to exactly one `StudentID`. However, consider a student who shares an email address with a family member also enrolled. The FD would then fail as a universal constraint. We must decide based on domain rules, not just the current data.

**Try this yourself:** In the `ENROLLMENT` table above, what is a candidate key? Which attributes are prime, and which are nonprime?

*(Answer: $\{\text{StudentID}, \text{CourseID}\}$ is the only minimal superkey. Both attributes are prime. `Grade` and `StudentEmail` are nonprime.)*

### 1.5 Keys Revisited Through the Lens of FDs

- A **superkey** $SK$ satisfies $SK \rightarrow R$ (all attributes of $R$).
- A **candidate key** $K$ is a superkey such that no proper subset $K' \subset K$ satisfies $K' \rightarrow R$.

### 1.6 Computing Attribute Closure

Given a set $F$ of FDs, we often need to determine whether an attribute set $X$ is a superkey. We compute the **attribute closure** $X^+$: the set of all attributes functionally determined by $X$ under $F$.

**Algorithm for $X^+$:**
1. Start with $X^+ = X$.
2. Repeatedly: if there is an FD $Y \rightarrow Z$ in $F$ such that $Y \subseteq X^+$, then add $Z$ to $X^+$.
3. Stop when no more attributes can be added.

If $X^+ = R$, then $X$ is a superkey.

**Worked Example:** Let $R$ have attributes $\{A, B, C, D, E\}$ and FDs:
- $A \rightarrow B$
- $B \rightarrow C$
- $\{A, D\} \rightarrow E$

Compute $\{A, D\}^+$:
1. Start: $X^+ = \{A, D\}$
2. Using $A \rightarrow B$: add $B$ → $X^+ = \{A, D, B\}$
3. Using $B \rightarrow C$ (since $B \subseteq X^+$): add $C$ → $X^+ = \{A, D, B, C\}$
4. Using $\{A, D\} \rightarrow E$: add $E$ → $X^+ = \{A, D, B, C, E\}$
5. $X^+ = R$, so $\{A, D\}$ is a superkey.

**Try this yourself:** In the same relation, compute $\{A\}^+$. Is $\{A\}$ a superkey?

*(Answer: $\{A\}^+ = \{A, B, C\}$. Not all attributes, so $\{A\}$ is not a superkey.)*

---

## 2. First Normal Form (1NF)

### 2.1 Why It Matters

The relational model rests on a deceptively simple foundation: every cell holds exactly one atomic value—no lists, no nested tables, no repeating groups. This is not an arbitrary restriction. If a column contains a set of values, you cannot write a simple functional dependency about its individual elements, you cannot index it, and you cannot join on it reliably. 1NF is the baseline that makes all further normalization possible.

Imagine trying to sort a library where some books have multiple call numbers written on a single spine label, separated by commas. Finding all books in the 500s requires reading every label and parsing strings. You have abandoned the structure that makes a library navigable. That is what a non-1NF database does to your queries.

### 2.2 Definition

A relation schema $R$ is in **First Normal Form (1NF)** if the domain of every attribute consists of atomic (indivisible) values, and each tuple contains exactly one value from that domain per attribute.

The notion of "atomic" is relative to the operations the DBMS supports. A value is non-atomic if the application routinely needs to access its internal components. A JSON string is technically a single value, but if you constantly extract fields from it, your schema is not truly in 1NF with respect to how you use it.

### 2.3 Worked Example: Flattening a Multivalued Attribute

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

Now every cell is single-valued. The redundancy introduced (`Name` repeats for Alice) is exactly what higher normal forms will eliminate. Notice the pattern: achieving 1NF often creates the redundancy that 2NF and 3NF then resolve.

### 2.4 Worked Example: Healthcare

A `PATIENT_ALLERGY` table stores `PatientID` and `Allergies`, where `Allergies` is a comma-separated list such as "penicillin, sulfa, latex".

This violates 1NF. To find all patients allergic to penicillin, a query must perform a substring search—slow, error-prone, and incapable of using an index. Worse, "penicillin" might be misspelled as "penicilin" in one row, creating a silent failure where a patient's allergy is missed.

The 1NF decomposition yields:

| PatientID | Allergy    |
|-----------|------------|
| P001      | penicillin |
| P001      | sulfa      |
| P001      | latex      |

Now `Allergy` is atomic, indexable, and can participate in joins with an `ALLERGY` reference table that enforces a controlled vocabulary.

### 2.5 Worked Example: E-Commerce

An `ORDER` table stores `OrderID`, `CustomerID`, and `ProductIDs` as a JSON array `["P101", "P205", "P330"]`.

This violates 1NF. To find all orders containing product P205, we must use JSON extraction functions. Joining with a `PRODUCT` table to get product names requires unnesting the array. Indexing on individual product IDs is impossible, so every such query becomes a full table scan.

The 1NF decomposition yields:

| OrderID | CustomerID | ProductID |
|---------|------------|-----------|
| 1001    | C42        | P101      |
| 1001    | C42        | P205      |
| 1001    | C42        | P330      |

Now `ProductID` is a proper atomic attribute that can be indexed and joined.

**Cross-domain insight — Normalization as parsing.** Converting a comma-separated list to separate rows is structurally identical to tokenizing a string in a compiler. The non-1NF table is like source code before lexical analysis: a flat string that obscures its internal structure. Normalization performs the same decomposition that a lexer does: it breaks compound structures into atomic tokens that subsequent stages (higher normal forms, query optimization) can reason about precisely.

### 2.6 Common Misconception

"1NF means no duplicate rows." This is false. 1NF concerns the atomicity of attribute values, not uniqueness of tuples. Uniqueness is guaranteed by keys, not by 1NF. A relation in 1NF can contain identical rows (though it should not, because a proper key prevents that).

**Try this yourself:** Is a table with a JSON blob in a text column in 1NF?

*(Answer: Technically the column holds a single string, so the relational model may consider it atomic. But if queries routinely extract fields from the JSON using application code or special functions, then the value is not atomic relative to the operations performed on it. This is a design smell indicating that the schema should likely be further normalized into separate attributes.)*

---

## 3. Second Normal Form (2NF)

### 3.1 The Problem 2NF Solves

Consider a manufacturing database: `PART_SUPPLIER` with attributes:

| PartID | SupplierID | PartName | SupplierCity | Price |
|--------|------------|----------|--------------|-------|
| P1     | S1         | Bolt     | Detroit      | 2.50  |
| P1     | S2         | Bolt     | Chicago      | 2.75  |
| P2     | S1         | Nut      | Detroit      | 1.80  |

The candidate key is $\{\text{PartID}, \text{SupplierID}\}$: a part can come from multiple suppliers, and a supplier provides multiple parts.

Here is the tension: the table appears to store information about parts, suppliers, and pricing—three distinct facts bundled into one structure. `PartName` ("Bolt") depends only on `PartID`, not on the full key. `SupplierCity` depends only on `SupplierID`. These are **partial dependencies**: nonprime attributes depending on a proper subset of a candidate key. The table is trying to serve three masters and failing each one.

The anomalies:
- **Update anomaly:** If "Bolt" is renamed to "Hex Bolt," we must update every row where `PartID = P1` across all suppliers. Miss one row and the database now claims the part has two different names.
- **Deletion anomaly:** If we delete the last row linking a supplier to a part, we lose the supplier's city entirely. The supplier has not ceased to exist; we have simply lost the ability to record their location.
- **Insertion anomaly:** We cannot add a new supplier with their city until they supply at least one part. The database forces a relationship that does not exist in the real world.

**Analogy — A notebook with three sections glued together.** Imagine a notebook where each page has three sections: a part description, a supplier directory entry, and a pricing agreement, all sharing the same physical page. To change a supplier's city, you must find every page where that supplier appears and correct it. To add a new supplier who has not yet quoted a price, you must leave the part and price sections blank—but the notebook's format requires all three sections to be filled. The notebook's physical structure has entangled independent facts. 2NF separates them into distinct notebooks, each tracking one kind of fact.

### 3.2 Full Functional Dependency (Prerequisite Concept)

An FD $X \rightarrow Y$ is **full** (or $Y$ is fully functionally dependent on $X$) if no proper subset $X' \subset X$ satisfies $X' \rightarrow Y$. Otherwise, the dependency is **partial**.

Formally: $X \rightarrow Y$ is full if for every $X' \subset X$, $X' \not\rightarrow Y$.

**Example:** In `PART_SUPPLIER`:
- $\{\text{PartID}, \text{SupplierID}\} \rightarrow \{\text{Price}\}$ is **full**: you need both to determine the price. A price is not a property of a part alone, nor of a supplier alone—it is a property of their relationship.
- $\{\text{PartID}, \text{SupplierID}\} \rightarrow \{\text{PartName}\}$ is **partial**: $\{\text{PartID}\}$ alone determines `PartName`. The supplier is irrelevant to what the part is called.

### 3.3 Definition of 2NF

A relation schema $R$ is in **Second Normal Form (2NF)** if:
1. It is in 1NF, and
2. Every nonprime attribute is fully functionally dependent on **every** candidate key of $R$.

Note the quantifier: *every* candidate key. If $R$ has multiple candidate keys, a nonprime attribute must be fully dependent on each one. This is a stronger condition than it first appears.

### 3.4 Worked Example: Decomposing to 2NF

Starting from `PART_SUPPLIER` with attributes $\{\text{PartID}, \text{SupplierID}, \text{PartName}, \text{SupplierCity}, \text{Price}\}$ and candidate key $\{\text{PartID}, \text{SupplierID}\}$.

Given FDs:
- $\{\text{PartID}\} \rightarrow \{\text{PartName}\}$
- $\{\text{SupplierID}\} \rightarrow \{\text{SupplierCity}\}$
- $\{\text{PartID}, \text{SupplierID}\} \rightarrow \{\text{Price}\}$

**Step 1: Identify violations.**
- `PartName` is nonprime and depends on $\{\text{PartID}\}$ alone—a proper subset of the key. **Violation.**
- `SupplierCity` is nonprime and depends on $\{\text{SupplierID}\}$ alone. **Violation.**
- `Price` depends on the full key. No violation.

**Step 2: Decompose.** Create a new relation for each partial dependency, plus a relation for