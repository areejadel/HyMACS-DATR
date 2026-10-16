By the end of this lecture, you will be able to:  
1. **Define** the conditions for First Normal Form (1NF), Second Normal Form (2NF), Third Normal Form (3NF), and Boyce-Codd Normal Form (BCNF) using precise, measurable criteria.  
2. **Explain** how functional dependencies and candidate keys determine whether a relation violates a given normal form.  
3. **Apply** decomposition techniques to convert a relation into 2NF, 3NF, and BCNF, ensuring lossless joins.  
4. **Analyze** a database schema to identify insertion, deletion, and update anomalies caused by partial and transitive dependencies.  
5. **Evaluate** trade-offs between normalization (reducing redundancy) and denormalization (improving performance) in real-world design.

---

### The Anomaly That Broke the Registrar’s Office

Imagine this: a university registrar updates the instructor of a course from “Dr. Lee” to “Dr. Patel.” Simple change, right? But in their database, that single fact is repeated across hundreds of enrollment records. They update 98 rows… and accidentally skip two. Now the system claims CS101 has *two* instructors. Students are confused. Schedules conflict. The change log shows no trace of who made the error.

Now imagine the fix: the registrar changes one row—just one—and *every* reference to CS101 instantly reflects Dr. Patel. No search. No guesswork. The truth is singular, and consistency is automatic.

What separates these two worlds? Not better software. Not more careful users.  
It’s **schema design**.

This isn’t a software bug. It’s a **design flaw**—a consequence of storing logically independent facts as duplicated data. And it’s entirely preventable.

Normalization is not about rigid rules. It’s about **isolating facts** so that each piece of information has a single, unambiguous home. When you change a fact, you change it *once*, and the truth propagates everywhere.

Let’s begin.

---

### Prerequisites: Functional Dependencies and Candidate Keys

Before proceeding, we establish key concepts. Let $ R $ be a relation schema over a set of attributes. A **functional dependency (FD)** $ X \rightarrow Y $ holds on $ R $ if, for any two tuples in $ R $, equality on all attributes in $ X $ implies equality on all attributes in $ Y $. That is, the value of $ X $ uniquely determines the value of $ Y $.

Think of an FD as a **promise** the database makes: *“If you know X, you can look up Y with certainty.”*  
For example, $ \text{StudentID} \rightarrow \text{StudentName} $ means that each student ID corresponds to exactly one name—no ambiguity.

A **candidate key** is a minimal set of attributes that functionally determines all other attributes in the relation. It must satisfy two properties:
- **Uniqueness**: No two distinct tuples can have the same values on the key attributes.
- **Minimality**: No proper subset of the key functionally determines all attributes.

We use the following running example throughout:

> **Enrollments**(StudentID, StudentName, Course, Instructor, CourseLevel)  
> With functional dependencies:  
> - $ \text{StudentID} \rightarrow \text{StudentName} $  
> - $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $  
> - $ \text{StudentID}, \text{Course} \rightarrow \text{StudentName}, \text{Instructor}, \text{CourseLevel} $

This schema records student enrollments and includes derived data such as instructor and course level.

> **Common Misconception Alert**:  
> Having a primary key does not guarantee normalization beyond 1NF. Redundancy and anomalies may persist due to functional dependencies involving non-key attributes.

> **Quick Check**:  
> In the `Enrollments` relation, is `StudentID` a candidate key?  
> No. While `StudentID` determines `StudentName`, it does not determine `Course`, `Instructor`, or `CourseLevel`. Thus, it fails to determine all attributes and is not a candidate key. The only candidate key is $ \{\text{StudentID}, \text{Course}\} $, which is both unique and minimal.

---

### Step 1: First Normal Form (1NF) — Atomic Values and No Repeating Groups

**Learning Objective**: Define and achieve 1NF by ensuring atomic attribute values and eliminating repeating groups.

Normalization begins with **First Normal Form (1NF)**, which ensures that the relation adheres to the basic tabular structure of the relational model.

> A relation is in **1NF** if and only if:
> - Every attribute contains **atomic (indivisible)** values.
> - There are **no repeating groups** (e.g., multiple values in a single cell).

#### Why Atomicity Is Non-Negotiable

Consider a denormalized version of `Enrollments`:

| StudentID | StudentName | Course           | Instructor | CourseLevel |
|-----------|-------------|------------------|------------|-------------|
| S001      | Alice       | CS101, CS102     | Dr. Lee    | Intro       |

Here, `Course` contains a list. This looks convenient—until you try to answer: *“Which students are taking CS101?”*  
You can’t use equality. You must parse strings. What if one row says “CS101,CS102” and another “CS101, CS102”? Are they the same?

This is like storing a person’s phone numbers as a comma-separated string in a single field. If you ever need to validate, search, or update one number, you’re forced to manipulate the entire string—a fragile, error-prone process.

**Atomicity isn’t about neatness. It’s about computability.** Databases rely on exact matches. If a value isn’t atomic, it can’t participate reliably in joins, constraints, or queries.

Now, consider a deeper analogy: **chemical elements**. Just as a molecule must be broken into atoms to understand its composition and reactivity, data must be decomposed into atomic units to be meaningfully processed. You wouldn’t describe water as “wet-clear-flowing” in one box—you’d write H₂O, with each atom accountable. Similarly, a cell holding “CS101, CS102” is a compound; normalization splits it into elemental facts.

#### Worked Example: Achieving 1NF

To satisfy 1NF, we decompose multivalued entries into separate rows.

**Original (violates 1NF)**:

| StudentID | StudentName | Course           | Instructor | CourseLevel |
|-----------|-------------|------------------|------------|-------------|
| S001      | Alice       | CS101, CS102     | Dr. Lee    | Intro       |

**Normalized to 1NF**:

| StudentID | StudentName | Course  | Instructor | CourseLevel |
|-----------|-------------|---------|------------|-------------|
| S001      | Alice       | CS101   | Dr. Lee    | Intro       |
| S001      | Alice       | CS102   | Dr. Lee    | Intro       |

Each cell now contains a single, atomic value. Operations such as querying, inserting, and updating individual enrollments are now well-defined.

> **Clarification**: 1NF does not formally require a candidate key. However, in practice, we define one to ensure tuple distinguishability. In this case, $ \{\text{StudentID}, \text{Course}\} $ serves as the candidate key.

> **Try This Yourself**:  
> Suppose a course can have multiple instructors, and we store them as "Dr. Lee, Dr. Smith" in the `Instructor` column. Does this violate 1NF?  
> Yes. The `Instructor` attribute would then contain a multivalued, non-atomic entry. To preserve 1NF, we must either split into separate rows or introduce a separate relation (e.g., `CourseInstructors(Course, Instructor)`).

#### Real-World Application: Healthcare Records

In electronic health record (EHR) systems, a patient’s medications are sometimes stored as a single text field:  
`"Metformin 500mg, Lisinopril 10mg, Atorvastatin 20mg"`.

This violates 1NF. Queries like *“Which patients take Lisinopril?”* require string pattern matching, which is slow and error-prone (e.g., misspelled dosages). Worse, drug interaction checks cannot be automated reliably.

Modern EHRs enforce 1NF by storing medications in a separate table:

> **PatientMeds**(PatientID, DrugName, Dosage, Frequency, StartDate)

This enables precise queries, automated alerts, and integration with clinical decision support systems. For instance, when a new prescription is entered, the system can instantly flag dangerous combinations—only because each drug is an atomic fact.

#### Additional Real-World Application: Social Media Content Tagging

In a social media platform, user posts may include hashtags stored as a single string:  
`"Loving the weather #sunny #outdoors #weekend"`.

If the `Tags` field contains `"#sunny #outdoors"` as a single value, querying for all posts tagged `#outdoors` requires substring searches, which are inefficient and fail to leverage indexing. Moreover, analytics on trending topics become inaccurate due to inconsistent formatting (e.g., `#Outdoors`, `#outdoors`, `#outdoors!`).

To satisfy 1NF, platforms normalize tags into a junction table:

> **PostTags**(PostID, Tag)

Each hashtag is stored atomically, enabling:
- Fast retrieval of all posts under a given tag.
- Accurate trend analysis.
- Efficient enforcement of constraints (e.g., maximum of 10 tags per post).

This design underpins scalable features like real-time hashtag feeds and content moderation pipelines.

#### Expanded Real-World Application: Financial Transaction Systems

In high-frequency trading platforms, transaction records may include multiple securities traded in a single order. A denormalized schema might store:

> **Trades**(TradeID, TraderID, Securities, Quantities, Timestamp)

With `Securities` containing `"AAPL, TSLA, MSFT"` and `Quantities` `"100, 50, 200"`.

This violates 1NF and creates severe operational risks:
- Cannot validate individual security trades without parsing strings.
- Cannot enforce referential integrity to a `Securities` master table.
- Risk of mismatched lists (e.g., three securities but only two quantities).

To achieve 1NF, such systems use:

> **TradeDetails**(TradeID, SecuritySymbol, Quantity)

Each security in a trade becomes a separate row. This allows:
- Atomic validation against a security master list.
- Real-time compliance checks (e.g., position limits per ticker).
- Accurate audit trails required by regulators like the SEC.

Without 1NF, firms risk regulatory penalties and settlement failures.

---

### Step 2: Second Normal Form (2NF) — Eliminate Partial Dependencies

**Learning Objective**: Identify and eliminate partial dependencies to achieve 2NF.

Now that we’re in 1NF, we face a deeper issue: **redundant facts masquerading as independent data**.

> A relation is in **2NF** if and only if:
> - It is in 1NF, and  
> - Every **non-prime attribute** is **fully functionally dependent** on every candidate key.

- A **non-prime attribute** is an attribute not part of any candidate key.
- A **partial dependency** occurs when a non-prime attribute depends on a proper subset of a composite candidate key.

#### The Hidden Cost of Partial Dependencies

In the 1NF `Enrollments` table:

| StudentID | StudentName | Course  | Instructor   | CourseLevel |
|-----------|-------------|---------|--------------|-------------|
| S001      | Alice       | CS101   | Dr. Lee      | Intro       |
| S001      | Alice       | CS102   | Dr. Smith    | Advanced    |
| S002      | Bob         | CS101   | Dr. Lee      | Intro       |

Functional dependencies:
- $ \text{StudentID} \rightarrow \text{StudentName} $
- $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $
- Candidate key: $ \{\text{StudentID}, \text{Course}\} $

Here’s the problem:  
- `StudentName` depends only on `StudentID`, not the full key → partial dependency.  
- `Instructor` and `CourseLevel` depend only on `Course` → another partial dependency.

So when Bob enrolls in CS101, we record:
- That Bob’s name is Bob (already known),
- That CS101 is taught by Dr. Lee (already known),
- That CS101 is an Intro course (already known).

We’re **repeating known facts** just to record a new enrollment.

This is like mailing a full biography with every invoice—just to remind the recipient of your name.

But here’s a cross-domain insight: think of this like **version control in software**. Each enrollment row is like a commit that embeds the entire project state—even unchanged files. Git avoids this by storing only diffs and linking to immutable objects. Similarly, normalization extracts stable facts (like student names) into reference tables, so they’re stored once and referenced many times.

Now, here’s a moment to pause:  
What if you *couldn’t* change the schema? What if you had to live with this redundancy?  
You’d need triggers, application logic, or manual checks to maintain consistency. But those are **workarounds**, not solutions. The real fix is structural.

> **Consequence**:  
> - **Update anomaly**: Change Dr. Lee to Dr. Patel? You must update every row with CS101. Miss one? Inconsistency.  
> - **Insertion anomaly**: Want to add a new course before any enrollments? Can’t—no StudentID to fill.  
> - **Deletion anomaly**: Remove the last student in CS101? You lose the course’s instructor and level.

The tension is clear: we’re storing **two kinds of facts** in one table:
1. *Who is enrolled in what?*  
2. *Who teaches which course, and at what level?*

These should be separate.

> **Try This Yourself**:  
> In the `Enrollments` table, suppose we add `Semester` as an attribute, and the candidate key becomes $ \{\text{StudentID}, \text{Course}, \text{Semester}\} $.  
> If $ \text{Course} \rightarrow \text{Instructor} $ still holds, is `Instructor` fully functionally dependent on the key?  
> No. Since `Instructor` depends only on `Course`, a proper subset of the key, this is a partial dependency. The schema is not in 2NF.

#### Worked Example: Achieving 2NF via Decomposition

To eliminate partial dependencies, decompose the relation based on the determining attributes.

**Step 1**: Identify partial dependencies:
- $ \text{StudentID} \rightarrow \text{StudentName} $
- $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $

**Step 2**: Extract each dependency into a new relation.

Decompose `Enrollments` into:
1. **Students**(StudentID, StudentName)  
   Key: $ \{\text{StudentID}\} $
2. **Courses**(Course, Instructor, CourseLevel)  
   Key: $ \{\text{Course}\} $
3. **Enrollments**(StudentID, Course)  
   Key: $ \{\text{StudentID}, \text{Course}\} $

Now:
- `StudentName` depends fully on its key in `Students`.
- `Instructor` and `CourseLevel` depend fully on `Course` in `Courses`.
- `Enrollments` records only the relationship—no redundant data.

We’ve **isolated facts**: student identity, course metadata, and enrollment—all in their own homes.

> **Try This Yourself**:  
> Suppose we add `Department` to `Courses`, with $ \text{Course} \rightarrow \text{Department} $. Is `Courses` still in 2NF?  
> Yes—`Department` depends on the full key `Course`. No partial dependency.

#### Real-World Application: Retail Inventory Management

A large retail chain tracks inventory across stores using a denormalized schema:

> **Inventory**(StoreID, StoreCity, ProductID, ProductName, Category, Price, StockQty)

With FDs:
- $ \text{StoreID} \rightarrow \text{StoreCity} $
- $ \text{ProductID} \rightarrow \text{ProductName}, \text{Category}, \text{Price} $
- Candidate key: $ \{\text{StoreID}, \text{ProductID}\} $

This violates 2NF: `StoreCity` depends only on `StoreID`, and product data depends only on `ProductID`.

Result:  
- Updating the price of “Organic Milk” requires modifying thousands of rows—one per store.
- Opening a new store with 10,000 products means repeating all product metadata.
- If a store closes, product information could be lost if not stored elsewhere.

After 2NF decomposition:
1. **Stores**(StoreID, StoreCity)
2. **Products**(ProductID, ProductName, Category, Price)
3. **Inventory**(StoreID, ProductID, StockQty)

Now, price changes affect one row in `Products`. New stores inherit all product data via reference. The system scales cleanly.

#### Additional Real-World Application: Logistics and Shipment Tracking

A logistics company uses a table to track shipments:

> **Shipments**(TruckID, DriverName, RouteID, RouteDescription, PackageID, Weight, Destination)

With FDs:
- $ \text{TruckID} \rightarrow \text{DriverName} $
- $ \text{RouteID} \rightarrow \text{RouteDescription}, \text{Destination} $
- Candidate key: $ \{\text{TruckID}, \text{RouteID}, \text{PackageID}\} $

Partial dependencies exist: `DriverName` depends only on `TruckID`, and `RouteDescription`/`Destination` depend only on `RouteID`.

This leads to:
- Redundant storage of driver and route data across packages.
- Inability to record a new route before any shipments are scheduled.
- Risk of inconsistent route names if updated manually in multiple rows.

After 2NF decomposition:
1. **Trucks**(TruckID, DriverName)
2. **Routes**(RouteID, RouteDescription, Destination)
3. **Shipments**(TruckID, RouteID, PackageID, Weight)

Now, route changes are centralized, and new routes can be added independently. The system supports accurate auditing and scheduling, critical in time-sensitive delivery operations.

#### Expanded Real-World Application: Academic Research Collaboration Networks

A research funding agency tracks collaborations using:

> **Collaborations**(ProjectID, ProjectTitle, ResearcherID, ResearcherName, Institution, FundingAmount, StartDate)

With FDs:
- $ \text{ResearcherID} \rightarrow \text{ResearcherName}, \text{Institution} $
- $ \text{ProjectID} \rightarrow \text{ProjectTitle}, \text{FundingAmount}, \text{StartDate} $
- Candidate key: $ \{\text{ProjectID}, \text{ResearcherID}\} $

This violates 2NF: `ResearcherName` and `Institution` depend only on `ResearcherID`, while project metadata depends only on `ProjectID`.

Problems:
- A researcher joining five projects duplicates their institutional affiliation five times.
- If a researcher changes institutions, all project records must be updated.
- Cannot add a new project until at least one researcher is assigned.

After 2NF decomposition:
1. **Researchers**(ResearcherID, ResearcherName, Institution)
2. **Projects**(ProjectID, ProjectTitle, FundingAmount, StartDate)
3. **Collaborations**(ProjectID, ResearcherID)

Now, institutional changes require one update. New projects can be defined before staffing. The schema supports longitudinal analysis of collaboration patterns without data corruption.

---

### Step 3: Third Normal Form (3NF) — Eliminate Transitive Dependencies

**Learning Objective**: Identify and eliminate transitive dependencies to achieve 3NF.

We’ve removed partial dependencies. But redundancy can still hide **in chains**.

> A relation is in **3NF** if and only if:
> - It is in 2NF, and  
> - No **non-prime attribute** is transitively dependent on any candidate key.

That is, if $ K \rightarrow