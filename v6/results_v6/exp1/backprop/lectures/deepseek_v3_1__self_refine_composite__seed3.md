# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

- **Remember** the key components of a computational graph (nodes, edges, forward pass) and state why finite-difference gradient estimation fails for networks with more than a few thousand parameters.
- **Understand** the chain rule in its scalar, vector-Jacobian product, and multivariable (sum-over-paths) forms, and explain why reverse-mode accumulation avoids exponential recomputation.
- **Apply** the backpropagation algorithm to compute gradients for a two-layer neural network with a scalar cost, deriving layerwise update rules for weights and biases.
- **Analyze** gradient flow through common activation functions (ReLU, sigmoid, tanh) and diagnose vanishing/exploding gradient behaviors.
- **Create** a correct implementation of backpropagation for a small network, using dimensional analysis to verify all gradient shapes.

---

## 1. Why We Need Backpropagation

### 1.1 The Problem: Training Requires a Gradient

Imagine you're training a neural network to detect early-stage diabetic retinopathy from retinal scans — a task where missing a diagnosis can cost someone their eyesight. Your network has 10 million parameters. It processes a scan, outputs a risk score, and a cost function \(J\) measures how far that score is from the truth. To improve, every parameter must shift in the direction that reduces \(J\). Gradient descent prescribes the direction: the negative gradient \(-\nabla_{\boldsymbol{\theta}} J\).

The gradient \(\nabla_{\boldsymbol{\theta}} J\) is a vector of 10 million numbers. Each number answers a precise question: "If I nudge this one parameter by a microscopic amount, how much does the diagnostic error change?" With 10 million answers, we know exactly how to tune every knob.

**Why finite differences fail catastrophically.** The obvious brute-force method perturbs each parameter individually, runs a forward pass, and measures the resulting change in cost. For 10 million parameters, one gradient estimate requires 10 million forward passes. Training might need 100,000 gradient steps. That's \(10^{12}\) forward passes — roughly three years on a fast GPU for a modest-sized network. And that's for *one* training run. Hyperparameter tuning? Forget it.

We need an exact method that computes all 10 million gradient entries in roughly the cost of *two* forward passes. Backpropagation delivers exactly that.

**Pause and predict:** The cost function \(J\) is a deeply nested composition of simple operations — matrix multiplications, nonlinearities, sums. The chain rule from calculus tells us we can compute the exact gradient by multiplying local derivatives along every path from parameters to cost. So why not just recursively apply the chain rule starting from each parameter? What hidden trap lurks in that approach? Write down your hypothesis, then continue.

<details>
<summary>Click to reveal the issue</summary>
The trap is exponential path explosion. A weight in the first layer influences the cost through every possible combination of active neurons in subsequent layers. In a fully connected network with layers of width \(n\), the number of distinct paths from a first-layer weight to the cost grows as \(n^{L-1}\), where \(L\) is the depth. A naive recursive approach traces each path independently, recomputing the same intermediate derivatives exponentially many times. For a network with layers of width 100 and depth 10, that's \(100^9 = 10^{18}\) paths — for a single parameter. Without a strategy to share work across paths, the computation is hopeless.
</details>

### 1.2 The Core Idea: Reverse-Mode Accumulation

Backpropagation flips the computation inside out. Instead of starting from each parameter and tracing forward to the cost, we start at the cost and propagate gradients backward through the computation graph. Each intermediate gradient is computed exactly once, stored, and reused everywhere it's needed upstream.

**Analogy: Tracing contamination in a water distribution network.** A city's water supply flows from a reservoir through treatment plants, pumping stations, and neighborhood pipes to reach individual homes. One day, a bacterial contaminant is detected at a single tap. The public health team needs to know: how much did each upstream junction contribute to the contamination risk at that tap? The naive approach traces backward from the tap, but at every pipe junction that splits, the team would need to independently re-trace the entire upstream network for each incoming pipe — re-examining the treatment plant and reservoir over and over. The smart approach: start at the contaminated tap, measure the contaminant concentration, then move upstream junction by junction. At each junction, compute how much contaminant would have had to enter from each incoming pipe to produce the observed downstream concentration. Each pipe segment is analyzed exactly once. By the time the team reaches the reservoir, every junction's contribution has been quantified. Backpropagation is this contamination trace, applied to computation graphs: the "contaminant" is gradient signal, and the "junctions" are mathematical operations.

**Analogy: The auditor's spreadsheet.** Imagine auditing a multinational corporation to determine how every individual salesperson affects the CEO's bonus. The bonus depends on division profits. Division profits depend on department revenues. Department revenues depend on individual sales. A naive auditor traces each salesperson's path independently through the entire org chart, recomputing each division's profit sensitivity thousands of times. A smart auditor starts at the CEO's bonus, computes its sensitivity to each division's profit (once), then each division's profit sensitivity to each department's revenue (once), and so on backward. By the time they reach the salespeople, every intermediate sensitivity has been computed exactly once. Backpropagation is this audit, applied to computation graphs.

**Think-pair-share:** With a neighbor or in your notes, identify another real-world system where starting from the end and working backward avoids redundant work. Consider: electrical grid load analysis, supply chain disruption tracing, compiler optimization passes, or epidemiological contact tracing. What makes the backward strategy more efficient than the forward strategy in your example? Share your reasoning.

**Prerequisite check.** This lecture assumes comfort with:

- The chain rule for derivatives of composed functions.
- Matrix multiplication and transposition.
- The basic structure of a feedforward neural network: input layer, hidden layers with activation functions, output layer, and a scalar cost function.
- The concept of a directed acyclic graph (DAG) where nodes represent operations and edges represent data flow.

If any of these feel unfamiliar, pause and review them now — we build directly on these ideas.

**Test Yourself 1:** In one sentence, why is finite-difference gradient estimation infeasible for a network with 10 million parameters?

*Write your answer before checking:*

<details>
<summary>Click for answer</summary>
It would require over 10 million forward passes per gradient computation, making even a single gradient step prohibitively slow, let alone full training.
</details>

---

## 2. The Chain Rule: The Engine of Backpropagation

### 2.1 Intuition: Gradients as Flowing Signals

Think of the forward pass as water flowing through a network of pipes from inputs to the cost. Each pipe has a valve (a mathematical operation) that controls how the flow rate changes. Now, inject a unit of pressure at the cost node and let it propagate backward. At each valve, the backward pressure is multiplied by the local sensitivity of that valve — how much its output changes when its input changes. The pressure arriving at any upstream node tells us exactly how much that node influences the final cost.

This is the chain rule in physical form: the sensitivity of the cost to an upstream variable is the product of the downstream sensitivity and the local derivative.

**Quick reflection:** Based on this analogy, what do you expect happens when a node feeds into two downstream consumers? Does the backward signal split, sum, or something else? Keep your hypothesis in mind as we develop the formal rules — the answer may surprise you.

### 2.2 The Scalar Chain Rule

If \(y = f(x)\) and \(z = g(y)\), then:

\[
\frac{dz}{dx} = \frac{dz}{dy} \cdot \frac{dy}{dx}
\]

Here, \(\frac{dz}{dy}\) is the downstream gradient (the signal arriving at \(y\) from \(z\)), and \(\frac{dy}{dx}\) is the local gradient (the sensitivity of \(y\) to its input \(x\)).

**Worked Example 1:** Let \(y = x^2\) and \(z = 3y + 1\). Find \(\frac{dz}{dx}\) at \(x = 2\).

**Step 1 — Forward pass:** \(x = 2\), so \(y = 2^2 = 4\), then \(z = 3(4) + 1 = 13\).

**Step 2 — Downstream gradient:** \(\frac{dz}{dy} = 3\) (the derivative of \(3y + 1\) with respect to \(y\)).

**Step 3 — Local gradient:** \(\frac{dy}{dx} = 2x = 2(2) = 4\).

**Step 4 — Chain rule:** \(\frac{dz}{dx} = 3 \cdot 4 = 12\).

**Step 5 — Verify directly:** \(z = 3x^2 + 1\), so \(\frac{dz}{dx} = 6x = 6(2) = 12\). Matches.

### 2.3 The Vector-Jacobian Product

In neural networks, variables are rarely scalars. We often have a vector input \(\mathbf{x} \in \mathbb{R}^m\), a vector intermediate \(\mathbf{y} = f(\mathbf{x}) \in \mathbb{R}^n\), and a scalar cost \(z = g(\mathbf{y})\). The gradient of \(z\) with respect to \(\mathbf{x}\) is:

\[
\nabla_{\mathbf{x}} z = \left( \frac{\partial \mathbf{y}}{\partial \mathbf{x}} \right)^\top \nabla_{\mathbf{y}} z
\]

Here, \(\frac{\partial \mathbf{y}}{\partial \mathbf{x}}\) is the \(n \times m\) Jacobian matrix, where entry \((i, j)\) is \(\frac{\partial y_i}{\partial x_j}\). The incoming gradient \(\nabla_{\mathbf{y}} z\) is a column vector of shape \(n \times 1\). Multiplying by the \(m \times n\) transposed Jacobian produces \(\nabla_{\mathbf{x}} z\), an \(m \times 1\) column vector.

**Why the transpose? A dimensional check that catches most bugs.** If \(\mathbf{x} \in \mathbb{R}^m\) and \(z\) is a scalar, then \(\nabla_{\mathbf{x}} z\) must have shape \(m \times 1\). The incoming gradient \(\nabla_{\mathbf{y}} z\) has shape \(n \times 1\). To get from shape \(n \times 1\) to \(m \times 1\), we must multiply by a matrix of shape \(m \times n\). The Jacobian is \(n \times m\), so we need its transpose. This check — \(m \times 1 = (m \times n) \times (n \times 1)\) — catches most shape errors before they propagate. Whenever you implement backpropagation, verify every gradient's shape against the parameter it will update. If the shapes don't match, you've transposed something wrong.

**Cross-domain insight: The adjoint method in fluid dynamics.** When aerospace engineers optimize a wing shape to minimize drag, they face the same computational challenge: the drag depends on the wing shape through the entire airflow field, which is governed by partial differential equations with millions of variables. Computing the sensitivity of drag to each shape parameter by finite differences would require re-simulating the entire airflow millions of times. Instead, they solve the *adjoint equation* — a linear system that propagates sensitivity information backward from the drag measurement through the flow field to the shape parameters. The adjoint equation is the continuous analogue of the vector-Jacobian product in backpropagation. Both methods compute gradients of a scalar output with respect to many inputs in time proportional to one forward solve plus one backward solve, independent of the number of parameters.

**Worked Example 2: Vector-Jacobian product.** Let \(\mathbf{x} = [x_1, x_2]^\top\). Define:

\[
y_1 = 3x_1 + x_2,\quad y_2 = x_1^2,\quad z = y_1 + 2y_2
\]

Find \(\nabla_{\mathbf{x}} z\) at \(x_1 = 2, x_2 = -1\).

**Step 1 — Forward pass:**
\[
y_1 = 3(2) + (-1) = 5,\quad y_2 = 2^2 = 4,\quad z = 5 + 2(4) = 13
\]

**Step 2 — Downstream gradient:**
\[
\nabla_{\mathbf{y}} z = \begin{bmatrix} \partial z / \partial y_1 \\ \partial z / \partial y_2 \end{bmatrix} = \begin{bmatrix} 1 \\ 2 \end{bmatrix}
\]

**Step 3 — Jacobian of \(\mathbf{y}\) with respect to \(\mathbf{x}\):**
\[
\frac{\partial \mathbf{y}}{\partial \mathbf{x}} =
\begin{bmatrix}
\frac{\partial y_1}{\partial x_1} & \frac{\partial y_1}{\partial x_2} \\[4pt]
\frac{\partial y_2}{\partial x_1} & \frac{\partial y_2}{\partial x_2}
\end{bmatrix}
= \begin{bmatrix} 3 & 1 \\ 2x_1 & 0 \end{bmatrix}
= \begin{bmatrix} 3 & 1 \\ 4 & 0 \end{bmatrix}
\]

**Step 4 — Vector-Jacobian product:**
\[
\nabla_{\mathbf{x}} z =
\begin{bmatrix} 3 & 4 \\ 1 & 0 \end{bmatrix}
\begin{bmatrix} 1 \\ 2 \end{bmatrix}
= \begin{bmatrix} 3(1) + 4(2) \\ 1(1) + 0(2) \end{bmatrix}
= \begin{bmatrix} 11 \\ 1 \end{bmatrix}
\]

**Step 5 — Verify directly:** \(z = 3x_1 + x_2 + 2x_1^2\), so \(\partial z / \partial x_1 = 3 + 4x_1 = 11\), \(\partial z / \partial x_2 = 1\). Matches.

**Try this yourself:** Modify the example: let \(y_1 = x_1 - 2x_2\) and keep everything else the same. Compute \(\nabla_{\mathbf{x}} z\) at \(x_1 = 2, x_2 = -1\) using the vector-Jacobian product method, then verify by direct differentiation.

*Work through all five steps on paper before checking:*

<details>
<summary>Click for answer</summary>

**Step 1:** \(y_1 = 2 - 2(-1) = 4\), \(y_2 = 4\), \(z = 4 + 8 = 12\).

**Step 2:** \(\nabla_{\mathbf{y}} z = [1, 2]^\top\) (unchanged).

**Step 3:**
\[
\frac{\partial \mathbf{y}}{\partial \mathbf{x}} =
\begin{bmatrix} 1 & -2 \\ 2x_1 & 0 \end{bmatrix}
= \begin{bmatrix} 1 & -2 \\ 4 & 0 \end{bmatrix}
\]

**Step 4:**
\[
\nabla_{\mathbf{x}} z =
\begin{bmatrix} 1 & 4 \\ -2 & 0 \end{bmatrix}
\begin{bmatrix} 1 \\ 2 \end{bmatrix}
= \begin{bmatrix} 1(1) + 4(2) \\ -2(1) + 0(2) \end{bmatrix}
= \begin{bmatrix} 9 \\ -2 \end{bmatrix}
\]

**Step 5:** Direct: \(z = x_1 - 2x_2 + 2x_1^2\), so \(\partial z/\partial x_1 = 1 + 4x_1 = 9\), \(\partial z/\partial x_2 = -2\). Matches.
</details>

### 2.4 The Multivariable Chain Rule: Summing Over Paths

Now we confront the question from Section 2.1: what happens when a node feeds into multiple downstream consumers? In a computational graph, a single node often fans out — a hidden layer's output might be used by both the next layer and a skip connection. The gradient of the cost with respect to that node must sum the contributions from all downstream consumers.

**The rule:** If node \(u^{(j)}\) is used as input by nodes \(u^{(i_1)}, u^{(i_2)}, \dots, u^{(i_k)}\), then:

\[
\frac{\partial J}{\partial u^{(j)}} = \sum_{p=1}^{k} \frac{\partial J}{\partial u^{(i_p)}} \cdot \frac{\partial u^{(i_p)}}{\partial u^{(j)}}
\]

**Intuition through a physical analogy: A river delta.** Imagine a river that splits into two channels before reaching the ocean. If you add one liter of water per second at the split point, that extra flow divides between both channels. The total increase in water reaching the ocean is the sum of the increases through each channel. Similarly, if a variable increases by \(\Delta\), each consumer changes, and each of those changes propagates to the cost. The total cost change is the sum of all these propagated effects. The backward signals don't split — they *accumulate*.

**Common misconception:** A frequent error is applying the single-path chain rule when a node has multiple consumers. This silently drops entire pathways of influence, as if one channel of the river delta didn't exist. Always ask: "Which operations directly use this intermediate?" Sum over all of them.

**Worked Example 3: Sum over paths.** Consider:

\[
a = x^2,\quad b = \sin(x),\quad y = a + b
\]

Here, \(x\) feeds into both \(a\) and \(b\), which both feed into \(y\). The multivariable chain rule gives:

\[
\frac{\partial y}{\partial x} = \frac{\partial y}{\partial a} \cdot \frac{\partial a}{\partial x} + \frac{\partial y}{\partial b} \cdot \frac{\partial b}{\partial x} = 1 \cdot 2x + 1 \cdot \cos(x) = 2x + \cos(x)
\]

Using only one path would yield either \(2x\) or \(\cos(x)\) — both incorrect. The correct gradient is their sum.

**Test Yourself 2:** In the graph \(a \to b \to d\) and \(a \to c \to d\) with \(d = b + c\), write the formula for \(\partial d / \partial a\). Then, let \(b = a^2\) and \(c = a^3\). Compute \(\partial d / \partial a\) at \(a = 2\).

*Write your answer before checking:*

<details>
<summary>Click for answer</summary>

**Formula:**
\[
\frac{\partial d}{\partial a} = \frac{\partial d}{\partial b}\frac{\partial b}{\partial a} + \frac{\partial d}{\partial c}\frac{\partial c}{\partial a} = 1 \cdot 2a + 1 \cdot 3a^2 = 2a + 3a^2
\]

**At \(a = 2\):** \(2(2) + 3(4) = 4 + 12 = 16\).

**Direct verification:** \(d = a^2 + a^3\), so \(\partial d / \partial a = 2a + 3a^2 = 2(2) + 3(4) = 16\). Matches.
</details>

---

## 3. Backpropagation as Dynamic Programming

### 3.1 The Problem with Naive Recursion

We've seen that multiple paths from a node to the cost require summing gradients. But there's a deeper computational trap: recursively applying the chain rule from the cost back to the inputs *without caching* recomputes the gradient at a node every time it is encountered on a different path. In a deep network, the number of paths from early parameters to the cost grows exponentially with depth. Without caching, computation time explodes.

**Analogy: Naive Fibonacci and the cost of forgetting.** Computing \(\text{Fib}(n)\) recursively without memoization calls \(\text{Fib}(n-1)\) and \(\text{Fib}(n-2)\), but \(\text{Fib}(n-1)\) independently calls \(\text{Fib}(n-2)\) again. The number of redundant calls grows as the golden ratio raised to the power \(n\) — exponential. With memoization — storing each result after computing it once — the