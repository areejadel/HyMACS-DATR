## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember** the definitions of 1NF, 2NF, 3NF, and BCNF, including what each prohibits regarding functional dependencies.
2.  **Understand** why partial and transitive dependencies cause update, insertion, and deletion anomalies, and distinguish between a candidate key and a superkey.
3.  **Apply** a systematic normalization process to decompose an unnormalized relation through successive normal forms up to BCNF, identifying all functional dependencies, candidate keys, and violations at each step.
4.  **Analyze** a given relational schema to determine its current normal form and identify the functional dependency responsible for any violation.
5.  **Evaluate** the trade-offs between full normalization and intentional denormalization, and explain the role of lossless-join and dependency-preservation properties in decomposition decisions.

---

## Opening Challenge: The Database That Forgot a Branch Existed

In 2015, a European bank discovered that 1,200 customer accounts had been silently orphaned. The accounts and their funds existed, but the branch that owned them had been deleted from the system three years earlier. The deletion itself was legitimate—the physical branch had closed. However, when an operator ran `DELETE FROM Branches WHERE BranchID = 247`, the database removed the branch and, through a cascading foreign key, every account associated with it.

The accounts vanished from customer statements, the general ledger, and all reports. The bank discovered the problem only because a customer called to complain about a missing interest payment.

This failure was not a software bug. It was a schema design error—specifically, a normalization error. The schema allowed a fact about accounts (their existence) to depend on a fact about branches (their existence). Deleting the branch fact also deleted the account fact. This is a deletion anomaly.

But here is the unsettling part: the schema probably looked perfectly reasonable to its designers. It likely had a `Branch` table and an `Account` table with a foreign key, a pattern taught in every introductory database course. The error was subtler—it involved a cascade rule that conflated two independent facts. By the time we reach BCNF, you will know how to spot this specific class of error before it reaches production.

**Pause and predict:** Before reading further, sketch a quick schema for a bank with branches and accounts. What foreign key relationships would you create? Under what conditions could deleting a branch delete accounts? Write down your prediction—we will return to it when we reach BCNF.

**Your challenge:** By the end of this lecture, you will be able to examine a schema and predict exactly which operations will cause data loss, inconsistency, or impossible insertions—before any code is written. You will also be able to fix those schemas systematically.

---

## Prerequisites

We assume you are comfortable with:

-   The structure of a relational table: attributes (columns), tuples (rows), and domains (data types).
-   The concept of a **primary key** and the uniqueness constraint it enforces.
-   The notion of a **functional dependency** (FD), written \(X \rightarrow Y\), meaning: if two tuples agree on the attributes in \(X\), they must also agree on the attributes in \(Y\).
-   The terms **superkey** (any set of attributes that uniquely identifies a tuple) and **candidate key** (a minimal superkey).
-   The **closure** of a set of functional dependencies, denoted \(F^+\), which is the set of all FDs logically implied by a given set \(F\).
-   **Armstrong's axioms** for reasoning about FDs:
    -   **Reflexivity:** If \(Y \subseteq X\), then \(X \rightarrow Y\).
    -   **Augmentation:** If \(X \rightarrow Y\), then \(XZ \rightarrow YZ\) for any \(Z\).
    -   **Transitivity:** If \(X \rightarrow Y\) and \(Y \rightarrow Z\), then \(X \rightarrow Z\).

If any of these concepts feel rusty, review them now. We will build directly on these ideas.

**Quick Check 1:** Consider a table with attributes \(A\), \(B\), \(C\) and the FD \(\{A\} \rightarrow \{B, C\}\). Is \(\{A\}\) a superkey? Is it a candidate key?

*Answer: Yes to both. \(\{A\}\) uniquely identifies every other attribute, and it is minimal because it is a single attribute. If a larger set, such as \(\{A, B\}\), were the key, then \(\{A\}\) would be a superkey but not a candidate key.*

---

## 1. Why Normalize?

### 1.1 The Hidden Cost of Redundancy

A mid-sized bank once stored customer accounts and branch information in a single table. One Friday evening, a routine update renamed a branch from "Elm Street" to "Oak Avenue." The SQL `UPDATE` modified 23,417 rows, but the transaction log filled up and rolled back halfway through. By Monday morning, half the accounts at that branch showed "Oak Avenue" and half still showed "Elm Street." The system now believed two different branches served the same set of customers. Reconciling the mess took a team of five engineers an entire weekend.

The root cause was a design decision: storing branch names redundantly across thousands of account rows. The table was in 1NF—every cell was atomic—but the schema silently invited corruption with every update.

Normalization prevents this by arranging data so that every fact lives in exactly one place. When a fact lives in one place, updating it updates it everywhere. When a fact is duplicated, consistency becomes a statistical gamble.

**Analogy — the library catalog card:** Before digital systems, libraries used physical catalog cards. Each book had one master card in the central catalog. Branch libraries held duplicate cards for their local holdings. When a book was reclassified, the central card was updated, but branch cards were often missed. The solution was not better discipline—it was eliminating the duplicates. A union catalog with a single card per book, referenced by every branch, made inconsistency structurally impossible. Normalization does the same for databases: it eliminates the duplicates so that discipline is no longer required.

**Quick Check 2:** If branch names had been stored in a separate `Branch` table with one row per branch, how many rows would the `UPDATE` have touched? What would a rollback have meant in that design?

*Answer: The update would have touched exactly one row. A rollback would have been trivial—the single row would revert to its previous value, and no inconsistency could arise because no other table redundantly stored the branch name.*

### 1.2 A Single-Table Design and Its Anomalies

Consider a database for a small company that tracks employees, their projects, and project locations. A naive first attempt might put everything into one table called `EMPLOYEE_PROJECTS`:

```
EMP_ID | EmpName | ProjID | ProjName | Location | Hours
-------|---------|--------|----------|----------|------
E01    | Smith   | P1     | Alpha    | NYC      | 20
E01    | Smith   | P1     | Alpha    | BOS      | 20
E01    | Smith   | P2     | Beta     | CHI      | 15
E02    | Jones   | P3     | Gamma    | SFO      | 30
```

This design causes three specific anomalies:

-   **Update anomaly:** If project "Alpha" is renamed to "AlphaPlus," we must update every row where `ProjName = 'Alpha'`. Missing one row produces inconsistent data. In healthcare databases, inconsistent patient records due to unnormalized provider information can lead to incorrect treatment histories. In supply chain systems, updating a supplier's address in a non-normalized inventory table can cause purchase orders to be routed to outdated locations if any rows are missed.
-   **Insertion anomaly:** We want to add a new project `P4` named `Delta` with no employees yet assigned. We cannot insert it because `EMP_ID` is part of the key and cannot be null. The database forces us to invent a fake employee just to record a project's existence. In e-commerce platforms, this manifests when a new product category cannot be created until at least one product is assigned to it. In university registration systems, a new course cannot be entered into the catalog until at least one student enrolls.
-   **Deletion anomaly:** If employee `E02` leaves and we delete their only row, we lose all information about project `P3` and its name `Gamma`, even though the project still exists. Deleting a person deletes a project—a fact we never intended to couple. In financial systems, deleting the last transaction for a particular account type could inadvertently destroy the account type definition itself. In healthcare, discharging the last patient assigned to a particular treatment protocol could erase the protocol's existence.

These anomalies are not merely theoretical. They cause data corruption, wasted storage, and application bugs. Normalization eliminates these anomalies by *decomposing* one badly designed table into several well-designed tables.

**Quick Check 3:** Before reading further, predict which anomalies would occur if you tried to (a) change Smith's name to "Smythe," (b) add a new employee with no project assignment, or (c) delete the row where Hours = 30.

*Answer: (a) Update anomaly—Smith's name appears in three rows; missing one leaves inconsistency. (b) Insertion anomaly—a new employee with no project has no valid key value because `ProjID` and `Location` are part of the primary key and cannot be null. (c) Deletion anomaly—deleting the row with Hours = 30 removes Jones and all information about project P3. We will verify these predictions as we normalize.*

### 1.3 The Core Idea: One Fact in One Place

The guiding principle of normalization is:

> Every attribute should describe the key, the whole key, and nothing but the key.

This mnemonic, often attributed to William Kent, encodes a precise technical condition. When we violate this principle—for example, by storing an employee's name in a table where the key is a combination of employee, project, and location—the employee name depends on only part of the key (`EMP_ID` alone). It gets repeated unnecessarily, and every repetition is an opportunity for inconsistency.

**Cross-domain connection — information theory and the Single Source of Truth:** Normalization can be understood through the lens of information theory. When `EmpName` appears in multiple rows, those rows share mutual information they should not share—they are coupled. Decomposition removes that coupling, reducing the channel capacity required to maintain consistency. The same principle appears in software engineering as the Single Responsibility Principle: a module should have one reason to change. In distributed systems, it appears as data partitioning and the single-writer principle. In statistics, it appears as reducing multicollinearity—removing redundant information that distorts analysis. In each domain, the goal is identical: isolate independent facts so that changes propagate cleanly and failures remain contained.

**Cross-domain connection — impact on data analytics:** Normalization directly affects the quality of analytical queries. When a fact like `ProjName` is duplicated across thousands of rows, any aggregation that groups by project name must scan and deduplicate those repetitions. Worse, if an update anomaly has already introduced inconsistencies—some rows say "Alpha" and others say "AlphaPlus" for the same `ProjID`—your `GROUP BY` will silently produce two groups for what should be one project. Analysts then spend hours chasing "data quality issues" that are actually schema design issues. Normalization prevents this class of error entirely by making the schema a truthful representation of the domain's functional dependencies.

**Try this yourself:** Consider a table tracking university course enrollments with columns `StudentID`, `StudentName`, `CourseID`, `CourseTitle`, `ProfessorID`, `ProfessorName`, and `Grade`. Identify at least three facts that are stored redundantly. For each, predict what anomaly could occur if that fact changes. We will resolve this exact scenario when we reach 3NF.

**Quick Check 4:** In the table above, which attributes depend on the whole key \(\{\text{EMP_ID}, \text{ProjID}, \text{Location}\}\), and which depend on only part of it?

*Hint: Does `EmpName` need all three attributes to be determined? What about `ProjName`? What about `Hours`?*

*Answer: `EmpName` depends only on `EMP_ID`. `ProjName` depends only on `ProjID`. `Hours` depends on the full combination of `EMP_ID` and `ProjID` (and implicitly `Location`, but we will refine this). `Location` is the tricky one—we will analyze it carefully in Section 3.*

### 1.4 Two Non-Negotiable Properties of Decomposition

When we split a table, we must ensure two properties:

1.  **Lossless-join property:** We must be able to reconstruct the original table exactly by joining the decomposed tables. No spurious tuples should appear. Formally, a decomposition of relation \(R\) into \(R_1\) and \(R_2\) is lossless-join if and only if the common attributes of \(R_1\) and \(R_2\) form a superkey for at least one of the decomposed relations. That is, if we decompose \(R\) into \(R_1\) and \(R_2\), the decomposition is lossless-join if and only if \((R_1 \cap R_2) \rightarrow R_1\) or \((R_1 \cap R_2) \rightarrow R_2\) holds in \(F^+\).

2.  **Dependency preservation property:** All original functional dependencies should be enforceable directly on the decomposed tables, without needing to join them to check a constraint. Formally, let \(F\) be the set of FDs on \(R\), and let \(F_1, F_2, \ldots, F_k\) be the projections of \(F\) onto the decomposed schemas \(R_1, R_2, \ldots, R_k\). The decomposition is dependency-preserving if \((F_1 \cup F_2 \cup \ldots \cup F_k)^+ = F^+\). This matters because joins are expensive, and a constraint that requires a join on every insert is a performance problem.

We will verify these properties as we proceed. A decomposition that loses information or loses constraints is not a valid normalization.

**Analogy — the torn photograph:** Imagine tearing a photograph into two pieces so that two people can each carry half. A lossless decomposition is like cutting along a line where every fragment on one side has a unique matching fragment on the other—like a jigsaw puzzle with perfectly interlocking edges. If you cut arbitrarily, you might create edges that match multiple fragments, and reassembling the photo produces Frankenstein images that never existed. The superkey condition guarantees interlocking edges: the common attributes uniquely identify at most one fragment in at least one of the pieces.

**Quick Check 5:** Why must the common attributes form a superkey for a lossless join? Consider a counterexample: decompose \(R(A, B, C)\) into \(R_1(A, B)\) and \(R_2(B, C)\) where neither \(B \rightarrow A\) nor \(B \rightarrow C\) holds. If we have tuples \((a_1, b_1)\) in \(R_1\) and \((b_1, c_1), (b_1, c_2)\) in \(R_2\), joining produces \((a_1, b_1, c_1)\) and \((a_1, b_1, c_2)\). But if the original relation only contained \((a_1, b_1, c_1)\), we have now introduced a spurious tuple \((a_1, b_1, c_2)\). The superkey condition prevents this by ensuring that each value of the common attributes matches at most one tuple in at least one of the decomposed relations.

**Quick Check 6:** Suppose we decompose a table `R(A, B, C)` with FDs \(\{A \rightarrow B, B \rightarrow C\}\) into `R1(A, B)` and `R2(B, C)`. The common attribute is `B`. Is `B` a superkey for either `R1` or `R2`?

*Answer: Yes—`B` is a superkey for `R2` because \(B \rightarrow C\) holds, so `B` uniquely determines all attributes in `R2`. The join on `B` is lossless. Note that `B` is not a superkey for `R1` because we only know \(A \rightarrow B\), not \(B \rightarrow A\). The condition requires only that the common attributes form a superkey for at least one of the relations.*

---

## 2. First Normal Form (1NF)

### 2.1 Intuition and Analogy

The relational model is built on the idea of a flat, two-dimensional grid. At every row-column intersection, we expect exactly one atomic value—a single number, a single string, a single date. If a column contains a list, a set, or a nested table, we cannot uniformly use relational operators like `SELECT`, `JOIN`, or `GROUP BY` on that column. 1NF is the rule that says: "Flatten everything. No lists inside cells."

**Analogy — the filing cabinet:** Imagine a filing cabinet where each drawer represents a table and each folder represents a row. Inside each folder, every field (Name, Date, Amount) has exactly one slip of paper. 1NF says: do not staple multiple slips to the same field. If you staple three phone numbers to the "Phone" field, you cannot sort by phone number, search for a specific phone number with a simple query, or enforce uniqueness across phone numbers. You must give each phone number its own folder (row) in a separate drawer (table) or flatten it into the current drawer by repeating the other fields.

**Analogy — the spreadsheet formula cell:** Another way to think about 1NF is through the lens of a spreadsheet. A cell containing `=SUM(A1:A10)` is atomic from the user's perspective—it displays a single number. But a cell containing "Alice, Bob, Carol" is not atomic because no built-in spreadsheet function can treat those three names as separate values without text parsing. 1NF draws the same line: the value must be indivisible by the operators of the data model. A JSON blob is like that comma-separated cell—technically one value, but opaque to the relational engine.

### 2.2 Formal Definition

A relation schema is in **First Normal Form (1NF)** if the domain of every attribute includes only atomic (indivisible) values, and every tuple contains exactly one value from that domain for each attribute. In other words, 1NF disallows:

-   Multivalued attributes (e.g., a column `PhoneNumbers` storing a set of numbers).
-   Composite attributes (e.g., a column `Address` that is itself composed of `Street`, `City`, `Zip`).
-   Nested relations (a table inside a table).

An important subtlety: "atomic" is defined relative to the operations of the data model. A string containing comma-separated values is not atomic from the perspective of the relational model because relational operators cannot directly access the individual values without string manipulation. A date, however, is typically considered atomic even though it has internal structure (year, month, day), because SQL provides operators that treat it as a single value.

**Provocative question:** Is a JSON blob stored in a text column atomic? By the letter of 1NF, yes—it is a single string value. But in practice, it hides internal structure that the DBMS cannot query, index, or constrain. This is why many practitioners say "1NF is the bare minimum; you almost always need more." The relational model earns its guarantees only when you actually use its structure.

### 2.3 Worked Example: Flattening a Nested Relation

Consider a design that is *not* in 1NF:

```
EMP_ID | EmpName | Projects(ProjID, ProjName, Locations(*))
-------|---------|----------------------------------------------
E01    | Smith   | { (P1, Alpha, {NYC, BOS}), (P2, Beta, {CHI}) }
E02    | Jones   | { (P3, Gamma, {SFO}) }
```

Here, `Projects` is a nested relation—a table inside a cell. Inside it, `Locations` is a multivalued set. This is a clear 1NF violation.

**Step 1: Flatten the nested relation into tuples.** We expand each project entry into its own row and each location into its own row. For E01's first project, (P1, Alpha, {NYC, BOS}) becomes two rows because there are two locations. The result is a flat table:

```
EMP_ID | EmpName | ProjID | ProjName | Location
-------|---------|--------|----------