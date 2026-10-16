# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** – State the definitions of 1NF, 2NF, 3NF, BCNF, 4NF, and 5NF, and identify the key property each form enforces.
2. **Understand** – Explain why partial dependencies, transitive dependencies, non-superkey determinants, multi-valued dependencies, and join dependencies cause update anomalies.
3. **Apply** – Given a relation schema and a set of dependencies (functional, multi-valued, join), determine its normal form and decompose it to the next higher form.
4. **Analyze** – Diagnose a real-world schema for normalization violations and predict the specific anomalies that will occur.
5. **Evaluate** – Decide when to stop at 3NF versus BCNF versus 4NF/5NF based on dependency preservation, performance trade-offs, and the nature of the dependencies present.

---

## Prerequisites Check

We assume you can:

- Read a relation schema written as `R(attr1, attr2, ...)` with a primary key underlined.
- Write a basic SQL `SELECT` statement and recognize that a table is a set of tuples.
- Understand the idea of a constraint: a rule that limits what data is valid.

If the term "tuple" is unfamiliar: a tuple is a row in a table. We use "tuple" and "row" interchangeably.

---

## Intuition First: The Problem Normalization Solves

**Before we dive in, pause for a moment on this question:** You're building an application that tracks university course enrollments. A student changes their email address. How many places in your database must you update that single fact? If your answer is "more than one," then your database has a design flaw that will eventually cause it to contradict itself. How would you even *know* which copy is correct when they diverge?

This is the central tension normalization addresses, and we'll resolve it systematically. But first, let's see what happens when it goes wrong.

Imagine you're a detective arriving at a crime scene — except the crime scene is a database, and the crime is that every time someone tries to change a single fact, the database fights back by corrupting itself. Your job: figure out why the database keeps lying to you.

Here's the crime scene. A company spreadsheet tracks employees and their projects:

| EmpID | EmpName | Dept | DeptPhone | ProjectID | ProjName |
|-------|---------|------|-----------|-----------|-----------|
| 101   | Alice   | Sales | 555-0100 | P1        | WidgetX  |
| 101   | Alice   | Sales | 555-0100 | P2        | WidgetY  |
| 102   | Bob     | Sales | 555-0100 | P1        | WidgetX  |
| 103   | Carol   | HR    | 555-0200 | P3        | Onboard  |

**The three ways this database will betray you:**

- *Update anomaly:* If the Sales department's phone number changes, you must update three rows. Miss one, and Sales now has two phone numbers. The database now claims two contradictory facts about the same department. Which one is true? The database cannot tell you — it has no mechanism to prevent this contradiction.

- *Insertion anomaly:* You want to record that a new department "Legal" exists with phone 555-0300. But you can't. The `EmpID` column is part of the key, and it demands a value. You are forced to invent a ghost employee just to record a department fact. The database's structure is holding your data hostage.

- *Deletion anomaly:* Carol leaves the company. You delete her row — and suddenly the fact that HR's phone number is 555-0200 vanishes from existence. The database just forgot a fact about a department that still exists, all because you removed an employee.

**Try this yourself:** Before reading further, look at the table above and identify: how many distinct *facts* are stored in this single table? List them. Then count how many times each fact appears. You should find that some facts appear multiple times — those are the ones causing trouble.

**The root cause is simple but devastating:** a single fact (like "the Sales department's phone number") is stored in multiple places. Every copy is an opportunity for contradiction. Normalization is the mechanical process of restructuring the schema so each fact lives in exactly one place — no more, no less. We use functional dependencies as our forensic tool to detect where facts are being duplicated, and decomposition as our surgical instrument to separate them.

**A cross-domain lens: the DRY principle in software engineering.** If you've written code, you know "Don't Repeat Yourself" — a single logical fact should have a single authoritative representation. When you copy-paste a function, you create a maintenance nightmare: fix one copy, forget the other, and the system now behaves inconsistently. Normalization is DRY applied to data. A violation of 3NF is the database equivalent of the same magic number appearing in five different source files. BCNF is the stricter version that catches edge cases DRY alone might miss — like when two modules each think they "own" the same mapping between concepts. The normalization forms give you a formal, provable way to detect and eliminate these repetitions, rather than relying on programmer vigilance.

**Industry practice: normalization in the software development lifecycle.** In professional software engineering, normalization is not a one-time academic exercise performed in isolation. It is embedded in the iterative process of database design and typically occurs during logical data modeling, before any SQL is written. Practitioners use Entity-Relationship (ER) diagrams or UML class diagrams to capture entities and their relationships, then systematically convert these into normalized relation schemas. Tools such as Oracle SQL Developer Data Modeler, ERwin, and MySQL Workbench can automatically analyze a schema for normalization violations and suggest decompositions. In agile environments, normalization is often performed incrementally: the team normalizes only the tables directly affected by the current sprint's user stories, deferring broader refactoring until integration testing reveals anomalies. A senior database administrator at a major financial services firm describes their rule of thumb: "We normalize to 3NF by default for all transactional systems. We denormalize only when a specific query pattern is proven, through load testing, to be a bottleneck — and we document every denormalization with a comment block explaining which form was violated, why, and what integrity checks the application layer now owns." This deliberate, documented approach ensures that the team understands the trade-offs and can revisit decisions as requirements evolve.

**Case study: an e-commerce inventory disaster.** In 2018, a mid-size e-commerce company migrated their product catalog from a denormalized spreadsheet to a relational database. The original schema stored product details, warehouse locations, and supplier information in a single table:

```
ProductInventory(ProductID, ProductName, SupplierID, SupplierName, 
                 SupplierPhone, WarehouseID, WarehouseAddress, QuantityOnHand)
```

The candidate key was `{ProductID, WarehouseID}`. The FDs included `ProductID → ProductName, SupplierID` and `SupplierID → SupplierName, SupplierPhone`. This violated 2NF (partial dependencies on `ProductID`) and 3NF (transitive dependencies through `SupplierID`). Within six months of going live, the company experienced three critical incidents:

1. A supplier changed their phone number. The update script missed 47 rows out of 2,300, causing purchase orders to carry an outdated contact number. Two shipments were delayed by a week.
2. A new supplier was contracted but had not yet shipped any products. The system could not record the supplier's information because `ProductID` (part of the key) could not be null. The procurement team maintained a separate shadow spreadsheet, which fell out of sync.
3. A product line was discontinued. Deleting the last product from a supplier also deleted that supplier's record, severing the relationship with a vendor who still supplied other categories of goods.

The remediation normalized the schema into:

```sql
Supplier(SupplierID, SupplierName, SupplierPhone)
Product(ProductID, ProductName, SupplierID)  -- SupplierID is a foreign key
Warehouse(WarehouseID, WarehouseAddress)
Inventory(ProductID, WarehouseID, QuantityOnHand)
```

The total engineering cost of the incidents — including emergency fixes, data reconciliation, and lost sales — was estimated internally at $180,000. The normalized redesign took two developer-weeks. This case illustrates a hard-won industry lesson: the cost of normalization is paid upfront in design time; the cost of denormalization is paid repeatedly in production incidents.

**Interactive discussion prompt:** In small groups, discuss: have you ever encountered a situation in your own projects — whether a spreadsheet, a personal database, or a coding project — where the same information was stored in multiple places and got out of sync? What was the cost of that inconsistency? How did you resolve it? Share one example with the class.

---

## 1. Foundational Concepts: Keys and Functional Dependencies

### 1.1 Learning Objective for This Section

Given a relation schema and a set of business rules, you will identify candidate keys, classify attributes as prime or nonprime, and express the rules as functional dependencies.

---

### 1.2 Functional Dependencies: The Detective's Tool

**Intuition.** A functional dependency (FD) captures a statement of the form: "If I know X, then I know exactly one Y." Think of it like a fingerprint at a crime scene: if you find a particular fingerprint pattern (X), it points to exactly one suspect (Y). Two crime scenes with the same fingerprint must involve the same person. Similarly, two database rows with the same X must have the same Y.

It is a business rule, not a property of the current data.

**Formal Definition.** Given a relation schema $R$, an FD $X \rightarrow Y$ holds if, for every allowable instance $r(R)$, whenever two tuples agree on all attributes in $X$, they must also agree on all attributes in $Y$. $X$ and $Y$ are sets of attributes from $R$.

We write $X \rightarrow Y$ and read it as "$X$ functionally determines $Y$."

**Example.** In a university database, the rule "each instructor belongs to exactly one department" becomes:

$$\text{Instructor} \rightarrow \text{Department}$$

If two rows show `Instructor = 'Dr. Chen'`, they must both show the same `Department` value. If they do not, the business rule is violated.

**Important:** An FD is a constraint on *all possible future states* of the database, not just the current snapshot. You cannot verify an FD by looking at today's data alone; you must know the business rule. It's like trying to prove "every person has exactly one biological mother" by surveying a single classroom — the data might accidentally support it, but the rule is about how the world works, not what you happened to observe today.

**Quick quiz:** A student looks at a table of current course enrollments and observes that every student has a different email address. They conclude `Email → StudentID` is an FD. Is this conclusion valid? Why or why not? *(Pause and discuss with a neighbor for 30 seconds.)*

**Cross-domain insight: FDs as a one-way hash function.** In computer security, a cryptographic hash function maps an input to a fixed output: `hash(X) → Y`. Given X, you can always find Y; given Y, you cannot reconstruct X. A functional dependency is structurally similar but semantically inverted — it's a deterministic mapping where X determines Y, but unlike a hash, the mapping is not designed to be irreversible. The analogy helps because it highlights a critical property: just as two different inputs should not produce the same hash (collision resistance), two tuples with the same X must not produce different Y values. A violation of an FD is a collision in this "business-rule hash function" — and collisions in databases are anomalies, not security vulnerabilities.

**Industry practice: how FDs are discovered in real projects.** In practice, functional dependencies are rarely handed to a database designer as a tidy list. They are extracted through three primary methods. First, *stakeholder interviews*: a data architect asks domain experts questions like "If I give you an employee ID, can you tell me exactly one department?" The answers are formalized as FDs. Second, *data profiling*: tools such as Apache Griffin, Talend Data Quality, or custom SQL scripts scan existing datasets to identify columns that appear to be functionally determined by others. However, these tools flag *candidate* FDs only — the designer must validate with business stakeholders that the observed pattern reflects a rule, not a coincidence. Third, *reverse-engineering from application code*: when inheriting a legacy system, developers examine `WHERE` clauses, unique constraints, and application-level validation logic to infer the FDs that the original designers assumed. A common pitfall is discovering that the application enforces an FD in code (e.g., a Python script checks that each product has exactly one supplier) but the database schema does not — leaving the constraint invisible to anyone querying the database directly. Normalization brings these implicit rules into the schema where they belong.

---

### 1.3 Superkeys and Candidate Keys

**Superkey (Intuition).** A set of attributes that, taken together, uniquely identifies every row. No two rows can have the same combination of values for a superkey. Think of it as a DNA sample: if two crime scenes yield the same DNA, they involve the same person. The DNA is a superkey for identifying individuals.

**Formal Definition.** A set of attributes $SK \subseteq R$ is a superkey of relation schema $R$ if, for any two tuples $t_1, t_2$ in any valid instance $r(R)$, whenever $t_1[SK] = t_2[SK]$, then $t_1 = t_2$.

**Worked Example.** In a table `Employee(EmpID, SSN, Name, Dept)`:

- $\{\text{EmpID}\}$ is a superkey: no two employees share the same EmpID.
- $\{\text{SSN}\}$ is a superkey: SSN is unique per person.
- $\{\text{EmpID}, \text{Name}\}$ is a superkey, but it is *redundant*—we do not need `Name` to guarantee uniqueness.

**Candidate Key.** A candidate key is a *minimal* superkey. Remove any attribute from it, and it stops being a superkey. It's the smallest DNA sample that still uniquely identifies someone — no extra information included.

In the example above:

- $\{\text{EmpID}\}$ is a candidate key (minimal).
- $\{\text{SSN}\}$ is a candidate key (minimal).
- $\{\text{EmpID}, \text{Name}\}$ is *not* a candidate key because we can drop `Name` and still have a superkey.

A schema may have multiple candidate keys. We designate one as the *primary key* for physical implementation; the others are *alternate keys*.

**Industry practice: choosing a primary key.** In production systems, the choice of primary key from among candidate keys involves practical considerations beyond minimality. Natural keys (e.g., SSN, email address) carry business meaning and can serve as the primary key when they are stable, universally available, and guaranteed unique. However, natural keys are often problematic: SSNs raise privacy concerns and are not assigned to non-citizens, email addresses change when users switch providers, and product codes get reused after discontinuation. For this reason, many organizations default to *surrogate keys* — system-generated integers or UUIDs with no business meaning — as the primary key, while enforcing uniqueness on natural keys through `UNIQUE` constraints. A data architect at a healthcare startup notes: "We use surrogate primary keys on every table. Our natural keys — patient medical record numbers, provider NPI numbers — have `UNIQUE NOT NULL` constraints. This gives us stable foreign key references that never need cascading updates, while still preventing duplicate business entities." The trade-off is that surrogate keys obscure the business rules that FDs capture, so normalization analysis must still be performed against the natural candidate keys, not the surrogates.

---

### 1.4 Prime vs. Nonprime Attributes

**Definition.** An attribute is **prime** if it belongs to at least one candidate key. Otherwise it is **nonprime**.

**Worked Example.** Consider `Enrollment(StudentID, CourseID, Grade)`. Candidate key: $\{\text{StudentID}, \text{CourseID}\}$.

- `StudentID` is prime (it is in the key).
- `CourseID` is prime (it is in the key).
- `Grade` is nonprime (it is not in any candidate key).

This distinction is central to 3NF. Prime means "part of some key"; nonprime means "not part of any key." Think of prime attributes as the identification system — they tell you who or what a row is about. Nonprime attributes are just facts about whatever the key identifies.

**Try this yourself:** In a table `Flight(FlightID, Date, PilotID, PassengerID, SeatNumber)` where no two passengers on the same flight can share a seat, what is a candidate key? Which attributes are prime, and which are nonprime?

---

### 1.5 Full vs. Partial Functional Dependencies

**Intuition.** A full dependency means the entire left-hand side is needed to determine the right-hand side. A partial dependency means a piece of the left-hand side already does the job. Imagine a safe with two keys that must be turned simultaneously to open it — that's a full dependency. If one key alone can open it, that's partial.

**Formal Definition.** An FD $X \rightarrow Y$ is **full** if removing any attribute $A$ from $X$ causes the dependency to fail. That is, there is no proper subset $X' \subset X$ such that $X' \rightarrow Y$ holds.

If such an $X'$ does exist, the dependency is **partial**.

**Worked Example.** In `EMP_PROJ(EmpID, ProjID, Hours, EmpName)` with candidate key $\{\text{EmpID}, \text{ProjID}\}$:

- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$ is full: you need both the employee and the project to know the hours worked. Neither EmpID alone nor ProjID alone tells you the hours.
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{EmpName}$ is partial: $\text{EmpID} \rightarrow \text{EmpName}$ already holds. `EmpName` depends on only part of the key.

Partial dependencies are the defect that 2NF eliminates. Notice the pattern: a nonprime attribute depending on a proper subset of a candidate key. It's a signal that the attribute actually describes only part of what the key identifies — like storing a person's name in a table keyed by both person and project. The name doesn't care which project you're looking at.

**Cross-domain connection: the data science perspective.** In machine learning, feature engineering involves selecting which variables predict a target. A partial dependency in a database schema is structurally identical to a feature that is redundant given a subset of other features. If `EmpID` alone predicts `EmpName` perfectly, then adding `ProjID` to the predictor set adds no information — it inflates dimensionality without improving predictive power. Data scientists call this multicollinearity or feature redundancy and eliminate it to avoid overfitting and wasted computation. Database designers call it a 2NF violation and eliminate it to avoid update anomalies. Same mathematical structure, different consequences: one degrades model performance, the other degrades data integrity.

**Industry practice: detecting partial dependencies in legacy schemas.** When inheriting a database that was never formally normalized, partial dependencies are among the most common — and most damaging — violations. A practical detection technique used by database reliability engineers is the "GROUP BY test": for each candidate key K and each nonprime attribute A, run `SELECT subset_of_K, COUNT(DISTINCT A) FROM table GROUP BY subset_of_K HAVING COUNT(DISTINCT A) > 1`. If any subset of K yields exactly one distinct value of A across all groups, that signals a potential partial dependency. For example, if `SELECT EmpID, COUNT(DISTINCT EmpName) FROM EMP_PROJ GROUP BY EmpID` returns a count of 1 for every EmpID, then `EmpID → EmpName` is likely an FD. This is a heuristic, not a proof — it confirms the pattern in current data but does not guarantee the business rule — but it efficiently surfaces candidate violations for stakeholder review. A database engineer at a logistics firm reports: "We ran this test against our 15-year-old shipment database and found 23 partial dependency candidates in a single afternoon. Twelve were confirmed as business rules and decomposed. The rest were coincidences — for example, every warehouse in Texas happened to have