---

### Learning Objectives

By the end of this lecture, you will be able to:  
1. **Define** each normal form (1NF, 2NF, 3NF, BCNF) using precise, measurable criteria. *(Remember)*  
2. **Explain**, using examples, how violations of normal forms lead to insertion, deletion, and update anomalies. *(Understand)*  
3. **Apply** normalization rules to decompose a relation into higher normal forms step by step. *(Apply)*  
4. **Analyze** a given schema for functional dependencies and determine its highest normal form. *(Analyze)*  
5. **Design** a normalized database schema from a real-world scenario, justifying each decomposition. *(Create)*

---

### Prerequisites

Before we proceed, ensure familiarity with the following foundational concepts:  
- A **relation** is a table with named attributes (columns) and tuples (rows).  
- A **functional dependency (FD)** $X \rightarrow Y$ holds if, for any two tuples agreeing on $X$, they must also agree on $Y$.  
- A **candidate key** is a minimal set of attributes that uniquely identifies each tuple.  
- A **superkey** is any superset of a candidate key.  
- A **prime attribute** is part of at least one candidate key; a **non-prime attribute** is not part of any candidate key.

These definitions will be used consistently throughout the lecture.

> 🔍 **Formative Check: Prerequisites**  
> Consider the relation *Enrollments(StudentID, CourseID, Grade)*.  
> - Is *(StudentID, CourseID)* a candidate key? Why or why not?  
> - If *CourseID → Instructor*, is *Instructor* a prime or non-prime attribute?  
>   
> *(Answers: Yes, assuming one grade per student-course pair. Non-prime, unless Instructor is part of a candidate key.)*

---

### The Hook: Why Normalization Feels Invisible—Until It Fails

You rarely notice normalization—because when it works, it is invisible. But consider this: your university’s registrar system crashes during course registration because changing one professor’s name inadvertently erases every enrollment in a 300-student lecture. Or a hospital’s patient database duplicates medication records so severely that two nurses see conflicting dosages.

These are not software bugs. They are **schema design failures**—symptoms of unnormalized data. Normalization is not about aesthetics; it is about **preventing silent data corruption**. The normal forms 1NF through BCNF serve as safeguards, each addressing a specific class of structural flaw. We will explore them not as abstract rules, but as responses to real-world failure modes.

Normalization has tangible impacts across industries:
- In **healthcare**, violating 1NF by storing comma-separated diagnoses in a single field prevents accurate tracking of disease prevalence and interferes with automated alerts for drug interactions [1].
- In **e-commerce**, partial dependencies (violating 2NF) cause product price updates to fail across thousands of order records, leading to revenue loss or customer disputes.
- In **banking**, transitive dependencies (violating 3NF) can result in interest rates being inconsistently applied when branch locations are reclassified, triggering regulatory scrutiny.

These are not hypotheticals. In 2012, Knight Capital Group lost $440 million in 45 minutes due to a software deployment that interacted with poorly normalized trading tables—where outdated schema constraints allowed invalid state transitions [2]. While the root cause was operational, the impact was magnified by data redundancy and update anomalies inherent in unnormalized designs.

But here’s a thought experiment: **What if your database could pass a Turing test for consistency?** That is, no matter how many updates, inserts, or deletes occur, a human auditor could never detect contradictions or missing data. Normalization brings us closer to that ideal—not by magic, but by eliminating the structural blind spots where data goes to die.

Let’s begin with the first requirement: atomicity.

---

### 1. First Normal Form (1NF): Enforce Atomicity

**A Concrete Example First**  
Let’s start with a real table from a school’s legacy system:

| StudentID | Courses             |
|-----------|---------------------|
| S3        | Math, Physics, Chem |

We want to answer: *How many students are taking Physics?*  
We might try:
```sql
SELECT COUNT(*) FROM Enrollments WHERE Courses = 'Physics';
```
But this returns **0**—because no row has exactly "Physics" in the Courses column.  
Using `LIKE '%Physics%'` could help, but it risks false matches (e.g., “Physical Education”) and cannot count enrollments accurately.

This is a **data access failure caused by poor design**—not a query error.

**Intuition: One Fact Per Cell**  
Think of a database cell like a single checkbox on a form. You wouldn’t check “Math and Physics” in one box—you’d use two separate boxes. Similarly, a database field should hold **one atomic value**, not a list.

Atomic means **indivisible**—you shouldn’t need to parse or split the value to use it.

**Formal Definition**  
A relation is in **First Normal Form (1NF)** if and only if:  
- All attribute values are **atomic** (indivisible).  
- Each row-column intersection contains **exactly one value** from the attribute’s domain.  
- There are **no repeating groups** (e.g., Course1, Course2, Course3 columns).

**Worked Example: Fixing the Courses Table**  
Original (violates 1NF):

| StudentID | Courses             |
|-----------|---------------------|
| S3        | Math, Physics, Chem |

We decompose it into individual facts:

| StudentID | Course    |
|-----------|-----------|
| S3        | Math      |
| S3        | Physics   |
| S3        | Chem      |

Now we can write:
```sql
SELECT COUNT(*) FROM Enrollments WHERE Course = 'Physics';
```
This returns **1**—correctly and reliably.

This new structure allows:
- Accurate queries
- Proper indexing
- Foreign key constraints (e.g., to a *Courses* table)
- Prevention of inconsistent updates

**Misconception Alert**  
❌ “Using JSON or arrays in PostgreSQL means I’m still normalized.”  
✅ No—normalization concerns **logical design**, not physical storage. If your application treats `['Math','Physics']` as a list and queries depend on its structure, you violate 1NF. Only when data is **flattened into rows** is it truly relational.

> 💡 **Test Yourself**  
> Is the following table in 1NF?

| StudentID | Grade |
|-----------|-------|
| S1        | A     |
| S2        | B, A  |

> ✅ **No.** The second row contains two grades in one cell.  
> **Fix:** Split into two rows: (S2, B) and (S2, A).  
> Now every cell has one atomic value.

> 🔍 **Try This Yourself: The Hidden Cost of Lists**  
> Suppose you have a table *Authors(BookID, AuthorList)* where AuthorList stores names as "Asimov, Clarke, Le Guin".  
> - Write a query to find all books co-authored by Clarke.  
> - Now imagine one author legally changes their name. How many rows must you update?  
> - What happens if you miss one?  
>   
> This is not just inefficiency—it’s a **consistency time bomb**.

Having enforced atomicity through 1NF, we now turn to the next structural flaw: redundancy caused by partial dependencies. This leads us to Second Normal Form.

---

### 2. Second Normal Form (2NF): Eliminate Partial Dependencies

**A Concrete Example First**  
Consider the table:  
*Registration(StudentID, CourseID, Instructor)*  
with candidate key *(StudentID, CourseID)*.  

Suppose the functional dependency $CourseID \rightarrow Instructor$ holds. Then every student enrolled in “CS101” repeats “Dr. Lee” as instructor. This redundancy becomes dangerous when Dr. Lee changes her name: you must update every row containing CS101. Miss one, and your data becomes inconsistent.

This occurs because a non-key attribute (*Instructor*) depends on only a **subset** of the composite key.

**Intuition: Full Key Dependence**  
Imagine your identity depends on your full name: first and last. If someone’s title (e.g., “Dr.”) depends only on their last name, then anyone with that last name must have the same title—clearly wrong. Similarly, in a database, **non-key attributes must depend on the entire key**, not just part of it.

This kind of flaw is called a **partial dependency**.

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

That is, no non-prime attribute may depend on a proper subset of any candidate key.

**Worked Example: E-Commerce Order Processing**  
Consider an online retailer’s *OrderItems* table:

| OrderID | ProductID | ProductName | Quantity | Price |
|---------|-----------|-------------|----------|-------|
| O1      | P100      | Laptop      | 1        | 999   |
| O2      | P100      | Laptop      | 2        | 999   |
| O1      | P200      | Mouse       | 1        | 25    |

**Step 1: Identify the candidate key**  
→ *(OrderID, ProductID)* — together, they uniquely identify each line item.

**Step 2: Identify functional dependencies**  
- *(OrderID, ProductID)* → Quantity ✅ (depends on full key)  
- *ProductID* → ProductName ✅  
- *ProductID* → Price ✅  

So *ProductName* and *Price* depend only on *ProductID*—a **partial dependency**.

**Step 3: Identify non-prime attributes**  
- *ProductName*, *Price*, *Quantity* are non-prime (not part of any candidate key)

But *ProductName* and *Price* depend only on part of the key → **violates 2NF**

**Step 4: Decompose to eliminate partial dependencies**  
We split the table:

**Products(ProductID, ProductName, Price)**  
| ProductID | ProductName | Price |  
|-----------|-------------|-------|  
| P100      | Laptop      | 999   |  
| P200      | Mouse       | 25    |  

**OrderItems(OrderID, ProductID, Quantity)**  
| OrderID | ProductID | Quantity |  
|---------|-----------|----------|  
| O1      | P100      | 1        |  
| O2      | P100      | 2        |  
| O1      | P200      | 1        |  

Now:
- Price and name changes affect only *Products*
- Historical orders retain original pricing context
- Updates are localized and safe

**Limitation and Pitfall**  
⚠️ 2NF eliminates partial dependencies but does not address transitive dependencies (e.g., *ProductID → CategoryID*, *CategoryID → CategoryName*). Such structures still risk update anomalies and require further normalization to 3NF.

> 💡 **Test Yourself**  
> Given the table:  
> *Enrollment(StudentID, CourseID, CourseName, Grade)*  
> with candidate key *(StudentID, CourseID)* and FD: *CourseID → CourseName*  
>   
> - Is this in 2NF?  
> - If not, how would you decompose it?  
>   
> ✅ **No**, because *CourseName* depends only on *CourseID* (partial dependency).  
> **Fix:**  
> - *Courses(CourseID, CourseName)*  
> - *Enrollment(StudentID, CourseID, Grade)*

> 🔍 **Try This Yourself: The Hidden Link**  
> Consider a table *Shipments(OrderID, WarehouseID, WarehouseCity, DeliveryEstimate)*  
> with key *(OrderID, WarehouseID)* and FD: *WarehouseID → WarehouseCity*  
>   
> - Is this in 2NF?  
> - What happens if the city of a warehouse changes?  
> - How many rows must be updated?  
> - What if a new warehouse opens in a city already represented? Does the city get duplicated?  
>   
> You’re not just storing data—you’re encoding business geography into transactional records. That’s a **design smell**.

Having eliminated partial dependencies, we now address the next class of redundancy: attributes determined indirectly through other non-key attributes. This brings us to Third Normal Form.