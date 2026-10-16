## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember:** State why naive gradient computation fails for deep networks and identify the dynamic programming principle that makes backpropagation efficient.
2.  **Understand:** Explain the vector-Jacobian product (VJP) as the core operation of the backward pass and trace how a gradient signal flows through a simple computational graph.
3.  **Apply:** Compute the gradient of a scalar loss with respect to weights and biases in a 2-layer feedforward network by hand, given forward-pass activations.
4.  **Analyze:** Diagnose common backpropagation bugs (transpose errors, missing summation over paths, incorrect activation derivative shapes) using dimensional analysis.
5.  **Create:** Derive the backward-pass equations for a novel activation function or layer type not covered in this lecture.

---

## 1. Why We Need Backpropagation

### 1.1 The Problem: Computing Gradients for Millions of Parameters

Imagine standing at the base of a mountain in complete fog. You need to find the steepest descent path, but you can only feel the slope by taking a step and checking if you went up or down. Now imagine the mountain has 60 million independent dimensions you must test one by one before taking a single step. That is the situation training a neural network without backpropagation.

Training a neural network with \( P \) parameters using gradient descent requires the gradient of the scalar loss \( \mathcal{L} \) with respect to every parameter, \( \nabla_{\boldsymbol{\theta}} \mathcal{L} \).

A naive approach is **finite differences**: perturb each parameter \( \theta_i \) by a small \( \epsilon \), run a forward pass, and estimate \( \frac{\partial \mathcal{L}}{\partial \theta_i} \approx \frac{\mathcal{L}(\theta_i + \epsilon) - \mathcal{L}(\theta_i)}{\epsilon} \). This requires \( P + 1 \) forward passes for a single gradient evaluation.

**Why this fails in practice.** In 2012, AlexNet had approximately 60 million parameters. A single forward pass on the hardware of that era required roughly \( 10^9 \) floating-point operations (FLOPs). A single gradient step using finite differences would therefore require \( 6 \times 10^7 \times 10^9 = 6 \times 10^{16} \) FLOPs. Training for a typical \( 10^5 \) iterations would be impossible. We need a method that computes the exact gradient in time proportional to **one** forward pass, not \( P \) forward passes.

But here is the tension: mathematically, the chain rule already tells us the gradient exists and is computable. The barrier is purely algorithmic — how do we organize the computation so that we do not repeat work? Keep this question in mind as we proceed. The answer will feel almost inevitable once you see it.

**Test yourself 1.1:** A small network has 1,000 parameters. A forward pass takes 1 millisecond. How long would one gradient evaluation take using finite differences? How long using backpropagation (which requires one forward and one backward pass, each ~1 ms)?

<details>
<summary>Solution</summary>
Finite differences: 1,001 forward passes × 1 ms = ~1 second. Backpropagation: 2 passes × 1 ms = 2 milliseconds. The gap widens exponentially as the number of parameters grows.
</details>

---

### 1.2 The Core Insight: Dynamic Programming on a Computation Graph

A neural network's loss function is a composition of many simple operations:

\[
\mathcal{L} = f^{(L)} \circ f^{(L-1)} \circ \cdots \circ f^{(1)}(\mathbf{x}; \boldsymbol{\theta})
\]

The chain rule guarantees that the gradient is computable by multiplying local Jacobians along all paths from parameters to the loss. The problem is **computational, not mathematical**: the computation graph is a directed acyclic graph (DAG) with extensive sharing, but naive recursion treats it as a tree, recomputing shared subexpressions exponentially many times.

**Analogy: Corporate audit.** A CEO asks: "If I had allocated one more dollar to Department A, how would profit change?" You could run a separate simulation for each department (finite differences). Or you could start at profit and work backward: profit depends on revenue and costs; revenue depends on sales and price; sales depends on marketing. At each step, you compute the sensitivity of profit to an intermediate quantity **once**, then pass it to every upstream department that feeds into it. The total sensitivity of profit to marketing spend is the sum of sensitivities along all influence paths. Backpropagation performs exactly this audit, in reverse order, computing each intermediate sensitivity exactly once.

**Analogy: Electrical circuit sensitivities.** Consider a resistor network where you want to know how the output voltage changes with respect to every resistor value. You could tweak each resistor individually and remeasure — or you could apply Tellegen's theorem, which lets you compute all sensitivities in one reverse pass by injecting a unit current at the output and measuring voltages across each resistor. Backpropagation is the computational equivalent: inject the gradient signal at the output and let it propagate backward through the network, accumulating contributions at each parameter.

**Dynamic programming formulation.** Backpropagation is **reverse-mode automatic differentiation**: compute \( \frac{\partial \mathcal{L}}{\partial v} \) for each node \( v \) exactly once, store the result, and reuse it for all upstream dependencies. This reduces the computational cost from \( O(\text{number of paths}) \)—which grows combinatorially with depth—to \( O(\text{number of operations}) \), proportional to the forward pass.

**Try this yourself:** Before reading further, sketch a simple computation graph where one intermediate value is used by three different downstream operations. Mentally trace how many times a naive recursive gradient computation would visit that node versus how many times backpropagation visits it. The answer should convince you that caching is not optional — it is the entire algorithm.

---

### 1.3 Prerequisites and Notation

Before proceeding, ensure you are comfortable with:

- **Chain rule (scalar):** If \( y = f(x) \) and \( z = g(y) \), then \( \frac{dz}{dx} = \frac{dz}{dy} \cdot \frac{dy}{dx} \).
- **Chain rule (vector):** If \( \mathbf{y} = f(\mathbf{x}) \) and \( z = g(\mathbf{y}) \), then \( \nabla_{\mathbf{x}} z = \left( \frac{\partial \mathbf{y}}{\partial \mathbf{x}} \right)^\top \nabla_{\mathbf{y}} z \).
- **Matrix operations:** Matrix multiplication, transposition, and the Hadamard (element-wise) product \( \odot \).
- **Feedforward network anatomy:** Input layer, hidden layers with activation functions, output layer, and scalar loss.

**Notation conventions used throughout:**

| Symbol | Meaning | Shape |
|--------|---------|-------|
| \( \mathbf{a}^{(l)} \) | Pre-activation vector at layer \( l \) | \( n_l \times 1 \) |
| \( \mathbf{h}^{(l)} \) | Activation vector at layer \( l \) | \( n_l \times 1 \) |
| \( \mathbf{W}^{(l)} \) | Weight matrix from layer \( l-1 \) to \( l \) | \( n_l \times n_{l-1} \) |
| \( \mathbf{b}^{(l)} \) | Bias vector at layer \( l \) | \( n_l \times 1 \) |
| \( \sigma^{(l)}(\cdot) \) | Activation function at layer \( l \) | Element-wise |
| \( \boldsymbol{\delta}^{(l)} \) | Gradient of \( \mathcal{L} \) w.r.t. \( \mathbf{a}^{(l)} \) | \( n_l \times 1 \) |
| \( \mathcal{L} \) | Scalar loss function | Scalar |

**Input layer convention:** \( \mathbf{h}^{(0)} = \mathbf{x} \), the input to the network.

---

## 2. The Chain Rule as the Engine of Backpropagation

### 2.1 Scalar Chain Rule Refresher

For scalar functions \( y = f(x) \) and \( z = g(y) \):

\[
\frac{dz}{dx} = \frac{dz}{dy} \cdot \frac{dy}{dx}
\]

- \( \frac{dz}{dy} \) is the **downstream gradient signal** arriving at \( y \).
- \( \frac{dy}{dx} \) is the **local sensitivity** of \( y \) with respect to \( x \).
- The product propagates the signal one step backward.

**Worked example.** Let \( y = x^2 \) and \( z = \sin(y) \). Compute \( \frac{dz}{dx} \) at \( x = 3 \).

*Forward pass:* \( y = 3^2 = 9 \), \( z = \sin(9) \approx 0.412 \).

*Local derivatives:* \( \frac{dy}{dx} = 2x = 6 \), \( \frac{dz}{dy} = \cos(y) = \cos(9) \approx -0.911 \).

*Backward pass:* \( \frac{dz}{dx} = \frac{dz}{dy} \cdot \frac{dy}{dx} = (-0.911) \times 6 \approx -5.467 \).

*Direct verification:* \( z = \sin(x^2) \), so \( \frac{dz}{dx} = \cos(x^2) \cdot 2x = \cos(9) \cdot 6 \approx -5.467 \). ✓

**Critical observation:** Computing \( \frac{dz}{dy} = \cos(y) \) requires the forward-pass value \( y = 9 \). This is why backpropagation must store (or recompute) intermediate activations. The forward pass is not just computation — it is building the data that the backward pass will need.

**Test yourself 2.1:** Let \( u = e^{2x} \) and \( \mathcal{L} = \ln(u) \). Compute \( \frac{d\mathcal{L}}{dx} \) at \( x = 1 \) using the chain rule, then verify by direct simplification.

<details>
<summary>Solution</summary>
Forward: \( u = e^{2} \approx 7.389 \), \( \mathcal{L} = \ln(e^2) = 2 \).
Local derivatives: \( \frac{du}{dx} = 2e^{2x} \), \( \frac{d\mathcal{L}}{du} = \frac{1}{u} \).
Backward: \( \frac{d\mathcal{L}}{dx} = \frac{1}{u} \cdot 2e^{2x} = \frac{2e^{2x}}{e^{2x}} = 2 \).
Direct: \( \mathcal{L} = \ln(e^{2x}) = 2x \), so \( \frac{d\mathcal{L}}{dx} = 2 \). ✓
</details>

---

### 2.2 The Vector-Jacobian Product (VJP): The Core Operation

When intermediates are vectors, the chain rule operates via the **vector-Jacobian product (VJP)**. Let \( \mathbf{x} \in \mathbb{R}^m \), \( \mathbf{y} = f(\mathbf{x}) \in \mathbb{R}^n \), and \( z = g(\mathbf{y}) \in \mathbb{R} \). Then:

\[
\nabla_{\mathbf{x}} z = \left( \frac{\partial \mathbf{y}}{\partial \mathbf{x}} \right)^\top \nabla_{\mathbf{y}} z
\]

where \( \frac{\partial \mathbf{y}}{\partial \mathbf{x}} \) is the \( n \times m \) Jacobian matrix with entries \( \left[ \frac{\partial \mathbf{y}}{\partial \mathbf{x}} \right]_{ij} = \frac{\partial y_i}{\partial x_j} \).

**Why the transpose? A geometric perspective.** The Jacobian \( \frac{\partial \mathbf{y}}{\partial \mathbf{x}} \) maps perturbations in \( \mathbf{x} \) to perturbations in \( \mathbf{y} \): \( d\mathbf{y} = \frac{\partial \mathbf{y}}{\partial \mathbf{x}} d\mathbf{x} \). But gradients live in the dual space: \( \nabla_{\mathbf{x}} z \) tells us how a change in \( \mathbf{x} \) affects \( z \), which requires pulling back the gradient from \( \mathbf{y} \)-space to \( \mathbf{x} \)-space. Linear algebra dictates that pulling back covectors requires the transpose. If this feels abstract, the dimensional analysis below gives you a concrete, error-proofing check that works without full geometric intuition.

**Dimensional analysis as a debugging tool.** The incoming gradient \( \nabla_{\mathbf{y}} z \) has shape \( n \times 1 \). The upstream gradient \( \nabla_{\mathbf{x}} z \) must have shape \( m \times 1 \). Therefore, the matrix multiplying \( \nabla_{\mathbf{y}} z \) must have shape \( m \times n \). The Jacobian \( \frac{\partial \mathbf{y}}{\partial \mathbf{x}} \) has shape \( n \times m \), so its transpose—shape \( m \times n \)—is required. This dimensional check (\( m \times 1 = (m \times n)(n \times 1) \)) catches the majority of transpose errors before they propagate into code.

**Worked example: full VJP computation.** Let \( \mathbf{x} = [x_1, x_2]^\top \). Define:

\[
y_1 = 3x_1 + x_2, \quad y_2 = x_1^2, \quad z = y_1 + 2y_2
\]

Compute \( \nabla_{\mathbf{x}} z \) at \( \mathbf{x} = [2, -1]^\top \) using the VJP.

*Step 1 — Forward pass:*
\[
y_1 = 3(2) + (-1) = 5, \quad y_2 = 2^2 = 4, \quad z = 5 + 2(4) = 13
\]

*Step 2 — Downstream gradient:*
\[
\nabla_{\mathbf{y}} z = \begin{bmatrix} \frac{\partial z}{\partial y_1} \\ \frac{\partial z}{\partial y_2} \end{bmatrix} = \begin{bmatrix} 1 \\ 2 \end{bmatrix}
\]

*Step 3 — Jacobian of \( \mathbf{y} \) w.r.t. \( \mathbf{x} \):*
\[
\frac{\partial \mathbf{y}}{\partial \mathbf{x}} =
\begin{bmatrix}
\frac{\partial y_1}{\partial x_1} & \frac{\partial y_1}{\partial x_2} \\
\frac{\partial y_2}{\partial x_1} & \frac{\partial y_2}{\partial x_2}
\end{bmatrix}
= \begin{bmatrix} 3 & 1 \\ 2x_1 & 0 \end{bmatrix}
= \begin{bmatrix} 3 & 1 \\ 4 & 0 \end{bmatrix}
\]

*Step 4 — VJP (transpose and multiply):*
\[
\nabla_{\mathbf{x}} z =
\begin{bmatrix} 3 & 4 \\ 1 & 0 \end{bmatrix}
\begin{bmatrix} 1 \\ 2 \end{bmatrix}
= \begin{bmatrix} 3(1) + 4(2) \\ 1(1) + 0(2) \end{bmatrix}
= \begin{bmatrix} 11 \\ 1 \end{bmatrix}
\]

*Step 5 — Verify by direct differentiation:*
\[
z = 3x_1 + x_2 + 2x_1^2 \implies \frac{\partial z}{\partial x_1} = 3 + 4x_1 = 3 + 8 = 11, \quad \frac{\partial z}{\partial x_2} = 1
\]
✓ Results match.

**Key insight:** We never explicitly formed the full Jacobian matrices for large layers. In practice, we directly compute the VJP for each operation without materializing the Jacobian. For example, if \( \mathbf{y} = \mathbf{W}\mathbf{x} \), the VJP is \( \mathbf{W}^\top \nabla_{\mathbf{y}} z \), computed as a matrix-vector product. This is why backpropagation is fast: we never build the Jacobian, only its product with a vector.

**Test yourself 2.2:** Let \( \mathbf{x} = [x_1, x_2]^\top \), \( \mathbf{y} = [x_1 + 2x_2, \, x_1 x_2]^\top \), and \( z = 3y_1 - y_2 \). Compute \( \nabla_{\mathbf{x}} z \) at \( \mathbf{x} = [1, 2]^\top \) using the VJP method.

<details>
<summary>Solution</summary>
Forward: \( y_1 = 1 + 2(2) = 5 \), \( y_2 = 1 \cdot 2 = 2 \), \( z = 3(5) - 2 = 13 \).
Downstream: \( \nabla_{\mathbf{y}} z = [3, -1]^\top \).
Jacobian: \( \frac{\partial \mathbf{y}}{\partial \mathbf{x}} = \begin{bmatrix} 1 & 2 \\ x_2 & x_1 \end{bmatrix} = \begin{bmatrix} 1 & 2 \\ 2 & 1 \end{bmatrix} \).
VJP: \( \nabla_{\mathbf{x}} z = \begin{bmatrix} 1 & 2 \\ 2 & 1 \end{bmatrix}^\top \begin{bmatrix} 3 \\ -1 \end{bmatrix} = \begin{bmatrix} 1 & 2 \\ 2 & 1 \end{bmatrix} \begin{bmatrix} 3 \\ -1 \end{bmatrix} = \begin{bmatrix} 3 - 2 \\ 6 - 1 \end{bmatrix} = \begin{bmatrix} 1 \\ 5 \end{bmatrix} \).
Direct: \( z = 3(x_1 + 2x_2) - x_1 x_2 = 3x_1 + 6x_2 - x_1 x_2 \). \( \frac{\partial z}{\partial x_1} = 3 - x_2 = 1 \), \( \frac{\partial z}{\partial x_2} = 6 - x_1 = 5 \). ✓
</details>

---

### 2.3 The Multivariable Chain Rule: Summing Over All Paths

In a computation graph, a node may influence the loss through multiple downstream consumers. The gradient with respect to that node is the **sum** of contributions from all such paths:

\[
\frac{\partial \mathcal{L}}{\partial u^{(j)}} = \sum_{i:\, j \in \text{Parents}(u^{(i)})} \frac{\partial \mathcal{L}}{\partial u^{(i)}} \frac{\partial u^{(i)}}{\partial u^{(j)}}
\]

**Common misconception:** "I can just follow one path from the loss back to my parameter." This is incorrect when a node feeds into multiple downstream operations. Changing that node affects the loss through **all** downstream paths simultaneously, and the chain rule requires summing those effects.

**Worked example: summation over paths.** Let \( a = 2 \), \( b = a^2 \), \( c = a^3 \), and \( d = b + c \). Compute \( \frac{\partial d}{\partial a} \).

*Identify all paths from \( a \) to \( d \):*
- Path 1: \( a \to b \to d \): \( \frac{\partial d}{\partial b} \frac{\partial b}{\partial a} = 1 \cdot 2a = 2a \)
- Path 2: \( a \to c \to d \): \( \frac{\partial d}{\partial c} \frac{\partial c}{\partial a} = 1 \cdot 3a^2 = 3a^2 \)

*Sum contributions:* \( \frac{\partial d}{\partial a} = 2a + 3a^2 \). At \( a = 2 \): \( 4 + 12 = 16 \).

*Direct verification:* \( d = a^2 + a^3 \), so \( \frac{\partial d}{\partial a} = 2a + 3a^2 \). At \( a = 2 \): \( 4 + 12 = 16 \). ✓

**Analogy: River delta.** A pollutant introduced at a single point in a river delta reaches the ocean via