# Normalization Forms and Database Schema Design (1NF–BCNF)

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** — State the definitions of 1NF, 2NF, 3NF, and BCNF and identify the dependency each eliminates.
2. **Understand** — Explain, with concrete examples, the insertion, update, and deletion anomalies caused by violating each normal form, and articulate why those anomalies are structurally inevitable.
3. **Apply** — Given a relation schema and a set of functional dependencies, determine the highest normal form the relation satisfies and identify the exact dependency causing any violation.
4. **Analyze** — Given a real-world scenario and a proposed table design, predict which anomalies will occur and trace them back to specific functional dependencies.
5. **Create** — Perform a lossless decomposition of a relation into 3NF or BCNF using standard algorithms, and verify that the result preserves all original functional dependencies and eliminates the targeted anomalies.

---

## 0. The Paradox That Drives Everything

Here is a puzzle that has destroyed real production databases:

You design one table to hold everything about your customers and their orders. It works perfectly for six months. Then a customer changes their phone number, and your UPDATE statement touches 14,000 rows. It runs for 47 seconds during peak traffic. Three orders ship to the wrong address because a concurrent transaction read stale data. Your database has no bugs, no hardware failures, and no malicious actors. Yet it corrupted data.

**The paradox:** A design that is *logically complete* — it stores all the facts you need — can be *structurally dangerous*. The danger is not in what you store, but in *how many independent facts you force into each row*.

Normalization is the systematic method for resolving this paradox. It is not about "clean design" or academic purity. It is about designing schemas where a single fact lives in exactly one place, so updating that fact requires exactly one write, and no fact's existence depends on the presence of an unrelated fact.

**The core insight, stated early:** Every normal form from 1NF through BCNF answers the same question: "Given this set of functional dependencies, where should each attribute live so that it depends on the key, the whole key, and nothing but the key?" The normal forms are just increasingly strict interpretations of "nothing but the key."

---

## 0. Prerequisites and Warm-Up

Normalization builds on three foundational concepts. Review them now—every section ahead depends on them.

### 0.1 Essential Concepts

- **Relation schema** — A named set of attributes \(R(A_1, A_2, \dots, A_n)\). It defines the blueprint for a table: columns and their domains. A *relation instance* \(r(R)\) is the actual data—a set of tuples conforming to that blueprint.

- **Superkey** — A set of attributes \(SK \subseteq R\) such that, in any valid instance, no two distinct tuples have identical values for all attributes in \(SK\). We write \(SK \rightarrow R\): "\(SK\) functionally determines all attributes of \(R\)." A superkey guarantees uniqueness.

- **Candidate key** — A minimal superkey. Remove any attribute from a candidate key, and the remainder is no longer a superkey. A relation may have multiple candidate keys; one is designated the *primary key*.

**Intuition:** In a university database, `StudentID` is a candidate key for `STUDENT` because it uniquely identifies each student, and no smaller piece of it (e.g., the first three digits) can do the same. `Email` might also be a candidate key if uniqueness is guaranteed. Both are candidate keys; we pick one as primary.

### 0.2 Warm-Up Exercise

Consider `STUDENT(StudentID, NationalID, Name, Email)`. Both `StudentID` and `NationalID` uniquely identify each student.

**Question:** Is `{StudentID, Name}` a candidate key? Why or why not?

*Think before reading on. What two properties must a candidate key satisfy?*

**Answer:** No. It is a superkey because the pair determines all attributes—if you know both, you can look up everything else. But it is not *minimal*: we can remove `Name` and still have `{StudentID}`, which is itself a superkey. Since a proper subset is also a superkey, `{StudentID, Name}` fails the minimality test. It is a superkey, but not a candidate key.

> **Quick Check 0:** In `BOOK(ISBN, Title, Edition, PublisherID)`, suppose `ISBN` alone uniquely identifies each book, and `{Title, Edition}` also uniquely identifies each book. Is `{ISBN, Title}` a candidate key?
>
> *(Answer: No. `{ISBN}` alone is a superkey, so `{ISBN, Title}` is not minimal. It is a superkey but not a candidate key.)*

---

## 1. The Engine of Normalization: Functional Dependencies

Normalization is the systematic application of one core concept: the **functional dependency**. Master this, and the normal forms become natural consequences.

### 1.1 Why This Matters: Four Scenarios

For each scenario below, diagnose the problem before reading the analysis. What *structural property* of the design makes the problem unavoidable?

**Scenario A: The Online Bookstore.** Orders are recorded in a single table with columns `OrderID`, `CustomerID`, `CustomerName`, `ShippingAddress`, and `BookTitle`. When a loyal customer moves, you must update their address in every order they ever placed. Miss one row, and the next shipment goes to the wrong house. When a new customer registers but has not yet placed an order, you have nowhere to store their name and address—the table demands an `OrderID` and `BookTitle` before accepting any row.

**Scenario B: The Hospital Admissions System.** Each patient admission is recorded with `PatientID`, `PatientName`, `WardID`, `WardName`, `DoctorID`, and `DoctorSpecialty`. If a ward is renamed, you must update dozens of admission rows. If the last patient is discharged from a ward, deleting that row erases the fact that the ward exists and which specialty it serves.

**Scenario C: The Logistics Warehouse.** Inventory is tracked with `WarehouseID`, `WarehouseCity`, `ProductID`, `QuantityOnHand`, and `RegionalManager`. Each warehouse has exactly one regional manager, and each manager oversees warehouses in exactly one city. When a manager is reassigned from Chicago to Detroit, you must update every product row in every Chicago warehouse. If a warehouse temporarily empties, deleting its last inventory row erases the warehouse's city and manager assignment.

**Scenario D: The Manufacturing Bill of Materials.** An automotive parts supplier uses `PartAssembly(PartID, PartName, SubpartID, SubpartName, Quantity, SupplierID, SupplierName)`. A given part (e.g., an engine) is assembled from many subparts (pistons, valves, etc.). `SupplierName` depends only on `SupplierID`, not on the composite key `{PartID, SubpartID}`. If a supplier changes its name, the update must propagate to thousands of rows. If a supplier currently provides no subparts, their name and existence cannot be recorded.

> **Pause and diagnose:** In Scenario A, what structural property makes the address-update problem unavoidable? Articulate it in one sentence before reading on.
>
> *(Answer: `ShippingAddress` depends on `CustomerID` alone, not on the full key `{OrderID, BookTitle}`. The table forces us to store customer facts inside order facts, so changing a customer fact requires finding every order—and new customers with no orders cannot be stored at all.)*

**A unifying analogy: filing cabinets and cross-referenced dossiers.** Imagine a paper-based intelligence agency. Each dossier (row) contains a suspect's name, their known associates, each associate's phone number, and each associate's last known address. When a phone number changes, an analyst must open every dossier where that associate appears and update it by hand. If an associate has no current connection to any suspect, their information exists nowhere—the filing system cannot store "unlinked" individuals. This is exactly the structural problem in Scenarios A–D: you are embedding entity facts (customer, ward, warehouse, supplier) inside event or relationship records (order, admission, inventory, part-assembly). The filing cabinet forces you to store independent facts together, and every anomaly follows inevitably.

> **Try this yourself:** Take Scenario B. On paper, sketch three admission rows for Ward "Cardiology" with WardName "Heart Unit." Now rename the ward to "Cardiovascular Services." Count how many cells you must modify. Now discharge the last patient from Cardiology and delete their row. What ward-related facts vanish? *(You should find: three cells to update; the fact that "Cardiology" exists as a ward, its name, and its specialty all disappear—not because they are false, but because the filing system tied their existence to the presence of patients.)*

These are structural defects in the table design, not bugs in application code. The tool that reveals them is the **functional dependency**.

> **Check Your Understanding (Anomaly Identification):** In Scenario C, which anomaly occurs when a new warehouse is built but has not yet received any inventory? What fact cannot be recorded, and why?
>
> *(Answer: Insertion anomaly. We cannot record the warehouse's city and regional manager because the table requires a `ProductID` and `QuantityOnHand`—the composite key includes `ProductID`, so a row without a product cannot be inserted. The design forces us to store warehouse facts and inventory facts together; we cannot record one without the other.)*

### 1.2 Intuition: What Is a Functional Dependency?

A given `StudentID` always belongs to exactly one `StudentName`. Whenever two rows share the same `StudentID`, they must share the same `StudentName`. This is a rule enforced by the real world, not by the database. We say `StudentID` **functionally determines** `StudentName`, and write:

\[\{\text{StudentID}\} \rightarrow \{\text{StudentName}\}\]

Think of a functional dependency as a deterministic function: `getStudentName(studentID)` always returns the same result for the same input, regardless of what else has changed. The difference is that FDs are *declared constraints*, not executable code—they describe what must be true, and the DBMS (or the designer) enforces them.

**A cross-domain analogy:** Functional dependencies are to databases what conservation laws are to physics. Conservation of energy does not describe what *does* happen in one experiment—it constrains what *can* happen in any valid physical process. Similarly, an FD does not describe your current data snapshot; it constrains all possible valid states of your database. You cannot prove an FD holds by inspecting a single table instance; you must know the governing rules of the domain. Just as a physicist who observes momentum apparently disappearing knows to look for an unmeasured particle, a database designer who sees apparent FD violations knows to look for a missing attribute or a misunderstood business rule.

### 1.3 Formal Definition

Let \(X\) and \(Y\) be sets of attributes in a relation schema \(R\). A **functional dependency (FD)** , written \(X \rightarrow Y\), holds if, for every possible valid instance \(r\) of \(R\), whenever two tuples \(t_1, t_2 \in r\) agree on all attributes in \(X\) (i.e., \(t_1[X] = t_2[X]\)), they also agree on all attributes in \(Y\) (i.e., \(t_1[Y] = t_2[Y]\)).

**Key points:**
- An FD is a constraint on *all possible instances*, not a statement about current data.
- You cannot prove an FD holds by inspecting a single snapshot; you must know the business rules.
- A single counterexample in any valid instance disproves the FD.

### 1.4 Worked Example: Spotting FDs in Data

Consider this `ENROLLMENT` table:

| StudentID | CourseID | Grade | StudentEmail     |
|-----------|----------|-------|------------------|
| S1        | C101     | A     | s1@univ.edu      |
| S1        | C102     | B     | s1@univ.edu      |
| S2        | C101     | A     | s2@univ.edu      |

We examine each proposed FD:

- **FD1:** \(\{\text{StudentID}\} \rightarrow \{\text{StudentEmail}\}\) — Every time S1 appears, the email is `s1@univ.edu`. S2 confirms the pattern. Based on the business rule that each student has exactly one email, this FD holds. The current data is consistent with the FD, but the business rule is what matters.

- **FD2:** \(\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Grade}\}\) — The combination (S1, C101) always gives A; (S1, C102) gives B; (S2, C101) gives A. A student receives exactly one grade per course, so this holds.

- **FD3:** \(\{\text{CourseID}\} \rightarrow \{\text{Grade}\}\) — This fails. Although C101 appears with A in both rows here, different students can receive different grades in the same course. The business rule does not enforce this FD. The current data happens to show a pattern, but the FD is not guaranteed.

> **Check Your Understanding (FD Reasoning):** Does \(\{\text{StudentEmail}\} \rightarrow \{\text{StudentID}\}\) hold? In this instance, yes—each email maps to exactly one StudentID. But consider two siblings sharing a family email address while enrolled in different courses. The FD fails in the real world because the business rule does not guarantee uniqueness of emails unless the university explicitly enforces it. Always reason from business rules, not snapshots.

**A deeper insight — FDs as information compression:** An FD \(X \rightarrow Y\) means that knowing \(X\) is sufficient to determine \(Y\); you do not need to store the \(X \rightarrow Y\) mapping once per row. This is why FDs drive decomposition: if \(Y\) depends only on \(X\), you can store the \((X, Y)\) pairs once in a separate table and replace repeated occurrences with references to \(X\). The storage savings are a side effect; the real win is that updating a single \((X, Y)\) pair now requires exactly one write. Normalization is, at its core, the elimination of redundant representations of the same functional dependency.

### 1.5 Keys Revisited Through the Lens of FDs

Using functional dependencies, we define keys precisely:

- A **superkey** \(SK\) is a set of attributes such that \(SK \rightarrow R\) (the superkey functionally determines all attributes of the relation).
- A **candidate key** \(K\) is a superkey such that no proper subset \(K' \subset K\) satisfies \(K' \rightarrow R\).

We also classify attributes based on their relationship to candidate keys:
- **Prime attribute:** An attribute that belongs to at least one candidate key.
- **Nonprime attribute:** An attribute that belongs to no candidate key.

**Worked Example:** In `ENROLLMENT` above, what are the candidate keys? We know \(\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Grade}, \text{StudentEmail}\}\). Is any subset also a superkey? \(\{\text{StudentID}\}\) determines `StudentEmail` but not `CourseID` or `Grade`. \(\{\text{CourseID}\}\) determines nothing else. Therefore, \(\{\text{StudentID}, \text{CourseID}\}\) is the only candidate key. Both `StudentID` and `CourseID` are prime attributes; `Grade` and `StudentEmail` are nonprime.

> **Quick Check 1:** In `SUPPLY(SupplierID, PartID, Quantity, SupplierCity)` with FDs \(\{\text{SupplierID}\} \rightarrow \{\text{SupplierCity}\}\) and \(\{\text{SupplierID}, \text{PartID}\} \rightarrow \{\text{Quantity}\}\), what is the candidate key? Which attributes are prime?
>
> *(Answer: The candidate key is \(\{\text{SupplierID}, \text{PartID}\}\). Both are prime. `Quantity` and `SupplierCity` are nonprime. `SupplierCity` is nonprime because it does not belong to the candidate key—it depends on part of the key, which will become important in 2NF.)*

---

## 2. First Normal Form (1NF): The Starting Line

### 2.1 Why It Matters

The relational model assumes that every cell holds exactly one atomic value—no lists, no sets, no nested tables. If a column contains a collection, we cannot write a simple functional dependency about it, nor can we index it or join on it reliably. 1NF is the baseline that makes all further normalization possible.

**An analogy from graph theory:** A relation in 1NF is like a simple graph where each edge connects exactly two vertices. A non-1NF table with multivalued attributes is like a hypergraph, where a single edge can connect many vertices simultaneously. Hypergraphs are more expressive, but nearly all graph algorithms assume simple edges. Similarly, the relational algebra assumes atomic values. Normalization converts the hypergraph into an equivalent simple graph that our tools can process.

### 2.2 Definition

A relation schema \(R\) is in **First Normal Form (1NF)** if the domain of every attribute is atomic, and each tuple contains exactly one value from that domain per attribute. "Atomic" means the value is indivisible from the perspective of the relational model—it cannot be decomposed into smaller meaningful parts that the database can manipulate independently using standard relational operators (selection, projection, join, etc.).

### 2.3 Worked Example: Flattening a Multivalued Attribute

**Before (not in 1NF):**

| EmpID | Name  | Projects    |
|-------|-------|-------------|
| 101   | Alice | {P1, P2}   |
| 102   | Bob   | {P3}        |

The `Projects` column contains sets of values. We cannot write a simple SQL query to ask "which employees work on P1?" without parsing the set. We cannot create a foreign key from `Projects` to a `PROJECT` table. The value is not atomic from the relational perspective.

**After (in 1NF, one row per project assignment):**

| EmpID | Name  | Project |
|-------|-------|---------|
| 101   | Alice | P1      |
| 101   | Alice | P2      |
| 102   | Bob   | P3      |

Every cell now holds a single value. We have introduced redundancy—`Name` repeats for Alice—but higher normal forms will eliminate that. The new candidate key is \(\{\text{EmpID}, \text{Project}\}\), because an employee can work on multiple projects, and a project can have multiple employees, but the combination is unique.

### 2.4 Common Misconception

**"1NF means no duplicate rows."** This is false. 1NF concerns the atomicity of attribute values, not uniqueness of tuples. Uniqueness is guaranteed by keys (a separate concept), not by 1NF. A table can be in 1NF and still have duplicate rows—though we would typically define a key to prevent that.

> **Quick Check 2:** Is a table with a JSON blob stored in a text column in 1NF?
>
> *(Answer: Technically, the column holds a single string value, so the relational model may consider it atomic. However, the values inside the JSON are not accessible to standard relational operators without parsing. Most practitioners treat such columns as violating the spirit of 1NF because they hide structure that should be normalized into separate attributes or relations. The relational model cannot enforce FDs on fields inside the JSON blob.)*

**A practical litmus test for atomicity:** Can you write a WHERE clause that filters rows based on a sub-value inside the column, using only standard SQL operators (no JSON-extraction functions)? If not, the column is not atomic in the relational sense. The `Projects` set fails this test; a properly decomposed `Project` column passes it.

---

## 3. Second Normal Form (2NF): Eliminating Partial Dependencies

### 3.1 The Problem 2NF Solves

Consider `EMP_PROJ` with attributes `EmpID`, `ProjectID`, `HoursWorked`, `EmpName`, and `ProjectBudget`. The key is composite: \(\{\text{EmpID}, \text{ProjectID}\}\). Each row represents the fact that a specific employee works on a specific project for a certain number of hours.

Now observe the dependencies:
- `EmpName` depends only on `EmpID`—a *part* of the key. If