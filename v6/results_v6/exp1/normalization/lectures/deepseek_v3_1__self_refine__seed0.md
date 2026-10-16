# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **State** the definitions of 1NF, 2NF, 3NF, and BCNF and identify the specific anomaly each normal form eliminates.
2. **Explain** why update, insertion, and deletion anomalies arise from poor schema design and how functional dependencies capture their root cause.
3. **Apply** a step-by-step decomposition algorithm to a given relation, using its functional dependencies and candidate keys, to produce schemas in 3NF or BCNF.
4. **Analyze** a real-world schema to determine which normal form it satisfies and pinpoint exactly which functional dependency violates the next higher form.
5. **Evaluate** design trade-offs between 3NF and BCNF and justify when deliberate denormalization is a defensible performance decision.

---

## Prerequisites

This lecture assumes you can:

- Define a relation as a table with rows (tuples) and columns (attributes).
- Identify a primary key and explain why it uniquely identifies each row.
- Read and interpret a simple SQL `CREATE TABLE` statement, including `PRIMARY KEY` and `FOREIGN KEY` constraints.
- Understand basic set theory notation, including subset relations and set membership.

If any of these terms are unfamiliar, please review the introductory module on the relational model before proceeding.

**Pre-lecture self-assessment (30 seconds):** Given the table `STUDENT(StudentID, Name, Email)`, where `StudentID` is the primary key, can you explain why `Email` should also be unique? If a student changes their email, how many rows must you update? Keep your answer in mind — we will formalize this intuition shortly.

---

## Opening: The Paradox of the Perfectly Correct Database

The most dangerous database errors are those that violate no constraints, trigger no alarms, and pass every integrity check. They are errors of *structure*, not of data.

In 2019, a payroll system at a mid-sized logistics company overpaid 47 employees by a combined total of $52,000 in a single pay period. An engineer updated an employee's department transfer. The department's hourly billing rate was stored redundantly across every employee row in that department. One `UPDATE` statement missed three rows due to a mistyped `WHERE` clause. For two weeks, those three employees were paid at both their old and new rates simultaneously.

No constraint was violated. No error message appeared. The database was internally consistent yet factually impossible: it asserted that one department could have two different pay rates at the same time. The schema trusted humans to enforce a rule the structure itself should have guaranteed. Normalization is the discipline of making such lies structurally impossible — of designing schemas where the laws of the business are enforced by the laws of the schema.

Here is the unsettling truth this lecture confronts: a database can return *perfectly correct answers* to every query while containing *logically impossible facts*. The payroll system would have correctly reported each employee's pay rate on demand — yet the fact it stored (one department, two rates) was a contradiction in the business's own terms. Normalization theory exists because correctness of output does not guarantee correctness of state.

**Pause and predict:** Before we dive in, take 20 seconds to hypothesize: what structural property of the payroll table allowed one department to have two different pay rates? Write down your hypothesis. We will check it at the end of Section 4.

---

## 1. Why Normalize? The Problem in One Table

### 1.1 A Single-Table Design

Consider building a company directory for a mid-sized organization. You must store information about employees, departments, and buildings. A natural first instinct — reinforced by spreadsheet habits — is to place everything in one table. Each employee belongs to a department, and each department occupies a building. So we write:

```
EMP_DEPT_BUILDING(EmpID, EmpName, DeptID, DeptName, Building)
```

Assume these business rules:

- Each employee has a unique `EmpID`.
- Each employee belongs to exactly one department, identified by `DeptID`.
- Each department has one name (`DeptName`) and is housed in exactly one building (`Building`).

A sample instance:

| EmpID | EmpName | DeptID | DeptName   | Building   |
|-------|---------|--------|------------|------------|
| E01   | Alice   | D01    | Sales      | Building A |
| E02   | Bob     | D01    | Sales      | Building A |
| E03   | Charlie | D02    | Engineering| Building C |
| E04   | Diana   | D02    | Engineering| Building C |
| E05   | Eve     | D03    | Marketing  | Building A |

The fact "Sales is in Building A" appears twice. This redundancy is not merely wasteful — it invites inconsistency. But why does this specific fact repeat while others do not? Notice: "Alice works in Sales" appears only once. The difference is that `EmpName` depends on `EmpID` alone, while `Building` depends on `DeptID` — an attribute that is *not* the key of this table. This asymmetry is the thread we will pull throughout the lecture.

### 1.2 Three Anomalies

**Update Anomaly.** The Sales department relocates from Building A to Building B. An `UPDATE` statement changes `Building` for Sales. If the `WHERE` clause inadvertently misses one row, the database contains:

| EmpID | EmpName | DeptID | DeptName | Building   |
|-------|---------|--------|----------|------------|
| E01   | Alice   | D01    | Sales    | Building B |
| E02   | Bob     | D01    | Sales    | Building A |

The database now asserts that Sales occupies two buildings simultaneously. No declarative constraint can prevent this because the rule "each department is in exactly one building" is not expressed structurally in the schema.

**Analogy — the library catalog:** Imagine a library where the same book's title is handwritten on multiple index cards in different drawers. If the book is renamed, a librarian must find and update every card. Miss one, and the catalog claims two different titles for the same ISBN. The catalog's *structure* allowed the contradiction; only human diligence prevented it.

Now extend the analogy: what if the library stores each book's title on a single master card, and every other card merely references that master by ISBN? A title change becomes a single edit. The physical layout now *enforces* consistency — it is structurally impossible for one ISBN to have two titles. This is precisely what normalization achieves: it reorganizes data so that each fact lives in exactly one place, making inconsistency structurally impossible rather than procedurally avoidable.

**Insertion Anomaly.** The organization creates a new department, "AI Research" (DeptID D04), before hiring any employees. Inserting a row fails because `EmpID` is part of the primary key and constrained `NOT NULL`. You must either invent a placeholder employee or defer recording the department's existence.

Consider a different domain: a hospital database tracking patients and their prescribed medications in a single table `PATIENT_MEDS(PatientID, PatientName, Medication, Dosage, PrescribingDoctor)`. A new medication is approved by the pharmacy board and added to the formulary, but no patient has yet been prescribed it. The medication's existence cannot be recorded because `PatientID` is part of the key and `NOT NULL`. The database structure prevents the hospital from maintaining an accurate medication catalog independently of patient records.

**Deletion Anomaly.** Eve, the last employee in Marketing, resigns. Deleting her row removes all evidence that Marketing ever existed, including its name and building assignment.

In a university context, consider `STUDENT_CLUB(StudentID, StudentName, ClubName, ClubAdvisor)`. If the last student graduates and leaves the Chess Club, deleting their row erases the club's existence entirely — including who advises it. The registrar loses the ability to track active clubs independently of membership.

**The unifying pattern:** In every anomaly, one table tries to represent two independent facts, and one fact is held hostage by the other. The insertion anomaly holds department facts hostage to employee facts. The deletion anomaly holds club facts hostage to membership facts. The update anomaly forces you to modify the same department fact in multiple places. Normalization is the systematic method for identifying these hostage situations and freeing each fact into its own table.

**Try this yourself:** Before reading further, take 30 seconds to sketch a quick fix for the insertion anomaly. What would you need to change about the table's structure to record a department with zero employees? We will build toward the answer systematically.

### 1.3 The Root Cause

These three anomalies share one root cause: a single table attempts to represent multiple independent facts — about employees, about departments, and about buildings — with no mechanism to enforce their independence.

**Intuition — the filing cabinet:** Think of a filing cabinet. You would not store employee records, department budgets, and building floor plans in the same folder. You would use separate folders and cross-reference them. Normalization is the formal method for deciding how many folders you need and what belongs in each.

**Cross-domain connection — the CAP theorem parallel:** Database designers working with distributed systems face a similar structural tension. The CAP theorem states you cannot simultaneously guarantee consistency, availability, and partition tolerance. The unnormalized table faces its own impossibility: you cannot simultaneously store everything in one place, avoid all redundancy, and prevent all anomalies. Normalization is the systematic trade-off — it sacrifices the convenience of a single table to gain anomaly-free data. Understanding *which* trade-off you are making distinguishes a designer who has moved beyond memorizing rules.

**A deeper parallel — information theory:** Claude Shannon proved that redundancy in a message enables error detection and correction. A database schema is a message about the structure of a business. Normalization *reduces* redundancy in that message — making the schema concise and anomaly-free. Denormalization *reintroduces* controlled redundancy for performance, much like error-correcting codes add bits for reliability. The designer's art is knowing which redundancy is structural waste and which is deliberate engineering.

> **Quick Check 1:** In the table above, suppose we change Alice's name to "Alicia." Must we update multiple rows? Is this an update anomaly?
>
> *Answer:* No, we update only one row because Alice appears once. This is not an update anomaly — the employee's name depends on `EmpID`, which is the primary key, so no redundancy exists for this fact. An update anomaly requires the same fact stored in multiple rows.

---

## 2. The Diagnostic Tool: Functional Dependencies

### 2.1 Intuition

Normalization does not rely on intuition. It uses a precise, mechanical tool: the **functional dependency (FD)**. An FD tells you exactly which facts are tangled together — and therefore exactly how to untangle them.

Consider the mathematical function $f(x) = x^2$. For each input $x$, there is exactly one output. If $x = 3$, then $f(x) = 9$ with certainty. A functional dependency works analogously: given an employee's ID, we know their name with certainty. The ID *determines* the name.

But here is the critical distinction that separates novice from expert: FDs are not discovered by looking at data. They are statements about the *rules of the business*. In our sample table, every `DeptID = D01` row shows `Building = Building A`. Does that prove $\text{DeptID} \rightarrow \text{Building}$? No — it only proves it holds in this instance. Tomorrow, Sales could move to Building B, and the data would change, but the FD would still hold (each department still has exactly one building — just a different one). If we derived FDs from data alone, we would be normalizing against yesterday's snapshot, not against reality.

This distinction — FD as business rule, not data observation — is where most normalization mistakes begin. A database administrator who infers FDs by querying the current data is like a physicist who derives the laws of motion by watching one falling apple.

**Worked Example: Distinguishing Business Rules from Data Patterns.** Suppose we inspect the sample data and observe that every employee named "Alice" works in department D01. Does $\text{EmpName} \rightarrow \text{DeptID}$ hold? No — the business allows two different employees to share the name "Alice" but work in different departments. The data pattern is coincidental. Always ask: "Does the business rule guarantee this, or is it just true in the current data?"

### 2.2 Formal Definition

Let $R$ be a relation schema with attribute set $U$. A **functional dependency**, denoted $X \rightarrow Y$ (read as "$X$ determines $Y$"), is a constraint asserting: in any valid relation instance $r$ of $R$, whenever two tuples $t_1, t_2 \in r$ agree on all attributes in $X$, they must agree on all attributes in $Y$.

Formally:

$$\forall t_1, t_2 \in r(R): \quad t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]$$

where $t[X]$ denotes the projection of tuple $t$ onto the attribute set $X$.

**Worked Example: Spotting FDs.** Test the claim $\text{DeptID} \rightarrow \text{Building}$ against the sample data:

- Rows with `DeptID = D01`: both have `Building = Building A`. Agreement holds.
- Rows with `DeptID = D02`: both have `Building = Building C`. Agreement holds.
- Rows with `DeptID = D03`: only one row, so the condition is vacuously satisfied.

The FD holds in this instance. However, an FD is a constraint that must hold in *all possible* valid instances, not just the current one. We derive FDs from business rules, not from inspecting data.

### 2.3 Trivial vs. Nontrivial FDs

An FD $X \rightarrow Y$ is **trivial** if $Y \subseteq X$. For example, $\{\text{EmpID}, \text{EmpName}\} \rightarrow \text{EmpName}$ is trivial: knowing the combination of ID and name certainly determines the name. Trivial FDs hold in every possible relation instance and convey no useful structural constraint. Only **nontrivial** FDs (where $Y \not\subseteq X$) constrain allowable instances and drive normalization.

**Why trivial FDs matter despite being useless for normalization:** They matter for reasoning about keys. When we say $\{\text{EmpID}\}$ is a superkey, we mean the FD $\text{EmpID} \rightarrow U$ holds, where $U$ includes every attribute. This FD is nontrivial precisely because `EmpID` does not contain all other attributes. The nontriviality is what makes it a meaningful constraint.

**Worked Example: Classifying FDs.** Consider the FDs on `EMP(EmpID, DeptID, DeptName)`:

- $\{\text{EmpID}, \text{DeptID}\} \rightarrow \text{DeptID}$: Trivial, because `DeptID` is a subset of the left-hand side.
- $\text{EmpID} \rightarrow \text{DeptID}$: Nontrivial, because `DeptID` is not a subset of `EmpID`.
- $\text{DeptID} \rightarrow \text{DeptName}$: Nontrivial.

Only the last two drive normalization decisions.

### 2.4 Keys Defined Through FDs

Keys are defined entirely through functional dependencies:

- A **superkey** $SK$ is any subset of attributes such that $SK \rightarrow U$ — knowing $SK$ determines the entire tuple.
- A **candidate key** $K$ is a *minimal* superkey: $K \rightarrow U$, and no proper subset $K' \subset K$ satisfies $K' \rightarrow U$.
- A **prime attribute** belongs to at least one candidate key.
- A **nonprime attribute** belongs to no candidate key.

**Worked Example: Identifying Keys.** In `EMP_DEPT_BUILDING`, the business rules give:

- $\text{EmpID} \rightarrow \text{EmpName}, \text{DeptID}, \text{DeptName}, \text{Building}$
- $\text{DeptID} \rightarrow \text{DeptName}, \text{Building}$

From the first FD, $\{\text{EmpID}\}$ is a superkey. It is minimal — removing the only attribute leaves an empty set, which cannot determine anything. So $\{\text{EmpID}\}$ is the sole candidate key.

Attribute classification: `EmpID` is prime. All other attributes — `EmpName`, `DeptID`, `DeptName`, `Building` — are nonprime.

**The fault line:** The distinction between prime and nonprime separates 2NF from 3NF, and 3NF from BCNF. Every normal form decision flows from this classification. Here is why: 2NF cares only about nonprime attributes and their relationship to the whole key. 3NF cares about nonprime attributes and their relationship to *each other*. BCNF removes the prime/nonprime distinction entirely and applies the same rule to all attributes. This progression is not arbitrary — it reflects increasingly strict standards for what constitutes an independent fact.

**Try this yourself — a subtle key identification problem:** Consider a relation `FLIGHT(PilotID, CopilotID, FlightNumber, Date, AircraftID)` with these business rules: (1) each flight on a given date has exactly one aircraft, (2) no pilot serves as both pilot and copilot on the same flight, (3) each flight number on a given date uniquely identifies the crew and aircraft. What are the candidate keys? Take 60 seconds to reason through it before continuing.

*Answer:* `{FlightNumber, Date}` is a candidate key by rule (3). Could `{PilotID, FlightNumber, Date}` also be a candidate key? It is a superkey (since it contains the candidate key), but it is not minimal — removing `PilotID` still leaves `{FlightNumber, Date}`, which is already a superkey. So `{FlightNumber, Date}` is the sole candidate key. `PilotID` and `CopilotID` are nonprime — a fact that will matter when we reach 3NF.

> **Quick Check 2:** In the relation `EMP(EmpID, Name, SSN)`, suppose both `EmpID` and `SSN` are unique per employee — each determines the other two attributes. What are the candidate keys? Which attributes are prime, and which are nonprime?
>
> *Answer:* Candidate keys are $\{\text{EmpID}\}$ and $\{\text{SSN}\}$. Prime attributes: `EmpID` and `SSN` (each belongs to at least one candidate key). Nonprime attribute: `Name` (belongs to no candidate key).

---

## 3. First Normal Form (1NF): The Flat-Table Foundation

### 3.1 Definition

A relation $R$ is in **first normal form (1NF)** if and only if the domain of each attribute contains only atomic (indivisible) values. No attribute may be relation-valued, set-valued, list-valued, or contain repeating groups within a single cell. In SQL terms, every column must have a scalar data type — no arrays, no nested tables, no JSON objects treated as opaque blobs.

**The hidden depth in "atomic":** Atomicity is not an absolute property of a value — it is relative to the operations you need to perform. A string containing a comma-separated list of project IDs is atomic if you only ever display it as a block of text. It becomes non-atomic the moment you need to query "find all employees on project 102." The relational model demands atomicity because it guarantees that every operator works uniformly on every value. 1NF is not a metaphysical claim about what is indivisible — it is a contract: every value can be compared, sorted, and joined using the same set of operations.

### 3.2 Why Atomicity Matters

The relational algebra — the formal foundation of SQL — operates on flat tables. Operators like selection ($\sigma$), projection ($\pi$), and join ($\bowtie$) assume that each cell contains exactly one value from the attribute's domain. A cell containing a list `{101, 102, 103}` breaks these operators because the algebra has no primitive for "element-of" comparisons within a cell. A query for "find all employees enrolled in project 102" cannot simply evaluate $\sigma_{\text{ProjID}=102}$; it must first decompose the list, which requires procedural logic outside the relational model.

**Analogy — the spreadsheet trap:** Think of a spreadsheet where one cell contains "Math, Physics, Chemistry." You cannot