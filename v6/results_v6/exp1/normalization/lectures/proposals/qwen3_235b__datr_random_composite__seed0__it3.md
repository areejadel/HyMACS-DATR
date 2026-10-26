---

### Step 1: First Normal Form (1NF) — Atomic Values and No Repeating Groups

**Learning Objectives**:  
By the end of this section, you will be able to:  
1. **Define** 1NF using precise conditions.  
2. **Identify** violations of atomicity and repeating groups in a table.  
3. **Transform** a non-1NF table into 1NF by row decomposition.

#### Prerequisites  
Before we begin, ensure you understand:  
- What a **relation (table)** is in databases.  
- The meaning of **attribute (column)** and **tuple (row)**.  
- That databases perform **exact matches** when querying.

#### Intuition: Why Should One Cell Hold Only One Thing?

Imagine a university registration system where a student’s courses are stored as a comma-separated list:  

| StudentID | StudentName | Course           | Instructor | CourseLevel |
|-----------|-------------|------------------|------------|-------------|
| S001      | Alice       | CS101, CS102     | Dr. Lee    | Intro       |

Now, suppose we want to answer:  
*“Which students are enrolled in CS101?”*  

We might write:  
```sql
SELECT StudentName FROM Enrollments WHERE Course = 'CS101';
```

But this returns **no rows**, because the actual value is `"CS101, CS102"` — not an exact match. We’d have to use `LIKE '%CS101%'`, which risks false positives (e.g., matching `CS1010`). Worse, if spacing varies (`"CS101,CS102"` vs `"CS101, CS102"`), the system behaves unpredictably.

> **Key Insight**: Databases rely on **exact equality** for indexing, constraints, and joins. If a value isn’t atomic, these mechanisms break.

> **Analogy**: Think of a database like a postal sorting machine. It reads one address line at a time. If the "Name" field says “Alice, Bob, Charlie,” the machine doesn’t know whether to deliver to all three or treat it as a single recipient. **Atomicity ensures each field holds exactly one deliverable unit.**

#### Formal Definition of 1NF

A relation is in **First Normal Form (1NF)** if and only if:  
- Every attribute contains **atomic (indivisible)** values.  
- There are **no repeating groups** (e.g., multiple values in one cell).

> **Note**: 1NF does **not require** a primary key by definition, but in practice, we assign one to uniquely identify rows. Without it, duplicates can’t be distinguished.

#### Worked Example: Achieving 1NF

**Before (violates 1NF)**:

| StudentID | StudentName | Course           | Instructor | CourseLevel |
|-----------|-------------|------------------|------------|-------------|
| S001      | Alice       | CS101, CS102     | Dr. Lee    | Intro       |

We see:
- `Course` contains two values → **not atomic**.
- This is a **repeating group**.

**Step-by-step fix**:  
1. Split the multivalued `Course` into separate rows.  
2. Repeat all other attributes for each new row (since they apply to the same student).  

**After (in 1NF)**:

| StudentID | StudentName | Course  | Instructor | CourseLevel |
|-----------|-------------|---------|------------|-------------|
| S001      | Alice       | CS101   | Dr. Lee    | Intro       |
| S001      | Alice       | CS102   | Dr. Lee    | Intro       |

Now:
- Every cell has a single value → **atomic**.
- No repeating groups → **1NF achieved**.
- Candidate key: $ \{\text{StudentID}, \text{Course}\} $ ensures uniqueness.

> **Misconception Alert**:  
> “Atomic” doesn’t mean “single word” — it means **indivisible for the application**. For example, a full name like “Alice Johnson” is atomic *if* the system never needs to query by first name. But if we must search by first name, we should split it.

#### Quick Check: Test Yourself

Suppose `Instructor` stores multiple names as `"Dr. Lee, Dr. Smith"`.  
- Does this violate 1NF?  
- If yes, how would you fix it?

**Answer**:  
Yes — the value is not atomic. To fix:  
- Option 1: Split into multiple rows (if multiple instructors co-teach).  
- Option 2: Create a separate table `CourseInstructors(Course, Instructor)`.

---

### Step 2: Second Normal Form (2NF) — Eliminate Partial Dependencies

**Learning Objectives**:  
By the end of this section, you will be able to:  
1. **Recall** the definition of 2NF.  
2. **Identify** partial dependencies in a relation.  
3. **Decompose** a table to achieve 2NF using functional dependencies.

#### Prerequisites  
You should now be able to:  
- Identify 1NF violations.  
- Understand **functional dependencies** (e.g., `StudentID → StudentName`).  
- Recognize **candidate keys** and **prime attributes** (those in any key).

#### Intuition: Why Store Facts Only Once?

Let’s extend our 1NF table:

| StudentID | StudentName | Course  | Instructor   | CourseLevel |
|-----------|-------------|---------|--------------|-------------|
| S001      | Alice       | CS101   | Dr. Lee      | Intro       |
| S001      | Alice       | CS102   | Dr. Smith    | Advanced    |
| S002      | Bob         | CS101   | Dr. Lee      | Intro       |

We observe:
- `StudentID → StudentName`  
- `Course → Instructor, CourseLevel`  
- Candidate key: $ \{\text{StudentID}, \text{Course}\} $

But notice:
- `StudentName` depends only on `StudentID` — a **subset** of the key → **partial dependency**.  
- Similarly, `Instructor` and `CourseLevel` depend only on `Course`.

So when Bob enrolls in CS101, we re-record:
- Bob’s name (already known),
- Dr. Lee teaches CS101 (already known),
- CS101 is Intro (already known).

We’re **repeating facts** just to record an enrollment.

> **Consequence**: This leads to **anomalies**:
> - **Update anomaly**: Change Dr. Lee to Dr. Patel? Must update every CS101 row — miss one → inconsistency.  
> - **Insert anomaly**: Add a new course with no students? Can’t — no `StudentID` to insert.  
> - **Delete anomaly**: Remove last student in CS101? Lose course info.

> **Analogy**: Imagine a library catalog that lists “Book Title” and “Author” but also includes “Author’s Birthplace” in every entry for that author. Every time you add a book by Zadie Smith, you re-enter London. That’s inefficient. Worse, if one entry says “London” and another “Cambridge,” which do you trust? 2NF says: store the author’s details once, where they belong.

#### Formal Definition of 2NF

A relation is in **Second Normal Form (2NF)** if:  
- It is in **1NF**, and  
- Every **non-prime attribute** (not part of any candidate key) is **fully functionally dependent** on the **entire** candidate key.

#### Worked Example: Achieving 2NF via Decomposition

**Step 1**: Identify partial dependencies.  
From the `Enrollments` table:
- $ \text{StudentID} \rightarrow \text{StudentName} $ → partial (depends on subset of key)  
- $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $ → partial

**Step 2**: Extract each dependency into its own table.

**Decompose into**:
1. **Students**(StudentID, StudentName)  
   Key: $ \{\text{StudentID}\} $  
2. **Courses**(Course, Instructor, CourseLevel)  
   Key: $ \{\text{Course}\} $  
3. **Enrollments**(StudentID, Course)  
   Key: $ \{\text{StudentID}, \text{Course}\} $

Now:
- `StudentName` depends fully on its key.  
- `Instructor` and `CourseLevel` depend fully on `Course`.  
- `Enrollments` stores only the relationship — **no redundancy**.

> **Note**: This decomposition **preserves information** and **eliminates anomalies**.

#### Quick Check: Test Yourself

Suppose we add `Department` to `Courses`, with $ \text{Course} \rightarrow \text{Department} $.  
Is `Courses` in 2NF?

**Answer**:  
Yes. `Department` depends on the full key `Course`. No partial dependency exists.

---

### Step 3: Third Normal Form (3NF) — Eliminate Transitive Dependencies

**Learning Objectives**:  
By the end of this section, you will be able to:  
1. **Define** 3NF using functional dependencies.  
2. **Recognize** transitive dependencies in a table.  
3. **Decompose** a relation to achieve 3NF.

#### Prerequisites  
You should now be able to:  
- Identify partial dependencies.  
- Understand **non-prime attributes** and **functional dependency chains**.

#### Intuition: Don’t Store What You Can Look Up

In the 1990s, a university stored instructor office locations in the `Courses` table:

| Course  | Instructor | Office     |
|---------|------------|------------|
| CS101   | Dr. Lee    | Room 305   |
| CS102   | Dr. Smith  | Room 412   |
| CS103   | Dr. Lee    | Room 305   |

When Dr. Lee moved to Room 412, 47 course records had to be updated — but one was missed. A visiting scholar waited outside an empty office.

Why? The **office** is a fact about **Dr. Lee**, not about CS101. But we’re storing it in every course they teach.

> **Chain of dependency**:  
> $ \text{Course} \rightarrow \text{Instructor} \rightarrow \text{Office} $  
> So `Office` depends on `Course` *through* `Instructor* → **transitive dependency**.

> **Analogy**: Think of transitive dependencies as a game of telephone. The course “says” the instructor’s name. The instructor “says” the office. But if the instructor’s office is stored in the course record, it’s like writing down what the instructor *might* say, without checking. When the instructor moves, the message is out of date.

#### Formal Definition of 3NF

A relation is in **Third Normal Form (3NF)** if:  
- It is in **2NF**, and  
- No **non-prime attribute** is **transitively dependent** on any candidate key.  
  That is, if $ K \rightarrow A $ and $ A \rightarrow B $, then $ B $ should not depend on $ K $ through $ A $, unless:
  - $ A $ is a **superkey**, or  
  - $ B $ is **prime** (part of a candidate key).

#### Worked Example: Achieving 3NF

From:
- **Courses**(Course, Instructor, Office)  
  FDs: $ \text{Course} \rightarrow \text{Instructor} $, $ \text{Instructor} \rightarrow \text{Office} $

We see:
- `Office` is transitively dependent on `Course` via `Instructor`.  
- `Instructor` is not a superkey.  
- `Office` is non-prime.

**Decompose using the transitive dependency** $ \text{Instructor} \rightarrow \text{Office} $:

1. **Courses**(Course, Instructor)  
   Key: $ \{\text{Course}\} $  
2. **Instructors**(Instructor, Office)  
   Key: $ \{\text{Instructor}\} $

Now:
- `Office` depends directly on `Instructor`.  
- One update changes the office for all courses.

> **Misconception Alert**:  
> “3NF is only about keys” — No. 3NF allows a non-key attribute to determine another **only if** it’s a superkey or the result is prime. The rule prevents **hidden dependencies**.

#### Quick Check: Test Yourself

In `Students`(StudentID, Advisor, Dept, DeptPhone), with:  
- $ \text{StudentID} \rightarrow \text{Advisor} $  
- $ \text{Advisor} \rightarrow \text{Dept} $  
- $ \text{Dept} \rightarrow \text{DeptPhone} $  

What transitive dependencies exist? How would you fix them?

**Answer**:  
- $ \text{StudentID} \rightarrow \text{Advisor} \rightarrow \text{Dept} $  
- $ \text{StudentID} \rightarrow \text{Dept} \rightarrow \text{DeptPhone} $  

Decompose into:  
- `Students`(StudentID, Advisor)  
- `Advisors`(Advisor, Dept)  
- `Departments`(Dept, DeptPhone)

---

### Step 4: Boyce-Codd Normal Form (BCNF) — Strengthening the Key

**Learning Objectives**:  
By the end of this section, you will be able to:  
1. **State** the BCNF condition.  
2. **Detect** violations where a non-superkey determines attributes.  
3. **Decompose** a schema to satisfy BCNF.

#### Prerequisites  
You should now be able to:  
- Identify functional dependencies.  
- Distinguish **superkeys** from **candidate keys**.  
- Recognize when 3NF allows undesirable dependencies.

#### Intuition: Only Keys Should Make Promises

Consider a hospital rotation system:

| Course     | Instructor | Time   |
|------------|------------|--------|
| MED501     | Dr. Lee    | M9am   |
| MED502     | Dr. Patel  | T9am   |

With FDs:  
- $ \text{Instructor}, \text{Time} \rightarrow \text{Course} $ (One course per instructor per time)  
- $ \text{Course} \rightarrow \text{Instructor} $ (Each course has one instructor)

Candidate keys:  
- $ \{\text{Instructor}, \text{Time}\} $  
- $ \{\text{Course}, \text{Time}\} $ (since `Course` → `Instructor`)

Now, $ \text{Course} \rightarrow \text{Instructor} $.  
Is this allowed in 3NF? Yes — because `Course` is prime (part of a key).

But what if we insert:
- (MED501, Dr. Lee, M9am)
- (MED501, Dr. Patel, T9am)

Now MED501 has two instructors — violating $ \text{Course} \rightarrow \text{Instructor} $.

The issue? `Course` determines `Instructor`, but `Course` is **not a superkey** — so multiple rows can disagree.

> **Analogy**: BCNF is like a constitution: every functional dependency must be backed by sovereign authority. If a non-sovereign (non-superkey) makes a decree, the schema is invalid. Here, `Course` is making a binding claim about `Instructor`, but it doesn’t have full authority (it’s not a superkey). The constitution is broken.

#### Formal Definition of BCNF

A relation is in **Boyce-Codd Normal Form (BCNF)** if and only if:  
For every non-trivial functional dependency $ X \rightarrow Y $, $ X $ is a **superkey**.

That is, **only superkeys can determine other attributes**.

#### Worked Example: Achieving BCNF

From:
- **Teaching**(Course, Instructor, Time)  
  FDs: $ \text{Instructor}, \text{Time} \rightarrow \text{Course} $, $ \text{Course} \rightarrow \text{Instructor} $

Check each FD:
- $ \text{Instructor}, \text{Time} \rightarrow \text{Course} $: Is $ \{\text{Instructor}, \text{Time}\} $ a superkey? Yes → OK.  
- $ \text{Course} \rightarrow \text{Instructor} $: Is `Course` a superkey? No → **violates BCNF**.

**Decompose using the violating FD**: $ \text{Course} \rightarrow \text{Instructor} $

1. **CourseInstructor**(Course, Instructor)  
   Key: $ \{\text{Course}\} $ → now `Course` is a key.  
2. **InstructorTime**(Instructor, Time)  
   Key: $ \{\text{Instructor}, \text{Time}\} $

Now:
- The FD $ \text{Course} \rightarrow \text{Instructor} $ is safe — `Course` is a superkey.  
- Scheduling is tracked separately.

> **Misconception Alert**:  
> “BCNF is always better than 3NF” — Not necessarily. BCNF eliminates more anomalies, but decomposition may lose **dependency preservation**. Always check if your queries still work.

#### Quick Check: Test Yourself

Is `Students`(StudentID, Major, Advisor) with:  
- $ \text{StudentID} \rightarrow \text{Major} $  
- $ \text{Major} \rightarrow \text{Advisor} $  
in BCNF?

**Answer**:  
No. $ \text{Major} \rightarrow \text{Advisor} $, but `Major` is not a superkey.  
Decompose into:  
- `Students`(StudentID, Major)  
- `Majors`(Major, Advisor)

---

### Step 5: Trade-Offs — When to Normalize, When to Pause

**Learning Objectives**:  
By the end of this section, you will be able to:  
1. **Compare** the benefits and costs of normalization.  
2. **Evaluate** when to stop normalizing based on use case.  
3. **Justify** controlled denormalization in specific scenarios.

#### Intuition: Normalization Is a Design Choice

We’ve seen how normalization prevents anomalies. But each decomposition adds **joins**.

Querying “Which students are in CS101, and who teaches it?” now requires joining `Enrollments`, `Students`, `Courses`, and `Instructors`.

In high-throughput systems — say, a live registration portal — joins can slow responses.

> **Trade-off**:  
> - **Normalized**: Safe, consistent, easy to update.  
> - **Denormalized**: Fast to read, but risks inconsistency.

> **Analogy**: Think of normalization like normalizing scientific measurements: you break down complex phenomena into independent variables. But in real-time weather prediction, you might use a simplified model that trades precision for speed. Similarly, in databases, you choose your abstraction level based on the task.

#### Real-World Practice

- **Transactional systems** (e.g., registration, banking):  
  Normalize to **BCNF or 3NF** — updates are frequent; consistency is critical.

- **Data warehouses / analytics**:  
  Often **denormalize** (e.g., star schemas) for reporting speed. Redundancy is acceptable if consistency is managed (e.g., via ETL processes).

> **Rule of Thumb**:  
> **Normalize by default.**  
> Denormalize only when performance is proven to be a bottleneck — and document the redundancy clearly.

#### Quick Check: Test Yourself

In a read-heavy analytics database tracking course enrollments over time, would you recommend full BCNF or controlled denormalization?

**Answer**:  
Controlled denormalization. Analytics prioritize fast reads over frequent updates. Redundancy can be acceptable if consistency is managed (e.g., via ETL processes). But for transactional systems (e.g., registration), BCNF is preferred.