**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Remember** the forward and backward pass steps in a neural network and identify the role of each in gradient computation.  
2. **Understand** how the chain rule applies to a computational graph by tracing gradients through a simple example.  
3. **Apply** the backpropagation algorithm to compute gradients for weights and biases in a two-layer neural network.  
4. **Analyze** the structure of a computational graph to determine the order and dependencies of gradient calculations.  
5. **Create** a complete forward and backward pass for a small neural network given inputs, weights, and a cost function.

---

### 1. Prerequisites

This lecture assumes familiarity with:  
- **Matrix and vector operations**, including matrix-vector multiplication and transposition.  
- **Basic calculus**, particularly the chain rule for composite functions.  
- **Neural network components**: layers, weights $W^{(l)}$, biases $b^{(l)}$, activation functions $f^{(l)}$, and cost functions $J$.

If you can compute $\frac{d}{dw} \sin(w^T x)$, you are prepared. If not, review the multivariable chain rule.

> **Formative Check (Prerequisites)**  
> Compute $\frac{d}{dw} \left( (w^2 + 1)^3 \right)$.

**Solution**:  
Let $u = w^2 + 1$, so $f = u^3$. Then:  
$$
\frac{df}{dw} = \frac{df}{du} \cdot \frac{du}{dw} = 3u^2 \cdot 2w = 6w(w^2 + 1)^2
$$

> **Interactive Prompt: Predict the Gradient Path**  
> Sketch $f(w) = (w^2 + 1)^3$. Ask: *If I nudged $w$ slightly, where would that change first appear in the computation?* List the sequence of intermediate values affected—this is the forward path. Now reverse it: that’s your first intuition for backpropagation.

> **Mini-Simulation Challenge: Gradient Echoes**  
> Imagine you're a drop of water flowing down a branching river system from a mountain ($w$) to the sea ($J$). Each junction is a computation. Now reverse time: the sea level drops—how does that signal propagate upstream? Which tributaries feel it first? This is backpropagation: a *reverse flow of sensitivity*, not data.

---

### 2. Forward Pass: Computing Predictions and Cost

The forward pass computes the network’s output and cost. It also stores intermediate values—$z^{(l)}$, $h^{(l)}$, $\hat{y}$, $J$—not for immediate use, but to enable gradient computation during backpropagation. Influence flows forward; responsibility flows backward.

#### Example Network

Consider a two-layer feedforward network:  
- Input: $x = 2$  
- Weights:  
  $$
  W^{(1)} = \begin{bmatrix} 1 \\ -1 \end{bmatrix} \in \mathbb{R}^{2 \times 1},\quad
  W^{(2)} = \begin{bmatrix} 2 & -1 \end{bmatrix} \in \mathbb{R}^{1 \times 2}
  $$  
- Biases:  
  $$
  b^{(1)} = \begin{bmatrix} 0 \\ 1 \end{bmatrix} \in \mathbb{R}^2,\quad
  b^{(2)} = 0 \in \mathbb{R}
  $$  
- Activation function: $\text{ReLU}(z) = \max(0, z)$  
- Output: $\hat{y} = z^{(2)}$ (no activation)  
- Cost function: $J = \frac{1}{2}(\hat{y} - y)^2$, with true label $y = 1$

#### Forward Pass Steps

1. Compute first pre-activation:  
   $$
   z^{(1)} = W^{(1)}x + b^{(1)} = \begin{bmatrix} 1 \\ -1 \end{bmatrix} \cdot 2 + \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} 2 \\ -1 \end{bmatrix}
   $$

2. Apply ReLU activation:  
   $$
   h^{(1)} = \text{ReLU}(z^{(1)}) = \begin{bmatrix} \max(0, 2) \\ \max(0, -1) \end{bmatrix} = \begin{bmatrix} 2 \\ 0 \end{bmatrix}
   $$

3. Compute second pre-activation:  
   $$
   z^{(2)} = W^{(2)} h^{(1)} + b^{(2)} = \begin{bmatrix} 2 & -1 \end{bmatrix} \begin{bmatrix} 2 \\ 0 \end{bmatrix} + 0 = 4
   $$

4. Output prediction:  
   $$
   \hat{y} = z^{(2)} = 4
   $$

5. Compute cost:  
   $$
   J = \frac{1}{2}(4 - 1)^2 = \frac{9}{2} = 4.5
   $$

All intermediate values are stored. The forward pass builds the computational history; backpropagation uses it to assign credit or blame.

> ✅ **Misconception Alert**  
> The forward pass computes predictions and cost. It does **not** compute gradients. However, it **must store** intermediate values for backpropagation.

> **Formative Check (Forward Pass)**  
> Using the same network, what is $h^{(1)}$ if $x = -1$?

**Solution**:  
$z^{(1)} = W^{(1)}(-1) + b^{(1)} = \begin{bmatrix} -1 \\ 1 \end{bmatrix} + \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} -1 \\ 2 \end{bmatrix}$, so  
$h^{(1)} = \text{ReLU}(z^{(1)}) = \begin{bmatrix} 0 \\ 2 \end{bmatrix}$

> **Interactive Prompt: Rewind the Tape**  
> Suppose you could only change one stored value to reduce $J$. Would you pick $z^{(1)}$, $h^{(1)}$, or $z^{(2)}$? Why? This is your first step toward gradient-based thinking.

> **Quiz: Gradient Readiness**  
> Which of these values *must* be saved for backpropagation?  
> A) $W^{(1)}$  
> B) $z^{(1)}$  
> C) $\frac{\partial J}{\partial \hat{y}}$  
> D) $x$  
>  
> *Pause and select before reading on.*  
>  
> **Answer**: B and D. $z^{(1)}$ is needed for local derivatives; $x$ appears in $\frac{\partial z^{(1)}}{\partial W^{(1)}}$. $W^{(1)}$ is already stored as a parameter; $\frac{\partial J}{\partial \hat{y}}$ will be computed during backprop.

---

### 3. Computational Graph and Chain Rule Intuition

A small change in $W^{(1)}_{11}$ affects $J$ through a sequence:  
$W^{(1)}_{11} \to z^{(1)}_1 \to h^{(1)}_1 \to z^{(2)} \to \hat{y} \to J$.  

Each transformation contributes a local derivative. The total effect is the product of these derivatives—this is the chain rule.

The computational graph makes dependencies explicit:

```
x → z¹ → h¹ → z² → ŷ → J
     ↑     ↑         ↑
    W¹    f¹        W²
```

To compute $\frac{\partial J}{\partial W^{(1)}_{11}}$, follow the path:  
$$
W^{(1)}_{11} \to z^{(1)}_1 \to h^{(1)}_1 \to z^{(2)} \to \hat{y} \to J
$$

By the chain rule:  
$$
\frac{\partial J}{\partial W^{(1)}_{11}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} \cdot \frac{\partial z^{(2)}}{\partial h^{(1)}_1} \cdot \frac{\partial h^{(1)}_1}{\partial z^{(1)}_1} \cdot \frac{\partial z^{(1)}_1}{\partial W^{(1)}_{11}}
$$

Computing this naively would repeat work. Instead, backpropagation reuses intermediate gradients—like measuring a bridge’s length once and using it for all routes that cross it.

**Analogy: Traffic Flow on a One-Way Grid**  
Traffic flows toward the stadium ($J$). To compute how a side street ($W^{(1)}$) affects congestion, work backward: measure flow at each intersection and reuse it upstream. Backpropagation is reverse-mode automatic differentiation—dynamic programming for gradients.

**Innovation: Backpropagation as a Biological Echo**  
Consider echolocation in bats: a signal is emitted forward, bounces off targets, and returns as an echo. The bat uses the *time and shape* of the echo to infer the environment. Similarly, the forward pass emits a signal ($x$), which propagates through layers; the backward pass is the echo ($\delta^{(l)}$), carrying information about error back to adjust weights. The farther the obstacle (layer), the more the echo distorts—just as deep gradients vanish or explode. This isn't metaphor: both systems solve inverse problems via signal reflection.

> ✅ **Misconception Alert**  
> Backpropagation is **not** “reverse chain rule.” It is the **efficient implementation** of the chain rule using memoization: each node’s gradient with respect to $J$ is computed once and reused.

> **Try This Yourself**  
> Sketch the computational graph for $f(w) = \sin(w^T x)^2$. Identify all nodes and edges. Predict how many times $\frac{\partial f}{\partial \sin(w^T x)}$ will be used.

> **Interactive Prompt: Simulate Backward Flow**  
> Pick $h^{(1)}_1$. If $J$ increases, which upstream nodes could have caused it? Trace backward paths. Now reverse: if you update $W^{(1)}_{11}$, which downstream nodes feel it? This duality—backward cause, forward effect—is the spine of backpropagation.

> **Real-Time Simulation Prompt: Gradient Ripple**  
> On paper, draw the network as a timeline: left (input) to right (cost). Annotate each node with its value. Now, pick $J$ and ask: *What if $J$ were more sensitive to $\hat{y}$?* Propagate that sensitivity backward manually through each gate. You are simulating the backward pass—*you* are the autodiff engine.

---

### 4. Backward Pass: Computing Gradients via Backpropagation

We compute gradients backward, starting from $J$. Define $\delta^{(l)} = \frac{\partial J}{\partial z^{(l)}}$, the error signal at layer $l$. It measures how $z^{(l)}$ affects $J$.

#### Step 1: Output Layer Gradient

Start with:  
$$
\frac{\partial J}{\partial \hat{y}} = \hat{y} - y = 4 - 1 = 3
$$

Since $\hat{y} = z^{(2)}$:  
$$
\frac{\partial J}{\partial z^{(2)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} = 3 \cdot 1 = 3
$$

Define:  
$$
\delta^{(2)} = \frac{\partial J}{\partial z^{(2)}} = 3
$$

This $\delta^{(2)}$ seeds all upstream gradients.

#### Step 2: Gradients for $W^{(2)}$ and $b^{(2)}$

From $z^{(2)} = W^{(2)} h^{(1)} + b^{(2)}$:  
$$
\frac{\partial z^{(2)}}{\partial W^{(2)}} = h^{(1)} \quad \text{(gradient in vectorized form)}
$$

So:  
$$
\frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} (h^{(1)})^\top = 3 \cdot \begin{bmatrix} 2 \\ 0 \end{bmatrix}^\top = \begin{bmatrix} 6 & 0 \end{bmatrix}
$$

Bias gradient:  
$$
\frac{\partial J}{\partial b^{(2)}} = \delta^{(2)} = 3
$$

> **Insight**: The bias gradient is always $\delta^{(l)}$, because $b^{(l)}$ adds directly to $z^{(l)}$.

#### Step 3: Propagate Error to Hidden Layer

Compute $\frac{\partial J}{\partial h^{(1)}}$:  
$$
\frac{\partial J}{\partial h^{(1)}} = (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix} \cdot 3 = \begin{bmatrix} 6 \\ -3 \end{bmatrix}
$$

Now compute $\frac{\partial J}{\partial z^{(1)}}$. For ReLU:  
$$
\frac{\partial h^{(1)}_i}{\partial z^{(1)}_i} =
\begin{cases}
1 & \text{if } z^{(1)}_i > 0 \\
0 & \text{if } z^{(1)}_i \leq 0
\end{cases}
$$

Given $z^{(1)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix}$, derivative is $\begin{bmatrix} 1 \\ 0 \end{bmatrix}$. So:  
$$
\frac{\partial J}{\partial z^{(1)}} = \frac{\partial J}{\partial h^{(1)}} \odot \frac{\partial h^{(1)}}{\partial z^{(1)}} = \begin{bmatrix} 6 \\ -3 \end{bmatrix} \odot \begin{bmatrix} 1 \\ 0 \end{bmatrix} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

Define:  
$$
\delta^{(1)} = \frac{\partial J}{\partial z^{(1)}} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

**Analogy: Electric Circuit with Switches**  
ReLU acts like a diode: gradient flows only if $z^{(1)}_i > 0$. Here, $z^{(1)}_2 = -1$, so neuron 2 is "off"—no gradient passes. $\delta^{(1)}_2 = 0$ reflects **neural silence**: inactive neurons receive no credit or blame.

**Innovation: Backpropagation as a Legal Chain of Liability**  
Imagine a manufacturing defect in a smartphone. The customer sues the retailer, who traces the fault to the assembler, then to the chipmaker, then to a faulty transistor design. Each party is liable only to their direct supplier—just as each gradient depends only on immediate derivatives. But liability is apportioned: the chipmaker isn’t blamed for the retailer’s markup. Backpropagation is the *contract law* of neural networks: it defines responsibility through direct contractual (computational) links, enforcing local accountability. This framing explains why global changes require distributed updates—no single neuron is "in charge."

#### Step 4: Gradients for $W^{(1)}$ and $b^{(1)}$

From $z^{(1)} = W^{(1)} x + b^{(1)}$:  
$$
\frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix} 6 \\ 0 \end{bmatrix} \cdot 2 = \begin{bmatrix} 12 \\ 0 \end{bmatrix}
$$

$$
\frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

> ✅ **Misconception Alert**  
> The gradient $\frac{\partial J}{\partial W^{(l)}}$ is the outer product $\delta^{(l)} (a^{(l-1)})^\top$, where $a^{(l-1)}$ is the previous layer’s activation. This ensures correct dimensionality and captures input-weight contributions.

> **Try This Yourself**  
> Suppose $x = -1$, so $h^{(1)} = \begin{bmatrix} 0 \\ 2 \end{bmatrix}$. Recompute $\frac{\partial J}{\partial W^{(1)}}$. Which neuron now gets gradient? Why?

> **Interactive Prompt: Gradient Switching**  
> For $x=2$, neuron 1 got all gradient. For $x=-1$, neuron 2 is active. Simulate alternating inputs: *Would both neurons learn equally?* Sketch $\delta^{(1)}$ over time. This is **feature selection through gradient routing**.

> **Quiz: Gradient Gatekeeping**  
> True or False: A ReLU neuron that outputs zero for all training examples can still receive non-zero gradients if its weights are large.  
>  
> *Pause. Reason through $z^{(1)}_i \leq 0 \Rightarrow \partial h_i / \partial z_i = 0$.*  
>  
> **Answer**: False. If output is always zero, gradient is always blocked. This is the **dying ReLU** problem—a real failure mode in practice.

---

### 5. The Big Picture: Why Backpropagation Works

Backpropagation is **systematic credit assignment**. It determines which parameters are responsible for the error by following the mathematical trail of influence.

It works because:  
- **Gradients are local**: Each node computes its contribution using only immediate inputs and outputs.  
- **Computation is reused**: Each $\delta^{(l)}$ is computed once and used for all upstream gradients.  
- **Order is critical**: We traverse backward because influence flows forward—like rewinding a video to find the source of an error.

This efficiency allows deep learning to scale: backpropagation reduces a combinatorial problem to a linear pass.

> **Non-Obvious Insight**:  
> Backpropagation is equivalent to the **adjoint method** from optimal control and differential equations. This connection enables generalizations to ODE networks and physics-informed models.

> **Innovation: Backpropagation in Evolutionary Biology**  
Consider gene regulatory networks: a mutation (weight change) may affect phenotype (output) through a cascade of protein expressions (activations). Natural selection acts like a cost function—favoring organisms with higher fitness. But evolution lacks a backward pass; it can't compute gradients. Instead, it uses random variation and selection—a slow, stochastic approximation to gradient descent. Backpropagation, in contrast, is evolution with a *feedback channel*: it doesn’t guess which gene to mutate—it *calculates* the direction of steepest improvement. This contrast reveals why deep learning learns in hours what took evolution billions of years.

> **Interactive Prompt: Design a Failure Mode**  
> Construct an input or weight configuration where backpropagation fails to update a neuron that should learn. (Hint: consider ReLU and repeated negative pre-activations.) You’ve discovered **vanishing gradient**—a real-world issue that influenced modern architectures like skip connections and batch normalization.

> **Challenge Quiz: Backpropagation Under Constraints**  
> You're training a network on a device with no memory