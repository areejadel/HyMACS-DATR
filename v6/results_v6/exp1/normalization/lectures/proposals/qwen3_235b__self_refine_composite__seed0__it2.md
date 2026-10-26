But

### Step 1: First Normal Form (1NF) — Atomicity and Structure

**Learning Objective**: Transform a relation into 1NF by ensuring atomic values and eliminating repeating groups.

> A relation is in **First Normal Form (1NF)** if:  
> - All attribute values are **atomic** (single, indivisible values).  
> - There are **no repeating groups** (e.g., lists or arrays stored in a single cell).

Why does this matter? Because relational operations like `SELECT`, `JOIN`, and `GROUP BY` assume each cell holds one value. Non-atomic data breaks these assumptions.

#### Intuition First: The Allergy List Problem — A Query That Lies

Consider a patient record:

| PatientID | Name   | Allergies               |
|---------|--------|-------------------------|
| P001    | Maria  | Penicillin, Latex       |
| P002    | James  | Peanuts, Bee stings     |

A nurse wants to find all patients allergic to *Latex*. She writes:  
```sql
SELECT * FROM Patients WHERE Allergies LIKE '%Latex%';
```
But what if another record says “latex (mild)” or “No known allergies except latex”? Or worse—what if “Latex” appears as part of “Penicillin-Latex combo”? The query fails silently.

This isn’t a query problem—it’s a **schema flaw**. Storing multiple values in one field prevents reliable querying.

**Analogy**: Think of it like storing a comma-separated list of GPS coordinates in a single field: “(40.7,-74.0), (34.1,-118.2)”. You *could* parse it, but you shouldn’t have to. Each coordinate represents a distinct location—each deserves its own row.

In data science, this is like storing a **feature vector** as a single string instead of structured columns. You wouldn’t store a pixel array from an image as “127,84,201,…” in one cell—you’d use a tensor. Similarly, in databases, **each atomic fact deserves its own cell**.

#### Formal Rule and Worked Example

To achieve 1NF:  
- Split multivalued cells into separate rows.  
- Ensure each attribute contains only atomic values.

Given:

| StudentID | StudentName | Course           | Instructor | CourseLevel |
|-----------|-------------|------------------|------------|-------------|
| S001      | Alice       | CS101, CS102     | Dr. Lee    | Intro       |

We expand the Course column:

| StudentID | StudentName | Course  | Instructor | CourseLevel |
|-----------|-------------|---------|------------|-------------|
| S001      | Alice       | CS101   | Dr. Lee    | Intro       |
| S001      | Alice       | CS102   | Dr. Lee    | Intro       |

Now all values are atomic. The candidate key $ \{\text{StudentID}, \text{Course}\} $ ensures uniqueness.

> **Clarification**: 1NF does not require a key by definition, but **practical databases must define one** to avoid duplicates and support joins.

> **Try This Yourself**:  
> Suppose a course has multiple instructors: “Dr. Lee, Dr. Smith” in one cell.  
> How do you fix this while preserving 1NF?  
> ✅ Create a new relation: `CourseInstructors(Course, Instructor)`, with one row per instructor.

> **Case Study: E-Commerce Product Tags**  
> An online store stores product tags as:  
> | ProductID | Tags               |  
> |----------|--------------------|  
> | P1       | Organic, Vegan, Gluten-Free |  
>  
> This breaks 1NF. To fix:  
> 1. Create `ProductTags(ProductID, Tag)`  
> 2. Insert: (P1, Organic), (P1, Vegan), (P1, Gluten-Free)  
> Now queries like “find all vegan products” are accurate and efficient.

---

### Step 2: Second Normal Form (2NF) — Full Dependency on the Key

**Learning Objective**: Eliminate partial dependencies to achieve 2NF.

> A relation is in **Second Normal Form (2NF)** if:  
> - It is in 1NF, and  
> - Every **non-prime attribute** is **fully functionally dependent** on every candidate key.

An attribute is **prime** if it belongs to any candidate key; otherwise, it is **non-prime**.  
A **partial dependency** occurs when a non-prime attribute depends on only a proper subset of a composite candidate key.

#### Intuition First: The Inventory Puzzle — Why Your Price Update Broke

> **Inventory**(StoreID, ProductID, ProductName, Price, Location)  
> Functional Dependencies:  
> - $ \text{ProductID} \rightarrow \text{ProductName} $  
> - $ \text{StoreID}, \text{ProductID} \rightarrow \text{Price}, \text{Location} $

Candidate key: $ \{\text{StoreID}, \text{ProductID}\} $  
Non-prime attributes: ProductName, Price, Location

But $ \text{ProductID} \rightarrow \text{ProductName} $: ProductName depends only on ProductID—a subset of the key → **partial dependency**

So ProductName repeats in every store that carries the product. Rename “iPhone” to “iPhone Pro”? You must update every store’s row. One missed update → inconsistency.

This is like storing a book’s title inside every chapter. The title belongs to the book, not the chapter.

**Analogy**: In machine learning, this is like **leaking metadata** into features. If you include a patient’s hospital ID as a feature in a diagnostic model, the model learns hospital-specific quirks instead of disease patterns. Similarly, storing ProductName in an inventory table couples it to StoreID—tying data to context it doesn’t belong to.

#### Formal Rule and Worked Example

To achieve 2NF:  
- Identify partial dependencies.  
- Decompose the relation by moving the dependent attributes into a new table with the determinant as key.

Recall **Enrollments**(StudentID, StudentName, Course, Instructor, CourseLevel)  
Functional Dependencies:  
- $ \text{StudentID} \rightarrow \text{StudentName} $  
- $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $  
- $ \text{StudentID}, \text{Course} \rightarrow \text{all} $

Candidate key: $ \{\text{StudentID}, \text{Course}\} $

Partial dependencies:  
- StudentName depends only on StudentID  
- Instructor and CourseLevel depend only on Course

Decompose:

1. **Students**(StudentID, StudentDialog)  
   Key: $ \{\text{StudentID}\} $  
2. **Courses**(Course, Instructor, CourseLevel)  
   Key: $ \{\text{Course}\} $  
3. **Enrollments**(StudentID, Course)  
   Key: $ \{\text{StudentID}, \text{Course}\} $

In each new table, non-prime attributes depend on the entire key.

> **Misconception Alert**:  
> 2NF **only applies when the candidate key is composite**. If the key is a single attribute, partial dependencies cannot exist.

> **Try This Yourself**:  
> Add $ \text{Course} \rightarrow \text{Department} $. Is Courses still in 2NF?  
> ✅ Yes—Department depends on the full key Course → no partial dependency.

> **Case Study: Library Book Checkout**  
> **Checkouts**(MemberID, ISBN, Title, Author, DueDate)  
> Functional Dependencies:  
> - $ \text{ISBN} \rightarrow \text{Title}, \text{Author} $  
> - $ \text{MemberID}, \text{ISBN} \rightarrow \text{DueDate} $  
>  
> Partial dependency: Title and Author depend only on ISBN.  
> Fix:  
> - Books(ISBN, Title, Author)  
> - Checkouts(MemberID, ISBN, DueDate)  
> Now updates to book info affect only one row.

---

### Step 3: Third Normal Form (3NF) — No Transitive Dependencies

**Learning Objective**: Eliminate transitive dependencies to achieve 3NF.

> A relation is in **Third Normal Form (3NF)** if:  
> - It is in 2NF, and  
> - For every non-trivial functional dependency $ X \rightarrow Y $, at least one of the following holds:  
>   - $ X $ is a superkey, or  
>   - $ Y $ is a prime attribute.

Equivalently: **no non-prime attribute should depend on another non-prime attribute**.

This prevents **transitive dependencies**, where $ A \rightarrow B \rightarrow C $, but $ A \not\rightarrow C $ directly.

#### Intuition First: The Doctor’s Hierarchy — When a Name Change Breaks Everything

> **Doctors**(DoctorID, Specialty, DeptHead, DeptPhone)  
> Functional Dependencies:  
> - $ \text{DoctorID} \rightarrow \text{Specialty} $  
> - $ \text{Specialty} \rightarrow \text{DeptHead} $  
> - $ \text{DeptHead} \rightarrow \text{DeptPhone} $

Candidate key: $ \{\text{DoctorID}\} $  
Non-prime attributes: DeptHead, DeptPhone

Transitive chain:  
$ \text{DoctorID} \rightarrow \text{Specialty} \rightarrow \text{DeptHead} \rightarrow \text{DeptPhone} $

Change the department head? You must update *every doctor* in that specialty. Miss one → inconsistency.

**Analogy**: This is like a **linked list in memory** where each node stores not just the next pointer, but the entire path. If one link changes, you have to update every node downstream. In databases, **chained dependencies create ripple effects**—just like poor memory management.

In data science, this is akin to **feature leakage**: using a derived variable (like DeptHead) that itself depends on other variables (Specialty), creating unstable models. 3NF forces you to **break the chain** and store only direct dependencies.

#### Formal Rule and Worked Example

To achieve 3NF:  
- Find functional dependencies $ X \rightarrow Y $ such that $ X $ is not a superkey and $ Y $ is non-prime.  
- Decompose using $ X \rightarrow Y $.

**Courses**(Course, Instructor, Office)  
Functional Dependencies:  
- $ \text{Course} \rightarrow \text{Instructor} $  
- $ \text{Instructor} \rightarrow \text{Office} $

Candidate key: $ \{\text{Course}\} $  
Office is non-prime and depends on Instructor (a non-key attribute) → violates 3NF

Decompose using $ \text{Instructor} \rightarrow \text{Office} $:

1. **Courses**(Course, Instructor)  
   Key: $ \{\text{Course}\} $  
2. **Instructors**(Instructor, Office)  
   Key: $ \{\text{Instructor}\} $

Now:  
- In Courses: $ \text{Course} \rightarrow \text{Instructor} $, and Course is a superkey → OK  
- In Instructors: $ \text{Instructor} \rightarrow \text{Office} $, and Instructor is a superkey → OK  

Both tables are in 3NF.

> **Try This Yourself**:  
> **Students**(StudentID, Advisor, Dept, DeptPhone)  
> - $ \text{StudentID} \rightarrow \text{Advisor} $  
> - $ \text{Advisor} \rightarrow \text{Dept} $  
> - $ \text{Dept} \rightarrow \text{DeptPhone} $  
>  
> Transitive dependencies: Advisor → Dept → DeptPhone  
> Decompose:  
> - Students(StudentID, Advisor)  
> - Advisors(Advisor, Dept)  
> - Departments(Dept, DeptPhone)

> **Case Study: Hotel Management**  
> **Rooms**(RoomID, HotelName, Manager, ManagerEmail)  
> Functional Dependencies:  
> - $ \text{RoomID} \rightarrow \text{HotelName} $  
> - $ \text{HotelName} \rightarrow \text{Manager}, \text{ManagerEmail} $  
>  
> Transitive dependency: Room → Hotel → Manager  
> Fix:  
> - Hotels(HotelName, Manager, ManagerEmail)  
> - Rooms(RoomID, HotelName)  
> Now manager updates affect only one row.

---

### Step 4: Boyce-Codd Normal Form (BCNF) — Only Keys Determine Attributes

**Learning Objective**: Apply BCNF to eliminate all non-superkey determinants.

> A relation is in **Boyce-Codd Normal Form (BCNF)** if:  
> For every non-trivial functional dependency $ X \rightarrow Y $, $ X $ is a **superkey**.

BCNF is stricter than 3NF. It ensures that **only keys can determine other attributes**, preventing subtle inconsistencies.

#### Intuition First: The Gate Assignment Conflict — When Two Keys Collide

> **Flights**(FlightNumber, Airline, Gate)  
> Functional Dependencies:  
> - $ \text{FlightNumber} \rightarrow \text{Airline} $  
> - $ \text{Airline}, \text{Gate} \rightarrow \text{FlightNumber} $

Candidate keys: $ \{\text{FlightNumber}\} $, $ \{\text{Airline}, \text{Gate}\} $

Now suppose: $ \text{Gate} \rightarrow \text{Airline} $?  
Then Gate 12 → Delta. But if United uses Gate 12 for a flight, contradiction.

Gate determines Airline—but Gate is not a key → violates BCNF.

**Analogy**: This is like a **type system in programming**: you can’t assign a string to an integer field. BCNF prevents attributes from being “reinterpreted” via weak determinants. Just as static typing catches errors at compile time, BCNF catches logical contradictions before they corrupt data.

In distributed systems, this is like **consensus protocols**: if two nodes claim authority over the same resource, conflict arises. BCNF ensures **only one source of truth** per attribute.

#### Formal Rule and Worked Example

To achieve BCNF:  
- Find any functional dependency $ X \rightarrow Y $ where $ X $ is not a superkey.  
- Decompose using $ X \rightarrow Y $.

**Teaching**(Course, Instructor, Time)  
Functional Dependencies:  
- $ \text{Instructor}, \text{Time} \rightarrow \text{Course} $  
- $ \text{Course} \rightarrow \text{Instructor} $

Candidate keys:  
- $ \{\text{Instructor}, \text{Time}\} $: determines Course → all → superkey  
- $ \{\text{Course}, \text{Time}\} $: $ \text{Course} \rightarrow \text{Instructor} $ → all → superkey

But $ \text{Course} \rightarrow \text{Instructor} $: Course is **not** a superkey (same course, different times, different instructors?) → violates BCNF

Decompose using $ \text{Course} \rightarrow \text{Instructor} $:

1. **CourseInstructor**(Course, Instructor)  
   Key: $ \{\text{Course}\} $  
2. **InstructorTime**(Instructor, Time)  
   Key: $ \{\text{Instructor}, \text{Time}\} $

Now:  
- In CourseInstructor: $ \text{Course} \rightarrow \text{Instructor} $, and Course is a superkey → OK  
- In InstructorTime: no functional dependencies given → trivially satisfies BCNF

> **Try This Yourself**:  
> **Students**(StudentID, Major, Advisor)  
> - $ \text{StudentID} \rightarrow \text{Major} $  
> - $ \text{Major} \rightarrow \text{Advisor} $  
>  
> Does this violate BCNF?  
> Yes—Major → Advisor, but Major is not a superkey.  
> Decompose:  
> - Students(StudentID, Major)  
> - Majors(Major, Advisor)

> **Case Study: University Class Scheduling**  
> **Classes**(ClassID, Room, Capacity, Building)  
> Functional Dependencies:  
> - $ \text{Room} \rightarrow \text{Building}, \text{Capacity} $  
> - $ \text{ClassID} \rightarrow \text{Room} $  
>  
> Room → Building: Room is not a key → violates BCNF  
> Fix:  
> - Rooms(Room, Building, Capacity)  
> - Classes(ClassID, Room)  
> Now room changes affect only one table.

---

### Step 5: Trade-Offs and Practical Design — When to Normalize, When to Denormalize

**Learning Objective**: Evaluate real-world trade-offs between normalization and performance.

Normalization reduces redundancy and anomalies—but introduces costs.

#### The Cost of Decomposition

- **Join Overhead**: Queries now require joins across tables → slower reads.  
- **Update vs. Read Frequency**:  
  - **Write-heavy systems** (e.g., banking): normalize to prevent corruption.  
  - **Read-heavy systems** (e.g., dashboards): denormalize for speed.  
- **Complexity**: More tables → harder to understand and maintain.

#### Limitations and Safeguards

1. **Lossless Join**:  
   A decomposition must reconstruct the original data without spurious tuples.  
   A sufficient condition for lossless join: $ R_1 \cap R_2 \rightarrow R_1 $ or $ R_1 \cap R_2 \rightarrow R_2 $.  
   Example: Students ∩ Enrollments = {StudentID}, and $ \text{StudentID} \rightarrow \text{StudentName} $ → lossless.

2. **Dependency Preservation**:  
   After decomposition, all functional dependencies should be enforceable in at least one table.  
   If not, some constraints require application-level checks.

3. **Denormalization Justification**:  
   Only denormalize when:  
   - Query performance is unacceptable.  
   - The denormalized schema can be kept consistent via triggers or application logic.  
   - The read-to-write ratio justifies increased update cost.

> **Case Study: Analytics Dashboard**  
> A reporting table aggregates daily sales:  
> `DailySales(Date, Product, Category, TotalUnits, TotalRevenue)`  
> Denormalized from Orders, Products, Categories.  
> Justification:  
> - Read-heavy: thousands of dashboard views per day.  
> - Updated once daily in batch.  
> - Dependencies preserved via ETL process.

> **Golden Rule**:  
> Normalize by default. Denormalize intentionally, with measurement and justification.