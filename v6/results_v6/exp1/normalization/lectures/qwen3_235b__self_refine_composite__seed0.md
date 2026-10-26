| PatientID | Name   | Allergies               |
|---------|--------|-------------------------|
| P001    | Maria  | Penicillin, Latex       |
| P002    | James  | Peanuts, Bee stings     |

A nurse queries for patients allergic to *Latex*:

```sql
SELECT * FROM Patients WHERE Allergies LIKE '%Latex%';
```

This query is unreliable:  
- It may yield **false positives** (e.g., "Latex-free").  
- It may yield **false negatives** (e.g., "Latex (severe)" stored inconsistently).  
- It cannot enforce constraints (e.g., no duplicates).

The issue is **non-atomic data**: the *Allergies* column holds multiple values. This violates the principle of **atomicity**—each cell must contain a single, indivisible value.

> **Analogy**: Storing a Python list as a string `"['a','b']"` prevents safe iteration without parsing. Similarly, databases require atomic values to support indexing, constraints, and joins.

But here’s the twist: imagine you’re designing software for a **space station medical bay**. An astronaut has a severe latex allergy. The system misreads "Latex (severe)" as "Latex-free" due to inconsistent formatting. A glove is issued. The consequence? Catastrophic.

Atomicity isn’t about neatness—it’s about **failure tolerance in critical systems**. In 1NF, every value must be indivisible *by design*, not just by convention.

#### Formal Definition of 1NF

A relation is in **First Normal Form (1NF)** if:  
1. All attribute values are **atomic**—indivisible within the domain.  
2. There are **no repeating groups**—each attribute contains exactly one value per row.

> **Note**: While 1NF does not formally require a candidate key, practical implementations do. Without a key, duplicate rows cannot be controlled, and joins become ambiguous.

#### Worked Example: Normalizing a Course List

Given this unnormalized table:

| StudentID | StudentName | Course           | Instructor | CourseLevel |
|-----------|-------------|------------------|------------|-------------|
| S001      | Alice       | CS101, CS102     | Dr. Lee    | Intro       |

The *Course* column contains multiple values. To achieve 1NF:  
1. **Decompose** the *Course* list into separate rows.  
2. **Duplicate** non-repeating attributes to preserve context.

Result:

| StudentID | StudentName | Course  | Instructor | CourseLevel |
|-----------|-------------|---------|------------|-------------|
| S001      | Alice       | CS101   | Dr. Lee    | Intro       |
| S001      | Alice       | CS102   | Dr. Lee    | Intro       |

Each cell is now atomic. The candidate key is {StudentID, Course}, ensuring uniqueness.

> **Misconception Alert**:  
> “Using `SPLIT()` or `LIKE` fixes 1NF.”  
> No—string manipulation is not normalization. Atomicity must be enforced at the **logical schema level**. Otherwise, indexing, constraints, and joins remain error-prone.

> **Try This Yourself**:  
> Suppose *Instructor* contains "Dr. Lee, Dr. Smith".  
> ✅ Fix: Create `CourseInstructors(Course, Instructor)` with one row per instructor.  
> What if the same instructor teaches multiple courses? Does your design still work?

> **Case Study: E-Commerce Product Tags**  
> | ProductID | Tags               |  
> |----------|--------------------|  
> | P1       | Organic, Vegan     |  
>  
> This violates 1NF. Fix by creating:  
> `ProductTags(ProductID, Tag)`  
> with rows: (P1, Organic), (P1, Vegan).  
> Now queries like “find all vegan products” are accurate.

> **Cross-Domain Insight**:  
> 1NF is like **dimensional consistency in physics**. Just as you can’t add meters to seconds, you can’t store multiple allergy entries in one field. Each attribute has a single "dimension" of meaning. Violating this leads to "type errors" in data logic.

---

### Step 2: Second Normal Form (2NF) — Full Functional Dependency

**Learning Objectives**  
By the end of this section, you will be able to:  
- Define 2NF and partial dependency.  
- Explain how partial dependencies cause update anomalies.  
- Eliminate partial dependencies via decomposition.

#### Prerequisites  
You should now be able to:  
- Identify atomic attributes.  
- Determine candidate keys.  
- Recognize functional dependencies (e.g., A → B).

#### Motivating Example: The Inventory Puzzle

Consider:

| StoreID | ProductID | ProductName | Price | Location |
|--------|-----------|-------------|-------|----------|
| S01   | P101      | iPhone      | 999   | Aisle 5  |
| S02   | P101      | iPhone      | 999   | Aisle 3  |

Functional Dependencies:  
- ProductID → ProductName  
- {StoreID, ProductID} → {Price, Location}

Candidate key: {StoreID, ProductID}  
Non-prime attributes: ProductName, Price, Location

But ProductName depends only on ProductID—a **proper subset** of the key. This is a **partial dependency**.

To rename “iPhone” to “iPhone Pro”, update all rows. Miss one → inconsistency.

> **Analogy**: Storing a book’s title in every chapter file. The title belongs to the book, not the chapter. Similarly, ProductName depends on ProductID, not the Store-Product pair.

But consider this: in a **library digital archive**, each scanned page of a book includes the full title, author, and ISBN. If the book is reclassified, every page must be updated. That’s inefficient and error-prone. Instead, we separate the **entity** (book) from its **instances** (pages). 2NF forces this separation.

#### Formal Definition of 2NF

A relation is in **Second Normal Form (2NF)** if:  
1. It is in 1NF, and  
2. Every **non-prime attribute** is **fully functionally dependent** on every candidate key.

A **partial dependency** occurs when a non-prime attribute depends on a proper subset of a composite key.

> **Important**: 2NF only applies when the candidate key is **composite**. If the key is a single attribute, 2NF is automatically satisfied.

#### Worked Example: Student Enrollments

Given:

**Enrollments**(StudentID, StudentName, Course, Instructor, CourseLevel)  
Functional Dependencies:  
- StudentID → StudentName  
- Course → {Instructor, CourseLevel}  
- {StudentID, Course} → all

Candidate key: {StudentID, Course}

Check for partial dependencies:  
- StudentName depends only on StudentID → partial  
- Instructor and CourseLevel depend only on Course → partial

Decompose using determinants:

1. **Students**(StudentID, StudentName) — key: {StudentID}  
2. **Courses**(Course, Instructor, CourseLevel) — key: {Course}  
3. **Enrollments**(StudentID, Course) — key: {StudentID, Course}

Now, in each table, non-prime attributes depend on the **entire** key.

> **Try This Yourself**:  
> Add Course → Department.  
> ✅ Courses remains in 2NF: Department depends on the full key Course.  
> But what if Department → Budget? Is that still 2NF? Hold that thought.

> **Case Study: Library Book Checkout**  
> **Checkouts**(MemberID, ISBN, Title, Author, DueDate)  
> FDs: ISBN → {Title, Author}, {MemberID, ISBN} → DueDate  
>  
> Partial dependency: Title and Author depend only on ISBN.  
> Fix:  
> - Books(ISBN, Title, Author)  
> - Checkouts(MemberID, ISBN, DueDate)  
> Now book updates affect only one row.

> **Cross-Domain Insight**:  
> 2NF is like **separating configuration from instance data** in software engineering. A Docker container’s image (Course) defines its environment; you don’t re-specify it for every run. Similarly, Course → Instructor belongs in a separate table, not repeated per enrollment.

---

### Step 3: Third Normal Form (3NF) — Eliminating Transitive Dependencies

**Learning Objectives**  
By the end of this section, you will be able to:  
- State the 3NF condition.  
- Identify transitive dependencies.  
- Decompose a relation into 3NF.

#### Prerequisites  
You should now be able to:  
- Identify candidate keys and non-prime attributes.  
- Recognize functional dependencies.  
- Eliminate partial dependencies.

#### Motivating Example: The Doctor’s Hierarchy

Consider:

**Doctors**(DoctorID, Specialty, DeptHead, DeptPhone)  
FDs:  
- DoctorID → Specialty  
- Specialty → DeptHead  
- DeptHead → DeptPhone

Candidate key: {DoctorID}  
Non-prime attributes: DeptHead, DeptPhone

Dependencies form a chain:  
DoctorID → Specialty → DeptHead → DeptPhone

Changing the department head requires updating **every doctor** in that specialty. Miss one → inconsistency.

This **transitive dependency** introduces redundancy and fragility.

> **Analogy**: A linked list storing the full path in each node. Changing one link forces updates to all downstream nodes. 3NF breaks such chains.

But here’s a **non-obvious framing**: think of this as **data versioning**. In Git, if you change a branch name, you don’t update every commit message. You update the reference. Similarly, DeptHead should be a reference, not a copied value.

#### Formal Definition of 3NF

A relation is in **Third Normal Form (3NF)** if:  
1. It is in 2NF, and  
2. For every non-trivial functional dependency X → Y, at least one holds:  
   - X is a superkey, or  
   - Y is a prime attribute.

Equivalently: **No non-prime attribute depends on another non-prime attribute.**

#### Worked Example: Course and Office

Given:

**Courses**(Course, Instructor, Office)  
FDs:  
- Course → Instructor  
- Instructor → Office

Candidate key: {Course}  
Office is non-prime and depends on Instructor (non-key) → violates 3NF

Decompose using Instructor → Office:

1. **Courses**(Course, Instructor) — key: {Course}  
2. **Instructors**(Instructor, Office) — key: {Instructor}

Now:  
- In Courses: Course → Instructor, Course is superkey → OK  
- In Instructors: Instructor → Office, Instructor is superkey → OK

Both tables are in 3NF.

> **Try This Yourself**:  
> **Students**(StudentID, Advisor, Dept, DeptPhone)  
> - StudentID → Advisor  
> - Advisor → Dept  
> - Dept → DeptPhone  
>  
> Transitive dependencies: Advisor → Dept → DeptPhone  
> Decompose:  
> - Students(StudentID, Advisor)  
> - Advisors(Advisor, Dept)  
> - Departments(Dept, DeptPhone)  
> What if two advisors share a department? Does your design scale?

> **Case Study: Hotel Management**  
> **Rooms**(RoomID, HotelName, Manager, ManagerEmail)  
> FDs: RoomID → HotelName, HotelName → {Manager, ManagerEmail}  
>  
> Transitive dependency: Room → Hotel → Manager  
> Fix:  
> - Hotels(HotelName, Manager, ManagerEmail)  
> - Rooms(RoomID, HotelName)  
> Now manager updates affect only one row.

> **Cross-Domain Insight**:  
> 3NF is like **normalizing a decision tree** in machine learning. Each split depends only on the input, not on intermediate outputs. Similarly, in 3NF, data depends only on the key, not on derived attributes.

> **Pitfall**: 3NF does **not** eliminate all anomalies—it does not handle multivalued dependencies (addressed in 4NF).

---

### Step 4: Boyce-Codd Normal Form (BCNF) — Only Keys Determine Attributes

**Learning Objectives**  
By the end of this section, you will be able to:  
- State the BCNF condition.  
- Identify BCNF violations.  
- Decompose a relation into BCNF.

#### Prerequisites  
You should now be able to:  
- Identify superkeys and candidate keys.  
- Recognize functional dependencies.  
- Normalize to 3NF.

#### Motivating Example: The Gate Assignment Conflict

Consider:

**Flights**(FlightNumber, Airline, Gate)  
FDs:  
- FlightNumber → Airline  
- {Airline, Gate} → FlightNumber

Candidate keys: {FlightNumber}, {Airline, Gate}

Now suppose Gate → Airline?  
Then Gate 12 → Delta. But if United uses Gate 12, contradiction.

Gate determines Airline—but Gate is not a key → violates BCNF.

This creates a **logical contradiction**: one gate cannot belong to two airlines unless the dependency is relaxed.

> **Analogy**: A type system prevents assigning a string to an integer field. BCNF prevents weak determinants from reinterpreting data. It ensures **only keys determine attributes**.

But here’s a **critical insight**: BCNF is about **logical consistency**, not just efficiency. In a distributed system, if two services assume different invariants (e.g., "gate determines airline" vs. "flight determines airline"), the system can enter an inconsistent state. BCNF enforces that **determinants are keys**, preventing such conflicts.

#### Formal Definition of BCNF

A relation is in **Boyce-Codd Normal Form (BCNF)** if:  
For every non-trivial functional dependency X → Y, X is a **superkey**.

BCNF is **stronger** than 3NF—it eliminates all non-superkey determinants.

#### Worked Example: Teaching Schedule

Given:

**Teaching**(Course, Instructor, Time)  
FDs:  
- {Instructor, Time} → Course  
- Course → Instructor

Candidate keys:  
- {Instructor, Time} → determines all → superkey  
- {Course, Time} → Course → Instructor → all → superkey

But Course → Instructor: is Course a superkey?  
No—multiple instructors can teach the same course at different times. So Course → Instructor violates BCNF.

Decompose using Course → Instructor:

1. **CourseInstructor**(Course, Instructor) — key: {Course}  
2. **InstructorTime**(Instructor, Time) — key: {Instructor, Time}

Now:  
- In CourseInstructor: Course → Instructor, Course is superkey → OK  
- In InstructorTime: no functional dependencies → trivially satisfies BCNF

But the original FD {Instructor, Time} → Course is **not preserved**. This is a known limitation of BCNF.

> **Try This Yourself**:  
> **Students**(StudentID, Major, Advisor)  
> - StudentID → Major  
> - Major → Advisor  
>  
> Does this violate BCNF?  
> Yes—Major → Advisor, but Major is not a superkey.  
> Decompose:  
> - Students(StudentID, Major)  
> - Majors(Major, Advisor)  
> Now, what if a student changes majors? Does the advisor update automatically?

> **Case Study: University Class Scheduling**  
> **Classes**(ClassID, Room, Instructor)  
> FDs:  
> - Room → Instructor (e.g., lab rooms assigned to specific faculty)  
> - {Instructor, Time} → Room  
>  
> If Room → Instructor but Room is not a key, BCNF is violated.  
> Fix: Decompose into:  
> - RoomAssignments(Room, Instructor)  
> - ClassSchedule(ClassID, Room)  
> Ensures consistency in room assignments.

> **Cross-Domain Insight**:  
> BCNF is like **unique pointers in memory management**. Just as two pointers shouldn’t alias the same memory unless intentional, two attributes shouldn’t determine a third unless one is a key. It prevents **dangling references** in data logic.

> **Pitfall**: BCNF decompositions may **lose functional dependencies** or **fail to preserve joinability**. Always verify that essential queries remain expressible after normalization.