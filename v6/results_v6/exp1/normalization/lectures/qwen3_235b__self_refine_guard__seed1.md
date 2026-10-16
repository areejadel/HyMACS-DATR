By the end of this lecture, you will be able to:  
1. **Recall** the definitions and requirements of 1NF, 2NF, 3NF, and BCNF by identifying functional dependencies, candidate keys, and attribute types (prime vs. non-prime).  
2. **Explain** how insertion, update, and deletion anomalies arise in poorly designed schemas using concrete examples.  
3. **Apply** step-by-step decomposition to normalize a relation into 1NF, 2NF, 3NF, and BCNF, ensuring lossless join and checking for dependency preservation.  
4. **Analyze** a given schema to determine its highest normal form and justify whether further normalization is needed.  
5. **Evaluate** real-world trade-offs between normalized and denormalized designs, balancing data integrity, performance, and maintainability.

---

### Prerequisites

Before proceeding, ensure familiarity with the following foundational concepts:  
- A **relation** is a table with named columns (attributes) and rows (tuples), where each attribute has a domain.  
- A **functional dependency** $X \rightarrow Y$ means that for any two tuples, if they agree on $X$, they must also agree on $Y$.  
- A **candidate key** is a minimal set of attributes that uniquely identifies a tuple. A **superkey** is any superset of a candidate key.  
- A **prime attribute** is an attribute that is part of *any* candidate key; otherwise, it is **non-prime**.

> 🔍 **Quick Check (Remember)**: In the relation *Employee(EID, Name, Dept, Manager)*, suppose $(EID, Dept)$ is a candidate key. Which attributes are prime?  
> *Answer: EID and Dept — both are components of a candidate key. Name and Manager are non-prime.*

> ⚠️ **Common Misconception**: “All keys are primary keys.”  
A **candidate key** is any minimal unique identifier. The **primary key** is one such candidate selected for implementation. Normalization considers *all* candidate keys, not just the primary.

---

### Motivation: Why Schema Design Matters — The Library Paradox

Imagine a library catalog where each book entry includes:
- Title
- Author
- Author’s birthplace
- Genre
- Genre’s recommended age group

Now suppose *The Hobbit* and *The Lord of the Rings* are both written by J.R.R. Tolkien (born in Bloemfontein) and classified as "Fantasy" (recommended for ages 13+).

You enter both books. Two rows. Two entries. But now ask:  
> What happens if you later discover Tolkien was actually born in Birmingham?

You update one row. Did you remember to update the other? What if a third book slips through? Or a script only updates titles matching "Hobbit"?

Now ask a different question:  
> Can you add the genre "Cyberpunk" before any cyberpunk book exists?

No — because there’s no book to anchor the genre fact.  
And when the last cyberpunk book is removed, does the genre vanish?

This isn’t a software flaw. It’s a **structural lie**: the schema claims that *author birthplace* depends on *book*, but it really depends on *author*. It claims *age group* depends on *book*, but it depends on *genre*.

> 🧩 **Try This Yourself**: Sketch a single row for a new author, Ursula K. Le Guin, born in Berkeley, writing a book titled *The Left Hand of Darkness* in the genre "Sci-Fi" (recommended for 16+). Now imagine adding her second book. Which facts repeat? Which could drift?

The database is conflating **three independent entities**: books, authors, and genres. Each has its own identity. Each should be anchored to its own key.

> 💡 **Cross-Domain Analogy**: This is like storing a web page’s content and its CSS styles in the same HTML file. You *can*, but when the design changes, you must edit every page. Better to separate concerns: content in HTML, styling in CSS. Here, facts about authors belong in an *Author* table, not embedded in *Book* entries.

Normalization is the process of **disentangling interwoven truths** so that each fact depends only on what it logically belongs to.

> 📌 **Core Insight**: A schema is healthy when **every non-key attribute is about the key**.  
If "birthplace" is in the *Book* table, is birthplace *about the book*? No — it’s about the author.  
If "age group" is in the *Book* table, is it about the book? No — it’s about the genre.

We now formalize this principle through normal forms — each eliminating a deeper layer of entanglement.

> ⚠️ **Common Misconception**: Normalization is only about reducing redundancy.  
The true goal is **semantic fidelity**: ensuring that dependencies reflect real-world relationships, not accidental co-location.

> 🔍 **Quick Check (Understand)**: In a *Movie*(Title, Director, DirectorBirthYear, Studio, StudioFounded) table, identify two functional dependencies that are not about the key. How might this lead to an insertion anomaly?  
> *Answer: $Director \rightarrow DirectorBirthYear$, $Studio \rightarrow StudioFounded$. You cannot add a new studio without a movie, and a new director without a film.*

---

### 1. First Normal Form (1NF): The Atomic Foundation

#### The Problem: Hidden Data

Suppose you’re building a calendar app. You store meeting attendees in a single field:  
`"Alice, Bob, Charlie"`.

Can you answer:  
> “Which meetings include Bob?”  
> “How many people attended meeting M101?”  
> “Send a reminder to all attendees of meeting M202.”

Not reliably — because the database sees `"Alice, Bob, Charlie"` as **one string**, not three people. It cannot index, search, or count the individuals.

> 🧩 **Try This Yourself**: Write a SQL query to find all meetings with “Bob” in the attendee list. Now write one to count how many meetings Alice attended. What edge cases arise (e.g., “Bobby”, “Robert”)?

The relational model requires **atomic values** — data that cannot be subdivided *within the model*. This is 1NF.

#### Formal Definition

A relation $R$ is in **First Normal Form (1NF)** if:  
1. All attribute values are **atomic** — indivisible within the relational framework.  
2. There are **no repeating groups** (e.g., Item1, Item2, Item3 columns).

> 📌 **Why it matters**: Non-atomic values break the relational contract. The database cannot reason about parts of a value unless those parts are exposed as attributes or rows.

#### Worked Example: Fixing a Multivalued Attribute

**Unnormalized Table**:

| OrderID | Items                     |
|--------|---------------------------|
| O100   | Laptop, Mouse, Charger    |
| O101   | Keyboard                  |

This violates 1NF — *Items* is not atomic.

**Step 1: Identify the repeating group**  
→ The *Items* column contains a multivalued attribute.

**Step 2: Decompose into atomic rows**  
→ Create **OrderItems**(OrderID, Product), with one row per product.

**Normalized Result**:

| OrderID | Product  |
|--------|----------|
| O100   | Laptop   |
| O100   | Mouse    |
| O100   | Charger  |
| O101   | Keyboard |

Now:  
- Each cell holds a single value.  
- Queries like “Which orders include a mouse?” become feasible:  
```sql
SELECT DISTINCT OrderID FROM OrderItems WHERE Product = 'Mouse';
```  
- Referential integrity can be enforced via a foreign key to a *Product* table.

> 💡 **Cross-Domain Analogy**: 1NF is like **pixelating an image**. A JPEG is one file, but to edit a face, you need pixels — the atomic units of the image. Similarly, a comma-separated list is one “blob”; to query individuals, you need atomic rows.

> ⚠️ **Common Misconception**: “1NF means no duplicate rows.”  
Duplicates are disallowed in relations by definition (a set), but this is not part of 1NF. The core requirement is **atomicity**, not uniqueness. However, duplicates often signal design issues and are typically resolved with keys.

> 🔍 **Quick Check (Apply)**: The table *StudentCourses*(StudentID, Courses) stores Courses as “Math, Physics” for one student. How would you restructure this to satisfy 1NF?  
> *Answer: Create a new table StudentCourses(StudentID, Course) with one row per course: (S1, Math), (S1, Physics).*

---

### 2. Second Normal Form (2NF): Full Key Dependence

#### The Problem: Partial Truths

Consider a composite key: $(StudentID, CourseID)$. This key identifies a **grade** — a fact about a student’s performance in a course.

But what about *StudentName*?  
It depends only on *StudentID* — not the full key.

So if the same student takes three courses, their name repeats. Update it in two places but not the third? Now the database contradicts itself.

> 🧩 **Try This Yourself**: In a table with key $(EmpID, ProjectID)$, suppose $EmpID \rightarrow OfficeLocation$. How many rows must you update if the employee moves offices? What if the update fails after two of five rows?

This is a **partial dependency**: a non-prime attribute depending on only part of a candidate key.

2NF eliminates this: **every non-prime attribute must depend on the entire candidate key**.

#### Formal Definition

A relation $R$ is in **Second Normal Form (2NF)** if:  
- $R$ is in 1NF, and  
- Every **non-prime attribute** is **fully functionally dependent** on every **candidate key**.

> 📌 Equivalently: No non-prime attribute depends on a proper subset of any candidate key.

#### Worked Example: University Enrollment

**Enrollment**(StudentID, CourseID, StudentName, Grade)  
- Candidate key: $(StudentID, CourseID)$  
- Functional dependency: $StudentID \rightarrow StudentName$

**Step 1: Identify prime and non-prime attributes**  
- Prime: StudentID, CourseID  
- Non-prime: StudentName, Grade

**Step 2: Check for partial dependencies**  
- $StudentID \rightarrow StudentName$: $StudentID$ is a proper subset of the key → **partial dependency** → violates 2NF.

**Step 3: Decompose to eliminate partial dependency**  
- Extract $StudentID \rightarrow StudentName$ into **Student**(StudentID, StudentName)  
- Retain **Enrollment**(StudentID, CourseID, Grade)

Now:  
- In *Student*, $StudentID$ is the key → full dependence.  
- In *Enrollment*, $Grade$ depends on the full key $(StudentID, CourseID)$ → satisfies 2NF.

**Anomalies eliminated**:  
- Redundancy: StudentName no longer repeats.  
- Update: Change name once in *Student*.  
- Deletion: Dropping a course does not delete student data.

> 💡 **Cross-Domain Analogy**: 2NF is like **separating configuration from logs** in a system. A log entry’s timestamp depends on the event, but the user’s time zone depends only on the user. Store the time zone with the user, not repeated in every log.

> ⚠️ **Limitation**: 2NF only addresses dependencies involving **non-prime attributes**. It does not prevent dependencies between non-key attributes — this is the role of 3NF.

> 🔍 **Quick Check (Analyze)**: In *ProjectAssign*(EmpID, ProjID, EmpName, Hours), with key $(EmpID, ProjID)$ and $EmpID \rightarrow EmpName$, is this in 2NF? If not, how would you decompose it?  
> *Answer: No—$EmpID \rightarrow EmpName$ is a partial dependency. Decompose into Employee(EmpID, EmpName) and ProjectAssign(EmpID, ProjID, Hours).*

---

### 3. Third Normal Form (3NF): Eliminate Transitive Dependencies

#### The Problem: Indirect Control

Suppose:  
- Your employee ID determines your department.  
- Your department determines your office building.  

Then your ID indirectly determines your building — a **transitive dependency**.

If the department moves buildings, you must update every employee in that department. Miss one? Now the database lies.

> 🧩 **Try This Yourself**: In a *Patient*(PatientID, DoctorID, DoctorSpecialty) table, $DoctorID \rightarrow DoctorSpecialty$. How many rows must you update if a doctor changes specialties? What if a new doctor joins but hasn’t been assigned a patient?

3NF breaks such chains: **non-prime attributes must depend directly on the key, not on other non-prime attributes**.

#### Formal Definition

A relation $R$ is in **Third Normal Form (3NF)** if:  
- $R$ is in 2NF, and  
- For every non-trivial functional dependency $X \rightarrow Y$:  
  - $X$ is a **superkey**, or  
  - $Y$ is a **prime attribute**.

> 📌 Intuition: No non-prime attribute should be determined by a non-superkey.

#### Worked Example: Hospital Staff Management

**Doctor**(DoctorID, Department, HeadNurse, NursePhone)  
- Candidate key: $DoctorID$  
- Functional dependencies:  
  - $DoctorID \rightarrow Department$  
  - $Department \rightarrow HeadNurse$  
  - $HeadNurse \rightarrow NursePhone$

This creates a transitive chain:  
$DoctorID \rightarrow Department \rightarrow HeadNurse \rightarrow NursePhone$

**Step 1: Identify 3NF violations**  
- $Department \rightarrow HeadNurse$: $Department$ is not a superkey, $HeadNurse$ is non-prime → violates 3NF.  
- $HeadNurse \rightarrow NursePhone$: same issue.

**Step 2: Decompose**  
1. **NurseContact**(HeadNurse, NursePhone) — $HeadNurse$ is key.  
2. **Department**(Department, HeadNurse) — $Department$ is key.  
3. **Doctor**(DoctorID, Department) — $DoctorID$ is key.

Now:  
- All dependencies are either key → attribute or involve prime attributes.  
- Each fact is stored once.  
- Updates are localized.

All resulting relations are in 3NF.

> 💡 **Cross-Domain Analogy**: 3NF is like **direct addressing in networking**. You don’t route a packet via an intermediate node unless necessary. If $DoctorID$ needs $NursePhone$, it shouldn’t go through $Department$ and $HeadNurse$ — it should reference the nurse directly or via a foreign key.

> ⚠️ **Pitfall**: 3NF allows $X \rightarrow Y$ if $Y$ is prime, even if $X$ is not a superkey. This loophole permits some redundancy — eliminated by BCNF.

> 🔍 **Quick Check (Analyze)**: In *Employee*(EmpID, Dept, Manager, ManagerEmail), with $EmpID \rightarrow Dept$, $Dept \rightarrow Manager$, and $Manager \rightarrow ManagerEmail$, list two FDs that violate 3NF. How would you decompose?  
> *Answer: $Dept \rightarrow Manager$ and $Manager \rightarrow ManagerEmail$ violate 3NF. Decompose into: DeptManager(Dept, Manager), ManagerEmail(Manager, Email), Employee(EmpID, Dept).*

---

### 4. Boyce-Codd Normal Form (BCNF): Functional Determinism

#### The Problem: The Prime Loophole

3NF allows a non-superkey to determine a **prime attribute**. But if that prime attribute is part of another candidate key, trouble returns.

**Example**:  
*Course*(CourseID, Instructor, Textbook)  
- $CourseID \rightarrow Instructor$  
- $Instructor \rightarrow Textbook$  
- Candidate key: $CourseID$

But suppose Dr. Lee *only* uses *Database Systems*. Then $Instructor \rightarrow Textbook$.

Now, can two different textbooks be assigned to Dr. Lee’s course? No — the dependency forces consistency. But $Instructor$ is not a superkey, so this violates **BCNF**, even if it satisfies 3NF.

> 🧩 **Try This Yourself**: Suppose Dr. Lee teaches two courses. You assign *DB1* to one, *DB2* to the other. Does this violate $Instructor \rightarrow Textbook$? What if the system allows it — is the dependency still valid?

BCNF closes this loophole: **every functional dependency must be driven by a superkey**.

#### Formal Definition

A relation $R$ is in **Boyce-Codd Normal Form (BCNF)** if:  
For every non-trivial functional dependency $X \rightarrow Y$, $X$ is a **superkey**.

> 📌 BCNF is stricter than 3NF: every BCNF relation is in 3NF, but not vice versa.

#### Worked Example: Course-Textbook Assignment

**Course**(CourseID, Instructor, Textbook)  
- Functional dependencies:  
  - $CourseID \rightarrow Instructor$  
  - $Instructor \rightarrow Textbook$  
- Candidate key: $CourseID$

**Step 1: Check each FD**  
- $CourseID \rightarrow Instructor$: $CourseID$ is a superkey → valid.  
- $Instructor \rightarrow Textbook$: $Instructor$ is not a superkey → **violates BCNF**.

**Step 2: Decompose using the violating FD**  
- Create **InstructorText**(Instructor, Textbook) — $Instructor$ is key.  
- Retain **CourseInst**(CourseID, Instructor) — $CourseID$ is key.

Now both relations are in BCNF.

> ⚠️ **Critical Limitation**: **BCNF decomposition does not guarantee dependency preservation**.

**Example**: Let $R(A,B,C)$ have FDs:  
- $A \rightarrow B$  
- $B \rightarrow C$  
- $C \rightarrow B$  
Candidate keys: $A$, $C$

Check $B \rightarrow C$: $B$ is not a superkey → violates BCNF.

Decompose into:  
- $R_1(B,C)$  
- $R_2(A,B)$

Now:  
- $B \rightarrow C$ and $C \rightarrow B$ are preserved in $R_1$.  
- $A \rightarrow B$ is preserved in $R_2$.  
- The join on $B$ is lossless.

But $A \rightarrow C$ (implied by transitivity) spans tables and cannot be enforced without a join.

> 💡 **Cross-Domain Analogy**: BCNF is like **type safety in programming**. In 3NF, you can sometimes assign a value through a weak reference. In BCNF, every assignment must go through a complete, verified type path — no implicit conversions.

> 📌 **Practical Implication**: In OLTP systems, **3NF is often preferred** because it allows **dependency-preserving decompositions**. BCNF is used when eliminating all anomalies is critical, even at the cost of complexity.

> 🔍 **Quick Check (Evaluate)**: Why might a data warehouse use 3NF instead of BCNF, even if BCNF is “stronger”?  
> *Answer: 3NF often allows dependency-preserving decompositions, making constraint enforcement easier. BCNF may require expensive joins to maintain consistency, which is impractical in large-scale systems.*

---

### 5. Trade-offs and Denormalization: When Perfection Hurts Performance

#### The Dilemma: Consistency vs. Speed

You’ve normalized perfectly. Every fact is in its place. But now a simple dashboard query requires **five joins** over millions of rows. Response time: 8 seconds.

Users leave.

> 🧩 **Try This Yourself**: You’re building a real-time analytics dashboard showing sales by product, category, region, and salesperson. How many joins would a fully normalized schema require? Could you reduce it? At what cost?

Normalization ensures **correctness**. But **usability** requires **performance**.

Denormalization is the **deliberate relaxation** of normalization to reduce join cost — a trade-off, not a failure.

#### When to Denormalize

| Scenario | Rationale | Example |
|--------|---------|--------|
| **Read-heavy analytics** |