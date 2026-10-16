**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. Recall the definitions and conditions for 1NF, 2NF, 3NF, and BCNF, and distinguish between them.  
2. Understand how functional dependencies, candidate keys, and attribute types (prime vs. non-prime) determine normal form compliance.  
3. Apply decomposition techniques to normalize a schema step-by-step from 1NF to BCNF while preserving data integrity and avoiding anomalies.  
4. Analyze a given schema to identify partial, transitive, and determinant-based violations, and determine the highest normal form it satisfies.  
5. Evaluate trade-offs between normalization levels in real-world scenarios, including performance, consistency, and maintainability.

---

## Prerequisites: Functional Dependencies, Keys, and Attribute Classification

Imagine you’re debugging a hospital database where a patient allergic to penicillin was just prescribed it—again. The system *knew* about the allergy, stored in a comma-separated list. But because the field wasn’t searchable atomically, the alert never fired.

This isn’t a software bug. It’s a **structural flaw**—a failure to enforce atomicity. And it starts with **First Normal Form**.

But before we get there, we need to understand *why* data depends on other data. That begins with **functional dependencies**.

### Functional Dependencies — From Business Rules to Data Constraints

> **Intuition First**: A functional dependency (FD) is a *promise*: whenever these inputs appear, this output must follow.  
Like a mathematical function: same input, same output—every time.

For example:  
- **FlightNumber, Date** → **Pilot**: You can’t have two pilots for the same flight on the same day.  
- **ISBN** → **Title**: One book identifier, one title.

We write $ X \rightarrow Y $: “$ X $ determines $ Y $.” Formally:

> **Definition (Functional Dependency)**: Let $ R $ be a relation schema. A functional dependency $ X \rightarrow Y $ holds on $ R $ if, for every valid instance $ r $ of $ R $,  
> $$
> \forall t_1, t_2 \in r, \quad t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]
> $$

> **Trivial vs. Non-Trivial FDs**:  
- $ A \rightarrow A $ is **trivial**—always true.  
- $ \text{SSN} \rightarrow \text{BirthDate} $ is **non-trivial**—it reveals real-world constraints.

We focus on non-trivial FDs because they expose **structure**—and potential redundancy.

> **Analogy (Electrical Circuits)**:  
Think of an FD as a one-way circuit: when voltage (input) is applied at $ X $, current *must* flow to $ Y $. If it doesn’t, the circuit is broken. Similarly, if $ \text{OrderID} \rightarrow \text{CustomerID} $ fails for one record, the rule is violated.

> **Worked Example**:  
Schema: `Orders(OrderID, CustomerID, CustomerEmail)`  
Business rule: Each customer has one email.  
Then:  
- $ \text{CustomerID} \rightarrow \text{CustomerEmail} $ ✅  
But:  
- $ \text{CustomerEmail} \rightarrow \text{CustomerID} $? Only if emails are globally unique. This depends on policy—not data.

> **Common Misconception**: “If $ X \rightarrow Y $, then $ X $ must be a key.”  
❌ False. $ X $ can be any determinant.  
Example: In `Employees`, $ \text{Department} \rightarrow \text{DeptManager} $ may hold, but `Department` is not a key.

> **Try This Yourself 1**:  
In `Movies(Title, Year, Director)`, suppose $ \text{Title, Year} \rightarrow \text{Director} $.  
Does $ \text{Director} \rightarrow \text{Title} $ hold?  
👉 No—directors make multiple movies.  
Now consider $ \text{ISBN} \rightarrow \text{Title} $. Does $ \text{Title} \rightarrow \text{ISBN} $?  
👉 No—many books share titles. This asymmetry affects indexing: only the determinant side supports reliable lookups.

---

### Keys and Attribute Classification — Identifying Determinants

Functional dependencies let us define **keys** precisely—not just by naming them, but by proving their power.

> **Intuition First**: A **key** is the minimal set of attributes that *uniquely identifies* a row.  
“John Smith” isn’t enough. But “SSN: 123-45-6789” is.

> **Definitions**:  
- **Superkey**: A set $ K $ such that $ K \rightarrow R $ (determines all attributes in the schema).  
- **Candidate Key**: A minimal superkey—no proper subset is a superkey.  
- **Primary Key**: One selected candidate key for implementation.

> **Analogy (Biological Keys)**:  
A superkey is like a full DNA profile. A candidate key is the *smallest unique fragment*—say, a specific gene sequence—that still uniquely identifies an individual. The primary key is the one labs actually use for matching.

> **Prime vs. Non-Prime Attributes**:  
- An attribute is **prime** if it belongs to *any* candidate key.  
- Otherwise, it is **non-prime**.

> **Worked Example 1**:  
Schema: $ R(A, B, C) $, FDs: $ A \rightarrow B $, $ B \rightarrow C $, candidate key $ A $.  
- $ A $: prime (in candidate key)  
- $ B, C $: non-prime (not in any candidate key)

> **Worked Example 2**:  
Same schema, FDs: $ A \rightarrow B $, $ C \rightarrow B $, candidate key $ \{A, C\} $.  
Then $ A $ and $ C $ are both **prime**, even though neither determines all attributes alone.

> **Common Misconception**: “Only the primary key defines prime attributes.”  
❌ False. **Primality depends on membership in *any* candidate key**, not just the primary key.

> **Try This Yourself 2**:  
In $ R(\text{ISBN}, \text{Author}, \text{Title}) $, suppose:  
- $ \text{ISBN} \rightarrow \text{Title, Author} $  
- $ \text{Title} \rightarrow \text{Author} $  

Is $ \text{Title} $ prime?  
👉 No—titles are not unique, so $ \text{Title} $ cannot be part of a candidate key → **non-prime**.

Now suppose $ \text{Author, Title} \rightarrow \text{ISBN} $. Could $ \text{Title} $ be prime?  
👉 Yes—if $ \{\text{Author, Title}\} $ is a candidate key, then both $ \text{Author} $ and $ \text{Title} $ are **prime**.

---

### Lossless Decomposition — Preserving Data Integrity During Splitting

Imagine you’re a genomicist reconstructing a genome from fragmented DNA reads. If the fragments don’t overlap meaningfully, you’ll assemble the wrong sequence—or create fake genes.

Database decomposition is the same: split tables, but only if you can **reconstruct the original without error**.

> **Intuition First**: When splitting a table, the join must **exactly reproduce** the original data—no missing rows, no fake ones.

> **Definition (Lossless Join Decomposition)**: A decomposition of $ R $ into $ R_1 $ and $ R_2 $ is **lossless** if, for every valid instance $ r $ of $ R $,  
> $$
> \pi_{R_1}(r) \bowtie \pi_{R_2}(r) = r
> $$

> **Key Rule (Sufficient Condition for Losslessness)**:  
A decomposition of $ R $ into $ R_1 $ and $ R_2 $ is lossless if:  
$$
R_1 \cap R_2 \rightarrow R_1 \quad \text{or} \quad R_1 \cap R_2 \rightarrow R_2
$$  
The **common attributes** must functionally determine one of the decomposed relations.

> **Analogy (Jigsaw Puzzle)**:  
If two puzzle pieces share a unique edge pattern that fits only one way, you can reassemble them correctly. The intersection is that edge. If it’s ambiguous, you might force a wrong connection—like joining unrelated employee and department pairs.

> **Worked Example 1**:  
$ R(A, B, C) $, FDs: $ A \rightarrow B $, $ B \rightarrow C $, key $ A $.  
Decompose into:  
- $ R_1(A, B) $  
- $ R_2(B, C) $  
Intersection: $ \{B\} $  
Check: $ B \rightarrow C $? Yes → $ B $ determines $ R_2 $ → lossless ✅

> **Worked Example 2**:  
$ R(A, B, C, D) $, FDs: $ A \rightarrow B $, $ C \rightarrow D $, key $ \{A, C\} $.  
Decompose into $ R_1(A, B) $, $ R_2(C, D) $.  
Intersection: $ \emptyset $ → no common attributes → **lossy** ❌ (produces spurious tuples)

Now try: $ R_1(A, B, C) $, $ R_2(C, D) $  
Intersection: $ \{C\} $  
Does $ C \rightarrow D $? Yes → determines $ R_2 $ → lossless ✅

> **Common Misconception**: “As long as all attributes are preserved, no data is lost.”  
❌ False. Without a common determinant, joining creates **spurious tuples**—combinations not present in the original data.

> **Try This Yourself 3**:  
Decompose $ R(\text{EmpID}, \text{Dept}, \text{Manager}) $ into:  
- $ R_1(\text{EmpID}, \text{Dept}) $  
- $ R_2(\text{Dept}, \text{Manager}) $  
Assume $ \text{Dept} \rightarrow \text{Manager} $.  
Is this lossless?  
👉 Yes—intersection $ \text{Dept} $ determines $ R_2 $.

> **Practical Application**:  
In a warehouse system, `Inventory(ItemID, Location, ShelfCapacity)` is decomposed into:  
- `ItemLocation(ItemID, Location)`  
- `Shelf(Location, ShelfCapacity)`  
With $ \text{Location} \rightarrow \text{ShelfCapacity} $, the join is lossless—preserving integrity during restocking.

---

## First Normal Form (1NF): The Atomic Foundation

Back to the hospital.  
`PatientAllergies: "penicillin, peanuts"`  
Query: `WHERE Allergies = 'penicillin'` → returns nothing.  
Why? Because the database sees "penicillin, peanuts" as **one string**, not two allergies.

This is a **1NF violation**.

> **Definition (1NF)**: A relation is in **1NF** if:  
> 1. All attribute values are **atomic** (indivisible).  
> 2. Each attribute contains **exactly one value per tuple**.  
> 3. Row and column order is irrelevant.

> **Intuition First**: Every cell must contain a **single scalar value**—no lists, sets, or nested structures.

> **Analogy (Chemistry: Elements vs. Compounds)**:  
Just as water (H₂O) must be broken into hydrogen and oxygen to study its components, "Math, Physics" must be split into atomic facts. 1NF is the **elemental level** of data.

> **Normalization to 1NF**:  
Replace multivalued attributes with a new relation:  
```
StudentCourses(StudentID, Course)
```
| StudentID | Course  |
|-----------|---------|
| S01       | Math    |
| S01       | Physics |

Each value is atomic → 1NF achieved ✅

> **Worked Example**:  
`Employees(EmpID, Name, Skills)` with `Skills = ["Java", "Python"]`  
Normalize to:  
`EmployeeSkills(EmpID, Skill)`  
Insert: (E01, "Java"), (E01, "Python")

> **Common Misconception**: “Storing JSON in PostgreSQL breaks 1NF.”  
❌ Not necessarily. If the JSON represents a **single fact** (e.g., `Location: {"lat": 40.7, "lon": -74.0}`), it may be atomic.  
But if it contains **multiple values** (e.g., `Skills: ["Java", "Python"]`), it violates 1NF.

> **Try This Yourself 4**:  
Is this in 1NF?  
`Patients(PatientID, Name, Allergies)` where `Allergies = "penicillin, peanuts"`  
👉 No. Fix: create `PatientAllergies(PatientID, Allergy)`.

> **Real-World Impact**: In electronic health records, storing allergies as strings has caused missed drug interactions. Modern systems (e.g., Epic) normalize allergies to atomic rows—a life-saving application of 1NF.

> **Cross-Industry Example (E-Commerce)**:  
Amazon stores `ProductTags` in a junction table, not as a string. This enables filtering, analytics, and recommendations—demonstrating 1NF’s relevance beyond databases.

---

## Second Normal Form (2NF): Eliminate Partial Dependencies

Now consider a university enrollment table:

```
Enrollments(OrderID, CourseID, CourseName, Credits)
```
- Candidate key: $ \{OrderID, CourseID\} $  
- FD: $ \text{CourseID} \rightarrow \text{CourseName} $  

`CourseName` depends only on `CourseID`—a **proper subset** of the key. This is a **partial dependency**.

> **Definition (2NF)**: A relation is in **2NF** if:  
> 1. It is in 1NF.  
> 2. No non-prime attribute is **partially dependent** on any candidate key.  
> (i.e., no non-key attribute depends on a proper subset of a composite key.)

> **Intuition First**: If a non-key attribute depends on only part of a composite key, it is **redundantly stored** across multiple rows.

> **Analogy (Postal System)**:  
ZIP code determines city. Writing “New York” on every “10001” envelope is redundant. Similarly, storing `CourseName` with every enrollment wastes space and risks inconsistency.

> **Anomalies in 2NF Violation**:  
- 🔁 **Redundancy**: `CourseName` repeats across enrollments.  
- ➕ **Insert anomaly**: Cannot add a course without an enrollment.  
- ➖ **Deletion anomaly**: Canceling the last enrollment deletes course data.  
- ✏️ **Update anomaly**: Renaming a course requires updating multiple rows.

> **Normalization to 2NF**:  
Decompose into:  
- `Enrollments(OrderID, CourseID)`  
- `Courses(CourseID, CourseName, Credits)`

Now `CourseName` depends fully on `CourseID`, which is a key in `Courses`.

> **Worked Example**:  
$ R(A, B, C) $, key $ \{A, B\} $, FD $ A \rightarrow C $, $ C $ non-prime.  
- $ A $ is a proper subset of the key → partial dependency → not in 2NF.  
Decompose:  
- $ R_1(A, C) $  
- $ R_2(A, B) $  
Now $ A \rightarrow C $ holds in $ R_1 $, where $ A $ is a key → 2NF achieved.

> **Common Misconception**: “2NF is outdated.”  
❌ False. Any schema with composite keys (e.g., order lines, enrollments) must consider 2NF.

> **Try This Yourself 5**:  
$ R(\text{EmpID}, \text{ProjectID}, \text{ProjectLead}) $, key $ \{\text{EmpID}, \text{ProjectID}\} $, FD $ \text{ProjectID} \rightarrow \text{ProjectLead} $.  
Is this in 2NF?  
👉 No—`ProjectLead` depends only on `ProjectID` → violates 2NF.

What if `ProjectLead` were part of the key?  
👉 Then `ProjectLead` would be **prime**, and the FD would not violate 2NF.

> **Practical Application (Logistics)**:  
FedEx separates `ShipmentDetails(TrackingID, PackageID, Destination)` from `PackageInfo(PackageID, Weight, Category)` to avoid repeating metadata—ensuring consistency in billing and routing.

---

## Third Normal Form (3NF): Eliminate Transitive Dependencies

Consider:

```
Student(StudentID, Advisor, AdvisorOffice)
```
FDs:  
- $ \text{StudentID} \rightarrow \text{Advisor} $  
- $ \text{Advisor} \rightarrow \text{AdvisorOffice} $

So: $ \text{StudentID} \rightarrow \text{AdvisorOffice} $, but through a **non-key intermediary**.

This is a **transitive dependency**—and it’s dangerous.

> **Definition (3NF)**: A relation is in **3NF** if, for every non-trivial FD $ X \rightarrow Y $, at least one of the following holds:  
> 1. $ X $ is a superkey, or  
> 2. $ Y $ is a **prime** attribute.

> **Intuition First**: “Non-key attributes should depend on the key, the whole key, and nothing but the key—unless the result is part of a key.”

> **Analogy (Chain of Command)**:  
In a military hierarchy, a Lieutenant should not issue orders that bind a Captain. Similarly, a non-key attribute (`AdvisorOffice`) should not be determined by another non-key (`Advisor`) unless that determinant is a superkey.

> **Normalization to 3NF**:  
Decompose into:  
- `Students(StudentID, Advisor)`  
- `Advisors(Advisor, AdvisorOffice)`

Now `AdvisorOffice` depends on `Advisor`, which is a key in `Advisors`.

> **Worked Example**:  
$ R(A, B, C) $, key $ A $, FDs: $ A \rightarrow B $, $ B \rightarrow C $, $ C $ non-prime.  
- $ B \rightarrow C $: $ B $ is not a superkey, $ C $ is non-prime → violates 3NF.  
Decompose:  
- $ R_1(A, B) $  
- $ R_2(B, C) $  
Now $ B \rightarrow C $ holds in $ R_2 $, where $ B $ is a key → 3NF achieved.

> **Common Misconception**: “3NF allows any dependency as long as it’s not redundant.”  
❌ False. The rule is strict: either the determinant is a superkey, or the determined attribute is prime.

> **Try This Yourself 6**:  
$ R(\text{EmpID}, \text{Dept}, \text{DeptManager}) $, key $ \text{EmpID} $, FD $ \text{Dept} \rightarrow \text{DeptManager} $.  
Is this in 3NF?  
👉 No—`Dept` is not a superkey, `DeptManager` is non-prime → violates 3NF.

Can we fix it?  
👉 Yes: decompose into `Employees(EmpID, Dept)` and `Departments(Dept, DeptManager)`.

> **Practical Application (HR Systems)**:  
Google’s employee database separates `Employee(EmpID, Dept)` from `Department(Dept, Manager)` to ensure manager updates propagate consistently—preventing data drift.

---

## Boyce-Codd Normal Form (BCNF): Strengthening the Key

Here’s a puzzle:

```
Teaching(Professor, Course, Time)
```
Suppose:
- Each professor teaches only one course. → $ \text{Professor} \rightarrow \text{Course} $
- Each course meets at only one time. → $ \text{Course} \rightarrow \text{Time} $
- Candidate keys: $ \{\text{Professor}, \text{Time}\} $ and