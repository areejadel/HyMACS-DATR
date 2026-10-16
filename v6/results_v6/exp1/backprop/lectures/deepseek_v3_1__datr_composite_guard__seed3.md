# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

- **Explain** why naive gradient computation is computationally prohibitive for deep networks and how backpropagation resolves this bottleneck.
- **Trace** the flow of gradient signals through a feedforward network’s computational graph using the chain rule in reverse topological order.
- **Derive** the full backpropagation update rules for a two-layer neural network with a scalar cost, including activation-function gating.
- **Diagnose and correct** shape mismatches in gradient computations using dimensional analysis.
- **Relate** hand-derived layerwise formulas to the automatic differentiation (reverse-mode AD) machinery used in modern frameworks.

---

## 1. Why We Need Backpropagation

### 1.1 The Optimization Problem

Here is a puzzle that should bother you: a neural network with 10 million parameters trains in hours on a single GPU. Yet if you tried to estimate the gradient by the most obvious method — tweak one parameter, measure the change in cost, repeat for all 10 million — each gradient computation would require 10 million forward passes. At even 1 millisecond per forward pass, that is nearly three hours for *one* gradient. A single training run would take years. Something radically more efficient must be at work.

Training a neural network means finding weights and biases — collectively denoted \(\boldsymbol{\theta}\) — that minimize a scalar cost function \(J(\boldsymbol{\theta})\). For gradient-based optimizers such as SGD or Adam, we must compute the gradient \(\nabla_{\boldsymbol{\theta}} J\): a vector containing the partial derivative of \(J\) with respect to every parameter.

If the network has \(P\) parameters, a naive finite-difference approximation requires at least \(P+1\) forward passes to estimate the gradient — one per parameter perturbation. For a modern network with millions of parameters, this is impossible. We therefore need an **exact, efficient** gradient computation.

But here is the tension that makes this problem genuinely hard: the function we want to differentiate is a deeply nested composition of hundreds of simple operations. The chain rule guarantees we *can* compute the gradient exactly by multiplying local derivatives along every path from parameters to cost. Yet if we naively traverse all those paths independently, the sheer number of repeated subcomputations explodes. A weight matrix used in layer 1 might influence the cost through \(10^6\) distinct downstream routes — and without a strategy, we'd recompute its contribution \(10^6\) times.

**The resolution:** backpropagation reorganizes the computation so that every intermediate gradient is computed exactly once and reused everywhere upstream. It is not an approximation, not a new learning algorithm — it is the computational engine that makes gradient descent feasible in deep architectures.

**Pause and predict:** Before reading the solution, take 30 seconds to sketch how *you* would avoid recomputing the same sub-gradient a million times. What information would you cache, and in what order would you compute? Your answer will likely anticipate the dynamic programming structure of backpropagation.

### 1.2 The Core Idea: Reverse-Mode Computation

Consider a function built by composing many simple operations. The chain rule from calculus tells us we can compute the derivative of the final output with respect to any intermediate variable by multiplying local derivatives along the computation path. The question is: which order minimizes work?

Backpropagation answers: **start at the cost, and propagate gradients backward through the computation graph.** Every intermediate gradient is computed once and reused wherever it is needed upstream. This is the same algorithmic insight that powers reverse-mode automatic differentiation in every modern deep learning framework.

**Analogy: A factory audit.** Picture a factory with hundreds of assembly stations, each taking parts from upstream stations, transforming them, and passing them downstream. At the end, a quality inspector measures the final product against specifications. Now management asks: "Which upstream stations contributed most to the defect rate, and by how much?" The naive approach — shut down each station individually and measure the output change — would halt production thousands of times. The efficient approach: the inspector hands a "responsibility report" to the final station, which calculates how its own actions contributed to the error, appends its local contribution, and passes the accumulated report backward to every station that fed it. Each station processes reports from all its downstream consumers exactly once. By the time reports reach the raw materials, every station knows its precise contribution — in a single backward sweep.

**Prerequisite Check.** We assume you are comfortable with:

- The chain rule for scalar and vector-valued functions (Section 2 will refresh this).
- Computational graphs as directed acyclic graphs where nodes are operations and edges are data flow.
- Matrix multiplication, transposition, and element-wise (Hadamard) products.
- The anatomy of a feedforward network: input layer, hidden layers with activation functions, output layer, and a scalar cost.

If any term above feels unfamiliar, review it before continuing — the rest of the lecture builds directly on these ideas.

---

## 2. The Chain Rule as the Backbone

### 2.1 Intuition: Local Derivatives and Signal Flow

Think of the computation as an electrical circuit flowing forward from inputs to cost. Each node holds a voltage — the numerical value computed during the forward pass. Now imagine we apply a unit current source at the cost node and ask: *what is the resulting current at each upstream node?* The chain rule answers by multiplying the **local conductance** (the derivative of a node’s output with respect to its input) by the **incoming signal** from downstream.

This is more than a metaphor. In circuit analysis, current divides across parallel branches and sums at junctions — exactly the behavior captured by the multivariable chain rule in Section 2.5. The same summation-over-paths principle governs how gradients accumulate when a node feeds multiple consumers.

**Why this analogy works:** In an electrical network, Kirchhoff’s current law says the sum of currents entering a junction equals the sum leaving. In a computational graph, the multivariable chain rule says the gradient at a node equals the sum of gradient contributions from all its consumers. Both are conservation laws — one for charge, one for sensitivity. Recognizing this parallel turns backpropagation from an abstract algorithm into a physical intuition: gradients flow backward like currents, obeying the same additive rules at every branch point.

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

**Try this yourself:** Before reading further, take a minute to verify the dimensional logic. If \(\mathbf{x} \in \mathbb{R}^m\) and \(z\) is a scalar, \(\nabla_{\mathbf{x}} z\) must have shape \(m \times 1\). The incoming gradient \(\nabla_{\mathbf{y}} z\) has shape \(n \times 1\). What shape must the matrix multiplying it have to produce an \(m \times 1\) output? This simple check — \(m \times 1 = (m \times n)(n \times 1)\) — catches the majority of transpose errors before they propagate.

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

### 2.5 The Multivariable Chain Rule (Sum Over Paths)

In a computational graph, a node \(u^{(j)}\) may influence the final cost \(u^{(n)}\) through multiple downstream consumers. The gradient must sum contributions from all such paths:

\[
\frac{\partial u^{(n)}}{\partial u^{(j)}} = \sum_{i:\, j \in \text{Parents}(u^{(i)})} \frac{\partial u^{(n)}}{\partial u^{(i)}} \frac{\partial u^{(i)}}{\partial u^{(j)}}
\]

This is the **multivariable chain rule**: a node receives gradient signals from every operation that directly uses it, and those signals add.

**Analogy: A river delta.** Imagine a river splitting into multiple channels before reaching the ocean. If you pour a tracer dye at the ocean (the cost) and want to know how much originated from each upstream tributary, you must sum the dye concentration across all channels that connect that tributary to the sea. A node feeding multiple downstream operations is like a river junction — its gradient is the sum of signals returning through every branch.

**Misconception Alert.** A common error is to apply the single-path chain rule when a node feeds into multiple downstream operations. Omitting the sum silently drops entire pathways of influence. Always ask: “Which nodes directly consume this intermediate?” Sum over all of them.

**Quick Check.** In the graph \(a \to b \to d\), \(a \to c \to d\) with \(d = b + c\), write the formula for \(\partial d / \partial a\). *(Answer: \(\frac{\partial d}{\partial a} = \frac{\partial d}{\partial b}\frac{\partial b}{\partial a} + \frac{\partial d}{\partial c}\frac{\partial c}{\partial a}\).)*

---

## 3. Dynamic Programming: Fill the Table Once

### 3.1 The Problem with Naive Recursion

If we recursively applied the chain rule from the cost back to the inputs without caching, we would recompute the gradient at a node every time it is encountered on a different path. In a graph with many shared subexpressions (e.g., a weight matrix used in multiple forward passes), the number of redundant computations grows exponentially with depth.

Think of it like computing Fibonacci numbers recursively without memoization: Fib(100) calls Fib(99) and Fib(98), but Fib(99) independently calls Fib(98) again. The same subproblem is solved exponentially many times. In a neural network, a weight matrix in layer 1 is the "Fib(98)" — reused by every downstream path, yet naively recomputed for each one.

**Try this yourself:** For the Fibonacci analogy, estimate how many times Fib(2) is recomputed when calculating Fib(20) recursively without memoization. The answer (over 4,000 times) reveals why caching matters. Now imagine a weight matrix in a 100-layer network — the redundancy is astronomically worse.

### 3.2 Reverse Topological Ordering

Backpropagation avoids this by treating gradient accumulation as a **dynamic programming** problem. Each node in the computational graph has a memory slot storing its gradient \(\frac{\partial J}{\partial u}\). We fill these slots in **reverse topological order** — from the cost node backward to the inputs. Because a node is processed only after all its consumers have been processed, each local gradient is computed exactly once and then reused wherever it is needed upstream.

**Analogy.** Imagine filling out a spreadsheet where each cell depends on cells to its right. If you fill columns from right to left, every formula references already-computed values. Backpropagation does the same for the computational graph: process nodes in reverse dependency order, and every gradient you need is already in memory. The cost? One forward pass to compute and store all intermediate values, then one backward pass to accumulate gradients — \(O(\text{number of operations})\) total, versus exponential for naive recursion.

**Try this yourself:** Draw a simple computational graph — say \(x \to a = x^2\), \(x \to b = \sin(x)\), and \(y = a + b\). Identify the reverse topological order. Which node must you process first: \(y\), \(a\), \(b\), or \(x\)? Convince yourself that processing \(y\) first gives you the gradient signal needed to compute \(\partial y/\partial a\) and \(\partial y/\partial b\), which then flow to \(x\).

---

## 4. Backpropagation Through a Two-Layer Network

### 4.1 Network Architecture and Notation

We now make everything concrete. Consider a two-layer network:

- **Input:** \(\mathbf{x} \in \mathbb{R}^d\)
- **Hidden layer:** \(\mathbf{h} = \sigma(W^{[1]}\mathbf{x} + \mathbf{b}^{[1]})\), where \(W^{[1]} \in \mathbb{R}^{h \times d}\), \(\mathbf{b}^{[1]} \in \mathbb{R}^h\), and \(\sigma\) is an element-wise activation (e.g., ReLU, sigmoid).
- **Output layer:** \(\hat{\mathbf{y}} = W^{[2]}\mathbf{h} + \mathbf{b}^{[2]} \in \mathbb{R}^k\)
- **Scalar cost:** \(J = \ell(\hat{\mathbf{y}}, \mathbf{y}_{\text{true}})\) for some loss function \(\ell\) (e.g., mean squared error, cross-entropy).

**Real-World Application: Handwritten Digit Classification (MNIST).** Consider the classic problem of classifying \(28 \times 28\) grayscale images into digits 0–9. Here, \(\mathbf{x} \in \mathbb{R}^{784}\) is a flattened image (each pixel intensity scaled to \([0,1]\)). The output layer produces \(\hat{\mathbf{y}} \in \mathbb{R}^{10}\) — a score for each digit class. We train with cross-entropy loss: \(J = -\sum_{c=1}^{10} y_{\text{true},c} \log(\text{softmax}(\hat{\mathbf{y}})_c)\), where \(y_{\text{true}}\) is a one-hot encoding of the true digit. Backpropagation through this network computes the gradient of \(J\) with respect to every weight and bias. A typical architecture uses \(h = 128\) hidden units, yielding \(784 \times 128 + 128 = 100{,}480\) parameters in the first layer and \(128 \times 10 + 10 = 1{,}290\) in the second — over 100,000 parameters total. Training on the full MNIST dataset (60,000 examples) with mini-batch SGD requires computing gradients for roughly 100,000 parameters per batch, repeated over thousands of iterations. Without backpropagation, each gradient computation by finite differences would require 100,001 forward passes per batch — completely infeasible. With backpropagation, a single backward pass computes all 100,000+ gradients in roughly the cost of one forward pass. This is not a theoretical curiosity; it is the reason a modest GPU can train a handwritten digit classifier to 98% accuracy in under a minute.

**Thought experiment:** Before we derive the backward pass equations, estimate the memory cost of storing all forward-pass intermediates for this MNIST network with a batch size of 64. Each intermediate (activations, pre-activations) must be cached. For 100,000+ parameters and 64 samples, are we talking kilobytes, megabytes, or gigabytes? This tension between memory and compute — store everything versus recompute from scratch — is one of the central engineering tradeoffs in deep learning, and we will return to it.

### 4.2 Forward Pass: Store Everything

During the forward pass, we compute and **store** every intermediate: \(\mathbf{x}\), the linear combination \(\mathbf{z}^{[1]} = W^{[1]}\mathbf{x} + \mathbf{b}^{[1]}\), the activation \(\mathbf{h} = \sigma(\mathbf{z}^{[1]})\), \(\mathbf{z}^{[2]} = W^{[2]}\mathbf{h} + \mathbf{b}^{[2]}\), and \(\hat{\mathbf{y}} = \mathbf{z}^{[2]}\) (for simplicity; the output may also pass through an activation, but we absorb it into the loss).

Why store? Because the backward pass needs the *numerical values* of these intermediates to evaluate local derivatives. For instance, if \(\sigma\) is ReLU, its derivative at \(\mathbf{z}^{[1]}\) depends on which entries were positive during the forward pass. Without the cached \(\mathbf{z}^{[1]}\), we cannot compute \(\sigma'\).

**Analogy: A breadcrumb trail.** The forward pass leaves a trail of intermediate values — like breadcrumbs through a forest. The backward pass retraces the path in reverse, and at each step it needs the breadcrumb (the cached value) to determine which direction to go next. Without stored intermediates, the backward pass is navigating blind.

### 4.3 Backward Pass: The Three Gates

The gradient flows backward through three operations: the cost function, the linear transformation, and the activation. Each acts as a **gate** that modulates the incoming signal.

#### Gate 1: The Cost Function

We start with \(\frac{\partial J}{\partial \hat{\mathbf{y}}}\). This is a row vector of shape \(1 \times k\) (or column vector \(k \times 1\), depending on convention — we use column vectors). For mean squared error \(J = \frac{1}{2}\|\hat{\mathbf{y}} - \mathbf{y}_{\text{true}}\|^2\), we have \(\nabla_{\hat{\mathbf{y}}} J = \hat{\mathbf{y}} - \mathbf{y}_{\text{true}}\).

**Case Study: Image Segmentation with Dice Loss.** Consider a medical imaging task — segmenting tumors in CT scans. Here, the network outputs a pixel-wise probability map \(\hat{\mathbf{y}} \in [0,1]^{H \times W}\) indicating tumor presence at each pixel. A common cost function is the Dice loss: \(J = 1 - \frac{2 \sum_i \hat{y}_i y_{\text{true},i} + \epsilon}{\sum_i \hat{y}_i + \sum_i y_{\text{true},i} + \epsilon}\), where \(\epsilon\) is a small constant (e.g., \(10^{-7}\)) for numerical stability. The gradient at the output is:

\[
\frac{\partial J}{\partial \hat{y}_i} = -\frac{2 y_{\text{