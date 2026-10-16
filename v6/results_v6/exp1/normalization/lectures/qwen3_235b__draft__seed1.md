By the end of this lecture, you will be able to:  
1. **Recall** the definitions and requirements of 1NF, 2NF, 3NF, and BCNF using precise criteria based on functional dependencies and keys.  
2. **Explain** the practical motivations for normalization by identifying insertion, update, and deletion anomalies in unnormalized schemas.  
3. **Apply** decomposition procedures to transform a relation into higher normal forms (up to BCNF), ensuring lossless join and checking for dependency preservation.  
4. **Analyze** a given database schema to determine its highest normal form and justify whether further decomposition is needed.  
5. **Evaluate** trade-offs between normalization and denormalization in real-world database design, considering both data integrity and performance.

---

### Prerequisites

Before proceeding, ensure familiarity with the following concepts:  
- The relational model: relations (tables), attributes (columns), and tuples (rows).  
- Functional dependencies (FDs): for sets of attributes $X$ and $Y$, the notation $X \rightarrow Y$ means that the values of $X$ uniquely determine the values of $Y$.  
- Candidate keys: minimal sets of attributes that uniquely identify a tuple.  
- Superkeys: sets of attributes that contain a candidate key.  
- Prime attributes: attributes that are part of any candidate key. Non-prime attributes are those not in any key.

> 🔍 **Quick Check (Remember)**: In the relation *Employee(EID, Name, Dept, Manager)*, suppose *(EID, Dept)* is a candidate key. Which attributes are prime?  
> *Answer: EID and Dept, since both belong to the candidate key.*

Now, let’s confront a puzzle that has quietly broken databases for decades.

---

### Motivation: The Silent Data Time Bomb

Imagine you're maintaining a university enrollment system. You add a new course—“Quantum Computing”—and assign Dr. Alvarez as instructor. But no student has enrolled yet. You try to insert the course into the database…

**And the system refuses.**

Why? Because the only table available is *Enrollment*, which requires a *StudentID*. No student, no record. The course doesn’t exist in the database.

This isn’t a bug. It’s a design flaw—**an insertion anomaly**, born from treating multiple independent facts as if they were one.

The schema forces you to bundle:
- Who is enrolled in what course
- Which course has which title
- Who teaches which course

…into a single table. So when one fact is missing (a student), another fact (a course exists) cannot be recorded.

> 💡 **Try this yourself**: Sketch a table that stores all three facts above. Now, try to insert a course with no students. What breaks?

This is not just inconvenient—it’s dangerous. The same table that tracks grades also stores instructor assignments. So if Bob drops Databases, does the system really need to forget that Dr. Smith teaches it?

Normalization is the disciplined way to **separate independent facts** so each can be managed independently. It’s not about neatness—it’s about **logical independence**.

> 🧩 **Core Insight**: A well-normalized schema ensures that each *fact* lives in exactly one place, determined by what *kind* of thing it describes. This is like organizing a library: you don’t store the author’s biography inside every copy of their book.

We now formalize this idea through normal forms.

---

### 1. First Normal Form (1NF): The Atomic Foundation

#### Objective: Recall and apply 1NF criteria.

A relation is in **First Normal Form (1NF)** if and only if:
1. All attribute values are **atomic** (indivisible).
2. There are **no repeating groups**.

> 📌 **Why it matters**: The relational model treats each cell as a single data point. If a cell contains a list, you lose the ability to query, index, or constrain individual elements.

#### Example: Violation of 1NF

| StudentID | Name   | Courses               |
|-----------|--------|------------------------|
| S01       | Alice  | {CS101, CS202}         |
| S02       | Bob    | {CS101}                |

Here, *Courses* is a set—multiple values in one cell. You cannot write a simple `WHERE Courses = 'CS101'` to find all students in CS101. The database sees the entire set as one value.

#### Fix: One fact per row

Decompose so each enrollment is a separate tuple:

| StudentID | Name   | Course  |
|-----------|--------|--------|
| S01       | Alice  | CS101  |
| S01       | Alice  | CS202  |
| S02       | Bob    | CS101  |

Now, every cell is atomic. Queries work predictably.

> 🔍 **Quick Check (Apply)**: Is the following table in 1NF?  
| OrderID | Items          |  
|--------|----------------|  
| O1     | Laptop, Mouse  |  

*Answer: No. "Items" contains multiple values. To fix: split into (O1, Laptop) and (O1, Mouse).*

> ⚠️ **Common Misconception**: “1NF means no duplicate rows.”  
Clarification: 1NF is about **atomicity**, not uniqueness. While duplicates should be avoided (relations are sets), they don’t violate 1NF. But if your cell says “Java, Python”, you’re not even in the relational game.

> 💡 **Analogy**: 1NF is like requiring each sentence in an essay to express exactly one idea. If a sentence says “Alice studies databases and Bob likes algorithms,” it’s hard to search for who studies databases. Split it: one sentence per fact.

Now that each cell holds one value, we ask: **Does each fact depend on the whole key?**

---

### 2. Second Normal Form (2NF): Full Key Dependence

#### Objective: Eliminate partial dependencies.

A relation is in **Second Normal Form (2NF)** if:
- It is in 1NF, and  
- Every **non-prime attribute** is **fully functionally dependent** on every **candidate key**.

> 📌 **Intuition**: If your key is composite, no non-key attribute should depend on just part of it.

#### Example: Partial Dependency

Consider:  
**Enrollment**(StudentID, CourseID, StudentName, Grade)  
- Candidate key: *(StudentID, CourseID)*  
- FD: StudentID → StudentName

*StudentName* depends only on *StudentID*—a subset of the key. This is a **partial dependency**.

So every time Alice enrolls in a course, her name is repeated. If she changes her name, you must update every row. Miss one? Now your data lies.

> 💡 **Analogy**: Think of a composite key as a two-part password. If you can guess the user’s name using only the first half of the password, the system is leaky. Similarly, if *StudentName* is revealed by *StudentID* alone, the schema leaks redundancy.

#### Step-by-Step Decomposition

1. **Find partial dependencies**:  
   - StudentID → StudentName (uses only part of key)

2. **Extract**: Create a new relation with the determinant and dependent.  
   - **Student**(StudentID, StudentName)  
   - **Enrollment**(StudentID, CourseID, Grade)

Now:
- In *Student*, StudentID is the key → full dependence.
- In *Enrollment*, Grade depends on (StudentID, CourseID) → full dependence.

Both are in 2NF.

> ✅ **Worked Example**:  
**Registration**(Term, StudentID, CourseID, StudentEmail)  
- Key: (Term, StudentID, CourseID)  
- FD: StudentID → StudentEmail → violates 2NF  
Fix:  
- **Student**(StudentID, StudentEmail)  
- **Registration**(Term, StudentID, CourseID)

> 🔍 **Try this yourself**: In *Project*(EmpID, ProjectID, EmpName, Hours), key is (EmpID, ProjectID), and EmpID → EmpName. Is this in 2NF? If not, decompose it.

> ⚠️ **Clarification**: 2NF only handles partial dependencies. It doesn’t stop *EmpName → OfficeLocation* if both are in the same table. That’s the next problem.

---

### 3. Third Normal Form (3NF): Cut the Middlemen

#### Objective: Eliminate transitive dependencies.

A relation is in **Third Normal Form (3NF)** if:
- It is in 2NF, and  
- For every non-trivial FD $X \rightarrow Y$:  
  - $X$ is a **superkey**, or  
  - $Y$ is a **prime attribute**.

> 📌 **Intuition**: No non-key attribute should depend on another non-key attribute. Avoid chains like: Key → A → B.

#### Example: Transitive Dependency

**Employee**(EmpID, Dept, Manager, ManagerPhone)  
- Key: EmpID  
- FDs:  
  - EmpID → Dept  
  - Dept → Manager  
  - Manager → ManagerPhone

So: EmpID → Dept → Manager → ManagerPhone

This is a **transitive dependency**. ManagerPhone is two steps away from the key.

Consequences:
- If two departments share a manager, ManagerPhone is duplicated.
- If the manager changes phone, update all rows where they appear.
- If the last employee in a department quits, you lose the manager’s phone.

> 💡 **Analogy**: This is like routing mail through a chain of assistants. To reach the CEO, you give the letter to an intern, who gives it to a manager, who gives it to the director. Each hop risks delay or error. In 3NF, you go straight to the source.

#### Decomposition to 3NF

Break the chain:
1. **Manager**(Manager, ManagerPhone)  
2. **Department**(Dept, Manager)  
3. **Employee**(EmpID, Dept)

Now:
- Each FD is either key → attribute or prime attribute → attribute.
- ManagerPhone stored once.
- Updates localized.

All relations in 3NF.

> ✅ **Worked Example**:  
**Student**(SID, Advisor, AdvisorOffice, GPA)  
- SID → Advisor, Advisor → AdvisorOffice  
- Key: SID

Transitive dependency: SID → Advisor → AdvisorOffice  
Fix:  
- **Advisor**(Advisor, AdvisorOffice)  
- **Student**(SID, Advisor, GPA)

> 🔍 **Quick Check (Analyze)**: In *Book*(ISBN, Author, Publisher, PubCity), with ISBN → Author, Author → Publisher, Publisher → PubCity, identify all transitive dependencies. How many tables do you need to reach 3NF?

> ⚠️ **Clarification**: 3NF allows $Y$ to be prime even if $X$ isn’t a superkey. This exception is why 3NF isn’t always sufficient—leading us to BCNF.

---

### 4. Boyce-Codd Normal Form (BCNF): The Gold Standard

#### Objective: Achieve functional dependency purity.

A relation is in **BCNF** if:
- For every non-trivial FD $X \rightarrow Y$, $X$ is a **superkey**.

> 📌 **Key difference from 3NF**: BCNF removes the “or $Y$ is prime” loophole. *Every* determinant must be a superkey.

#### Why BCNF? A Subtle Flaw in 3NF

Consider:  
**Course**(CourseID, Instructor, Textbook)  
- Each course has one instructor.  
- Each instructor teaches only one textbook per course.  
- But: an instructor may use the same textbook in multiple courses.

FDs:
- CourseID → Instructor  
- (Instructor, Textbook) → CourseID  
- No other FDs.

Candidate keys:  
- {CourseID}, {Instructor, Textbook} → both are candidate keys.

Now suppose:  
- C101 → Dr. Smith  
- Dr. Smith → uses “DB Fundamentals” in C101  

But can Dr. Smith use “DB Fundamentals” in C102? Not if (Instructor, Textbook) → CourseID is enforced—because that FD says this pair determines *one* course.

So the FD (Instructor, Textbook) → CourseID implies that a given instructor can use a textbook in only one course.

But this FD is not on a superkey? Wait—(Instructor, Textbook) *is* a candidate key. So we’re in BCNF?

Yes. But suppose we only knew CourseID → Instructor and nothing else. Then we might miss that (Instructor, Textbook) is a key.

> 💡 **Cross-Domain Insight**: This is like a cryptographic hash: if two inputs produce the same output, they must be the same input. Here, if two (Instructor, Textbook) pairs point to the same course, they must be identical. BCNF ensures that *only* keys can determine data—no hidden functional power.

But here’s the catch: **Some 3NF schemas cannot be decomposed into BCNF without losing dependencies**.

> 🔍 **Try this yourself**: Given a relation *R*(A, B, C) with FDs: A → B, B → C.  
- Candidate key: A  
- Is it in 3NF? (B → C: B is not a superkey, C is not prime → violates 3NF)  
- So decompose to 3NF: *R1*(A,B), *R2*(B,C)  
- Now check BCNF: In *R2*, B → C, and B is key → OK. In *R1*, A → B, A is key → OK. So we reached BCNF.

But suppose FDs were: A → B, B → C, C → B.  
- Keys: A, C  
- Now B → C: B is not a superkey (B ≠ A or C), so violates BCNF.  
- Can we decompose? Try: *R1*(B,C), *R2*(A,B)  
- But now A → B is split: B is in both, but A only in *R2*. Can we check B → C? Yes. But C → B? Also in *R1*.  
- But is A → B preserved? Only if the join reconstructs it. It does—but **dependency preservation is not guaranteed in BCNF decomposition**.

> 📌 **Non-obvious framing**: BCNF is about **functional determinism**—only keys should have the power to determine other attributes. 3NF is more permissive, allowing prime attributes to break the rule. BCNF is stricter, but sometimes too strict for practical decomposition.

---

### 5. Trade-offs: When to Stop Normalizing

Normalization eliminates anomalies—but can hurt performance.

Consider a reporting query:  
“List all students, their courses, instructors, and grades.”

In a fully normalized schema, this requires joining 4 tables: Student, Course, Instructor, Enrollment.

Each join costs time.

> 💡 **Analogy**: Normalization is like storing ingredients in separate labeled bins. Cooking is precise, but slower. Denormalization is pre-mixing common ingredient blends—faster for frequent recipes, but risky if one ingredient changes.

**When to denormalize**:
- Read-heavy workloads (e.g., analytics)
- Stable data (e.g., product catalog)
- Joins are performance bottlenecks

**When to normalize**:
- High update frequency
- Data integrity is critical (e.g., banking)
- Multiple independent facts evolve separately

> 🔍 **Evaluate**: A social media app stores posts and user names. Posts are read 10,000x more than they’re written. Would you normalize User and Post into separate tables? Why or why not?

> 📌 **Best Practice**: Normalize first to understand dependencies. Then **selectively denormalize**, documenting which anomalies you accept and how you mitigate them (e.g., application-level checks, triggers).

---

### Summary: The Normalization Ladder

| Normal Form | Rule | Prevents |
|------------|------|--------|
| 1NF | Atomic values, no repeating groups | Unstructured cells |
| 2NF | No partial dependencies | Redundant non-key data on composite keys |
| 3NF | No transitive dependencies (unless Y is prime) | Indirect redundancy |
| BCNF | Every determinant is a superkey | Subtle FD anomalies |

Each step answers: **“What determines what, and who’s allowed to decide?”**

Normalization isn’t a checklist—it’s a way of thinking: **What fact belongs where, based on what it depends on?**

Master this, and you don’t just design databases. You design truth.