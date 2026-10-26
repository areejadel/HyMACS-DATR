# Normalization Forms and Database Schema Design (1NF–BCNF)

## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember** the formal definitions of 1NF, 2NF, 3NF, and BCNF, and recall the specific conditions that constitute a violation of each.
2.  **Understand** the concept of functional dependency and explain why FDs are domain constraints, not data observations.
3.  **Apply** normalization rules to diagnose whether a given relation schema violates 2NF, 3NF, or BCNF by identifying partial and transitive dependencies.
4.  **Analyze** a non-normalized schema to identify candidate keys, classify attributes as prime or nonprime, and determine the highest normal form satisfied.
5.  **Create** a lossless-join decomposition of a sub-normal schema into BCNF or 3NF, and evaluate the trade-offs between redundancy elimination and dependency preservation.

---

## Opening: The Database That Forgot the Truth

In 2018, a major airline's crew scheduling database grounded hundreds of flights. The root cause was a pilot's certification expiration date stored in multiple places. When the date was updated in one table but not another, the system simultaneously asserted that the pilot was both qualified and unqualified to fly. The database contained a logical contradiction, and the software trusted both versions.

This is not a bug; it is a structural property of the schema. The database was designed in a way that *permitted* contradictory facts to coexist. No amount of application-level validation could reliably prevent it, because the problem was in the shape of the tables, not the code.

Normalization is the discipline of designing table structures that make certain classes of contradictions *impossible to represent*. By the end of this lecture, you will be able to analyze a schema and say: "This design permits these specific anomalies—and here is exactly how to restructure it so they cannot occur."

**Pause and predict:** Before reading further, consider: what would it mean for a database to make a contradiction "impossible to represent"? How is that different from writing application code that checks for contradictions before inserting data? Write down one sentence answering this, then continue. We will return to this question.

---

## Prerequisites

Before we begin, ensure you are comfortable with:

- The relational model: relations (tables), tuples (rows), attributes (columns), and schema definitions.
- The concept of a **key**: what it means for a set of attributes to uniquely identify a tuple.
- Basic set notation and logical implication: if $X$ determines $Y$, what constraint that places on the data.

We build everything else from these foundations.

---

## 1. Functional Dependencies and Keys: The Formal Foundation

### 1.1 Intuition: What is a Functional Dependency?

Consider designing a database for a national election commission. Every registered voter is assigned to exactly one polling station based on their residential address. If two officials independently look up the same voter, they must arrive at the same polling station. This is not a coincidence we hope holds; it is a constraint the system must enforce. The database equivalent is a **functional dependency (FD)**:

$$\text{VoterID} \rightarrow \text{PollingStation}$$

Read this as: "VoterID functionally determines PollingStation." The left-hand side (`VoterID`) is the **determinant**; the right-hand side (`PollingStation`) is the **dependent**.

This FD is a statement about the **rules of the application domain**, not a deduction from a single table snapshot. Even if the current table contains only one row per voter, the FD declares that any two valid rows with the same `VoterID` must have the same `PollingStation`. Violating this would mean the same voter is registered at two places—a logical contradiction in this domain.

**Why this matters beyond correctness:** FDs encode the business rules that prevent your database from silently contradicting reality. A table that permits two different polling stations for one voter has allowed an anomaly that could disenfranchise a real person. Normalization is the systematic removal of structures that make such contradictions possible.

**Another concrete intuition—the university registrar:** A `StudentID` determines a `StudentName` and `DateOfBirth`. A `CourseCode` determines a `CourseTitle` and `CreditHours`. Together, `{StudentID, CourseCode}` determine a `Grade`. These are not design choices; they are constraints imposed by how the university operates. If two rows show the same `StudentID` with different `DateOfBirth` values, the database is asserting a contradiction about reality. Normalization prevents the database structure from ever allowing such contradictions to be stored.

**Cross-domain connection — compiler type systems as FDs:** In a statically typed programming language, a variable's type declaration acts as a functional dependency: `variableName → type`. The compiler enforces that every occurrence of `x` in a given scope has exactly one type. If you write code that implies `x` is both an integer and a string, the type checker rejects it—not by examining runtime values, but by verifying that the structure of the program cannot produce such a contradiction. This is precisely what normalization does for databases: it verifies that the schema structure cannot produce contradictory facts, regardless of what data is inserted. The FD `VoterID → PollingStation` is to a database schema what a type declaration `x: int` is to a program: a structural guarantee enforced before any data or execution exists.

**Industry Application — Healthcare Information Systems:**
In modern Electronic Health Record (EHR) systems following HL7 FHIR standards, functional dependencies are explicitly modeled as constraints. A `Patient` resource has an identifier that functionally determines demographic attributes. When integrating data from multiple hospital systems, identifying and enforcing these FDs prevents a single patient from having conflicting blood types recorded across different encounters—a literal life-or-death matter. Major EHR vendors like Epic and Cerner implement FD enforcement through unique patient master indices, which are essentially materialized candidate keys spanning distributed systems. The failure to properly identify FDs during healthcare data integration has led to documented cases of wrong-patient errors, making this a core patient safety concern, not merely an academic exercise.

**Test Yourself 1a — Spot the FD:**
Consider a university database. For each of the following, state whether the FD likely holds based on domain rules, and explain your reasoning:
- $\text{StudentID} \rightarrow \text{DateOfBirth}$
- $\text{AdvisorName} \rightarrow \text{AdvisorOffice}$
- $\text{CourseCode} \rightarrow \text{StudentID}$

<details>
<summary>Answer</summary>
- **Holds:** Each student has exactly one date of birth.
- **Holds:** Each advisor has exactly one office (assuming one office per advisor).
- **Does NOT hold:** A course can have many students enrolled, so one `CourseCode` maps to many `StudentID`s.
</details>

### 1.2 Formal Definition

Let $R$ be a relation schema with attribute sets $X$ and $Y$. A functional dependency $X \rightarrow Y$ holds if, for any two tuples $t_1$ and $t_2$ in any valid instance $r(R)$:

$$t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]$$

The FD is **nontrivial** if $Y \not\subseteq X$. We focus on nontrivial FDs because trivial ones (e.g., $\text{VoterID} \rightarrow \text{VoterID}$) hold automatically and convey no useful constraint.

**A subtlety worth pausing on:** The definition says "any valid instance," not "the current instance." An FD is a constraint on the set of all possible states the database can ever be in. You cannot prove an FD holds by inspecting today's data; you can only disprove one by finding a counterexample. FDs must therefore come from domain analysis, not from data profiling.

**Analogy — The laws of physics versus a photograph:** A photograph of a ball in mid-air tells you its position at one instant. It does not tell you that gravity will pull it downward. The FD is the law of gravity—it constrains all possible future states. The table snapshot is the photograph—it shows one valid state but does not reveal the underlying constraints. Just as you cannot derive $F = ma$ from a single photograph, you cannot derive FDs from a single table instance.

**Cross-domain connection — cryptographic hash functions as a one-way FD:** A cryptographic hash function like SHA-256 exhibits a functional dependency: $\text{input} \rightarrow \text{hash\_output}$. Given the same input, you always get the same output. But unlike database FDs, this dependency is computationally irreversible—you cannot recover the input from the hash. Database FDs, by contrast, are constraints we want the system to enforce bidirectionally: if two tuples agree on the determinant, they must agree on the dependent, but we can also look up the dependent given the determinant. This asymmetry highlights why database FDs are semantic constraints, not computational transformations.

**Worked Example — Spotting an FD in a table snapshot:**

Suppose we examine today's `EMPLOYEE` table:

| EmpID | Name  | Dept  |
|-------|-------|-------|
| 101   | Alice | Sales |
| 102   | Bob   | Sales |
| 103   | Carol | HR    |

Can we conclude $\text{Dept} \rightarrow \text{Name}$? No—just because `Sales` currently contains Alice and Bob (different names) does not mean it always will. If we hire Dave into `Sales` tomorrow, the FD $\text{Dept} \rightarrow \text{Name}$ would be violated because `Sales` would then map to multiple names. The FD $\text{EmpID} \rightarrow \text{Name}$, however, reflects a domain rule: employee IDs are assigned uniquely to individuals. We accept this FD based on our understanding of how employee IDs work, not because the current table happens to show unique names per ID.

**Thought experiment — the "data profiling trap":** Imagine you are given a database from a company you know nothing about. You run a query and observe that in the `EMPLOYEE` table, every `Dept` value maps to exactly one `Name` value across all current rows. Could you safely conclude $\text{Dept} \rightarrow \text{Name}$? Why or why not? What additional information would you need before enforcing this as a constraint? Take a moment to articulate your reasoning—this distinction between observed correlation and semantic constraint is one of the most common errors in schema design.

### 1.3 Keys, Superkeys, and Prime Attributes

An FD provides a precise way to define keys:

- **Superkey:** A set of attributes $SK$ such that $SK$ functionally determines *all* attributes of $R$. Equivalently, no two distinct tuples can agree on $SK$. Every superset of a superkey is also a superkey.
- **Candidate key:** A **minimal** superkey. Remove any attribute from a candidate key, and it ceases to be a superkey. A relation may have multiple candidate keys.
- **Primary key:** One candidate key chosen by the designer as the principal identifier. This choice is arbitrary from a normalization perspective.
- **Prime attribute:** An attribute that belongs to *at least one* candidate key.
- **Nonprime attribute:** An attribute that belongs to *no* candidate key.

**Worked Example — Finding candidate keys and classifying attributes:**

Consider the relation schema `ENROLLMENT(StudentID, CourseID, Semester, Grade, StudentEmail)`.

Suppose the domain rules state:
- A student has one email: $\text{StudentID} \rightarrow \text{StudentEmail}$
- A student takes a specific course in exactly one semester and receives one grade: $\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Semester}, \text{Grade}\}$

To find candidate keys, we observe that $\{\text{StudentID}, \text{CourseID}\}$ determines all attributes: `StudentID` gives `StudentEmail`; together with `CourseID` they give `Semester` and `Grade`. Is it minimal? Removing `CourseID` leaves only `StudentID`, which does not determine `Semester` or `Grade` (a student takes many courses). Removing `StudentID` leaves only `CourseID`, which does not determine anything about a specific student. Therefore $\{\text{StudentID}, \text{CourseID}\}$ is the sole candidate key.

Consequently:
- Prime attributes: `StudentID`, `CourseID`
- Nonprime attributes: `Semester`, `Grade`, `StudentEmail`

**Worked Example — Multiple candidate keys:**

Consider `VEHICLE_REGISTRATION(VIN, LicensePlate, State, OwnerID, RegistrationDate)`.

Domain rules:
- A VIN uniquely identifies a vehicle: $\text{VIN} \rightarrow \{\text{LicensePlate}, \text{State}, \text{OwnerID}, \text{RegistrationDate}\}$
- Within a state, a license plate uniquely identifies a vehicle: $\{\text{State}, \text{LicensePlate}\} \rightarrow \{\text{VIN}, \text{OwnerID}, \text{RegistrationDate}\}$

Both $\{\text{VIN}\}$ and $\{\text{State}, \text{LicensePlate}\}$ are candidate keys. Therefore:
- Prime attributes: `VIN`, `State`, `LicensePlate` (each belongs to at least one candidate key)
- Nonprime attributes: `OwnerID`, `RegistrationDate`

Notice that `LicensePlate` is prime even though it is not part of the `{VIN}` candidate key—it qualifies because it belongs to the `{State, LicensePlate}` candidate key. This distinction becomes critical when we reach BCNF.

**Test Yourself 1b:**
Given a relation `CUSTOMER(CustID, Name, Address, Phone)` where `CustID` is the sole candidate key, and one customer can have multiple phone numbers (so `Phone` is not unique per customer), classify each attribute as prime or nonprime.

<details>
<summary>Answer</summary>
Candidate key: `{CustID}`. Prime: `CustID`. Nonprime: `Name`, `Address`, `Phone`.
</details>

**Test Yourself 1c:**
Consider `FLIGHT_RESERVATION(FlightID, PassengerID, SeatNumber, PassengerName, FlightDate)`. Domain rules: `{FlightID, PassengerID}` is a candidate key. Additionally, `{FlightID, SeatNumber}` uniquely identifies a passenger on that flight (no two passengers can have the same seat on the same flight). Classify each attribute as prime or nonprime.

<details>
<summary>Answer</summary>
Candidate keys: `{FlightID, PassengerID}` and `{FlightID, SeatNumber}`.
Prime attributes: `FlightID`, `PassengerID`, `SeatNumber` (each appears in at least one candidate key).
Nonprime attributes: `PassengerName`, `FlightDate`.
</details>

---

## 2. First Normal Form (1NF)

### 2.1 Intuition: The Atomicity Requirement

The relational model is built on the idea that each attribute holds a single, indivisible value. A table cell should contain one number, one string, or one date—not a list of values or a nested mini-table. 1NF is the formal statement of this structural rule. It is the **baseline** assumption of the relational model; every relation we consider from now on is assumed to be in 1NF.

**Why this is not obvious:** Many real-world data formats are naturally nested. A medical record might list multiple diagnoses per patient; an invoice contains line items. The impulse to store these as lists inside a single column is intuitive—it mirrors the document structure. 1NF forces us to flatten this structure, which can feel like "losing information" about the grouping. In fact, we are converting implicit grouping (position within a list) into explicit grouping (a shared key value across multiple rows). This is a trade-off: we gain queryability with standard relational operators at the cost of more rows.

**Cross-domain connection — the relational model versus document databases:** Document databases like MongoDB explicitly reject 1NF as a requirement—they encourage embedding nested arrays and subdocuments within a single document. This is not a design flaw; it is a different trade-off. Document databases optimize for read efficiency when you typically access the entire document (e.g., rendering a product page with all its images and reviews). Relational databases enforce 1NF to optimize for ad-hoc queries across entities (e.g., "find all products with at least one five-star review mentioning 'battery life'"). Understanding 1NF means understanding when the relational model's trade-off is appropriate and when a nested representation might serve your access patterns better. The key insight: 1NF is not universally superior; it is the cost of entry for the relational algebra's query flexibility.

**A different domain — library catalogs:** A library database might initially represent a book's authors as a single `Authors` column containing "Jane Smith, Robert Chen, Aisha Patel." This violates 1NF because the column contains multiple values. The 1NF decomposition creates an `AUTHORSHIP(BookID, AuthorName, AuthorOrder)` table, where `AuthorOrder` preserves the listing sequence. Now we can query "find all books co-authored by Robert Chen" using a standard equality predicate, and we can join with an `AUTHOR` table to retrieve biographical details. The grouping information—"these three authors collaborated on this book"—is preserved by the shared `BookID` across three rows.

**Industry Application — E-commerce Product Catalogs:**
Modern e-commerce platforms like Amazon and Shopify face the 1NF challenge at scale. A product can have multiple images, multiple variants (size, color), multiple categories, and multiple warehouse locations. The naive approach of storing these as JSON arrays in a single column is tempting—it mirrors the nested structure of a product page and simplifies the object-relational mapping in application code. However, when the analytics team needs to answer "which warehouse has the most red XL t-shirts in stock," querying nested JSON requires specialized operators and cannot leverage B-tree indexes effectively.

The industry-standard solution is exactly 1NF decomposition: a `ProductVariants` table with one row per SKU, a `ProductImages` table with one row per image URL, and a `ProductCategories` table with one row per category assignment. This increases row count by orders of magnitude but enables the full power of SQL indexing and aggregation. Companies that skip this step and rely on JSON columns inevitably build separate data warehouses with flattened schemas for analytics—paying the decomposition cost later, with added ETL complexity.

**Analogy — A spreadsheet with merged cells:** Imagine a spreadsheet where one cell in the "Diagnoses" column contains three lines of text separated by line breaks. You cannot sort by diagnosis, filter by diagnosis, or count patients per diagnosis without first splitting that cell programmatically. 1NF says: every cell must contain exactly one value, so that every relational operator works uniformly on every cell. The cost is more rows; the benefit is that the entire machinery of SQL—`WHERE`, `GROUP BY`, `JOIN`—works without special-case parsing.

### 2.2 Definition

A relation schema is in First Normal Form (1NF) if:
1.  The domain of each attribute includes only **atomic** (indivisible) values.
2.  The value of each attribute in any tuple is a single value from that domain.

This prohibits:
- **Multivalued attributes:** A column that holds sets, lists, or repeating groups (e.g., a `Diagnoses` column storing `{Hypertension, Diabetes, Asthma}`).
- **Composite attributes:** Nested structures treated as a single column (e.g., an `Address` column storing `(Street, City, Zip)` as a unit when we need to query individual components).

1NF is a **structural** constraint, not a dependency-based one. It says nothing about redundancy or anomalies; it only enforces the flat-table format.

### 2.3 Worked Example: Flattening a Repeating Group

**Before (violates 1NF):**
`EMPLOYEE_PROJECTS(EmpID, Name, Projects)`

| EmpID | Name  | Projects    |
|-------|-------|-------------|
| E1    | Alice | {P1, P2, P3}|
| E2    | Bob   | {P2, P4}    |

The `Projects` attribute holds a set of values, which is not atomic. The set notation `{P1, P2, P3}` is a miniature relation hiding inside a single cell. To query "which employees work on P2?" you cannot use a simple equality predicate; you need a set-membership operator, which most SQL dialects support but which breaks the uniform tuple-at-a-time model of the relational algebra.

**After (1NF):**
We flatten by creating one tuple per project assignment:
`ASSIGNMENT(EmpID, Name, Project)`

| EmpID | Name  | Project |
|