# Backpropagation in Neural Networks

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember:** State the two phases of backpropagation and identify what is computed and stored in each phase.
2. **Understand:** Explain why naive gradient computation repeats work and how backpropagation avoids it by reusing stored intermediate values.
3. **Apply:** Compute all partial derivatives for a single-hidden-layer network with MSE loss and sigmoid activation, given numerical inputs.
4. **Analyze:** Trace gradient flow through a computational graph, identifying all paths by which a given parameter influences the loss.
5. **Create:** Derive the backpropagation rules for a novel activation function or layer type by expressing it as a computational graph node.

---

## 0. Opening: The Blindfolded Sculptor

Imagine you are a blindfolded sculptor with a million chisels. You strike the marble, remove the blindfold, and check whether the statue looks more like your target. If it does, you remember that chisel angle; if not, you try the opposite next time. Now imagine doing this *for every chisel individually*—striking once, checking, resetting the marble, moving to the next chisel. With a million chisels, you would die before finishing the nose.

This is finite-difference gradient estimation: for \( p \) parameters, we need roughly \( 2p \) complete forward passes through the network. For a modern vision model with \( 10^7 \) parameters performing \( 10^8 \) operations per forward pass, that is \( 2 \times 10^{15} \) operations—roughly the number of seconds since the Big Bang if each operation took one second.

**Pause here.** Before reading on, ask yourself: we *do* train these networks routinely. The math we use—the chain rule—has been known since Leibniz. So what changed? Why did neural networks suddenly become trainable in the 1980s when the underlying calculus was available in the 1680s?

The answer is not about new mathematics. It is about recognizing that the sculptor does not need to start from scratch after each chisel strike. Every intermediate shape the marble took—every contour, every ridge—is information about how each chisel affects the final form. The sculptor simply forgot to take notes.

Backpropagation is the note-taking. It is not a new mathematical idea—the chain rule is centuries old. It is an algorithmic insight about *reuse*: record every intermediate result during the forward pass, then walk backward once, distributing credit and blame. The result: all \( p \) gradients in roughly the cost of two to three forward passes.

**Real-world impact:** This algorithmic efficiency makes modern deep learning possible. In computer vision, backpropagation enables training convolutional networks with hundreds of layers on millions of images. In natural language processing, transformer models with billions of parameters are trained via backpropagation for translation, summarization, and question answering. In scientific computing, backpropagation through neural differential equation solvers learns physical models from observational data. In reinforcement learning, policy gradient methods rely on backpropagation through stochastic computation graphs to train agents that master complex games and robotic control tasks. Each of these applications would be computationally intractable without the \( O(p) \) gradient computation that backpropagation provides.

**Cross-domain connection — Debugging:** If you have ever debugged a program by tracing backward from a crash to its root cause, you have already practiced the core intuition of backpropagation. A segmentation fault at line 500 does not mean the bug is at line 500—it means something upstream corrupted memory. You walk backward through the call stack, asking at each function: "Given that the output was wrong, how much did each input contribute to that wrongness?" The crash is your loss function; the call stack is your computational graph; your blame assignment is the gradient.

---

## 1. Prerequisites

We assume comfort with the following:

**Matrix multiplication and broadcasting:** Multiplying a weight matrix \( \mathbf{W} \in \mathbb{R}^{d_{\text{out}} \times d_{\text{in}}} \) by an input vector \( \mathbf{x} \in \mathbb{R}^{d_{\text{in}}} \), adding a bias vector \( \mathbf{b} \in \mathbb{R}^{d_{\text{out}}} \), and reasoning about the shapes of all intermediate quantities.

**The chain rule from calculus:** If \( y = g(u) \) and \( u = f(x) \), then \( \frac{dy}{dx} = \frac{dy}{du} \cdot \frac{du}{dx} \). For multivariate functions, the chain rule sums over all intermediate paths: if \( z \) depends on \( y_1, \ldots, y_k \), each of which depends on \( x \), then \( \frac{dz}{dx} = \sum_{i=1}^k \frac{\partial z}{\partial y_i} \frac{\partial y_i}{\partial x} \).

**Elementary partial derivatives:** The identity \( \frac{\partial}{\partial \mathbf{W}} (\mathbf{W}\mathbf{x}) = \mathbf{x}^\top \) for a vector input, and the ability to differentiate common activation functions: sigmoid (\( \sigma'(z) = \sigma(z)(1-\sigma(z)) \)), ReLU (\( \phi'(z) = \mathbb{1}[z > 0] \)), and softmax.

**The forward pass of a neural network:** Given an input, the network computes layer outputs sequentially to produce a prediction.

**Self-Check:** If \( \mathbf{z} = \mathbf{W}\mathbf{x} + \mathbf{b} \) with \( \mathbf{x} \in \mathbb{R}^3 \), \( \mathbf{W} \in \mathbb{R}^{2 \times 3} \), and \( \mathbf{b} \in \mathbb{R}^2 \), what is the shape of \( \mathbf{z} \)? What is \( \frac{\partial \mathbf{z}}{\partial \mathbf{W}} \)?

<details>
<summary>Answer</summary>
\( \mathbf{z} \in \mathbb{R}^2 \). \( \frac{\partial \mathbf{z}}{\partial \mathbf{W}} \) is a \( 2 \times (2 \times 3) \) Jacobian. In practice we use the vectorized form: for a scalar loss \( J \), \( \frac{\partial J}{\partial \mathbf{W}} = \frac{\partial J}{\partial \mathbf{z}} \mathbf{x}^\top \), which has shape \( 2 \times 3 \).
</details>

---

## 2. Motivation: Why We Need Backpropagation

### 2.1 The Problem: Gradients at Scale

Training a neural network means adjusting its parameters \( \boldsymbol{\theta} \) to minimize a scalar cost function \( J(\boldsymbol{\theta}) \). The cost measures the discrepancy between predictions and targets. To improve, we need the gradient \( \nabla_{\boldsymbol{\theta}} J \).

Modern networks can have millions or billions of parameters. Computing each partial derivative individually by finite differences—evaluating the network twice per parameter with a small perturbation—is hopelessly slow: for \( p \) parameters, finite differences require \( 2p \) forward passes. We need an algorithm that computes the entire gradient in roughly the same time it takes to compute the cost itself.

**Pause and consider:** If you had to train a network with finite differences, how would the cost scale if you doubled the number of parameters? What about doubling the depth? The answers differ—one multiplies forward passes, the other multiplies operations per pass. Backpropagation handles both gracefully.

### 2.2 Intuition: The Hidden Redundancy

Consider the expression:

\[
z = \bigl( f(w) \bigr)^2
\]

We want \( \frac{dz}{dw} \). The chain rule gives:

\[
\frac{dz}{dw} = 2 f(w) \cdot f'(w)
\]

The quantity \( f(w) \) appears twice—once as the factor \( 2f(w) \) and once inside \( f'(w) \). Computing \( f(w) \) from scratch each time it appears is redundant work. For a single parameter, the waste is trivial. But now imagine a deep network: an early parameter influences hundreds of downstream nodes, and each of those nodes needs that same intermediate value to compute its local derivative. Without a clever strategy, we would recompute the same quantities exponentially many times.

**Analogy — The river delta:** Think of the forward pass as water flowing from a mountain spring (the input) down through tributaries (hidden layers) to the ocean (the loss). The gradient is like saltwater flowing backward up the river. At each fork, the saltwater splits proportionally to the water that came down each branch. To know how to split it, we need to know how much water flowed down each branch during the forward pass. If we did not record the flow rates, we would have to re-measure them—which means sending fresh water down from the spring every time. Backpropagation simply writes down the flow rates as they happen.

**Try this yourself:** Consider a network where a single parameter \( w \) appears in three different hidden units, each of which connects to the output. Draw the computational graph. How many times would a naive gradient computation evaluate the function that produces \( w \)'s immediate output? How many times does backpropagation evaluate it?

<details>
<summary>Reflection</summary>
A naive approach would evaluate \( w \)'s output three separate times—once per downstream path. Backpropagation evaluates it once during the forward pass, stores it, and reuses that stored value for all three paths during the backward pass.
</details>

### 2.3 The Solution: Compute Once, Reuse Many Times

Backpropagation eliminates this redundancy by storing every intermediate value during the forward pass and reusing those stored values during the backward pass. The runtime becomes proportional to one forward pass plus one backward pass—typically only two to three times the cost of the forward pass alone.

**Concrete scale example:** A 50-layer convolutional network on a \( 224 \times 224 \) image performs roughly \( 10^8 \) floating-point operations in the forward pass. With \( 10^7 \) parameters, finite differences would need \( 2 \times 10^7 \) forward passes—a factor of \( 10^7 \) slowdown. Backpropagation computes all \( 10^7 \) gradients in one backward pass of comparable cost, making training feasible.

**Formative Check:** Why does the chain rule applied naively repeat work? Where does the repetition come from?

<details>
<summary>Reflection</summary>
The repetition comes from shared intermediate nodes. When a node \( u \) has multiple children, the chain rule requires \( \frac{\partial u}{\partial \text{input}} \) for each child's local derivative. A naive approach recomputes \( u \) for each child. Backpropagation computes \( u \) once, stores it, and reuses it.
</details>

---

## 3. Computational Graphs: Making Function Composition Visible

### 3.1 Intuition Before Formalism

A neural network is a composition of simple operations: matrix multiply, add bias, apply activation, repeat. We can draw this composition as a **directed acyclic graph** (DAG) where:

- **Nodes** are variables (inputs, intermediate results, parameters, and the final cost).
- **Edges** point from inputs to the operation that consumes them.

For a simple linear layer \( \mathbf{z} = \mathbf{W}\mathbf{x} + \mathbf{b} \), the graph is:

\[
\mathbf{x} \rightarrow [\text{matmul with } \mathbf{W}] \rightarrow \mathbf{W}\mathbf{x} \rightarrow [\text{add } \mathbf{b}] \rightarrow \mathbf{z}
\]

Here \( \mathbf{W}\mathbf{x} \) and \( \mathbf{z} \) are nodes; \( \mathbf{W} \) and \( \mathbf{b} \) are also nodes (parameters we will eventually differentiate with respect to). The operations live on the edges.

Drawing the graph reveals a powerful structural insight: the chain rule becomes a simple message-passing rule. Gradient signals flow backward along the edges, and at each node, incoming signals are summed. The graph is not just a visualization—it is an algorithm specification.

**Cross-domain connection — Electrical circuits:** A computational graph with backpropagation behaves like a resistive network where each node's voltage (forward value) is measured and recorded. Then we inject a unit current at the output node and measure how it distributes backward through the network. The gradient at each node is exactly the current flowing through it. This is not merely an analogy—the same linearity that makes Kirchhoff's current law work (currents sum at junctions) is what makes the chain rule sum over multiple paths. In both cases, the total flowing into a junction must equal the total flowing out, and the distribution among branches depends on the conductances (local derivatives).

**Cross-domain connection — Automatic differentiation in scientific computing:** Backpropagation is a special case of reverse-mode automatic differentiation, a technique used far beyond neural networks. When simulating fluid dynamics, researchers need gradients of a drag coefficient with respect to wing shape parameters. When designing chemical reactors, engineers need gradients of yield with respect to temperature profiles. In each case, the computational graph may involve differential equation solvers, iterative algorithms, or physical simulations—not just matrix multiplications. Backpropagation through these graphs uses exactly the same principles: record the forward computation, then propagate gradients backward. The neural network case is simply the one where the graph structure is particularly regular and deep.

**Cross-domain connection — Compiler optimization:** The computational graph perspective reveals that backpropagation is fundamentally a program transformation. Given a program that computes a scalar output from inputs, reverse-mode automatic differentiation produces a new program that computes the gradient with the same asymptotic complexity. This is why frameworks like PyTorch and TensorFlow are built as compilers: they construct the graph, optimize it (fusing operations, eliminating redundant computations), and then generate efficient backward code. The same dead-code elimination that removes unreachable lines in a compiler removes gradient computations for parameters that do not influence the loss.

### 3.2 Formal Definition

Let the graph have nodes \( \{u^{(1)}, u^{(2)}, \ldots, u^{(n)}\} \) sorted in **topological order**: every edge goes from an earlier node to a later node. The final node \( u^{(n)} \) is the scalar cost \( J \).

For any node \( u^{(i)} \), its value is computed by applying an operation to its **parents**—the nodes with edges pointing into it:

\[
u^{(i)} = f^{(i)}\bigl(\text{Pa}(u^{(i)})\bigr)
\]

Our goal is to compute \( \frac{\partial u^{(n)}}{\partial u^{(i)}} \) for every node that is a parameter.

### 3.3 The Chain Rule on the Graph

The chain rule describes how a change in node \( u^{(i)} \) propagates to the final cost. The influence flows through the children of \( u^{(i)} \):

\[
\frac{\partial u^{(n)}}{\partial u^{(i)}} = \sum_{j:\, u^{(i)} \in \text{Pa}(u^{(j)})} \frac{\partial u^{(n)}}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

**Interpretation:** The gradient of the final cost with respect to node \( i \) is the sum, over all immediate children \( j \) of node \( i \), of (the gradient signal coming into child \( j \)) times (the local derivative of child \( j \) with respect to node \( i \)).

**Why the sum?** Node \( i \) can influence the final cost through multiple downstream paths. The chain rule adds up all those influences. Forgetting to sum is one of the most common implementation errors.

**A non-obvious framing — The credit assignment problem:** What we are really solving is a centuries-old problem in distributed systems: how do you assign credit or blame to each component in a complex pipeline when you only observe the final outcome? This is the same problem faced by a manager evaluating a team where each person's work feeds into the next person's. If the project succeeds, who deserves the bonus? If it fails, who needs retraining? The chain rule gives the mathematically correct answer: each person's contribution is their marginal impact on the final outcome, accounting for all the ways their work flows through the organization. Backpropagation is just the efficient algorithm for computing those marginal impacts when the organization is a feedforward network.

**Misconception Alert:** A common mistake is to think that because we process nodes in reverse order, each node receives gradient from only one child. In reality, a node can have multiple children, and we must sum the gradient signals from all of them. The reverse order simply ensures that when we process node \( i \), all its children have already been processed and their gradient signals are available.

**Try this yourself:** Before reading the next example, sketch the computational graph for \( z = x^2 + xy \). Identify how many paths connect \( x \) to \( z \), and predict whether the gradient formula will contain a sum.

<details>
<summary>Thought process</summary>
The graph has two paths from \( x \) to \( z \): through \( x^2 \) and through \( xy \). The chain rule will sum contributions from both: \( \frac{\partial z}{\partial x} = 2x + y \).
</details>

### 3.4 Worked Example: From Graph to Gradient

Let's apply this to \( z = (x + y) \cdot (x - y) \).

**Step 1: Build the graph.**

- Leaf nodes: \( x, y \)
- Intermediate nodes: \( u_1 = x + y \), \( u_2 = x - y \)
- Output node: \( z = u_1 \cdot u_2 \)

**Step 2: Identify children.** \( x \) has two children: \( u_1 \) and \( u_2 \). \( y \) also has two children: \( u_1 \) and \( u_2 \).

**Step 3: Apply the chain rule for \( \frac{\partial z}{\partial x} \):**

\[
\frac{\partial z}{\partial x} = \frac{\partial z}{\partial u_1} \cdot \frac{\partial u_1}{\partial x} + \frac{\partial z}{\partial u_2} \cdot \frac{\partial u_2}{\partial x}
\]

**Step 4: Compute local derivatives using stored values:**

- \( \frac{\partial z}{\partial u_1} = u_2 = x - y \)
- \( \frac{\partial u_1}{\partial x} = 1 \)
- \( \frac{\partial z}{\partial u_2} = u_1 = x + y \)
- \( \frac{\partial u_2}{\partial x} = 1 \)

**Step 5: Sum:**

\[
\frac{\partial z}{\partial x} = (x - y) \cdot 1 + (x + y) \cdot 1 = 2x
\]

Notice we used the stored values of \( u_1 \) and \( u_2 \)—we did not recompute \( x+y \) or \( x-y \).

**Test Yourself:** Draw the computational graph for \( z = (x + y)^2 \) and compute \( \frac{\partial z}{\partial x} \) using the chain rule on the graph.

<details>
<summary>Solution</summary>
Graph: \( x, y \rightarrow u_1 = x + y \rightarrow z = u_1^2 \).
\( \frac{\partial z}{\partial x} = \frac{\partial z}{\partial u_1} \cdot \frac{\partial u_1}{\partial x} = 2u_1 \cdot 1 = 2(x + y) \).
</details>

---

## 4. The Backpropagation Algorithm: Two Phases, One Gradient

### 4.1 Phase 1 — Forward Propagation: Compute and Store

We traverse the graph in topological order (input to output). For each node \( u^{(i)} \):

1. Retrieve the current values of its parents (already computed and stored).
2. Compute \( u^{(i)} \) using its operation.
3. **Store \( u^{(i)} \)** in memory.

At the end, we have the scalar cost \( J = u^{(n)} \) and every intermediate activation stored.

**Why store everything?** During the backward pass, we need these values to evaluate local derivatives. For example, \( \sigma'(z) = \sigma(z)(1-\sigma(z)) \) requires the value of \( \sigma(z) \), which we computed and stored during the forward pass. The backward pass does not recompute—it looks up.

**The memory tension:** This is the central tradeoff of backpropagation—we exchange memory for time. Storing every activation for a deep network with large feature maps can consume gigabytes.