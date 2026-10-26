---

### 1. Prerequisites

This lecture assumes familiarity with the following concepts:  
- **Matrix and vector operations**, including matrix-vector multiplication and transposition.  
- **Basic calculus**, particularly the chain rule for composite functions.  
- **Neural network components**: layers, weights $W^{(l)}$, biases $b^{(l)}$, activation functions $f^{(l)}$, and cost functions $J$.

If you can compute $\frac{d}{dw} \sin(w^T x)$, you are prepared. If not, review the multivariable chain rule before proceeding.

> **Formative Check (Prerequisites)**  
> Compute $\frac{d}{dw} \left( (w^2 + 1)^3 \right)$.

**Solution**:  
Let $u = w^2 + 1$, so $f = u^3$. Then:  
$$
\frac{df}{dw} = \frac{df}{du} \cdot \frac{du}{dw} = 3u^2 \cdot 2w = 6w(w^2 + 1)^2
$$

---

### 2. Forward Pass: Computing Predictions and Cost — But Why Store Anything?

Imagine you're debugging a neural network, and your cost suddenly explodes. You check the weights—fine. Inputs—normal. Yet something is clearly wrong. What if you could *rewind* the computation, not just see the output, but trace *how* each parameter influenced that outcome?

That’s the hidden power of the forward pass: it doesn’t just predict—it **prepares for accountability**. Every value you compute ($z^{(1)}, h^{(1)}, \hat{y}, J$) is stored not because we’re paranoid, but because we’re about to conduct a forensic audit of influence. The forward pass builds the crime scene; backpropagation finds the culprit.

Let’s ground this in a concrete example.

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
- Output: $\hat{y} = z^{(2)}$ (no activation on output)  
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

All intermediate values—$x$, $z^{(1)}$, $h^{(1)}$, $z^{(2)}$, $\hat{y}$, $J$—are stored. Not because they’re useful now, but because **influence flows forward, but responsibility flows backward**.

> ✅ **Misconception Alert**  
> The forward pass computes only predictions and cost. It does **not** compute gradients. However, it **must store** intermediate activations and pre-activations, which are required during backpropagation.

> **Formative Check (Forward Pass)**  
> Using the same network, what is $h^{(1)}$ if $x = -1$?

**Solution**:  
$z^{(1)} = W^{(1)}(-1) + b^{(1)} = \begin{bmatrix} -1 \\ 1 \end{bmatrix} + \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} -1 \\ 2 \end{bmatrix}$, so  
$h^{(1)} = \text{ReLU}(z^{(1)}) = \begin{bmatrix} 0 \\ 2 \end{bmatrix}$

---

### 3. Computational Graph and Chain Rule Intuition: The Ripple Effect

Suppose you tweak $W^{(1)}_{11}$ slightly. How does that affect the final cost? The effect doesn’t jump directly—it ripples through $z^{(1)}_1$, then $h^{(1)}_1$, then $z^{(2)}$, then $\hat{y}$, and finally $J$. Each step is a transformation, and the total impact is the product of local sensitivities.

This is the **chain rule as causality**: if $A$ affects $B$, and $B$ affects $C$, then $A$ affects $C$—but only through $B$. The computational graph makes this causal chain explicit.

```
x → z¹ → h¹ → z² → ŷ → J
     ↑     ↑         ↑
    W¹    f¹        W²
```

Each node is a transformation; each edge is a dependency. To compute $\frac{\partial J}{\partial W^{(1)}}$, we follow the path:
$$
W^{(1)} \to z^{(1)} \to h^{(1)} \to z^{(2)} \to \hat{y} \to J
$$

By the chain rule:
$$
\frac{\partial J}{\partial W^{(1)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} \cdot \frac{\partial z^{(2)}}{\partial h^{(1)}} \cdot \frac{\partial h^{(1)}}{\partial z^{(1)}} \cdot \frac{\partial z^{(1)}}{\partial W^{(1)}}
$$

But here’s the catch: if we compute this naively, we’d recompute the same partials for every weight. That’s like measuring the same bridge’s length multiple times because it appears in different routes.

**Analogy: Traffic Flow on a One-Way Grid**  
Imagine a city where traffic flows only toward a central stadium (the cost $J$). Each road segment has a capacity (partial derivative). To compute how much a side street (a weight) contributes to stadium congestion, you don’t start from the stadium every time—you work backward, measuring flow at each intersection and reusing it upstream. That’s backpropagation: **reverse-mode automatic differentiation as traffic engineering**.

Backpropagation traverses the graph **backward**, computing and reusing local gradients—this is dynamic programming applied to differentiation.

> ✅ **Misconception Alert**  
> Backpropagation is **not** “reverse chain rule.” It is the **efficient implementation** of the chain rule using memoization: each node’s gradient with respect to $J$ is computed once and reused in upstream computations.

> **Try This Yourself**  
> Sketch the computational graph for $f(w) = \sin(w^T x)^2$. Identify all nodes and edges. Now, without computing, predict how many times $\frac{\partial f}{\partial \sin(w^T x)}$ will be used in the full gradient.

---

### 4. Backward Pass: Computing Gradients via Backpropagation

We now compute gradients step by step, starting from the output and moving backward. Define $\delta^{(l)} = \frac{\partial J}{\partial z^{(l)}}$, the error signal at layer $l$. This $\delta$ is the **gradient of cost with respect to pre-activation**—it answers: *How would changing $z^{(l)}$ change $J$?*

#### Step 1: Output Layer Gradient

Start with the cost derivative:
$$
\frac{\partial J}{\partial \hat{y}} = \hat{y} - y = 4 - 1 = 3
$$

Since $\hat{y} = z^{(2)}$, we have:
$$
\frac{\partial J}{\partial z^{(2)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} = 3 \cdot 1 = 3
$$

Define:
$$
\delta^{(2)} = \frac{\partial J}{\partial z^{(2)}} = 3
$$

This $\delta^{(2)}$ is the seed for all upstream gradients. It’s the **error at the output**, ready to be propagated.

#### Step 2: Gradients for $W^{(2)}$ and $b^{(2)}$

From $z^{(2)} = W^{(2)} h^{(1)} + b^{(2)}$, the gradient of $z^{(2)}$ with respect to $W^{(2)}$ is:
$$
\frac{\partial z^{(2)}}{\partial W^{(2)}} = h^{(1)} \quad \text{(in vectorized form, gradient is outer product)}
$$

Thus:
$$
\frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} \cdot \frac{\partial z^{(2)}}{\partial W^{(2)}} = \delta^{(2)} (h^{(1)})^\top = 3 \cdot \begin{bmatrix} 2 \\ 0 \end{bmatrix}^\top = \begin{bmatrix} 6 & 0 \end{bmatrix}
$$

The gradient with respect to the bias is:
$$
\frac{\partial J}{\partial b^{(2)}} = \delta^{(2)} = 3
$$

> **Insight**: The bias gradient is always $\delta^{(l)}$, because $b^{(l)}$ adds directly to $z^{(l)}$—no input scaling.

#### Step 3: Propagate Error to Hidden Layer

We now compute $\frac{\partial J}{\partial h^{(1)}}$. Since $z^{(2)} = W^{(2)} h^{(1)}$, we have:
$$
\frac{\partial z^{(2)}}{\partial h^{(1)}} = (W^{(2)})^\top
\quad \Rightarrow \quad
\frac{\partial J}{\partial h^{(1)}} = \left( \frac{\partial z^{(2)}}{\partial h^{(1)}} \right)^\top \delta^{(2)} = (W^{(2)})^\top \delta^{(2)}
$$

Substitute values:
$$
\frac{\partial J}{\partial h^{(1)}} = \begin{bmatrix} 2 \\ -1 \end{bmatrix} \cdot 3 = \begin{bmatrix} 6 \\ -3 \end{bmatrix}
$$

Now compute $\frac{\partial J}{\partial z^{(1)}}$. Since $h^{(1)} = \text{ReLU}(z^{(1)})$, the derivative element-wise is:
$$
\frac{\partial h^{(1)}_i}{\partial z^{(1)}_i} =
\begin{cases}
1 & \text{if } z^{(1)}_i > 0 \\
0 & \text{if } z^{(1)}_i < 0
\end{cases}
\quad \text{(We use 0 at } z = 0\text{)}
$$

Given $z^{(1)} = \begin{bmatrix} 2 \\ -1 \end{bmatrix}$, the derivative is $\begin{bmatrix} 1 \\ 0 \end{bmatrix}$.

Using the chain rule:
$$
\frac{\partial J}{\partial z^{(1)}} = \frac{\partial J}{\partial h^{(1)}} \odot \frac{\partial h^{(1)}}{\partial z^{(1)}} = \begin{bmatrix} 6 \\ -3 \end{bmatrix} \odot \begin{bmatrix} 1 \\ 0 \end{bmatrix} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

Define:
$$
\delta^{(1)} = \frac{\partial J}{\partial z^{(1)}} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

**Analogy: Electric Circuit with Switches**  
Think of ReLU as a diode: it conducts gradient (current) only if the pre-activation (voltage) is positive. Here, $z^{(1)}_2 = -1$, so the second neuron is "off"—no gradient flows through it. The gradient $\delta^{(1)}_2 = 0$ is not a mistake; it’s **neural silence**—a neuron that didn’t fire gets no credit or blame.

#### Step 4: Gradients for $W^{(1)}$ and $b^{(1)}$

From $z^{(1)} = W^{(1)} x + b^{(1)}$, we compute:

Gradient with respect to weights:
$$
\frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} \cdot \frac{\partial z^{(1)}}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix} 6 \\ 0 \end{bmatrix} \cdot 2 = \begin{bmatrix} 12 \\ 0 \end{bmatrix}
$$

Gradient with respect to bias:
$$
\frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} = \begin{bmatrix} 6 \\ 0 \end{bmatrix}
$$

> ✅ **Misconception Alert**  
> The gradient $\frac{\partial J}{\partial W^{(l)}}$ is always the **outer product** $\delta^{(l)} (a^{(l-1)})^\top$, where $a^{(l-1)}$ is the activation from the previous layer. This ensures correct dimensionality and captures how each input-weight pair contributed to the error.

> **Try This Yourself**  
> Suppose $x = -1$, so $h^{(1)} = \begin{bmatrix} 0 \\ 2 \end{bmatrix}$. Recompute $\frac{\partial J}{\partial W^{(1)}}$. Which neuron now gets gradient? Why?

---

### 5. The Big Picture: Why Backpropagation Works

Backpropagation is not magic—it’s **systematic credit assignment**. It answers: *Who is responsible for the error?* Not by guessing, but by following the mathematical trail of influence.

The algorithm works because:
- **Gradients are local**: Each node only needs to know its immediate effect on downstream nodes.
- **Computation is reused**: Once $\delta^{(l)}$ is computed, it’s used for all upstream gradients.
- **Order matters**: We go backward because influence flows forward—like rewinding a video to find where a mistake occurred.

This is why deep learning scales: backpropagation turns a combinatorial explosion of partial derivatives into a linear pass.

> **Non-Obvious Insight**:  
> Backpropagation can be viewed as **adjoint method in disguise**—a technique from optimal control and differential equations where you solve a forward system and a backward (adjoint) system to compute sensitivities. This connection allows backpropagation to be generalized to ODE networks and physics-informed models.