# Normalization Forms and Database Schema Design (1NF–BCNF)

## Learning Objectives

By the end of this lecture, you will be able to:  
1. **Identify** whether a given relation is in 1NF, 2NF, 3NF, or BCNF by applying formal definitions and analyzing functional dependencies.  
2. **Explain** the types of anomalies (update, insertion, deletion) that arise from violations of each normal form.  
3. **Transform** a denormalized schema into a normalized one by decomposing relations to eliminate partial and transitive dependencies.  
4. **Compare** BCNF and 3NF by evaluating trade-offs between dependency preservation and anomaly elimination.  
5. **Design** a normalized schema for a real-world scenario using functional dependencies and candidate keys.

---

## 1. First Normal Form (1NF): Enforce Atomicity of Values

### The Problem That Broke a Hospital

In 2014, a UK hospital’s patient record system stored multiple diagnoses in a single field: `"Diabetes, Hypertension"`. When researchers tried to count how many patients had hypertension, they accidentally included cases like `"Postural Hypotension"` due to string matching errors. The result? A flawed public health report.

This wasn’t just a query mistake—it was a **1NF violation**. Data structure dictated accuracy.

> 🔥 **Hook**: If your database can’t answer a simple counting question reliably, it’s not because of bad code—it’s because of broken *logical design*.

Let’s fix it.

### Intuition: Why Atomicity Matters
Relational databases are built on the idea that **one cell = one fact**. When you pack multiple facts into one value, you force the database to do linguistic interpretation—not logical reasoning.

Consider a query to find all students enrolled in Physics. If the course list is stored as `"Math, Physics"`, the database cannot extract individual courses without string parsing. This violates atomicity and turns simple queries into fragile pattern-matching gambles.

### Analogy: The Library Catalog vs. a Bookshelf Pile
Imagine a library where books are stacked in piles labeled “Science”, “History”, etc. To find all books about quantum physics, you’d have to dig through every pile manually. That’s pre-1NF.

Now imagine each book has its own entry in a catalog, with separate fields for title, author, subject. You can instantly retrieve all quantum physics books. That’s 1NF.

The difference isn’t storage—it’s **accessibility through structure**.

### Concrete Example: Student Course List
Suppose we have:

| StudentID | Courses         |
|-----------|-----------------|
| S1        | Math, Physics   |
| S2        | Chemistry       |

A query `WHERE Courses = 'Physics'` returns nothing. Even `LIKE '%Physics%'` risks false positives (e.g., "Physical Education").

Solution: Split into atomic facts:

| StudentID | Course    |
|-----------|-----------|
| S1        | Math      |
| S1        | Physics   |
| S2        | Chemistry |

Now, `WHERE Course = 'Physics'` works perfectly.

> 💡 **Try this yourself**:  
> You’re designing a ride-sharing app. Drivers list their car types as `"SUV, Sedan"`. How would a 1NF violation here affect a query for “all SUV drivers”? Rewrite the schema to fix it.

### Formal Definition
A relation schema $ R $ is in **First Normal Form (1NF)** if and only if:  
- Every attribute contains **atomic** (indivisible) values.  
- Each tuple has exactly one value per attribute.  
- There are no repeating groups (e.g., `Course1`, `Course2` columns).

> 🔍 **Note on Atomicity**: "Atomic" means indivisible *with respect to the intended operations*. A full name `'Smith'` may be atomic if treated as a unit. But if you parse `'Smith, Jones'` as two names, it’s not atomic—even as a string.

### Worked Example: Flattening a Denormalized Table
Given:

| OrderID | Items              |
|---------|--------------------|
| 101     | Laptop, Mouse      |
| 102     | Keyboard           |

To achieve 1NF:

| OrderID | Item     |
|---------|----------|
| 101     | Laptop   |
| 101     | Mouse    |
| 102     | Keyboard |

Now, “Which orders include a Mouse?” is a simple `SELECT`.

### Test Yourself
Is the following table in 1NF?

| EmployeeID | Skills               |  
|------------|----------------------|  
| E1         | Python, SQL, Java    |  

👉 No. `Skills` contains multiple values. To satisfy 1NF, restructure so each skill is in its own row.

### Common Misconception
*"If my database supports arrays or JSON, I am still in 1NF."*  
False. Logical design—not physical storage—determines 1NF compliance. If you query inside a JSON array (e.g., `skills @> 'Python'`), you’re treating the field non-atomically, violating 1NF at the logical level.

---

## 2. Second Normal Form (2NF): Eliminate Partial Dependencies

### Cross-Domain Insight: GPS Coordinates and Address Redundancy
Think of a GPS device that stores latitude/longitude *and* city name. If the city is determined solely by location (e.g., `(lat, lon) → city`), but you use a composite key `(userID, lat, lon)` to track movements, then `city` depends only on part of the key.

This is a **partial dependency**—and it leads to redundancy every time the same location is logged by the same user.

Now apply this to databases.

### Prerequisites
To understand 2NF, you must know:  
- **Functional dependency (FD)**: $ X \rightarrow Y $ means $ X $ determines $ Y $.  
- **Candidate key**: a minimal set of attributes that uniquely identifies each tuple.  
- **Prime attribute**: part of *any* candidate key.  
- **Non-prime attribute**: not part of any candidate key.

### Intuition: What Is a Partial Dependency?
Suppose a relation uses a composite key $(StudentID, CourseID)$, but `Instructor` depends only on `CourseID`. Then `Instructor` is determined by a *subset* of the key—a **partial dependency**.

This couples course-level data with enrollment records, creating redundancy.

### Concrete Example: Course Registration
| StudentID | CourseID | Instructor     |
|-----------|----------|----------------|
| S1        | C1       | Dr. Lee        |
| S2        | C1       | Dr. Lee        |
| S3        | C2       | Dr. Patel      |

Assume:  
- FD: $ CourseID \rightarrow Instructor $  
- Key: $ (StudentID, CourseID) $

Here, `Instructor` depends only on `CourseID`—a proper subset of the key.

#### Anomalies Caused by Partial Dependencies
- **Update anomaly**: Change Dr. Lee to Dr. Kim? Update all rows with `C1`.  
- **Insertion anomaly**: Can’t record that `C3` is taught by Dr. Kim unless a student enrolls.  
- **Deletion anomaly**: Unenrolling the last student in `C1` deletes instructor info.

> ⚠️ **Tension**: We’re storing **course metadata** in an **enrollment log**. Shouldn’t these be separate concerns?

Yes. Decompose.

### Formal Definition
A relation $ R $ is in **Second Normal Form (2NF)** if:  
- It is in 1NF, and  
- Every **non-prime attribute** is **fully functionally dependent** on every candidate key.  
That is, no non-prime attribute depends on a **proper subset** of any candidate key.

### Worked Example: Decomposition
Given:  
- $ Registration(StudentID, CourseID, Instructor) $  
- FD: $ CourseID \rightarrow Instructor $  
- Key: $ (StudentID, CourseID) $

Step 1: Identify partial dependency: $ CourseID \rightarrow Instructor $  
Step 2: Decompose:  
- $ CourseInstructors(CourseID, Instructor) $  
- $ Enrollments(StudentID, CourseID) $

Now:  
- In $ CourseInstructors $, $ CourseID $ is the key → fully determines $ Instructor $.  
- In $ Enrollments $, $ (StudentID, CourseID) $ is the key; no non-prime attributes.

Both are in 2NF.

> 💡 **Try this yourself**:  
> A lab testing system logs `(PatientID, TestCode, Technician, TestName)`.  
> Given $ TestCode \rightarrow TestName $, and key $ (PatientID, TestCode) $, how would you decompose to 2NF? What anomalies does this prevent?

### Test Yourself
Is the following table in 2NF?

| PatientID | TestCode | Technician | TestName     |  
|-----------|----------|------------|--------------|  
| P1        | T1       | TechA      | Blood Test   |  
| P2        | T1       | TechA      | Blood Test   |  

Given:  
- FD: $ TestCode \rightarrow TestName $  
- Key: $ (PatientID, TestCode) $

👉 No. $ TestName $ depends only on $ TestCode $, a proper subset of the key. Since $ TestName $ is non-prime, this violates 2NF.

### Common Misconception
*"If a table has a single-column key, I need to check for 2NF."*  
No. 2NF only applies when there exists a **composite candidate key**. If all candidate keys are single-attribute, every non-prime attribute is trivially fully dependent on the key—so the relation is automatically in 2NF.

---

## 3. Third Normal Form (3NF): Eliminate Transitive Dependencies

### Analogy: The Chain of Command
In a military hierarchy:  
- Soldier → Platoon  
- Platoon → Commander  

Then Soldier → Commander indirectly. But if the commander changes, you don’t update every soldier’s record—you update the platoon’s assignment.

In databases, **transitive dependencies** force you to do the opposite: update many records when a higher-level fact changes. That’s inefficient and error-prone.

### Intuition: What Is a Transitive Dependency?
Suppose:  
- $ EmpID \rightarrow Dept $  
- $ Dept \rightarrow Manager $  
Then $ EmpID \rightarrow Manager $ indirectly. But `Manager` depends on `Dept`, not directly on `EmpID`.

This couples independent facts and introduces redundancy.

### Concrete Example: Employee Management
| EmpID | Dept   | Manager     |
|-------|--------|-------------|
| E1    | Sales  | Alice       |
| E2    | Sales  | Alice       |
| E3    | HR     | Bob         |

FDs:  
- $ EmpID \rightarrow Dept $  
- $ Dept \rightarrow Manager $  
Key: $ EmpID $

If Alice leaves and Bob becomes Sales manager, we must update every employee in Sales—even though the change is departmental, not employee-specific.

This is an **update anomaly** due to transitive dependency.

> 🔥 **Tension**: Why should changing a department’s manager require editing employee records? Employees don’t “own” manager data.

Separate the concerns.

### Formal Definition (Zaniolo, 1982)
A relation $ R $ is in **Third Normal Form (3NF)** if:  
- It is in 2NF, and  
- For every non-trivial functional dependency $ X \rightarrow Y $:  
  - $ X $ is a **superkey**, or  
  - $ Y $ is a **prime attribute**.

This prevents non-prime attributes from being determined by non-superkeys unless the dependent attribute is itself part of a candidate key.

### Worked Example: Decomposition
Given:  
- $ Employee(EmpID, Dept, Manager) $  
- FDs: $ EmpID \rightarrow Dept $, $ Dept \rightarrow Manager $  
- Key: $ EmpID $

Check $ Dept \rightarrow Manager $:  
- $ Dept $ is not a superkey  
- $ Manager $ is non-prime  
→ Violates 3NF

Decompose using $ Dept \rightarrow Manager $:  
1. $ DeptMgr(Dept, Manager) $  
2. $ EmpDept(EmpID, Dept) $

Now:  
- In $ DeptMgr $, $ Dept $ is the key → $ Dept \rightarrow Manager $ is valid  
- In $ EmpDept $, $ EmpID $ is the key → $ EmpID \rightarrow Dept $ is valid  
Both relations are in 3NF.

> 💡 **Try this yourself**:  
> A university stores `(StudentID, Major, DepartmentChair)`.  
> Given $ Major \rightarrow DepartmentChair $, and key $ StudentID $, decompose to 3NF. What happens if the chair changes?

### Test Yourself
Is the following relation in 3NF?

| OrderID | CustomerID | Branch       | BranchManager |  
|---------|------------|--------------|---------------|  
| O1      | C1         | NYC          | John          |  
| O2      | C2         | NYC          | John          |  

Given:  
- FDs: $ OrderID \rightarrow CustomerID $, $ Branch \rightarrow BranchManager $  
- Key: $ OrderID $

👉 No. $ Branch \rightarrow BranchManager $, $ Branch $ is not a superkey, and $ BranchManager $ is non-prime → violates 3NF.

### Common Misconception
*"If an attribute is part of a key, it’s always prime."*  
Yes—but only if it is part of *any* **candidate key**. Always compute all candidate keys via attribute closure before labeling attributes as prime or non-prime.

---

## 4. Boyce-Codd Normal Form (BCNF): Every Determinant Must Be a Superkey

### The Hidden Flaw in 3NF: A Voting Paradox Analogy
In voting theory, a candidate can win under one system (e.g., plurality) but lose under another (e.g., ranked-choice). Similarly, **3NF accepts certain dependencies that BCNF rejects**—because 3NF allows exceptions when the dependent attribute is prime.

This loophole can still cause anomalies.

> 🔥 **Tension**: A relation can be in 3NF and still force you to duplicate data or risk inconsistency. How?

Let’s see.

### Concrete Example: Property Valuation
| PropertyID | Area     | County_name | Price   |
|-----------|----------|-------------|---------|
| P1        | A1       | CountyX     | $500K   |
| P2        | A1       | CountyX     | $480K   |
| P3        | A2       | CountyY     | $300K   |

FDs:  
- $ PropertyID \rightarrow Area $  
- $ Area \rightarrow County\_name $  
- $ Area \rightarrow Price $  
Key: $ PropertyID $

Check $ Area \rightarrow County\_name $:  
- $ Area $ is not a superkey → violates BCNF.

Even if `County_name` were prime, the determinant `Area` isn’t a superkey.

This means two properties in the same area must repeat `County_name`—and if the county boundary changes, all rows must be updated.

### Formal Definition
A relation $ R $ is in **Boyce-Codd Normal Form (BCNF)** if and only if, for every non-trivial functional dependency $ X \rightarrow Y $, $ X $ is a **superkey**.

BCNF is **strictly stronger** than 3NF: every BCNF relation is in 3NF, but not every 3NF relation is in BCNF.

### Worked Example: BCNF Decomposition
Given:  
- $ LOTS(PropertyID, Area, County\_name, Price) $  
- FDs: $ Area \rightarrow County\_name $, $ Area \rightarrow Price $  
- Key: $ PropertyID $

Step 1: $ Area \rightarrow County\_name $, $ Area $ not superkey → decompose:  
- $ R1(Area, County\_name) $  
- $ R2(PropertyID, Area, Price) $

Step 2: In $ R2 $, $ Area \rightarrow Price $, $ Area $ not superkey → decompose:  
- $ R3(Area, Price) $  
- $ R4(PropertyID, Area) $

Final schema:  
- $ R1(Area, County\_name) $  
- $ R3(Area, Price) $  
- $ R4(PropertyID, Area) $

All are in BCNF.

⚠️ **Trade-off**: The FD $ PropertyID \rightarrow Price $ is **not preserved**. Enforcing it now requires joins or application-level constraints.

### Worked Example 2: Instructor-Course Bijection
| Student   | Course   | Instructor   |
|-----------|----------|--------------|
| S1        | C1       | Dr. Lee      |
| S2        | C1       | Dr. Lee      |
| S3        | C2       | Dr. Patel    |

FDs: $ Course \rightarrow Instructor $, $ Instructor \rightarrow Course $  
Candidate keys: $ (Student, Course) $, $ (Student, Instructor) $

Check $ Course \rightarrow Instructor $: $ Course $ is not a superkey → violates BCNF.

Decompose using $ Course \rightarrow Instructor $:  
- $ CourseInst(Course, Instructor) $  
- $ EnrollOnly(Student, Course) $

Now:  
- In $ CourseInst $, $ Course $ is a key → satisfies BCNF  
- In $ EnrollOnly $, $ (Student, Course) $ is a key → satisfies BCNF  
- $ Instructor \rightarrow Course $ is preserved via $ CourseInst $  
- Join on $ Course $ reconstructs the original → **lossless decomposition**

> 💡 **Try this yourself**:  
> A music database stores `(Artist, Genre, Label)` with FDs:  
> $ Artist \rightarrow Genre $, $ Genre \rightarrow Label $, key: $ Artist $.  
> Is this in BCNF? If not, decompose it. What dependency is lost?

### Test Yourself
Is the following relation in BCNF?

| Course   | Instructor   | Textbook     |  
|----------|--------------|--------------|  
| C1       | Dr. Lee      | DB Book      |  
| C2       | Dr. Patel    | Algo Book    |  

Given:  
- FDs: $ Course \rightarrow Instructor $, $ Instructor \rightarrow Textbook $  
- Candidate keys: $ Course $, $ Instructor $

👉 No. $ Instructor \rightarrow Textbook $, but $ Instructor $ is not a superkey (e.g., in a relation where $ Course $ is the primary key). Thus, the FD violates BCNF.

### Common Misconception
*"BCNF always preserves all functional dependencies."*  
False. BCNF guarantees **lossless join decomposition** and **elimination of update anomalies**, but **does not guarantee dependency preservation**. Some FDs may be lost and must be enforced via triggers or application logic.

---

## 5. Trade-offs and Practical Design Decisions

### Normalization vs. Denormalization

| Aspect | Normalized (3NF/BCNF) | Denormalized |
|-------|------------------------|-------------|
| **Data Integrity** | ✅ High: minimal redundancy, consistent updates | ❌ Risk of anomalies |
| **Update Performance** | ✅ Efficient for OLTP systems | ❌ Complex updates |
| **Query Performance** | ❌ Requires joins → slower reads | ✅ Fast for reporting (OLAP) |
| **Maintainability** | ✅ Clear schema, easy evolution | ❌ Harder to modify |

### When to Stop Normalizing
- **3NF is often sufficient** for transactional systems where update safety is critical.  
- **BCNF is preferred** when anomalies are unacceptable (e.g., financial or medical systems).  
- **Denormalize selectively** when read performance is paramount—use materialized views, caching, or summary tables to maintain consistency.

### Real-World Example: Social Media Feed
Facebook’s News Feed stores precomputed data such as author name, like count, and comment count in a denormalized table. This avoids expensive joins during page loads. When a user likes a post, background jobs asynchronously update the counts. This trades **consistency latency** for **read speed**—a deliberate design choice.

> 🔍 **Cross-Domain Insight**: This is like pre-rendering a video game world map. You trade storage and update cost for instant access—just as denormalization trades redundancy for speed.

### Advanced Normal Forms (Brief Overview)
- **4NF**: Eliminates multi