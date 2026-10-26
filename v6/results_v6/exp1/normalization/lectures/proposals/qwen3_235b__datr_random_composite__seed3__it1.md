---

### Prerequisites

Before we proceed, ensure familiarity with the following foundational concepts:  
- A **relation** is a table with named attributes (columns) and tuples (rows).  
- A **functional dependency (FD)** $X \rightarrow Y$ holds if, for any two tuples agreeing on $X$, they must also agree on $Y$.  
- A **candidate key** is a minimal set of attributes that uniquely identifies each tuple.  
- A **superkey** is any superset of a candidate key.  
- A **prime attribute** is part of at least one candidate key; a **non-prime attribute** is not part of any candidate key.

These definitions will be used consistently throughout the lecture.

---

### The Hook: Why Normalization Feels Invisible—Until It Fails

You rarely notice normalization—because when it works, it is invisible. But consider this: your university’s registrar system crashes during course registration because changing one professor’s name inadvertently erases every enrollment in a 300-student lecture. Or a hospital’s patient database duplicates medication records so severely that two nurses see conflicting dosages.

These are not software bugs. They are **schema design failures**—symptoms of unnormalized data. Normalization is not about aesthetics; it is about **preventing silent data corruption**. The normal forms 1NF through BCNF serve as safeguards, each addressing a specific class of structural flaw. We will explore them not as abstract rules, but as responses to real-world failure modes.

---

### 1. First Normal Form (1NF): Enforce Atomicity

**The Problem That Breaks Queries**  
Suppose you are analyzing student performance and encounter the following `Grades` table:

| StudentID | Courses             |
|-----------|---------------------|
| S3        | Math, Physics, Chem |

You wish to count how many students are enrolled in Physics. Can you write `WHERE Courses = 'Physics'`? No—because “Physics” is embedded within a comma-separated string. The query either misses partial matches or falsely includes substrings like “Physical Education.”

This issue violates a core principle of the relational model: **each attribute must hold a single, indivisible value**. When a cell contains multiple facts, you cannot reason about them independently.

**Analogy: The Address Envelope**  
Think of a database row as a postal envelope. Each field—name, street, city—should contain exactly one piece of information. Writing “John; Jane” in the name field confuses the post office about how many people reside there. Similarly, storing “Math, Physics” in a course field obscures the number of courses a student takes. **Atomicity ensures that each field answers exactly one question.**

**Formal Definition**  
A relation is in **First Normal Form (1NF)** if and only if:  
- All attribute values are **atomic** (indivisible).  
- Each row-column intersection contains **exactly one value** from the attribute’s domain.  
- There are **no repeating groups** (e.g., Course1, Course2, Course3 columns).

**Worked Example**  
Consider the relation *Enrollment(StudentID, Courses)* with multi-valued cells:

| StudentID | Courses       |
|-----------|---------------|
| S1        | Math, Physics |
| S2        | Chemistry     |

To achieve 1NF, decompose the multi-valued attribute into individual rows:

| StudentID | Course    |
|-----------|-----------|
| S1        | Math      |
| S1        | Physics   |
| S2        | Chemistry |

Now, every cell contains a single atomic value. The relation satisfies 1NF.

**Misconception Alert**  
❌ “Using JSON or arrays in PostgreSQL means I’m still normalized.”  
✅ No—normalization concerns logical design, not physical storage. If your application treats `['Math','Physics']` as a list and queries depend on its structure, you violate 1NF. Only when data is **flattened into rows** is it truly relational.

**Test Yourself**  
Is the following table in 1NF?

| StudentID | Grade |
|-----------|-------|
| S1        | A     |
| S2        | B, A  |

> ✅ No. The second row contains two grades in one cell. Split into two rows: (S2, B), (S2, A).

---

### 2. Second Normal Form (2NF): Eliminate Partial Dependencies

Having established atomicity in 1NF, we now address redundancy arising from **partial dependencies**.

**A Concrete Example First**  
Consider the table:  
*Registration(StudentID, CourseID, Instructor)*  
with candidate key *(StudentID, CourseID)*.  

Suppose the functional dependency $CourseID \rightarrow Instructor$ holds. Then every student enrolled in “CS101” repeats “Dr. Lee” as instructor. This redundancy becomes dangerous when Dr. Lee changes her name: you must update every row containing CS101. Miss one, and your data becomes inconsistent.

This occurs because a non-key attribute (*Instructor*) depends on only a **subset** of the composite key.

**Intuition: What Is a Partial Dependency?**  
Imagine a key is a full name: first and last. If an attribute depends only on the last name, it is not fully dependent on the entire key. This is a **partial dependency**, and it introduces unnecessary redundancy.

**Prerequisite Check**  
2NF applies only if:  
- The relation is already in **1NF**, and  
- It has a **composite candidate key**.  
If the candidate key consists of a single attribute, 2NF is automatically satisfied.

**Analogy: The Library Checkout Receipt**  
A receipt lists:  
- Patron ID  
- Book ID  
- Book Title  
- Due Date  

The key is (Patron ID, Book ID). But *Book Title* depends only on *Book ID*. If the library later changes the book’s title, it must edit every past receipt—an absurd requirement. Instead, book details should be stored once, in a separate table. **Partial dependencies couple lifecycle events that should be independent.**

**Formal Definition**  
A relation is in **Second Normal Form (2NF)** if and only if:  
- It is in 1NF, and  
- Every **non-prime attribute** is **fully functionally dependent** on every candidate key.  

That is, no non-prime attribute may depend on a proper