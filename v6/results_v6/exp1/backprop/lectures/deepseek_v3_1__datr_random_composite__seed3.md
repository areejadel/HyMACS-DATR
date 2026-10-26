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

Imagine you’re standing on a foggy peak in a mountain range with millions of dimensions. You need to take one step downhill, but you can only feel the slope directly beneath your feet — you can’t see the terrain. To find that slope, you could take a tiny test step in each of the millions of directions, one by one, measuring how much the ground drops each time. That would take years.

This is exactly the situation when training a neural network. We need the gradient of a scalar cost \(J(\boldsymbol{\theta})\) with respect to every one of millions of parameters \(\boldsymbol{\theta}\). A naive finite-difference estimate — perturb each parameter, run the network, measure the change — demands at least \(P+1\) forward passes. For \(P = 10^7\), that’s ten million passes per gradient step. Impossible.

The function we want to differentiate is a deeply nested composition of hundreds of simple operations. The chain rule guarantees we *can* compute the gradient exactly by multiplying local derivatives along every path from parameters to cost. Yet if we naively traverse all those paths independently, the number of repeated subcomputations explodes. A weight matrix used in layer 1 might influence the cost through \(10^6\) distinct downstream routes — and without a strategy, we would recompute its contribution \(10^6\) times.

**The resolution:** backpropagation reorganizes the computation so that every intermediate gradient is computed exactly once and reused everywhere upstream. It is not an approximation, not a new learning algorithm — it is the computational engine that makes gradient descent feasible in deep architectures.

### 1.2 The Core Idea: Reverse-Mode Computation

Consider a function built by composing many simple operations. The chain rule tells us we can compute the derivative of the final output with respect to any intermediate variable by multiplying local derivatives along the computation path. The question is: which order minimizes work?

Backpropagation answers: **start at the cost, and propagate gradients backward through the computation graph.** Every intermediate gradient is computed once and reused wherever it is needed upstream. This is the same algorithmic insight that powers reverse-mode automatic differentiation in every modern deep learning framework.

**A real-world analogy that sticks:** Suppose you manage a global supply chain with thousands of suppliers feeding into factories, which feed into distribution centers, which feed into a final product. One day, the cost of the final product spikes. You need to know which upstream supplier contributed most to that spike — so you can renegotiate or switch. You could trace every possible path from every supplier to the final product independently, but that means revisiting the same factory hundreds of times. Instead, you start at the final product, compute the cost increase per unit of input from each distribution center, then push those numbers back to factories, then to suppliers. Each node is visited exactly once. Backpropagation is supply-chain cost attribution done right — and it scales.

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

**Why this rule is non-negotiable — a thought experiment:** Picture a neuron that sends its output to two different downstream neurons, each contributing to the final cost. If you only follow one path during backpropagation, you’re effectively pretending the other path doesn’t exist. The weight update would ignore half the influence that neuron had on the error. In training, this means the network learns as if it were blind in one eye — it can still see, but depth perception is gone. The sum-over-paths rule restores full depth.

**Misconception Alert.** A common error is to apply the single-path chain rule when a node feeds into multiple downstream operations. Omitting the sum silently drops entire pathways of influence. Always ask: “Which nodes directly consume this intermediate?” Sum over all of them.

**Quick Check.** In the graph \(a \to b \to d\), \(a \to c \to d\) with \(d = b + c\), write the formula for \(\partial d / \partial a\). *(Answer: \(\frac{\partial d}{\partial a} = \frac{\partial d}{\partial b}\frac{\partial b}{\partial a} + \frac{\partial d}{\partial c}\frac{\partial c}{\partial a}\).)*

---

## 3. Dynamic Programming: Fill the Table Once

### 3.1 The Problem with Naive Recursion

If we recursively applied the chain rule from the cost back to the inputs without caching, we would recompute the gradient at a node every time it is encountered on a different path. In a graph with many shared subexpressions (e.g., a weight matrix used in multiple forward passes), the number of redundant computations grows exponentially with depth.

Think of it like computing Fibonacci numbers recursively without memoization: Fib(100) calls Fib(99) and Fib(98), but Fib(99) independently calls Fib(98) again. The same subproblem is solved exponentially many times. In a neural network, a weight matrix in layer 1 is the "Fib(98)" — reused by every downstream path, yet naively recomputed for each one.

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

### 4.2 Forward Pass: Store Everything

During the forward pass, we compute and **store** every intermediate: \(\mathbf{x}\), the linear combination \(\mathbf{z}^{[1]} = W^{[1]}\mathbf{x} + \mathbf{b}^{[1]}\), the activation \(\mathbf{h} = \sigma(\mathbf{z}^{[1]})\), \(\mathbf{z}^{[2]} = W^{[2]}\mathbf{h} + \mathbf{b}^{[2]}\), and \(\hat{\mathbf{y}} = \mathbf{z}^{[2]}\) (for simplicity; the output may also pass through an activation, but we absorb it into the loss).

Why store? Because the backward pass needs the *numerical values* of these intermediates to evaluate local derivatives. For instance, if \(\sigma\) is ReLU, its derivative at \(\mathbf{z}^{[1]}\) depends on which entries were positive during the forward pass. Without the cached \(\mathbf{z}^{[1]}\), we cannot compute \(\sigma'\).

**A memory-for-speed tradeoff you’ve seen before:** This is the same principle as a chef prepping *mise en place* — chopping onions, measuring spices, and laying out every ingredient before the dinner rush. During service, there’s no time to dice garlic mid-recipe. The forward pass is prep; the backward pass is service. You pay in refrigerator space (memory) to save time when it counts.

### 4.3 Backward Pass: The Three Gates

The gradient flows backward through three operations: the cost function, the linear transformation, and the activation. Each acts as a **gate** that modulates the incoming signal.

#### Gate 1: The Cost Function

We start with \(\frac{\partial J}{\partial \hat{\mathbf{y}}}\). This is a column vector of shape \(k \times 1\). For mean squared error \(J = \frac{1}{2}\|\hat{\mathbf{y}} - \mathbf{y}_{\text{true}}\|^2\), we have \(\nabla_{\hat{\mathbf{y}}} J = \hat{\mathbf{y}} - \mathbf{y}_{\text{true}}\).

#### Gate 2: The Linear Transformation

For \(\mathbf{z}^{[2]} = W^{[2]}\mathbf{h} + \mathbf{b}^{[2]}\), the gradient with respect to \(\mathbf{h}\) is:

\[
\frac{\partial J}{\partial \mathbf{h}} = \left( \frac{\partial \mathbf{z}^{[2]}}{\partial \mathbf{h}} \right)^\top \frac{\partial J}{\partial \mathbf{z}^{[2]}} = (W^{[2]})^\top \frac{\partial J}{\partial \mathbf{z}^{[2]}}
\]

**Why the transpose?** The Jacobian \(\frac{\partial \mathbf{z}^{[2]}}{\partial \mathbf{h}}\) is \(W^{[2]}\) itself (since \(\mathbf{z}^{[2]} = W^{[2]}\mathbf{h} + \mathbf{b}^{[2]}\), each output component \(z_i^{[2]}\) depends linearly on \(\mathbf{h}\) with coefficients given by row \(i\) of \(W^{[2]}\)). The incoming gradient is \(k \times 1\). To map to the hidden space of dimension \(h\), we need \(h \times k\) — hence \((W^{[2]})^\top\).

**Dimensional check:** \(W^{[2]} \in \mathbb{R}^{k \times h}\). The incoming gradient \(\nabla_{\mathbf{z}^{[2]}} J\) is \(k \times 1\). The product \((W^{[2]})^\top \nabla_{\mathbf{z}^{[2]}} J\) yields \(h \times 1\), matching \(\nabla_{\mathbf{h}} J\). Correct.

The gradient with respect to \(W^{[2]}\) requires a different VJP. Since each weight \(W_{ij}^{[2]}\) affects exactly one output component \(z_i^{[2]}\) through its connection to \(h_j\), we obtain:

\[
\frac{\partial J}{\partial W^{[2]}} = \frac{\partial J}{\partial \mathbf{z}^{[2]}} \mathbf{h}^\top
\]

**Dimensional check:** \(\nabla_{\mathbf{z}^{[2]}} J\) is \(k \times 1\), \(\mathbf{h}^\top\) is \(1 \times h\). Their outer product is \(k \times h\), matching the shape of \(W^{[2]}\). This is the gradient of a matrix with respect to a scalar — each entry \((i,j)\) is \(\frac{\partial J}{\partial z_i^{[2]}} \cdot h_j\).

**A surprising duality — the transpose appears in one formula, the outer product in another. Why?** Think of \(W^{[2]}\) as playing two different roles at the same party. When gradients flow *through* it to reach \(\mathbf{h}\), it acts as a routing map — the transpose reverses the direction of every connection, sending the signal back along the same wires. When we compute the gradient *of* \(W^{[2]}\) itself, we’re asking: "How much did each wire contribute to the error?" That’s a correlation between the downstream error signal and the upstream activation — an outer product, capturing co-occurrence. Same matrix, two different questions, two different formulas.

#### Gate 3: The Activation Function (Element-wise)

For \(\mathbf{h} = \sigma(\mathbf{z}^{[1]})\), the activation is applied element-wise. The Jacobian \(\frac{\partial \mathbf{h}}{\partial \mathbf{z}^{[1]}}\) is therefore a **diagonal matrix** with \(\sigma'(z_i^{[1]})\) on the diagonal. The VJP becomes an element-wise multiplication:

\[
\frac{\partial J}{\partial \mathbf{z}^{[1]}} = \frac{\partial J}{\partial \mathbf{h}} \odot \sigma'(\mathbf{z}^{[1]})
\]

where \(\odot\) is the Hadamard (element-wise) product. The gradient signal arriving at each hidden unit is gated by the local slope of the activation function at that unit's operating point.

**Why this matters in practice:** If \(\sigma\) is ReLU, \(\sigma'(z) = 1\) for \(z > 0\) and \(0\) otherwise. Units that were inactive during the forward pass receive **zero gradient** in the backward pass — they are dead to the update. If \(\sigma\) is sigmoid, \(\sigma'(z) = \sigma(z)(1-\sigma(z