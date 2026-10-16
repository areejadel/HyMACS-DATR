# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** – State the definitions of 1NF, 2NF, 3NF, and BCNF in your own words.
2. **Understand** – Explain why each normal form addresses a specific type of redundancy anomaly.
3. **Apply** – Given a relation and a set of functional dependencies, determine which normal form the relation satisfies.
4. **Analyze** – Identify the precise functional dependency that violates a normal form and trace the resulting insertion, update, or deletion anomaly.
5. **Create** – Perform a lossless decomposition to bring a schema into 3NF or BCNF using the standard algorithms.

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

**Pause and imagine:** You're the DBA for a hospital system. A patient's allergy information lives in the `APPOINTMENTS` table because "that's where we need it during scheduling." The patient discovers a new drug allergy during a phone consultation. There's no appointment to attach it to. Where do you write it down? If your answer is "a sticky note," you've just lived an insertion anomaly. Normalization exists so your database never forces you to reach for that sticky note.

**Question to carry with you:** What if databases had been invented without normalization theory? Every application developer would be forced to invent their own ad-hoc rules for where to store each fact. Two teams building on the same database would make different choices, and data integrity would become a negotiation rather than a guarantee. Normalization is, at its core, a *discipline of agreement*—a shared vocabulary for reasoning about where facts belong.

### 1.2 Intuition

Consider a university database. We know that a given `StudentID` always belongs to exactly one `StudentName`. Whenever two rows share the same `StudentID`, they must share the same `StudentName`. This is not a coincidence—it is a rule enforced by the real world. We capture such rules as **functional dependencies (FDs)**.

### 1.3 Formal Definition

Let $X$ and $Y$ be sets of attributes in a relation schema $R$. A **functional dependency** $X \rightarrow Y$ holds if, for every possible instance of $R$, whenever two tuples agree on all attributes in $X$, they also agree on all attributes in $Y$.

Think of $X \rightarrow Y$ as: "Given a value for $X$, you can look up exactly one value for $Y$."

**Interactive moment:** Before we see an example, try articulating an FD from your own experience. If you've ever used a spreadsheet, you've likely internalized one without naming it. In a table of `(City, State, ZipCode)`, which attributes determine which others? Does `ZipCode` determine `City`? Does `City` determine `State`? Does `City` determine `ZipCode`? Hold your answers—we'll test them against the formal definition shortly.

### 1.4 Worked Example: Spotting an FD

Consider this `ENROLLMENT` table:

| StudentID | CourseID | Grade | StudentEmail     |
|-----------|----------|-------|------------------|
| S1        | C101     | A     | s1@univ.edu      |
| S1        | C102     | B     | s1@univ.edu      |
| S2        | C101     | A     | s2@univ.edu      |

- **FD1:** $\{\text{StudentID}\} \rightarrow \{\text{StudentEmail}\}$ holds. Every time S1 appears, the email is identical. S2 confirms it.
- **FD2:** $\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Grade}\}$ holds. The combination determines exactly one grade.
- **Does** $\{\text{CourseID}\} \rightarrow \{\text{Grade}\}$ hold? No—C101 appears with both A and B.

**Try this yourself:** Before reading on, scan the table and ask: does $\{\text{StudentEmail}\} \rightarrow \{\text{StudentID}\}$ hold? If two rows share the same email, must they share the same StudentID? (In this tiny instance, yes—but can you imagine a realistic scenario where it fails? What if two students share a family email address? That's the difference between an FD that holds in this instance and one that holds by the rules of the domain. An FD is a claim about *all possible* instances, not just the one you're looking at.)

### 1.5 Keys Revisited Through the Lens of FDs

- A **superkey** $SK$ satisfies $SK \rightarrow R$ (all attributes).
- A **candidate key** $K$ is a superkey such that no proper subset $K' \subset K$ satisfies $K' \rightarrow R$.

**Prime attribute:** An attribute that belongs to at least one candidate key.
**Nonprime attribute:** An attribute that belongs to no candidate key.

> **Quick Check 1:** In `ENROLLMENT`, what is a candidate key? Which attributes are prime, which are nonprime?
>
> *(Answer: $\{\text{StudentID}, \text{CourseID}\}$ is the only minimal superkey. Both are prime. `Grade` and `StudentEmail` are nonprime.)*

---

## 2. First Normal Form (1NF): The Starting Line

### 2.1 Why It Matters

The relational model assumes that every cell holds exactly one atomic value—no lists, no nested tables. If a column contains a set of values, we cannot write a simple FD about it, and we cannot index it or join on it reliably. 1NF is the baseline that makes all further normalization possible.

Think of it this way: a table not in 1NF is like a book where some "words" are actually whole paragraphs stuffed into a single character slot. You can't alphabetize it, you can't search it, and you certainly can't reason about what determines what.

**A real-world scar:** In the early days of a now-famous e-commerce platform, the `Orders` table had a `ProductsOrdered` column that stored comma-separated product IDs. Reporting on "how many units of product X sold last month" required string-parsing every row in the table. A query that should have been a simple `COUNT` with a `WHERE` clause became a nightly batch job that ran for hours. The developers weren't incompetent—they were optimizing for write speed without understanding what they were sacrificing. That's the trap 1NF prevents.

**Another industry example — healthcare:** A clinic's legacy system stored patient diagnoses in a single `Diagnoses` column as a pipe-delimited string: `"J45.0|E11.9|I10"`. When the billing department needed to count how many patients had each ICD-10 code for insurance reporting, the query required substring extraction, splitting, and deduplication across millions of records. A report that should take seconds ran for 45 minutes and occasionally crashed the production server. The fix—decomposing into a `PATIENT_DIAGNOSIS` table with one row per patient per code—reduced the report time to under two seconds and enabled proper indexing, constraint enforcement, and epidemiological analytics that were previously impossible. This is not merely an academic exercise: 1NF violations directly block operational and analytical capabilities.

**Yet another example — logistics and supply chain:** A freight company's `SHIPMENT` table stored `StopLocations` as a JSON array: `[{"city":"Chicago","type":"pickup"},{"city":"Denver","type":"transfer"},{"city":"Phoenix","type":"delivery"}]`. Routing optimization required extracting each stop, joining against a `WAREHOUSE` table for capacity planning, and computing transit times between consecutive stops. The JSON-in-a-column design made these queries nearly impossible to express in SQL; the team resorted to exporting data to Python scripts for processing, introducing latency and inconsistency. Normalizing to a `SHIPMENT_STOP` table with `(ShipmentID, StopSequence, City, StopType)` made the data queryable by standard SQL, enabled foreign key constraints to warehouse locations, and allowed the routing engine to operate directly on the database.

**Try this yourself:** Open a spreadsheet you use regularly—a budget tracker, a gradebook, a project log. Find a cell that contains multiple values separated by commas, pipes, or line breaks. Now imagine you needed to sort, filter, or count by one of those individual values. What would you have to do? That friction is exactly what 1NF eliminates.

### 2.2 Definition

A relation schema $R$ is in **First Normal Form (1NF)** if the domain of every attribute is atomic, and each tuple contains exactly one value from that domain per attribute.

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

Now every cell is single-valued. We have introduced redundancy (`Name` repeats for Alice), but that is exactly what higher normal forms will eliminate.

**Extended example — financial services:** A brokerage firm's `CLIENT_PORTFOLIO` table originally stored `Holdings` as a repeating group:

| ClientID | AccountType | Holdings                                  |
|----------|-------------|-------------------------------------------|
| C001     | Retirement  | {AAPL:200, GOOG:50, TSLA:30}             |
| C002     | Brokerage   | {AAPL:100, AMZN:15}                       |

This design prevented the firm from computing aggregate exposure to a single stock across all clients, from enforcing position limits per account type, and from running daily compliance checks. After 1NF decomposition:

| ClientID | AccountType | Ticker | Shares |
|----------|-------------|--------|--------|
| C001     | Retirement  | AAPL   | 200    |
| C001     | Retirement  | GOOG   | 50     |
| C001     | Retirement  | TSLA   | 30     |
| C002     | Brokerage   | AAPL   | 100    |
| C002     | Brokerage   | AMZN   | 15     |

With this structure, `SELECT Ticker, SUM(Shares) FROM CLIENT_HOLDINGS GROUP BY Ticker` instantly answers the exposure question. A `CHECK` constraint on `Shares > 0` enforces data integrity. An index on `Ticker` makes compliance scans efficient. The cost—repeating `ClientID` and `AccountType`—is real but manageable, and higher normal forms will address it.

### 2.4 Common Misconception

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

**Anecdote:** A logistics company once stored `(WarehouseID, ProductID, WarehouseAddress, QuantityOnHand)`. The composite key was `{WarehouseID, ProductID}`, but `WarehouseAddress` depended only on `WarehouseID`. When a warehouse relocated, someone updated 497 out of 512 rows—fat-fingering the 498th. For six months, half the inventory reports showed the old address for 14 products. Shipments went to an empty lot. The root cause wasn't a bad update script; it was a table asking one composite key to govern two unrelated facts.

**Another industry example — telecommunications:** A mobile carrier's `SUBSCRIBER_SERVICE` table tracked which subscriber used which service plan. The schema was `(SubscriberID, PlanID, SubscriberName, PlanMonthlyFee, ActivationDate)`. The key was `{SubscriberID, PlanID}`, but `SubscriberName` depended only on `SubscriberID`, and `PlanMonthlyFee` depended only on `PlanID`. When the carrier adjusted the monthly fee for a popular plan, the update had to touch hundreds of thousands of rows. During the update window, concurrent reads saw inconsistent fees—some rows showed the old price, others the new. The billing system generated incorrect invoices for thousands of customers, triggering a flood of support calls and regulatory complaints. The root cause: a partial dependency that should have been resolved by 2NF decomposition. After splitting into `SUBSCRIBER(SubscriberID, SubscriberName)`, `PLAN(PlanID, PlanMonthlyFee)`, and `SUBSCRIPTION(SubscriberID, PlanID, ActivationDate)`, a single-row update to the `PLAN` table changed the fee atomically for all affected subscribers.

**Yet another example — education administration:** A university's `COURSE_REGISTRATION` table stored `(StudentID, SectionID, StudentName, CourseTitle, InstructorName, Grade)`. The composite key was `{StudentID, SectionID}`, but `StudentName` depended only on `StudentID`, and both `CourseTitle` and `InstructorName` depended only on `SectionID` (assuming one instructor per section). When a professor changed their legal name, the registrar's office had to update every row for every section that professor had ever taught—a cascading update that occasionally missed rows, causing transcripts to show different names for the same instructor across different semesters. Decomposing into `STUDENT(StudentID, StudentName)`, `SECTION(SectionID, CourseTitle, InstructorName)`, and `REGISTRATION(StudentID, SectionID, Grade)` eliminated the redundancy and made name changes a single-row operation.

**Pause and predict:** Before we define 2NF formally, can you articulate what rule a table must follow to avoid these problems? You've seen the pattern: a non-key attribute that depends on only part of the key is the culprit. What would the formal statement look like?

### 3.2 Full Functional Dependency (Prerequisite Concept)

An FD $X \rightarrow Y$ is **full** if no proper subset $X' \subset X$ satisfies $X' \rightarrow Y$. Otherwise, it is **partial**.

### 3.3 Definition of 2NF

A relation schema $R$ is in **Second Normal Form (2NF)** if:
1. It is in 1NF, and
2. Every nonprime attribute is fully functionally dependent on every candidate key.

### 3.4 Worked Example: Decomposing to 2NF

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

**Extended example — insurance claims:** An insurance company's `CLAIM_PAYMENT` table had attributes `(ClaimID, PaymentSequence, PolicyHolderName, PolicyType, PaymentAmount, PaymentDate)` with key `{ClaimID, PaymentSequence}`. `PolicyHolderName` and `PolicyType` depended only on `ClaimID`, not on `PaymentSequence`—a partial dependency. When a claim involved multiple payments (e.g., initial estimate payment, supplement payment, final settlement), the policyholder's name was repeated in every payment row. A name correction required updating every payment row for that claim. Worse, a claim with no payments yet (just filed, awaiting adjuster review) could not be recorded because `PaymentSequence` was part of the key and had no value. Decomposition to 2NF produced `CLAIM(ClaimID, PolicyHolderName, PolicyType)` and `PAYMENT(ClaimID, PaymentSequence, PaymentAmount, PaymentDate)`, allowing claims to exist before any payment was issued—solving both the update anomaly and the insertion anomaly.

**Try this yourself:** Before moving to 3NF, ask: in $R_2$, does `ProjectBudget` depend on `ProjectID` alone? Yes—that's the key. But what if each project has a `DepartmentID`, and each department has a fixed budget allocation? Then `ProjectBudget` might depend on `ProjectID` only transitively, through `DepartmentID`. That's exactly the 3NF violation we tackle next.

### 3.5 Common Misconception

"If a table has a single-attribute primary key, it is automatically in 2NF." This is true only because a single-attribute key has no proper subsets to cause partial