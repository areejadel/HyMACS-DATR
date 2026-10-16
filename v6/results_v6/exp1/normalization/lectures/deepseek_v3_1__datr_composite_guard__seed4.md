# Normalization Forms and Database Schema Design (1NF–BCNF)

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Identify** functional dependencies from an application domain description and classify attributes as prime or nonprime given a set of candidate keys.
2. **Diagnose** whether a given relation schema violates 1NF, 2NF, 3NF, or BCNF by applying the formal definition of each normal form.
3. **Decompose** a relation schema that violates a normal form into a lossless-join, dependency-preserving set of normalized relations using the standard decomposition algorithms.
4. **Explain** the trade-offs between full normalization (BCNF) and 3NF in terms of redundancy elimination versus dependency preservation, and make a reasoned design choice for a given scenario.
5. **Correct** common misconceptions about normalization, including the belief that 1NF alone yields a good design, that every decomposition is beneficial, and that a higher normal form always implies a better schema.

---

## Prerequisites

Before we begin, ensure you are comfortable with:

- The relational model: relations (tables), tuples (rows), attributes (columns), and schema definitions.
- The concept of a **key**: what it means for a set of attributes to uniquely identify a tuple.
- Basic set notation and logical implication: if $X$ determines $Y$, what constraint does that place on the data?

If any of these feel shaky, take a moment to review them. We will build everything else from these foundations.

---

## 0. Opening Hook: The Database That Contradicted Reality

In 2018, a major airline's booking system suffered a cascading failure: passengers who had paid for seat assignments arrived at the gate to find those seats sold to someone else. The root cause was not a hardware failure or a cyberattack. It was a database schema that stored seat assignments redundantly across multiple tables. When an agent updated a seat in one place, the change failed to propagate — and the database silently held two contradictory versions of the truth.

This is not a bug you can patch with better application code. It is a structural defect in how the data is organized. The formal tools we are about to learn — functional dependencies and normal forms — exist to make this class of failure architecturally impossible. By the end of this lecture, you will be able to look at a schema and say with mathematical certainty: "This design cannot produce that kind of contradiction."

**The intellectual tension driving this whole topic:** Normalization feels destructive. You start with one table that "obviously" holds all the data, and every step of the process splits it into more and more pieces. The natural question — which you should keep asking throughout — is: *When does splitting stop being beneficial and start being pedantic?* The answer is not "always normalize to the highest form." It is: normalize until the remaining redundancy reflects genuine domain constraints you cannot enforce otherwise. We will make this precise.

---

## 1. Functional Dependencies and Keys: The Formal Foundation

### 1.1 Intuition: What is a Functional Dependency?

Imagine you are designing the database for a national election commission. Every registered voter is assigned to exactly one polling station based on their residential address. If two officials independently look up the same voter, they must arrive at the same polling station — otherwise someone has been disenfranchised. This is not a coincidence we hope holds; it is a constraint the system must enforce. The database equivalent is a **functional dependency (FD)**:

$$\text{VoterID} \rightarrow \text{PollingStation}$$

Read this as: "VoterID functionally determines PollingStation." The left-hand side (VoterID) is the **determinant**; the right-hand side (PollingStation) is the **dependent**.

This is a statement about the **rules of the application domain**, not a deduction from a single table snapshot. Even if the current table contains only one row per voter, the FD declares that any two valid rows with the same VoterID must have the same PollingStation. Violating this would mean the same voter is registered at two places — a logical contradiction in this domain.

**Why this matters beyond correctness:** FDs are not abstract formalism. They encode the business rules that prevent your database from silently contradicting reality. A table that permits two different polling stations for one voter has allowed an anomaly that could disenfranchise a real person. Normalization is the systematic removal of structures that make such contradictions possible.

**Cross-domain insight — FDs as the database analogue of mathematical functions:** If you have studied pure mathematics, the notation $X \rightarrow Y$ is deliberate. A function $f: X \to Y$ maps each input to exactly one output. An FD makes the same guarantee about data: for each value of $X$, there is exactly one permitted value of $Y$. The difference is that a mathematical function is defined by a formula, while an FD is defined by a domain constraint — it is a function enforced by reality, not by arithmetic. This connection is why the theory of normalization has the formal elegance it does.

### 1.2 Formal Definition

Let $R$ be a relation schema with attribute sets $X$ and $Y$. A functional dependency $X \rightarrow Y$ holds if, for any two tuples $t_1$ and $t_2$ in any valid instance $r(R)$:

$$t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]$$

The FD is **nontrivial** if $Y \not\subseteq X$. We focus on nontrivial FDs because trivial ones (e.g., $\text{VoterID} \rightarrow \text{VoterID}$) hold automatically and convey no useful information.

**A subtlety worth pausing on:** The definition says "any valid instance," not "the current instance." An FD is a constraint on the set of all possible states the database can ever be in. You cannot prove an FD holds by inspecting today's data; you can only disprove one by finding a counterexample. This is why FDs must come from domain analysis, not from data profiling.

**Try this yourself — the data profiling trap:** Suppose you examine a table of 10,000 employee records and observe that every employee in Department 5 has the job title "Engineer." Does $\text{DeptID} \rightarrow \text{JobTitle}$ hold? No. Tomorrow, Department 5 could hire a manager. The current data is consistent with the FD, but the FD is not a constraint of the domain. This is why you cannot automate normalization from data snapshots alone — you must understand what the data means.

### 1.3 Keys, Superkeys, and Prime Attributes

An FD provides a precise way to define keys:

- **Superkey:** A set of attributes $SK$ such that $SK$ functionally determines *all* attributes of $R$. Equivalently, no two distinct tuples can agree on $SK$. Every superset of a superkey is also a superkey.
- **Candidate key:** A **minimal** superkey. Remove any attribute from a candidate key, and it ceases to be a superkey. A relation may have multiple candidate keys.
- **Primary key:** One candidate key chosen by the designer as the principal identifier. This choice is arbitrary from a normalization perspective.
- **Prime attribute:** An attribute that belongs to *at least one* candidate key. **Nonprime attribute:** An attribute that belongs to *no* candidate key.

**Worked Example:**
Consider the relation schema `ENROLLMENT(StudentID, CourseID, Semester, Grade, StudentEmail)`.

Suppose the domain rules state:
- A student has one email: $\text{StudentID} \rightarrow \text{StudentEmail}$
- A student takes a specific course in exactly one semester and receives one grade: $\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Semester}, \text{Grade}\}$

To find candidate keys, observe that $\{\text{StudentID}, \text{CourseID}\}$ determines all attributes: StudentID gives StudentEmail; together with CourseID they give Semester and Grade. Is it minimal? Removing CourseID leaves only StudentID, which does not determine Semester or Grade (a student takes many courses). Removing StudentID leaves only CourseID, which does not determine anything about a specific student. Therefore $\{\text{StudentID}, \text{CourseID}\}$ is the sole candidate key.

Consequently:
- Prime attributes: StudentID, CourseID
- Nonprime attributes: Semester, Grade, StudentEmail

**Test Yourself 1:**
Given a relation `CUSTOMER(CustID, Name, Address, Phone)` where CustID is the sole candidate key, and one customer can have multiple phone numbers (so Phone is not unique per customer), classify each attribute as prime or nonprime.

<details>
<summary>Answer</summary>
Candidate key: {CustID}. Prime: CustID. Nonprime: Name, Address, Phone.
</details>

---

## 2. First Normal Form (1NF)

### 2.1 Intuition: The Atomicity Requirement

The relational model is built on the idea that each attribute holds a single, indivisible value. A spreadsheet cell should contain one number, one string, or one date — not a list of values, not a nested mini-table. 1NF is the formal statement of this structural rule. It is the **baseline** assumption of the relational model; every relation we consider from now on is assumed to be in 1NF.

**Why this is not obvious:** Many real-world data formats are naturally nested. A medical record might list multiple diagnoses per patient; an invoice contains line items. The impulse to store these as lists inside a single column is intuitive — it mirrors the document structure. 1NF forces us to flatten this structure, which feels like we are "losing information" about the grouping. In fact, we are not losing information; we are converting implicit grouping (position within a list) into explicit grouping (a shared key value across multiple rows). This is a trade-off: we gain queryability with standard relational operators at the cost of more rows.

**Industry Example — Electronic Health Records (EHR):** Consider a hospital system migrating from legacy flat-file storage to a modern relational database. A patient's record might arrive as a JSON document with a `diagnoses` array: `["ICD10-E11.9", "ICD10-I10", "ICD10-J45.21"]`. A developer might naively store this as a single TEXT or JSON column in a `PATIENT` table. This violates 1NF and has immediate practical consequences: (a) a query to find all patients with Type 2 diabetes (E11.9) now requires a full table scan with string matching or JSON path extraction, which cannot use standard B-tree indexes and degrades linearly with table size; (b) updating a diagnosis code — say, when ICD-11 replaces ICD-10 — requires parsing and rewriting every affected row's array, an operation that is both slow and error-prone; (c) the database's built-in foreign key mechanism cannot enforce that each diagnosis code references a valid entry in a `DIAGNOSIS_CODE` lookup table, so referential integrity must be enforced at the application layer, where bugs are far more likely. The correct 1NF design flattens this into a `PATIENT_DIAGNOSIS(PatientID, DiagnosisCode, DiagnosisDate)` table, where each diagnosis is an independent row, fully indexable, and constrained by a foreign key to `DIAGNOSIS_CODE(Code, Description)`.

**Industry Example — Financial Trading Systems:** In a trade-capture system for an investment bank, a single trade execution might involve multiple fills at different prices and times. A non-1NF design might store fills as a delimited string in a `FILLS` column: `"100@150.25|200@150.30|150@150.28"`. The practical cost of this design surfaces when the middle office needs to calculate volume-weighted average price (VWAP) for regulatory reporting. The SQL to parse, split, and compute over this string is not only complex and slow but also risks silent errors if the delimiter format changes. A 1NF `TRADE_FILL(TradeID, FillSequence, Quantity, Price, Timestamp)` table makes VWAP a trivial `SUM(Quantity*Price)/SUM(Quantity)` aggregation, ensures each fill can be independently audited, and allows the compliance team to query for fills within specific time windows using standard range predicates on `Timestamp`.

**Before we resolve the tension, pause here:** Why is the relational model so insistent on flat tables? Why not just support nested structures natively, as document databases do? The answer is that flat tables with explicit keys give you a uniform algebra — every query operation works on every attribute the same way. Once you allow nesting, you need separate operators for "query inside a list" versus "query across rows." 1NF is the price of algebraic uniformity. Whether that price is worth paying depends on your application's query patterns, but in a traditional RDBMS, it is non-negotiable.

### 2.2 Definition

A relation schema is in First Normal Form (1NF) if:
1. The domain of each attribute includes only **atomic** (indivisible) values.
2. The value of each attribute in any tuple is a single value from that domain.

This prohibits:
- **Multivalued attributes:** A column that holds sets, lists, or repeating groups (e.g., a `Diagnoses` column storing `{Hypertension, Diabetes, Asthma}`).
- **Composite attributes:** Nested structures treated as a single column (e.g., an `Address` column storing `(Street, City, Zip)` as a unit when we need to query individual components).

1NF is a **structural** constraint, not a dependency-based one. It says nothing about redundancy or anomalies; it only enforces the flat-table format.

### 2.3 Worked Example: Flattening a Repeating Group

**Before (violates 1NF):**
`EMPLOYEE_PROJECTS(EmpID, Name, Projects)`

| EmpID | Name | Projects |
|-------|------|----------|
| E1 | Alice | {P1, P2, P3} |
| E2 | Bob | {P2, P4} |

The `Projects` attribute holds a set of values, which is not atomic. But notice what is really happening: the set notation `{P1, P2, P3}` is a miniature relation hiding inside a single cell. To query "which employees work on P2?" you cannot use a simple equality predicate; you need a set-membership operator, which most SQL dialects support but which breaks the uniform tuple-at-a-time model of the relational algebra.

**After (1NF):**
We flatten by creating one tuple per project assignment:
`ASSIGNMENT(EmpID, Name, Project)`

| EmpID | Name | Project |
|-------|------|---------|
| E1 | Alice | P1 |
| E1 | Alice | P2 |
| E1 | Alice | P3 |
| E2 | Bob | P2 |
| E2 | Bob | P4 |

Now every attribute value is atomic. Notice, however, that `Name` is repeated for every project of the same employee. 1NF alone does not fix this redundancy; that is the job of higher normal forms.

### 2.4 Common Misconceptions About 1NF

**Misconception 1: "1NF means my schema is well-designed."**
Reality: 1NF is the minimum structural requirement. A schema in 1NF can still be riddled with update anomalies and redundancy. It is the starting line, not the finish line. The flattened `ASSIGNMENT` table above is in 1NF, yet updating Alice's name requires changing multiple rows — a classic update anomaly.

**Misconception 2: "Always split composite attributes into atomic parts."**
Reality: Decompose a composite attribute only if the application needs to query or constrain its sub-parts independently. If a `Date` attribute is always used as a whole (for comparison or formatting), splitting it into `Year`, `Month`, `Day` introduces unnecessary complexity and join overhead without semantic benefit. The atomicity judgment depends on the application's usage patterns. A useful heuristic: an attribute is non-atomic if the application treats its internal structure as meaningful for queries or constraints.

**Industry Example — Geographic Information Systems (GIS):** A municipal property-tax database stores parcel boundaries as `POLYGON` geometry types in a spatially-enabled database like PostGIS. The polygon is stored as a single attribute value, yet internally it is a complex structure of coordinate rings. Should we decompose it into individual `(longitude, latitude, ring_sequence)` rows to satisfy 1NF? Absolutely not. The application never queries individual coordinates; it queries spatial relationships — "find all parcels within 100 meters of this flood zone" — using spatial indexes and operators that treat the polygon as an atomic spatial object. Decomposing it would destroy the ability to use spatial indexing and make every spatial query an expensive reconstruction-and-comparison operation. Here, the domain's query patterns dictate that `POLYGON` is the appropriate atomic unit.

**Try this yourself:** Consider an attribute `PhoneNumber` that stores `+1-555-123-4567`. Would you split it into `CountryCode`, `AreaCode`, `Exchange`, `LineNumber`? The answer depends entirely on whether your application ever needs to query "all customers in area code 555" or validate country-code formats. If the application treats phone numbers as opaque identifiers for dialing, keeping them atomic is correct. If it needs to filter by geographic region, the composite structure matters and should be decomposed.

---

## 3. Second Normal Form (2NF)

### 3.1 Motivation: Partial Dependencies Cause Redundancy

Having established 1NF as the baseline, we now address the first source of redundancy: partial dependencies. Consider the 1NF relation `ASSIGNMENT(EmpID, Name, Project)` from our earlier example. Its candidate key is `{EmpID, Project}` — together they uniquely identify a row. But observe the FD: `EmpID → Name`. This FD's determinant (`EmpID`) is a *proper subset* of the candidate key. This is a **partial dependency**: a nonprime attribute (`Name`) depends on part of the key, not the whole key.

**Why this is a problem:** Think of the candidate key as the "atomic unit of identification" for a fact. If `Name` depends only on `EmpID`, then the fact "Alice is the name of employee E1" is independent of which project we are talking about. Yet in our 1NF table, that fact is stored redundantly — once for every project Alice is assigned to. If Alice changes her name, we must update three rows. If we delete Alice's last project assignment, we lose her name entirely. These are **update anomalies** and **delete anomalies**, respectively.

**Industry Example — Supply Chain and Inventory Management:** A large retailer's warehouse management system tracks inventory across multiple storage locations. Consider the schema `INVENTORY(ProductID, LocationID, ProductName, Category, QuantityOnHand)`, with candidate key `{ProductID, LocationID}`. The FDs `ProductID → ProductName` and `ProductID → Category` are partial dependencies. The practical consequence: if a product's category changes — say, "Organic Honey" is reclassified from "Condiments" to "Natural Foods" for a shelf-reset initiative — the update must be applied to every row for that product across potentially hundreds of warehouse locations. In a high-throughput system processing thousands of inventory adjustments per second, this multi-row update either holds locks on all those rows (blocking pick-list generation and order fulfillment) or, if done lazily, leaves the database in an inconsistent state where the same product reports different categories at different locations. A 2NF decomposition into `PRODUCT(ProductID, ProductName, Category)` and `INVENTORY(ProductID, LocationID, QuantityOnHand)` reduces the category update to a single-row operation on the `PRODUCT` table, eliminating both the locking contention and the consistency risk.

**Industry Example — Human Resources and Payroll:** A multinational corporation's HR system uses `EMPLOYEE_ASSIGNMENT(EmpID, ProjectID, EmpName, DeptID, DeptName, HoursWorked)` with key `{EmpID, ProjectID}`. The partial dependency `DeptID → DeptName` means that if the "Emerging Technologies" department is renamed to "Advanced Research," every employee in that department must have their `DeptName` updated across all their project assignments. In a company with 50,000 employees, each averaging three project assignments, that is 150,000 row updates. Worse, during the update window, a report joining this table with the payroll system might see some rows with the old name and some with the new name, producing a payroll summary that references a non-existent department. Decomposing to `DEPARTMENT(DeptID, DeptName)` and `EMPLOYEE(EmpID, EmpName, DeptID)` isolates