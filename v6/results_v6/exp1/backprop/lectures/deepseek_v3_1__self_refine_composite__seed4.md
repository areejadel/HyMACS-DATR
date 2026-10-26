## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember:** State the two-phase structure of backpropagation and explain why it reduces gradient computation from \(O(P)\) to \(O(1)\) times the forward pass cost.
2.  **Understand:** Trace the flow of gradient signals through a computational graph and explain why reverse topological ordering enables dynamic programming.
3.  **Apply:** Compute gradients for a small feedforward network by hand, correctly applying the chain rule at each node and summing over multiple downstream paths.
4.  **Analyze:** Identify shared intermediate values in a computational graph and explain how backpropagation exploits them to avoid redundant computation.
5.  **Create:** Design the backward pass for a novel operation (e.g., a custom activation function or a skip connection) by deriving its local Jacobian and integrating it into the reverse accumulation framework.

---

## 1. Prerequisites

We assume you are comfortable with:

- **Matrix calculus and broadcasting:** Multiplying a weight matrix \(\mathbf{W} \in \mathbb{R}^{m \times n}\) by an input vector \(\mathbf{x} \in \mathbb{R}^n\), adding a bias vector \(\mathbf{b} \in \mathbb{R}^m\), and rigorously managing the shapes of all intermediate quantities. You should be able to identify when broadcasting rules apply and verify dimensional consistency at each step.
- **The multivariate chain rule:** If a scalar cost \(J\) depends on a vector \(\mathbf{u} \in \mathbb{R}^m\), and \(\mathbf{u}\) depends on a vector \(\mathbf{x} \in \mathbb{R}^n\), then the gradient is \(\nabla_{\mathbf{x}} J = \left(\frac{\partial \mathbf{u}}{\partial \mathbf{x}}\right)^\top \nabla_{\mathbf{u}} J\). You must be comfortable summing over all intermediate paths when a variable influences the cost through multiple downstream nodes.
- **Elementary partial derivatives in matrix form:** The identity \(\frac{\partial}{\partial \mathbf{W}} (\mathbf{W}\mathbf{x}) = \mathbf{x}^\top\) for a vector input \(\mathbf{x}\), and the ability to differentiate common activation functions such as sigmoid, tanh, ReLU, and softmax. For softmax, the Jacobian is \(\frac{\partial \mathbf{s}}{\partial \mathbf{z}} = \operatorname{diag}(\mathbf{s}) - \mathbf{s}\mathbf{s}^\top\).
- **The forward pass of a neural network:** Given an input \(\mathbf{x}^{(0)}\), the network computes layer outputs sequentially via \(\mathbf{z}^{(l)} = \mathbf{W}^{(l)}\mathbf{a}^{(l-1)} + \mathbf{b}^{(l)}\) and \(\mathbf{a}^{(l)} = f^{(l)}(\mathbf{z}^{(l)})\), ultimately producing a scalar cost \(J(\mathbf{a}^{(L)}, \mathbf{y})\).

If any of these topics feel shaky, pause here and review them — they are the building blocks for everything that follows.

---

## 2. Motivation: The Gradient Computation Bottleneck

### 2.1 The Paradox at the Heart of Deep Learning

Here is a puzzle that should bother you.

Imagine you are blindfolded on a vast, million-dimensional mountainside in a storm. Your only goal is to take one step downhill. The obvious, brute-force method is absurd: you’d probe the elevation by taking a step in each of the million independent directions, one after another, to feel the slope. By the time you’d finished, the storm would have long passed. Yet, modern neural network training — an optimization on a million-dimensional surface — finds that single downhill step in the time it takes to check the elevation just two or three times. How?

The answer is not that we found a shortcut around the chain rule. It is that we found a shortcut around *redundant computation*. And that shortcut, backpropagation, is the subject of this lecture. It’s the difference between probing the entire mountain and instantly feeling the slope beneath your feet.

When you finish this section, you should be able to explain to a peer why backpropagation is not merely "the chain rule applied to neural networks" — it is the chain rule applied *with a specific dynamic programming scheduling strategy* that makes deep learning computationally feasible.

### 2.2 Why Gradients Matter

Training a neural network means adjusting its parameters \(\boldsymbol{\theta}\) to minimize a scalar cost function \(J(\boldsymbol{\theta})\). The cost measures the discrepancy between predictions and targets. To improve, we need to know how each parameter influences the cost — that is, we need the gradient \(\nabla_{\boldsymbol{\theta}} J\).

Modern networks routinely contain \(10^7\) to \(10^{11}\) parameters. Finite-difference gradient estimation requires \(O(P)\) forward passes for \(P\) parameters. We need an algorithm that computes the entire gradient in \(O(1)\) times the cost of a single forward pass.

### 2.3 The Core Intuition: Don't Repeat Yourself

Consider evaluating a deeply nested mathematical expression:

\[
z = \bigl( f(w) \bigr)^2
\]

You want \(\frac{dz}{dw}\). The chain rule gives:

\[
\frac{dz}{dw} = 2 f(w) \cdot f'(w)
\]

The quantity \(f(w)\) appears twice: as the factor \(2f(w)\) and inside \(f'(w)\). If you compute \(f(w)\) from scratch each time it appears, you do redundant work. In a deep network, this redundancy explodes combinatorially: a single early parameter influences many downstream nodes, and naive application of the chain rule recomputes the same intermediate values along every path.

**Analogy: The orchestra conductor's score.** A naive chain-rule application is like a conductor who, for every single note played by a violinist, re-reads the entire score from page one to understand its context. An experienced conductor, however, reads the score once, internalizing the musical structure. During the performance (the backward pass), they can instantly trace a single note's influence on the finale because they already hold the full harmonic structure in their mind. Backpropagation's forward pass is that single, careful reading; the stored activations are the internalized score, enabling an instantaneous backward trace.

Backpropagation eliminates this redundancy by computing every intermediate value once during the forward pass, storing it, and then reusing those stored values during the backward pass. The runtime becomes proportional to one forward pass plus one backward pass — a small constant factor overhead (typically 2–3× the forward pass cost).

**Cross-domain connection 1: Automatic differentiation in climate models.** The same forward-store-backward pattern powers gradient computation in differentiable climate simulators, where scientists train neural surrogates of physical processes. A climate model might have thousands of coupled differential equations; backpropagation through the solver computes sensitivities to initial conditions without re-running the century-scale simulation for each parameter. The principle is identical: store the trajectory, then reverse through it.

**Cross-domain connection 2: Adjoint methods in computational fluid dynamics.** Decades before backpropagation became synonymous with neural networks, the adjoint method was developed in CFD to compute gradients of an objective function (e.g., drag on an airfoil) with respect to design parameters (e.g., surface shape). The adjoint equation is derived by reversing the flow of the linearized governing equations — the exact analogue of the backward pass. A single adjoint solve provides the full gradient, enabling gradient-based shape optimization for aircraft design.

**Cross-domain connection 3: Bi-level optimization in meta-learning.** In model-agnostic meta-learning (MAML), the outer loop requires gradients through an inner-loop optimization process — effectively, gradients of gradients. Backpropagation through the inner loop's gradient descent steps is implemented by unrolling the computational graph of the inner optimizer and applying the same forward-backward pattern, enabling models to learn how to learn.

---

### ✏️ Test Yourself: Motivation

**Question:** A network has \(P = 5 \times 10^7\) parameters. A single forward pass takes 10 milliseconds. Roughly how long would one step of gradient descent take using finite differences? Using backpropagation? Which one is feasible?

<details>
<summary>Solution</summary>

**Finite differences:** Requires \(P + 1 \approx 5 \times 10^7\) forward passes. At 10 ms each, that is \(5 \times 10^8\) milliseconds = \(5 \times 10^5\) seconds ≈ 139 hours per gradient step. Completely infeasible.

**Backpropagation:** Requires roughly 2–3 forward pass equivalents (one forward, one backward). That is 20–30 milliseconds per gradient step. This is what makes training large models possible.
</details>

---

## 3. Computational Graphs: A Visual Language for Function Composition

### 3.1 Intuition Before Formalism

A neural network is a composition of operations: matrix multiply, add bias, apply activation, repeat. We can represent this composition as a **directed acyclic graph** (DAG) where:

- **Nodes** are variables (inputs, intermediate results, parameters, and the final cost).
- **Edges** point from inputs to the operation that consumes them.

For a simple linear layer \(\mathbf{z} = \mathbf{W}\mathbf{x} + \mathbf{b}\), the graph contains nodes for \(\mathbf{x}\), \(\mathbf{W}\), \(\mathbf{b}\), the intermediate \(\mathbf{W}\mathbf{x}\), and the output \(\mathbf{z}\). The operation \(\mathbf{z} = \mathbf{W}\mathbf{x} + \mathbf{b}\) has three parent nodes: \(\mathbf{x}\), \(\mathbf{W}\), and \(\mathbf{b}\).

**Why a graph?** Because the graph makes explicit something that remains hidden in a chain of equations: *which intermediate results are shared by multiple downstream computations*. When a node has multiple children, its stored value gets reused in multiple local derivative calculations — and the graph shows you exactly where those reuse opportunities live.

### 3.2 Formal Definition

Let the graph have nodes \(\{u^{(1)}, u^{(2)}, \ldots, u^{(n)}\}\) sorted in **topological order**: every edge goes from an earlier node to a later node. The final node \(u^{(n)}\) is the scalar cost \(J\).

For any node \(u^{(i)}\), its value is computed by applying an operation to its **parents** — the nodes with edges pointing into it. We write:

\[
u^{(i)} = f^{(i)}\bigl(\text{Pa}(u^{(i)})\bigr)
\]

The gradient we ultimately want is \(\frac{\partial u^{(n)}}{\partial u^{(i)}}\) for every node that is a parameter.

### 3.3 The Chain Rule on the Graph

The chain rule tells us that a change in an early node propagates to the final cost through *every possible downstream path*. If a node has three children, and each of those has three children, the number of paths grows exponentially with depth — yet backpropagation handles this in linear time. How?

The resolution lies in **dynamic programming**: instead of enumerating paths, we accumulate gradients node by node in reverse order, reusing partial results.

Formally, let \(\bar{u}^{(i)} \equiv \frac{\partial u^{(n)}}{\partial u^{(i)}}\) denote the gradient of the final cost with respect to node \(i\). The chain rule gives:

\[
\bar{u}^{(i)} = \sum_{j: u^{(i)} \in \text{Pa}(u^{(j)})} \bar{u}^{(j)} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

**Interpretation:** The gradient of the final cost with respect to node \(i\) is the sum, over all immediate children \(j\) of node \(i\), of (the gradient signal already computed at child \(j\)) times (the local partial derivative of child \(j\) with respect to node \(i\)).

**Why the sum?** Node \(i\) can influence the final cost through multiple downstream paths. The chain rule adds up all those influences. Each term \(\bar{u}^{(j)} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}\) represents the gradient signal flowing backward along the edge from \(j\) to \(i\).

**Why reverse topological order?** This is where the tension is resolved. If we processed nodes forward, the gradient at a node would depend on its children, whose gradients wouldn't be known yet. By reversing the order, we guarantee that when we process node \(i\), all its children \(j\) have already been processed. Therefore, \(\bar{u}^{(j)}\) is already known for every child \(j\). This simple reversal is the dynamic programming property that guarantees each edge is traversed exactly once, collapsing exponential path enumeration into linear time.

**Try this yourself:** Before reading further, pause and sketch the computational graph for a two-layer network with a skip connection: \(\mathbf{h}_1 = \sigma(\mathbf{W}_1 \mathbf{x} + \mathbf{b}_1)\), \(\mathbf{h}_2 = \sigma(\mathbf{W}_2 \mathbf{h}_1 + \mathbf{b}_2 + \mathbf{W}_{\text{skip}} \mathbf{x})\), \(J = \frac{1}{2}\|\mathbf{h}_2 - \mathbf{y}\|^2\). Identify which node has more than two parents — that is where the sum in the chain rule becomes nontrivial.

---

### ✏️ Quick Check 1: Path Summing

Draw the computational graph for \(z = (x + y) \cdot (x - y)\). Label nodes for \(x, y, x+y, x-y, z\). Write the chain-rule expression for \(\frac{\partial z}{\partial x}\) by summing over the paths through the two children of \(x\). Compute it.

<details>
<summary>Solution</summary>

Graph: \(x\) and \(y\) are leaf nodes. \(u_1 = x+y\) and \(u_2 = x-y\) are children of both \(x\) and \(y\). \(z = u_1 \cdot u_2\) is the final node.

\[
\frac{\partial z}{\partial x} = \frac{\partial z}{\partial u_1} \cdot \frac{\partial u_1}{\partial x} + \frac{\partial z}{\partial u_2} \cdot \frac{\partial u_2}{\partial x} = u_2 \cdot 1 + u_1 \cdot 1 = (x-y) + (x+y) = 2x
\]
</details>

---

### ✏️ Quick Check 2: Same Graph, Different Operation

In the graph above, suppose we change the operation at the final node from multiplication to addition: \(z = u_1 + u_2\). What is \(\frac{\partial z}{\partial x}\) now? Compute it using the same path-summing approach.

<details>
<summary>Solution</summary>

\[
\frac{\partial z}{\partial x} = \frac{\partial z}{\partial u_1} \cdot \frac{\partial u_1}{\partial x} + \frac{\partial z}{\partial u_2} \cdot \frac{\partial u_2}{\partial x} = 1 \cdot 1 + 1 \cdot 1 = 2
\]

The local derivatives \(\frac{\partial z}{\partial u_1}\) and \(\frac{\partial z}{\partial u_2}\) changed from \(u_2\) and \(u_1\) to simply \(1\) and \(1\), but the path structure remains identical.
</details>

---

### ✏️ Quick Check 3: Identifying Shared Nodes

Consider the expression \(J = (w \cdot x + b)^2 + \lambda w^2\). Draw the computational graph. Which node(s) have multiple children? Write the expression for \(\frac{\partial J}{\partial w}\) by summing over paths.

<details>
<summary>Solution</summary>

Graph nodes: \(w, x, b, u_1 = w \cdot x, u_2 = u_1 + b, u_3 = u_2^2, u_4 = w^2, u_5 = \lambda \cdot u_4, J = u_3 + u_5\).

Node \(w\) has two children: it feeds into \(u_1 = w \cdot x\) and into \(u_4 = w^2\). The gradient flows through both paths:

\[
\frac{\partial J}{\partial w} = \underbrace{\frac{\partial J}{\partial u_3} \cdot \frac{\partial u_3}{\partial u_2} \cdot \frac{\partial u_2}{\partial u_1} \cdot \frac{\partial u_1}{\partial w}}_{\text{path through } u_1} \;+\; \underbrace{\frac{\partial J}{\partial u_5} \cdot \frac{\partial u_5}{\partial u_4} \cdot \frac{\partial u_4}{\partial w}}_{\text{path through } u_4}
\]

\[
= 1 \cdot 2u_2 \cdot 1 \cdot x \;+\; 1 \cdot \lambda \cdot 2w = 2(wx + b)x + 2\lambda w
\]

The sum arises because \(w\) influences \(J\) through two independent downstream paths — exactly the pattern backpropagation handles automatically.
</details>

---

## 4. The Backpropagation Algorithm in Two Phases

### 4.1 Phase 1 — Forward Propagation: Compute and Store

We traverse the graph in topological order (input to output). For each node \(u^{(i)}\):

1.  Retrieve the current values of its parents (already computed and stored).
2.  Compute \(u^{(i)} = f^{(i)}(\text{Pa}(u^{(i)}))\).
3.  **Store \(u^{(i)}\)** in memory.

At the end, we have the scalar cost \(J = u^{(n)}\) and every intermediate activation stored.

**Why store everything?** Because during the backward pass, we need these values to evaluate local partial derivatives. For example, the derivative of \(\sigma(z)\) is \(\sigma(z)(1 - \sigma(z))\), which depends on the value of \(\sigma(z)\) computed in the forward pass. Similarly, the derivative of a matrix multiplication with respect to its weights requires the stored activations.

**Analogy: The detective's evidence board.** The forward pass is like a detective visiting a crime scene and meticulously photographing and cataloging every piece of evidence. The backward pass is the later deduction in the office, where the detective draws connections between the suspect (the parameters) and the crime (the error). The detective doesn't need to revisit the scene because every necessary detail is pinned to the board. The stored activations are those photographs, making the chain of causality instantly traceable.

**Memory as the hidden cost.** The tradeoff is explicit: we exchange memory for time. Storing every intermediate activation for a network with \(10^9\) parameters can consume tens of gigabytes. Techniques like **gradient checkpointing** (also called rematerialization) trade memory for computation: instead of storing all activations, we store only a subset (checkpoints) and recompute the others on the fly during the backward pass. This reduces peak memory from \(O(L)\) to \(O(\sqrt{L})\) for an \(L\)-layer network, at the cost of roughly \(1.5\times\) the forward pass computation.

### 4.2 Phase 2 — Backward Propagation: Accumulate Gradients

We now traverse the graph in **reverse topological order** (output back to inputs). We maintain a gradient accumulator for each node:

\[
\bar{u}^{(i)} \equiv \frac{\partial u^{(n)}}{\partial u^{(i)}}
\]

**Initialization:** At the output node, \(\bar{u}^{(n)} = \frac{\partial J}{\partial J} = 1\).

**For each node \(u^{(i)}\) in reverse order:**

We already know the gradient signals \(\bar{u}^{(j)}\) for all its **children** (since children come later in topological order, they are processed earlier in reverse order). We compute:

\[
\bar{u}^{(i)} = \sum_{j \in \text{children}(i)} \bar{u}^{(j)} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

**Key detail:** The local Jacobian \(\frac{\partial u^{(j)}}{\partial u^{(i)}}\) is evaluated using the **stored values** from the forward pass. This is what prevents redundant recomputation.

**A non-obvious framing: Backpropagation as message passing.** You can view each edge in the computational graph as carrying two messages. During the forward pass, the message is the activation value traveling forward. During the backward pass, the message is the gradient signal \(\bar{u}^{(j)} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}\) traveling backward. A node "knows" its total gradient only after it has received backward messages from all its children. This perspective generalizes elegantly to graph neural networks, where message passing over arbitrary graph structures is the core operation — and backpropagation through those message-passing layers itself uses the same two-phase algorithm.

### 4.3