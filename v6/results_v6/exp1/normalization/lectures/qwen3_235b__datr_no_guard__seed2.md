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

Now, here’s a twist: suppose you’re told that Dr. Lee is leaving the university, but CS101 will continue. Can your current schema reflect that the *course exists* and has an *instructor-to-be-assigned* without lying about who teaches it? If not, what structural gap prevents this?

What if we told you that this single table *cannot* represent a course without a student? That’s not a limitation of data entry—it’s a failure of *semantic expressiveness*. The schema cannot model reality because it ties independent facts together.

Let’s pause: **Can a database be logically broken even when all data is correct?**  
Yes—when the structure forces you to lie, omit, or repeat truths.

Having seen the consequences, we now formalize a path to robust design.

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

#### Real-World Case: GitHub Issue Tracking  
In GitHub’s issue tracking system, labels such as “bug”, “enhancement”, or “UI” are stored in a normalized structure. Internally, GitHub uses a junction table like `IssueLabels(issue_id, label_name)` rather than storing labels as comma-separated strings in the `Issues` table. This design enables efficient filtering (e.g., “show all UI bugs”), indexing on individual labels, and constraint enforcement (e.g., preventing invalid label names). Had they used denormalized strings, full-text search would be required for simple queries, performance would degrade at scale, and referential integrity would be impossible.

This illustrates the practical cost of violating 1NF: loss of query precision, scalability, and data integrity.

In modern database systems such as PostgreSQL and MySQL, support for JSON or array types (e.g., `tags TEXT[]` or `labels JSONB`) may tempt developers to store non-atomic data. However, experienced database architects use these features selectively—typically for read-heavy, schema-flexible contexts like logging or analytics—while maintaining 1NF in transactional schemas where consistency and integrity are paramount. For instance, Stripe’s billing system enforces atomicity in core tables like `invoices` and `line_items`, ensuring that every monetary value and product reference is individually addressable and auditable. Violating 1NF in such systems could lead to compliance risks or financial inaccuracies.

> **Try this yourself**: Suppose you're building a podcast app. Each episode has multiple hosts listed in a single field: `"Alex, Jamie, Taylor"`. What queries become impossible or inefficient? How would you redesign this to support searching “Which episodes did Jamie host?”  
> Now, imagine the app grows and hosts start changing names. How does your design handle that?

#### Additional Real-World Case: Electronic Health Records (EHR) in Primary Care  
Consider a primary care clinic managing patient diagnoses. A common anti-pattern is to store multiple diagnoses in a single field:  
```
PatientDiagnoses(patient_id, name, diagnoses)
```  
With `diagnoses = "Hypertension, Type 2 Diabetes, Asthma"`.

This violates 1NF and prevents critical operations:  
- Querying “How many patients have asthma?” requires string parsing, which is error-prone and inefficient.  
- Enforcing validity (e.g., only SNOMED-CT coded diagnoses) becomes impossible.  
- Indexing for fast retrieval fails.

Real EHR systems like Epic or Athenahealth use a normalized design:  
```
PatientDiagnoses(patient_id, diagnosis_code)
```  
with a separate `Diagnoses(code, description)` table. This allows:  
- Accurate population health reporting (e.g., identifying diabetic patients for outreach).  
- Integration with clinical decision support systems that trigger alerts based on specific codes.  
- Audit trails for regulatory compliance (e.g., Meaningful Use criteria).

Without 1NF, public health surveillance—such as tracking flu outbreaks or managing chronic disease cohorts—would be severely compromised. The atomicity of medical facts is not a theoretical concern; it is a clinical necessity.

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

Now, imagine the university decides to rename “CS101” to “Intro to Computing”. How many rows must be updated? What if one update fails mid-process—what inconsistency arises?

> **Formative Check 3**: Decompose the above schema into 2NF. Does your decomposition preserve all functional dependencies? Can you reconstruct the original data without loss?

#### Real-World Case: Amazon Order Processing  
Amazon’s order processing system separates product metadata from order line items. The `OrderItems` table contains `order_id`, `product_id`, and `quantity`, while `Products` stores `product_id`, `name`, `price`, and `category`. This 2NF-compliant design ensures that if the product name changes (e.g., “Echo Dot (3rd Gen)” → “Echo Dot (4th Gen)”), only one row in `Products` needs updating—no need to scan millions of historical orders. Without this separation, every past order referencing the product would require update or risk displaying outdated information. This architecture supports scalability and data consistency across petabytes of transactional data.

In modern cloud data warehouses like Amazon Redshift or Google BigQuery, denormalized schemas are sometimes used for analytical speed. However, even in these systems, 2NF principles guide the design of source transactional databases (e.g., in Amazon Aurora), where data integrity is non-negotiable. ETL pipelines then carefully denormalize data for reporting, preserving the benefits of normalization at the source. This layered approach—normalized OLTP, denormalized OLAP—reflects industry best practice: normalize first, denormalize deliberately.

#### Additional Real-World Case: Airline Reservation Systems  
In airline reservation systems, consider a table:  
```
FlightPassenger(flight_number, passenger_id, flight_date, aircraft_type)
```  
with FD $ \text{flight\_number} \rightarrow \text{aircraft\_type} $, and candidate key $ \{\text{flight\_number}, \text{passenger\_id}\} $.

Here, `aircraft_type` depends only on `flight_number`, a partial key—violating 2NF.

If the airline swaps aircraft for a flight, every passenger record for that flight must be updated. With thousands of passengers per day, this leads to massive redundancy and update anomalies.

Real systems like Sabre or Amadeus avoid this by normalizing into:  
- `Flights(flight_number, flight_date, aircraft_type)`  
- `Reservations(flight_number, passenger_id)`

This ensures that aircraft assignments are stored once per flight, not per passenger. It also enables accurate fleet utilization reporting and maintenance scheduling based on actual aircraft usage.

Moreover, during irregular operations (e.g., weather disruptions), the ability to reassign flights without cascading updates to passenger records is operationally critical. 2NF thus supports both data integrity and real-time operational resilience.

> **Try this yourself**: Design a table for a music streaming service: `UserPlayHistory(userID, songID, artistName, playCount)`. Assume $ \text{songID} \rightarrow \text{artistName} $. What normal form does this violate? What happens if an artist changes their name?  
> Now, suppose the artist has a legal name change. How many rows are affected? Could a partial update create a situation where the same song appears with two different artists in the same user’s history?

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

#### Analogy: The Game of Telephone  
Imagine a chain:  
`EmployeeID → Department → Manager`  

When Alice changes departments, her manager changes—not because she chose a new manager, but because the department carries that fact. Now suppose the manager of Data Science changes. You must update *every employee* in that department. Miss one? Now Alice still reports to the old manager.

This is the *data version of telephone*: information passed through intermediaries distorts. 3NF breaks the chain by ensuring that only authoritative sources (superkeys) can determine facts.

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

> **Formative Check 4**: In the decomposed schema, can you still determine Alice’s manager? How? What if two departments have the same manager? Is that a problem?

> **Try this yourself**: Design a scenario where a transitive dependency causes a deletion anomaly. What is lost when a row is deleted? Could that fact have been preserved?

Now, imagine the company dissolves the “Data Science” department. When you delete all employees from that department, should the manager’s record vanish too? What if they manage another team? What if not? How does your schema handle this edge?

#### Real-World Case: Hospital Patient Assignment System  
In a hospital management system, consider a table `PatientAssignments(patient_id, doctor_id, specialty)` with FDs:  
- $ \text{doctor\_id} \rightarrow \text{specialty} $  
- $ \text{patient\_id} \rightarrow \text{doctor\_id} $  

If the system stores this in a single table, changing a doctor’s specialty (e.g., from “Cardiology” to “Interventional Cardiology”) requires updating every patient assigned to that doctor. Worse, if the last patient of a doctor is discharged, the record—and potentially the doctor’s specialty—may be deleted accidentally.  

Real systems like Epic or Cerner avoid this by normalizing into:  
- `DoctorSpecialties(doctor_id, specialty)`  
- `PatientAssignments(patient_id, doctor_id)`  

This 3NF design isolates medical specialty data from patient assignments, ensuring that doctor metadata persists independently of patient load and enabling accurate reporting (e.g., “count of cardiologists on staff”) even when no patients are assigned.

In enterprise resource planning (ERP) systems such as SAP or Oracle Health, 3NF is a foundational design principle. These systems manage complex hierarchies (e.g., provider affiliations, insurance networks) where transitive dependencies are common. By enforcing 3NF, they ensure that updates to provider credentials or departmental structures do not cascade uncontrollably through patient records. This is critical for auditability and regulatory compliance (e.g., HIPAA), where data lineage and integrity must be traceable.

#### Additional Real-World Case: University Academic Advising  
Consider a university advising system with:  
```
StudentAdvisor(student_id, advisor_id, advisor_office)
```  
and FDs:  
- $ \text{student\_id} \rightarrow \text{advisor\_id} $  
- $ \text{advisor\_id} \rightarrow \text{advisor\_office} $  

If an advisor changes offices, every student’s record must be updated—a clear transitive dependency violating 3NF.