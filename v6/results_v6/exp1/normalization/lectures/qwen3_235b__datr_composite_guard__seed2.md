**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Identify** whether a given relation schema violates 1NF, 2NF, 3NF, or BCNF by applying formal definitions.  
2. **Explain** how partial and transitive dependencies lead to insertion, deletion, and update anomalies.  
3. **Apply** decomposition techniques to convert a schema into 2NF, 3NF, and BCNF, ensuring lossless join and dependency preservation where possible.  
4. **Analyze** a database schema to evaluate trade-offs among normalization levels, including redundancy, anomaly risk, and constraint enforcement.  
5. **Design** a normalized schema from a real-world scenario using functional dependencies and candidate keys.

---

### Prerequisites: Functional Dependencies and Keys

Before proceeding, we establish foundational definitions.

A **functional dependency (FD)** $ X \rightarrow Y $ holds in a relation if, for any two tuples, equality on all attributes in $ X $ implies equality on all attributes in $ Y $.  
For example, if `EmployeeID → Department`, then no two tuples with the same `EmployeeID` can differ in `Department`.

Think of an FD as a *data promise*: whenever two rows agree on $ X $, they must also agree on $ Y $. Break that promise, and your data lies.

A **candidate key** is a minimal set of attributes that functionally determines every other attribute in the relation. It satisfies two properties:  
- **Uniqueness**: No two distinct tuples have identical values on the key.  
- **Minimality**: No proper subset of the key functionally determines all attributes.

Here’s a subtle but critical insight: a candidate key is not just an identifier—it’s the *anchor* of truth for the entire row. Every other attribute depends on it, directly or indirectly. Lose that anchor, and the schema floats on assumptions.

With these tools, we now examine a motivating example—one that hides a paradox.

---

### Motivating Example: The Paradox of the Missing Instructor

Imagine a university database tracking students, courses, and instructors. Suppose we begin with a single relation:

```
TeachRecord(Student, Course, Instructor)
```

Sample instance:  
| Student   | Course     | Instructor    |  
|-----------|------------|---------------|  
| Alice     | Math101    | Dr. Smith     |  
| Bob       | CS101      | Dr. Lee       |  
| Charlie   | Math101    | Dr. Smith     |  
| Alice     | CS101      | Dr. Lee       |  

At first glance, this seems fine. But ask yourself: *Can the database answer the question “Who teaches CS101?” without relying on student enrollment?*

Suppose Dr. Lee teaches only CS101. Now consider:  
- **Insertion anomaly**: You cannot record that Dr. Lee teaches CS101 unless at least one student is enrolled.  
- **Deletion anomaly**: If all students drop CS101, the fact that Dr. Lee teaches it vanishes.  
- **Update anomaly**: If Dr. Lee changes her name, and the update applies to only some rows, the database reports both “Dr. Lee” and “Dr. Lopez” for the same course.

The paradox? *The database claims to store knowledge about teaching, but its ability to preserve that knowledge depends on unrelated data—student enrollment.*

This is not a bug. It’s a design flaw: the schema conflates *who is enrolled* with *who teaches what*. The cost? Fragile data semantics.

> **Try this yourself**: Sketch a scenario where updating one fact (e.g., instructor name) requires changing multiple rows. Why does this happen? What dependency is being violated?

Now, imagine you’re the database administrator. A faculty dean calls: “We need to assign Dr. Lee to CS101 *before* registration opens—no students are enrolled yet.” You try to insert the record `(NULL, CS101, Dr. Lee)`—but `Student` is part of the key. You can’t allow nulls. The system refuses.  

You’ve hit a wall built by poor design.  

Let’s dismantle it—starting with the atomic foundation.

---

### 1. First Normal Form (1NF): The Atomicity Boundary

Normalization begins with **First Normal Form (1NF)**, which defines the smallest unit of data the database can reason about.

#### Formal Definition  
A relation is in **1NF** if and only if:  
- Every attribute contains atomic (indivisible) values.  
- There are no repeating groups (e.g., `Course1`, `Course2`, `Course3` columns).  

This ensures that each cell holds exactly one value, enabling precise querying and integrity enforcement.

#### Analogy: The Periodic Table of Data  
Just as chemistry relies on atoms as indivisible building blocks, databases rely on atomic values. You can’t split a proton in chemical equations; you can’t split a comma-separated list in reliable queries. If `Tags = "bug, ui"` lives in one cell, the database treats it as a *single molecule*, not two elements. You can’t index “ui” alone. You can’t enforce constraints on individual tags. You’ve left the domain of relational algebra.

#### Worked Example  
Suppose we define:  
```
StudentCourses(StudentID, Name, Courses)
```  
With sample data:  
| StudentID | Name   | Courses           |  
|-----------|--------|-------------------|  
| 1         | Alice  | {CS101, CS102}    |  

Here, `Courses` contains a set — a non-atomic value — violating 1NF.

To satisfy 1NF, decompose into flat, single-valued tuples:  
```
Enrollment(StudentID, CourseID)
```  
| StudentID | CourseID |  
|-----------|----------|  
| 1         | CS101    |  
| 1         | CS102    |  

Each row now represents a single enrollment, and all attributes are atomic.

> **Common Misconception**: “1NF requires unique rows.”  
> **Correction**: 1NF does not mandate uniqueness. Duplicate rows are permitted under 1NF but typically disallowed via primary key constraints to prevent redundancy.

> **Formative Check 2**: Is the following table in 1NF?  
> | ID | Tags        |  
> |----|-------------|  
> | 1  | "bug, ui"   |  
> **Answer**: No. The `Tags` attribute contains a concatenated string, which is not atomic. To normalize, create a separate relation: `IssueTags(ID, Tag)`.

#### Real-World Case: E-Commerce Product Tags at Amazon

In large-scale e-commerce platforms like Amazon, product metadata often includes tags such as "bestseller", "eco-friendly", or "prime-eligible". Early schema designs sometimes stored these as comma-separated strings in a single column (e.g., `ProductTags = "bestseller,prime"`). This caused significant operational issues:

- **Search inefficiency**: Full-text scans were required to find all “eco-friendly” products.
- **Constraint violations**: No way to enforce valid tag values; misspellings like "prim" proliferated.
- **Indexing failure**: Secondary indexes could not be built on individual tags.

Amazon’s solution was to normalize into a junction table:
```
ProductTags(ProductID, Tag)
```
This allowed efficient filtering (`SELECT * FROM Products JOIN ProductTags USING (ProductID) WHERE Tag = 'eco-friendly'`), enabled referential integrity via a controlled vocabulary, and supported fast aggregation (e.g., counting how many items carry each tag). The shift from unstructured strings to atomic relations exemplifies 1NF in practice—transforming fragile data into queryable, maintainable assets.

#### Real-World Case: Patient Symptom Tracking in Electronic Health Records (EHR)

In clinical databases, physicians record patient symptoms during visits. A legacy EHR system used a schema:
```
PatientVisit(VisitID, PatientID, Symptoms)
```
where `Symptoms` contained values like `"fever, cough, fatigue"`. This violated 1NF and led to critical limitations:

- **Diagnostic errors**: Algorithms could not reliably detect symptom patterns (e.g., identifying influenza outbreaks) because “cough” was embedded in unstructured text.
- **Reporting failure**: Public health agencies required granular symptom reporting during the flu season, but the database could not extract individual symptoms systematically.
- **Machine learning incompatibility**: Predictive models for disease progression required binary symptom flags, which were impossible to derive consistently.

The system was restructured to:
```
VisitSymptoms(VisitID, Symptom)
```
Each symptom was stored as a separate row. This enabled:
- Automated flagging of symptom clusters (e.g., fever + cough → possible respiratory infection).
- Integration with natural language processing pipelines that parsed clinician notes into structured entries.
- Compliance with HL7 FHIR standards for interoperable health data exchange.

This transformation illustrates 1NF’s role beyond data cleanliness—it enables advanced analytics, regulatory compliance, and integration with AI systems in mission-critical domains.

> **Try this yourself**: Suppose you’re designing a blog platform. Authors can have multiple roles: “Editor”, “Reviewer”, “Admin”. You consider storing `Roles = "Editor,Admin"` in the `Authors` table. What anomalies could this cause? How would 1NF guide your schema?

> **Challenge Prompt**: Imagine you're building a music app. Each song has multiple genres: "rock, indie, alternative". If you store genres as a single string, what happens when a user searches for all *indie* songs? Can the database answer efficiently? What if “indie” is sometimes spelled “Indie” or “indie rock”? Design a normalized alternative.

---

### 2. Second Normal Form (2NF): The Cost of Partial Truths

After achieving 1NF, we target **partial dependencies**—situations where a non-key attribute depends on only part of a composite key.

#### Formal Definition  
A relation is in **Second Normal Form (2NF)** if:  
- It is in 1NF, and  
- Every **non-prime attribute** is **fully functionally dependent** on every candidate key.

An attribute is **prime** if it is part of any candidate key; otherwise, it is **non-prime**.  
A **partial dependency** occurs when a non-prime attribute depends on a proper subset of a candidate key.

#### Analogy: The Library Book Barcode  
Imagine a library where each book has a unique barcode (composite key: `ShelfNumber, PositionOnShelf`). Now suppose the book’s genre depends only on `ShelfNumber`. That means:  
- Every book on shelf 5 is sci-fi.  
- But the database stores “sci-fi” in every row for shelf 5.

If you move a book to shelf 6, you must update its genre—even though genre is logically tied to shelf, not the book. The dependency is partial, and the schema pays the price in redundancy.

The flaw? *Partial keys should not govern full truths.*

But here’s the twist: this isn’t just about redundancy. It’s about **authority**. Who gets to decide the genre? The shelf—or the book? If the shelf decides, then moving the book breaks consistency. If the book decides, then the shelf is just location. 2NF ensures that facts are owned by the right entity.

> **Pause and Predict**: Before reading the next example, imagine a table `Enrollment(StudentID, CourseID, CourseName)` where `CourseID → CourseName`. The key is `(StudentID, CourseID)`. Can you already spot the anomaly? What happens when CourseName changes? How many rows must change? Write down your answer.

#### Worked Example  
Consider:  
```
OrderDetails(OrderID, ProductID, ProductName, Quantity)
```  
Assume the following:  
- Functional dependency: $ \text{ProductID} \rightarrow \text{ProductName} $  
- Candidate key: $ \{\text{OrderID}, \text{ProductID}\} $  

Now evaluate $ \text{ProductName} $. It depends only on $ \text{ProductID} $, a subset of the key. Since $ \text{ProductName} $ is non-prime and partially dependent on the key, the schema violates 2NF.

To resolve this, decompose into two relations:  
1. `OrderItems(OrderID, ProductID, Quantity)` — key: $ \{\text{OrderID}, \text{ProductID}\} $  
2. `Products(ProductID, ProductName)` — key: $ \{\text{ProductID}\} $  

In `OrderItems`, all non-prime attributes (e.g., `Quantity`) depend fully on the entire key. In `Products`, `ProductName` depends on the full key `ProductID`. The decomposition eliminates partial dependencies.

> **Try this yourself**: Suppose `Enrollment(StudentID, CourseID, CourseName)` with key $ \{\text{StudentID}, \text{CourseID}\} $ and FD $ \text{CourseID} \rightarrow \text{CourseName} $. Why does this violate 2NF? What happens if two students enroll in the same course? How many times is `CourseName` repeated?

> **Formative Check 3**: Decompose the above schema into 2NF. Does your decomposition preserve all functional dependencies? Can you reconstruct the original data without loss?

#### Real-World Case: Order Management at Shopify

Shopify processes millions of orders daily. In early iterations of its order schema, line-item data was stored in a denormalized table:
```
OrderLineItems(OrderID, ProductID, ProductName, SKU, Quantity, Price)
```
With functional dependency $ \text{ProductID} \rightarrow \text{ProductName, SKU, Price} $, and composite key $ \{\text{OrderID}, \text{ProductID}\} $, this schema suffered from a severe partial dependency.

Consequences included:
- **Update anomalies**: When a product's price changed, historical order records risked corruption if updated retroactively.
- **Redundancy**: The same `ProductName` and `SKU` repeated across thousands of orders.
- **Storage bloat**: Millions of redundant entries inflated database size and slowed backups.

Shopify resolved this by decomposing into:
```
Orders(OrderID, ...)
OrderItems(OrderID, ProductID, Quantity, UnitPriceAtTimeOfSale)
Products(ProductID, ProductName, SKU, CurrentPrice)
```
Note: `UnitPriceAtTimeOfSale` is preserved in `OrderItems` to maintain historical accuracy, while current pricing logic resides in `Products`. This design satisfies 2NF: all non-prime attributes in `OrderItems` depend fully on the composite key, and product metadata is centralized. The result: consistent data, reduced storage, and reliable audit trails.

#### Real-World Case: Flight Scheduling at Delta Airlines

Delta Airlines’ flight operations database once used a table:
```
FlightAssignment(FlightNumber, CrewID, AircraftType, DepartureTime)
```
With FDs:
- $ \text{FlightNumber} \rightarrow \text{AircraftType, DepartureTime} $
- $ \text{CrewID} \rightarrow \text{AircraftType} $ (each crew is certified for one aircraft type)

The candidate key is $ \{\text{FlightNumber}, \text{CrewID}\} $. However, `AircraftType` depends on both `FlightNumber` and `CrewID` separately—introducing a partial dependency: $ \text{FlightNumber} \rightarrow \text{AircraftType} $, where `FlightNumber` is a proper subset of the key.

This caused:
- **Scheduling conflicts**: A crew certified only for Boeing 737s could be assigned to an Airbus flight if `AircraftType` was inconsistently updated.
- **Operational delays**: Manual validation checks were required before crew assignments, increasing planning time.
- **Violation of FAA regulations**: Certification mismatches posed compliance risks.

The solution was decomposition:
```
FlightInfo(FlightNumber, AircraftType, DepartureTime)
CrewCertification(CrewID, AircraftType)
FlightCrew(FlightNumber, CrewID)
```
Now, `AircraftType` is determined solely by superkeys in their respective tables. The schema satisfies 2NF, ensuring that aircraft type is consistently enforced through referential integrity. This redesign eliminated partial dependencies and supported automated, compliant crew assignment.

#### Industry Practice: Microservices and Bounded Contexts at Netflix

Modern software architecture increasingly embraces domain-driven design (DDD), where data models are aligned with business capabilities. Netflix, for instance, decomposes its data landscape into **bounded contexts**—autonomous services each owning normalized schemas for their domain.

For example, the **Billing Service** maintains a 2NF-compliant `SubscriptionItems` table:
```
SubscriptionItems(SubscriptionID, PlanID, PlanName, MonthlyFee)
```
But instead of allowing partial dependencies to persist, Netflix enforces strict service boundaries: `PlanName` and `MonthlyFee` are not stored directly but fetched via API calls to the **Pricing Service**. This architectural normalization mirrors 2NF’s principle: *non-key attributes must depend on the full key*—or not be stored at all.

In practice, this means:
- `SubscriptionItems` stores only `SubscriptionID, PlanID, Quantity`
- `PlanName` and `MonthlyFee` are retrieved on-demand from the Pricing Service
- Changes to pricing affect only one system, eliminating redundancy and ensuring consistency

This pattern—**schema normalization enforced through service decomposition**—is now standard in cloud-native applications. It reflects a deeper truth: 2NF is not just a relational rule; it’s a principle of *ownership* and *cohesion* in data architecture.

> **Try this yourself**: Imagine a new requirement: “Each product has a default discount code.” Where should this go? What if the same product has different discounts in different orders? How does this affect normalization?

> **Challenge Prompt**: You’re modeling a university lab. Each experiment has a `LabID`, `ExperimentID`, and `LabTechnician`. The `LabTechnician` depends only on `LabID`. Is this a partial dependency? What happens if the technician changes? How many rows must you update? Design a 2NF-compliant version.

---

### 3. Third Normal Form (3NF): Breaking the Dependency Chain

Even in 2NF, anomalies persist when non-key attributes determine other non-key attributes—**transitive dependencies**.

#### Formal Definition  
A relation is in **Third Normal Form (3NF)** if:  
- It is in 2NF, and  
- For every nontrivial functional dependency $ X \rightarrow Y $, **at least one** of the following holds:  
  1. $ X $ is a **superkey**, or  
  2. $ Y $ is a **prime attribute** (i.e., part of some candidate key).

This prevents non-prime attributes from being determined by non-superkeys.

#### Analogy: The Chain of Command  
Think of a military hierarchy:  
`Soldier → Sergeant → Captain`  

The captain assigns missions, but the soldier never talks to the captain directly. If the captain issues an order, it goes through the sergeant. But what if the sergeant is absent? The chain breaks.

In databases, a transitive dependency like `EmployeeID → Department → Manager` creates the same fragility. The manager isn’t directly accountable to the employee; they’re mediated by department. So when the manager changes, you must update every employee in that department—because the data chain forces indirect responsibility.

3NF demands: *No middlemen for facts.* If `Department → Manager`, then `Department` must be the authoritative source—stored separately. Otherwise, you’re playing telephone with data.

> **Pause and Predict**: Suppose you delete the last employee in the "Graphics" department. What happens to the fact that "Dr. Kim manages Graphics"? Is that information preserved? If not, where should it have been stored?

#### Worked Example  
Consider:  
```
Employee(EmployeeID, Department, Manager)
```  
With functional dependencies:  
- $ \text{EmployeeID} \rightarrow \text{Department} $  
- $ \text{Department} \rightarrow \text{Manager} $  

Candidate key: $ \{\text{EmployeeID}\} $  
Non-prime attributes: `Department`, `Manager` (neither is part of any candidate key)

Examine $ \text{Department} \rightarrow \text{Manager} $:  
- $ \text{Department} $ is not a superkey.  
- `Manager` is not a prime attribute.  

Thus, the schema violates 3NF.

To resolve, decompose into:  
1. `EmployeeDept(EmployeeID, Department)` — key: $ \{\text{EmployeeID}\} $  
2. `DeptManager(Department, Manager)` — key: $ \{\text{Department}\} $  

Now, `Manager` is determined directly by `Department`—a superkey in its own table. The chain is broken. Updates to management affect only one row per department.

> **Form