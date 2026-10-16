# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Explain** why naive gradient computation is computationally prohibitive for deep networks and how backpropagation resolves this bottleneck using dynamic programming.
2.  **Trace** the flow of gradient signals through a feedforward network’s computational graph using the chain rule in reverse topological order.
3.  **Derive** the full backpropagation update rules for a multi-layer network with arbitrary activation functions, including the role of activation-function gating.
4.  **Diagnose and correct** shape mismatches in gradient computations using dimensional analysis.
5.  **Extend** backpropagation to convolutional layers, recurrent architectures, and batch normalization.
6.  **Relate** hand-derived layerwise formulas to the automatic differentiation machinery used in modern frameworks.

---

## 1. Why We Need Backpropagation

### 1.0 Opening Hook: The Impossible Training Run

Imagine you're training a modest neural network with one million parameters on a single GPU. You kick off gradient descent, grab a coffee, and return eight hours later. The progress bar reads: *Iteration 1 of 10,000*. You haven't even finished computing the first gradient.

This isn't a hardware failure — it's what happens when you try to estimate gradients by finite differences for a network of realistic size. The training run that should take hours would instead take centuries. Yet every day, practitioners train networks a thousand times larger in minutes. The difference between these two scenarios is backpropagation — an algorithm so efficient that it compresses what would be millions of forward passes into just two. How does it pull that off? Let's find out.

### 1.1 The Optimization Problem

Training a neural network means finding weights and biases — collectively denoted \(\boldsymbol{\theta}\) — that minimize a scalar cost function \(J(\boldsymbol{\theta})\). For gradient-based optimizers, we must compute the gradient \(\nabla_{\boldsymbol{\theta}} J\), a vector of partial derivatives of \(J\) with respect to every parameter.

If a network has \(P\) parameters, a finite-difference approximation requires at least \(P+1\) forward passes per gradient estimate. For a modern network with millions of parameters, this is infeasible. We therefore need an exact, efficient method.

The difficulty arises because the cost function is a deeply nested composition of hundreds of simple operations. The chain rule guarantees that we can compute the gradient exactly by multiplying local derivatives along every path from parameters to cost. However, a naive traversal of all paths independently repeats subcomputations exponentially. A weight matrix in layer 1 might influence the cost through many distinct downstream routes; without a strategy, its contribution would be recomputed for each one.

**The intellectual tension:** The chain rule promises exact gradients for free, yet applying it naively is worse than useless — it's exponentially expensive. We need the *right* evaluation order. This is the same tension that arises in computing Fibonacci numbers: the recursive definition is elegant, but evaluating it directly is catastrophic. The solution in both cases is the same algorithmic idea: dynamic programming.

Backpropagation reorganizes the computation so that every intermediate gradient is computed exactly once and reused everywhere upstream. It is not an approximation or a new learning algorithm — it is the computational engine that makes gradient descent feasible in deep architectures.

### 1.2 The Core Idea: Reverse-Mode Computation

Consider a function built by composing many simple operations. The chain rule lets us compute the derivative of the final output with respect to any intermediate variable by multiplying local derivatives along the computation path. The question is: which order minimizes work?

**Analogy: Factory bill of materials.** Imagine you're the manager of a factory that produces one final product from thousands of raw parts through a complex assembly tree. The CEO asks: "If the price of one raw material increases by $1, how much does our final product cost change?" You could trace every path from that raw material through every subassembly to the final product — but that means revisiting the same subassemblies thousands of times. The smarter approach: start at the final product and propagate cost sensitivities *backward* through the bill of materials. Each subassembly's sensitivity is computed once and shared with all its upstream suppliers. This is exactly what backpropagation does with gradients.

Backpropagation answers: **start at the cost, and propagate gradients backward through the computation graph.** Every intermediate gradient is computed once and reused wherever it is needed upstream. This algorithmic insight powers reverse-mode automatic differentiation in every modern deep learning framework.

### 1.3 Real-World Impact

To appreciate the practical significance, consider training ResNet-50 on ImageNet. This architecture has approximately 25.6 million parameters. A single forward pass involves roughly 3.8 billion floating-point operations (FLOPs). Computing the full gradient via finite differences would require 25.6 million forward passes — approximately \(9.7 \times 10^{16}\) FLOPs per gradient evaluation. On a modern GPU capable of 10 teraFLOPs per second, that single gradient would take roughly 2.7 hours. Training for the standard 90 epochs with 1.28 million images would be impossible.

Backpropagation computes the exact gradient in approximately the same number of operations as **two forward passes** — one forward to cache activations, one backward to propagate gradients. The total cost per image is about 7.6 billion FLOPs, making large-scale training feasible.

**Prerequisite Check.** We assume you are comfortable with:

- The chain rule for scalar and vector-valued functions (Section 2 provides a refresher).
- Computational graphs as directed acyclic graphs where nodes are operations and edges are data flow.
- Matrix multiplication, transposition, and element-wise (Hadamard) products.
- The anatomy of a feedforward network: input layer, hidden layers with activation functions, output layer, and a scalar cost.

If any term feels unfamiliar, review it before continuing — the rest of the lecture builds directly on these ideas.

**✏️ Quick Check 1:** In your own words, why can't we use finite differences to compute the gradient for a network with 1 million parameters? Write down the number of forward passes required and estimate the time on a GPU doing \(10^{12}\) FLOPs per second if one forward pass costs \(10^9\) FLOPs.

<details>
<summary>Click for answer</summary>
Finite differences would require 1,000,001 forward passes. Total FLOPs ≈ \(10^9 \times 10^6 = 10^{15}\). At \(10^{12}\) FLOPs/sec, that's 1000 seconds (≈ 17 minutes) per gradient step. Training for thousands of steps would be infeasible. Backpropagation reduces this to roughly 2 forward-pass equivalents per step.
</details>

---

## 2. The Chain Rule as the Backbone

### 2.1 Intuition: Local Derivatives and Signal Flow

Think of the computation as an electrical circuit flowing forward from inputs to cost. Each node holds a voltage — the numerical value computed during the forward pass. Now imagine we apply a unit current source at the cost node and ask: *what is the resulting current at each upstream node?* The chain rule answers by multiplying the **local conductance** (the derivative of a node's output with respect to its input) by the **incoming signal** from downstream.

**Analogy: Water distribution network.** Picture a city water system where reservoirs feed into pipes that branch and merge. If the mayor asks, "How much does a leak at junction X increase total water loss at the central treatment plant?", you don't re-simulate the entire network from scratch. You start at the treatment plant with a unit of "loss sensitivity" and push it backward through the pipes. At each split, the sensitivity divides proportionally to flow rates; at each merge, sensitivities from different branches sum together. The chain rule does exactly this for gradients — local derivatives act as the pipe conductances, and the summation-over-paths principle captures how gradients merge at junctions.

In circuit analysis, current divides across parallel branches and sums at junctions — exactly the behavior captured by the multivariable chain rule in Section 2.5. The same summation-over-paths principle governs how gradients accumulate when a node feeds multiple consumers.

### 2.2 Scalar Chain Rule (Refresher)

If \(y = f(x)\) and \(z = g(y)\), then:

\[
\frac{dz}{dx} = \frac{dz}{dy} \cdot \frac{dy}{dx}
\]

The term \(\frac{dz}{dy}\) is the signal arriving at \(y\), and \(\frac{dy}{dx}\) is the local sensitivity of \(y\) to \(x\).

### 2.3 Vector-Jacobian Product: The Workhorse

In neural networks, intermediates are rarely scalars. Let \(\mathbf{x} \in \mathbb{R}^m\), \(\mathbf{y} = f(\mathbf{x}) \in \mathbb{R}^n\), and \(z = g(\mathbf{y}) \in \mathbb{R}\). The gradient of \(z\) with respect to \(\mathbf{x}\) is:

\[
\nabla_{\mathbf{x}} z = \left( \frac{\partial \mathbf{y}}{\partial \mathbf{x}} \right)^\top \nabla_{\mathbf{y}} z
\]

where \(\frac{\partial \mathbf{y}}{\partial \mathbf{x}}\) is the \(n \times m\) **Jacobian matrix** whose \((i,j)\) entry is \(\partial y_i / \partial x_j\).

**Why the transpose?** The incoming gradient \(\nabla_{\mathbf{y}} z\) is a column vector of shape \(n \times 1\). To map it back to the input space of dimension \(m\), we multiply by the \(m \times n\) transposed Jacobian. This product transforms a downstream gradient into an upstream gradient — it is the **vector-Jacobian product (VJP)**.

**Try this yourself:** Before reading further, verify the dimensional logic. If \(\mathbf{x} \in \mathbb{R}^m\) and \(z\) is a scalar, \(\nabla_{\mathbf{x}} z\) must have shape \(m \times 1\). The incoming gradient \(\nabla_{\mathbf{y}} z\) has shape \(n \times 1\). What shape must the matrix multiplying it have to produce an \(m \times 1\) output? This simple check — \(m \times 1 = (m \times n)(n \times 1)\) — catches the majority of transpose errors.

### 2.4 Worked Scalar-to-Vector Example

Let \(\mathbf{x} = [x_1, x_2]^\top\). Define \(y_1 = 3x_1 + x_2\), \(y_2 = x_1^2\), and \(z = y_1 + 2y_2\). We want \(\nabla_{\mathbf{x}} z\).

*Forward values:* Suppose \(x_1 = 2, x_2 = -1\). Then \(y_1 = 5\), \(y_2 = 4\), \(z = 13\).

*Downstream gradient:* \(\nabla_{\mathbf{y}} z = [\partial z/\partial y_1, \; \partial z/\partial y_2]^\top = [1, 2]^\top\).

*Jacobian of \(\mathbf{y}\) w.r.t. \(\mathbf{x}\):*
\[
\frac{\partial \mathbf{y}}{\partial \mathbf{x}} =
\begin{bmatrix}
\frac{\partial y_1}{\partial x_1} & \frac{\partial y_1}{\partial x_2} \\
\frac{\partial y_2}{\partial x_1} & \frac{\partial y_2}{\partial x_2}
\end{bmatrix}
= \begin{bmatrix} 3 & 1 \\ 2x_1 & 0 \end{bmatrix}
= \begin{bmatrix} 3 & 1 \\ 4 & 0 \end{bmatrix}
\]

*Upstream gradient:*
\[
\nabla_{\mathbf{x}} z =
\begin{bmatrix} 3 & 4 \\ 1 & 0 \end{bmatrix}
\begin{bmatrix} 1 \\ 2 \end{bmatrix}
= \begin{bmatrix} 3\cdot1 + 4\cdot2 \\ 1\cdot1 + 0\cdot2 \end{bmatrix}
= \begin{bmatrix} 11 \\ 1 \end{bmatrix}
\]

Check via direct differentiation: \(z = 3x_1 + x_2 + 2x_1^2\), so \(\partial z/\partial x_1 = 3 + 4x_1 = 11\), \(\partial z/\partial x_2 = 1\). Matches.

**✏️ Quick Check 2:** Let \(\mathbf{x} = [x_1, x_2]^\top\), \(y_1 = 2x_1 - x_2\), \(y_2 = x_1 x_2\), and \(z = 3y_1 + y_2\). Compute \(\nabla_{\mathbf{x}} z\) at \(x_1 = 1, x_2 = 2\) using the VJP approach. Verify by direct differentiation.

<details>
<summary>Click for answer</summary>
Forward: \(y_1 = 0\), \(y_2 = 2\), \(z = 2\). Downstream: \(\nabla_{\mathbf{y}} z = [3, 1]^\top\). Jacobian: \(\partial \mathbf{y}/\partial \mathbf{x} = \begin{bmatrix} 2 & -1 \\ x_2 & x_1 \end{bmatrix} = \begin{bmatrix} 2 & -1 \\ 2 & 1 \end{bmatrix}\). VJP: \(\nabla_{\mathbf{x}} z = \begin{bmatrix} 2 & 2 \\ -1 & 1 \end{bmatrix} \begin{bmatrix} 3 \\ 1 \end{bmatrix} = \begin{bmatrix} 8 \\ -2 \end{bmatrix}\). Direct: \(z = 3(2x_1 - x_2) + x_1 x_2 = 6x_1 - 3x_2 + x_1 x_2\), so \(\partial z/\partial x_1 = 6 + x_2 = 8\), \(\partial z/\partial x_2 = -3 + x_1 = -2\). ✓
</details>

### 2.5 The Multivariable Chain Rule (Sum Over Paths)

In a computational graph, a node \(u^{(j)}\) may influence the final cost \(u^{(n)}\) through multiple downstream consumers. The gradient must sum contributions from all such paths:

\[
\frac{\partial u^{(n)}}{\partial u^{(j)}} = \sum_{i:\, j \in \text{Parents}(u^{(i)})} \frac{\partial u^{(n)}}{\partial u^{(i)}} \frac{\partial u^{(i)}}{\partial u^{(j)}}
\]

This is the **multivariable chain rule**: a node receives gradient signals from every operation that directly uses it, and those signals add.

**Misconception Alert.** A common error is to apply the single-path chain rule when a node feeds into multiple downstream operations. Omitting the sum silently drops entire pathways of influence. Always ask: "Which nodes directly consume this intermediate?" Sum over all of them.

**Try this yourself:** Consider a ResNet skip connection where a tensor \(\mathbf{a}\) feeds into both a convolutional block (producing \(\mathbf{b}\)) and directly into an addition (producing \(\mathbf{c} = \mathbf{b} + \mathbf{a}\)). Write the expression for \(\frac{\partial J}{\partial \mathbf{a}}\). If you only included the path through \(\mathbf{b}\), what gradient information would you lose?

<details>
<summary>Click for answer</summary>
\(\frac{\partial J}{\partial \mathbf{a}} = \frac{\partial J}{\partial \mathbf{b}}\frac{\partial \mathbf{b}}{\partial \mathbf{a}} + \frac{\partial J}{\partial \mathbf{c}}\frac{\partial \mathbf{c}}{\partial \mathbf{a}}\). Since \(\frac{\partial \mathbf{c}}{\partial \mathbf{a}} = I\) (identity), the second term is simply \(\frac{\partial J}{\partial \mathbf{c}}\). If you omitted it, you'd lose the gradient flowing through the skip connection — precisely the pathway that makes ResNets trainable at depth.
</details>

**✏️ Quick Check 3:** In the graph \(a \to b \to d\), \(a \to c \to d\) with \(d = b + c\), write the formula for \(\partial d / \partial a\).

<details>
<summary>Click for answer</summary>
\(\frac{\partial d}{\partial a} = \frac{\partial d}{\partial b}\frac{\partial b}{\partial a} + \frac{\partial d}{\partial c}\frac{\partial c}{\partial a}\). Since \(d = b + c\), we have \(\frac{\partial d}{\partial b} = 1\) and \(\frac{\partial d}{\partial c} = 1\), so \(\frac{\partial d}{\partial a} = \frac{\partial b}{\partial a} + \frac{\partial c}{\partial a}\). If you forgot the second term, you'd miss the contribution through \(c\) entirely.
</details>

---

## 3. Dynamic Programming: Fill the Table Once

### 3.1 The Problem with Naive Recursion

If we recursively applied the chain rule from the cost back to the inputs without caching, we would recompute the gradient at a node every time it is encountered on a different path. In a graph with many shared subexpressions — such as a weight matrix used in multiple forward passes — the number of redundant computations grows exponentially with depth.

**Cross-domain connection: The shortest path problem.** In graph algorithms, computing the shortest path from a source to all nodes by independently exploring every route is hopelessly inefficient — it revisits the same intersections exponentially many times. Dijkstra's algorithm solves this by processing nodes in order of increasing distance, computing each node's shortest path exactly once and reusing it for all downstream routes. Backpropagation is the Dijkstra's algorithm of differentiation: process nodes in reverse dependency order, compute each gradient once, and reuse it for all upstream paths. Both algorithms transform an exponential naive approach into a linear-time solution through systematic memoization and optimal ordering.

Consider computing Fibonacci numbers recursively without memoization: `Fib(100)` calls `Fib(99)` and `Fib(98)`, but `Fib(99)` independently calls `Fib(98)` again. The same subproblem is solved exponentially many times. In a neural network, a weight matrix in layer 1 is the "Fib(98)" — reused by every downstream path, yet naively recomputed for each one.

### 3.2 Reverse Topological Ordering

Backpropagation treats gradient accumulation as a **dynamic programming** problem. Each node in the computational graph has a memory slot storing its gradient \(\frac{\partial J}{\partial u}\). We fill these slots in **reverse topological order** — from the cost node backward to the inputs. Because a node is processed only after all its consumers have been processed, each local gradient is computed exactly once and then reused wherever it is needed upstream.

**Analogy.** Imagine filling out a spreadsheet where each cell depends on cells to its right. If you fill columns from right to left, every formula references already-computed values. Backpropagation does the same for the computational graph: process nodes in reverse dependency order, and every gradient you need is already in memory. The cost is one forward pass to compute and store all intermediate values, then one backward pass to accumulate gradients — \(O(\text{number of operations})\) total, versus exponential for naive recursion.

**✏️ Quick Check 4:** Draw a simple computational graph — say \(x \to a = x^2\), \(x \to b = \sin(x)\), and \(y = a + b\). Identify the reverse topological order. Which node must you process first: \(y\), \(a\), \(b\), or \(x\)? Explain why.

<details>
<summary>Click for answer</summary>
Reverse topological order: \(y\), then \(a\) and \(b\) (in either order), then \(x\). We process \(y\) first because it's the output — its gradient is the seed \(\partial J/\partial y = 1\) (assuming \(J = y\)). Once we have \(\partial J/\partial y\), we can compute \(\partial J/\partial a = \partial J/\partial y \cdot \partial y/\partial a\) and \(\partial J/\partial b = \partial J/\partial y \cdot \partial y/\partial b\). With those in hand, we compute \(\partial J/\partial x = \partial J/\partial a \cdot \partial a/\partial x + \partial J/\partial b \cdot \partial b/\partial x\). Processing in any other order would require a gradient we haven't computed yet.
</details>

---

## 4. Backpropagation Through a Multi-Layer Network

### 4.1 Network Architecture and Notation

We now make everything concrete. Consider an \(L\)-layer network:

- **Input:** \(\mathbf{x} \in \mathbb{R}^d\)
- **Layer \(\ell\) (for \(\ell = 1, \ldots, L\)):**