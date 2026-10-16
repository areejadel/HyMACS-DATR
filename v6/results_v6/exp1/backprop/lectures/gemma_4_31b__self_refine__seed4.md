# Lecture: Backpropagation in Neural Networks

## Learning Objectives
By the end of this lecture, you will be able to:
1. **Understand** the "Credit Assignment Problem" and the application of the multivariate chain rule to solve it.
2. **Derive** the gradient of a cost function with respect to weights and biases for a single layer.
3. **Implement** the backpropagation recurrence relation to compute gradients across multiple layers.
4. **Analyze** the causes of vanishing and exploding gradients and **select** appropriate mitigation strategies.
5. **Explain** how architectural choices, such as Residual Connections, mathematically preserve gradient flow.

---

## 1. Prerequisites and Conceptual Framework

### The Hook: The "Blame Game" Paradox
Imagine a massive corporate hierarchy where a final product is released and fails catastrophically. The CEO knows the product is wrong, but the failure is the result of thousands of interlocking decisions made by managers, supervisors, and engineers across fifty departments. To fix the product, the CEO cannot simply tell everyone to "do better"; they must pinpoint exactly which specific decision by which specific employee caused the failure. 

This is the **Credit Assignment Problem**. In a neural network, the "product" is the final output $\mathbf{a}^{(L)}$ and the "failure" is the cost $J$. The challenge is that a weight $w$ in the first layer is separated from the cost by millions of other parameters. How do we "blame" a weight in Layer 1 for an error that only manifests at Layer 100? This requires calculating the sensitivity of the cost to that weight: $\frac{\partial J}{\partial w}$.

### The Feedforward Mechanism
To compute gradients backward, we must first define the forward pass. For any layer $l$, the network performs two operations:
1. **Linear Transformation:** $\mathbf{z}^{(l)} = \mathbf{W}^{(l)}\mathbf{a}^{(l-1)} + \mathbf{b}^{(l)}$
2. **Non-linear Activation:** $\mathbf{a}^{(l)} = \sigma(\mathbf{z}^{(l)})$

**Notation Guide:**
- $\mathbf{W}^{(l)}$: Weight matrix.
- $\mathbf{b}^{(l)}$: Bias vector.
- $\mathbf{z}^{(l)}$: Pre-activation (the weighted sum).
- $\mathbf{a}^{(l)}$: Activation (the output after the non-linearity $\sigma$).

### The Objective: Minimizing Cost
We measure error using a cost function $J$. For regression tasks, Mean Squared Error (MSE) is typically used:
$$J = \frac{1}{2} \|\mathbf{a}^{(L)} - \mathbf{y}\|^2$$
We optimize $J$ using **Gradient Descent**, updating parameters $\theta$ in the opposite direction of the gradient:
$$\theta_{t+1} = \theta_t - \eta \nabla_\theta J$$
where $\eta$ is the learning rate.

> **Try this yourself:** If you are training a model and the cost $J$ is increasing instead of decreasing, what is the most likely immediate cause regarding the relationship between $\eta$ and $\nabla_\theta J$?
> *(Answer: The learning rate $\eta$ is likely too high, causing the update to overstep the minimum and diverge).*

---

## 2. The Multivariate Chain Rule

### The Chain Rule Intuition: The Gear Train
Think of a neural network as a series of connected gears. If you turn the first gear (the input), it turns the second, which turns the third, and so on. If the final gear is rotating too slowly, you need to know how much to adjust the size of the first gear to fix the final speed. The total effect is the product of the gear ratios at every step:
$$\frac{\partial C}{\partial A} = \frac{\partial C}{\partial B} \times \frac{\partial B}{\partial A}$$

### Formal Derivation for Weights and Biases
To determine how a specific weight $w_{jk}^{(l)}$ affects the cost $J$, we trace the computational path:
$$w_{jk}^{(l)} \to z_j^{(l)} \to a_j^{(l)} \to J$$

We define the **local error** $\delta_j^{(l)}$ as the sensitivity of the cost to the pre-activation:
$$\delta_j^{(l)} = \frac{\partial J}{\partial z_j^{(l)}}$$

**The Tension:** We cannot calculate $\frac{\partial J}{\partial w}$ directly because $w$ does not touch $J$; it only touches $z$. We must "bridge" this gap using the chain rule.

Using the chain rule, we derive the gradients for the parameters:
1. **For weights:** $\frac{\partial J}{\partial w_{jk}^{(l)}} = \frac{\partial J}{\partial z_j^{(l)}} \cdot \frac{\partial z_j^{(l)}}{\partial w_{jk}^{(l)}}$. Given $z_j^{(l)} = \sum_k w_{jk}^{(l)}a_k^{(l-1)} + b_j^{(l)}$, it follows that $\frac{\partial z_j^{(l)}}{\partial w_{jk}^{(l)}} = a_k^{(l-1)}$.
   $$\frac{\partial J}{\partial w_{jk}^{(l)}} = \delta_j^{(l)} a_k^{(l-1)}$$
2. **For biases:** $\frac{\partial J}{\partial b_j^{(l)}} = \frac{\partial J}{\partial z_j^{(l)}} \cdot \frac{\partial z_j^{(l)}}{\partial b_j^{(l)}}$. Since $\frac{\partial z_j^{(l)}}{\partial b_j^{(l)}} = 1$:
   $$\frac{\partial J}{\partial b_j^{(l)}} = \delta_j^{(l)}$$

### Worked Example: Single-Path Gradient
Consider a network with one input $x$, one hidden neuron, and one output neuron.
- **Path:** $x \xrightarrow{w_1} z_1 \xrightarrow{\sigma} a_1 \xrightarrow{w_2} z_2 \xrightarrow{\sigma} a_2 \xrightarrow{J} \text{Cost}$
- **Assumptions:** $J = \frac{1}{2}(a_2 - y)^2$ and $\sigma(z) = \tanh(z)$, where $\sigma'(z) = 1 - \tanh^2(z)$.

**Step 1: Compute output error $\delta_2$**
$$\delta_2 = \frac{\partial J}{\partial a_2} \cdot \frac{\partial a_2}{\partial z_2} = (a_2 - y) \cdot (1 - a_2^2)$$

**Step 2: Compute hidden error $\delta_1$**
We propagate the error $\delta_2$ backward:
$$\delta_1 = \frac{\partial J}{\partial z_2} \cdot \frac{\partial z_2}{\partial a_1} \cdot \frac{\partial a_1}{\partial z_1} = \delta_2 \cdot w_2 \cdot (1 - a_1^2)$$

**Step 3: Compute weight gradient $\frac{\partial J}{\partial w_1}$**
$$\frac{\partial J}{\partial w_1} = \delta_1 \cdot x$$

> **Technical Note:** $\delta$ is the "error signal" at the pre-activation, not the final gradient. To obtain the gradient for a weight, this signal must be multiplied by the input that entered that weight.

> **Quick Check:** If $a_k^{(l-1)} = 0$, what happens to the gradient of $w_{jk}^{(l)}$ regardless of the value of $\delta_j^{(l)}$?
> *(Answer: The gradient becomes 0; the weight cannot learn if the incoming signal is zero).*

---

## 3. Backpropagation as Dynamic Programming

### Efficiency through Caching
If we calculated the gradient for every weight from scratch, we would re-calculate the same derivatives millions of times. Backpropagation avoids this by treating the network as a graph of dependencies. 

**Analogy:** It is like a relay race. Instead of the finish line runner running back to the start to tell every teammate how they did, the finish line runner tells the person who handed them the baton, who then tells the person who handed it to them. The "message" (the gradient) is passed backward, layer by layer.

**The Vectorized Recurrence Relation:**
The error at layer $l$ is the back-projection of the error from layer $l+1$:
$$\delta^{(l)} = \left( (\mathbf{W}^{(l+1)})^T \delta^{(l+1)} \right) \odot \sigma'(\mathbf{z}^{(l)})$$
where $\odot$ denotes the element-wise (Hadamard) product.

### Memory-Computation Trade-off
To compute $\delta^{(l)}$, the algorithm requires $\mathbf{z}^{(l)}$ and $\mathbf{a}^{(l-1)}$ from the forward pass. Consequently, deep learning frameworks must store a "snapshot" of every neuron's state. Memory consumption scales linearly with network depth and batch size, which is the primary cause of "Out of Memory" (OOM) errors.

---

## 4. General Gradient Computation Algorithm

The training step is executed in four stages:

**Step 1: Forward Pass (Caching)**
For $l = 1 \dots L$:
- Compute $\mathbf{z}^{(l)} = \mathbf{W}^{(l)}\mathbf{a}^{(l-1)} + \mathbf{b}^{(l)}$
- Compute $\mathbf{a}^{(l)} = \sigma(\mathbf{z}^{(l)})$
- Store $\mathbf{z}^{(l)}$ and $\mathbf{a}^{(l)}$ for the backward pass.

**Step 2: Output Layer Error**
$$\delta^{(L)} = \nabla_{\mathbf{a}^{(L)}} J \odot \sigma'(\mathbf{z}^{(L)})$$

**Step 3: Backward Pass (Recursive)**
For $l = L-1, L-2, \dots, 1$:
$$\delta^{(l)} = ((\mathbf{W}^{(l+1)})^T \delta^{(l+1)}) \odot \sigma'(\mathbf{z}^{(l)})$$

**Step 4: Parameter Gradients**
$$\nabla_{\mathbf{W}^{(l)}} J = \delta^{(l)} (\mathbf{a}^{(l-1)})^T, \quad \nabla_{\mathbf{b}^{(l)}} J = \delta^{(l)}$$

> **Try this yourself:** In a network with 100 layers, if you only store the activations for the first and last layers, why does the backward pass fail at layer 99?
> *(Answer: To compute $\delta^{(99)}$, you need $\delta^{(100)}$ and $\mathbf{z}^{(99)}$. Without the cached $\mathbf{z}^{(99)}$, you cannot apply the activation derivative $\sigma'(\mathbf{z}^{(99)})$).*

---

## 5. Numerical Instabilities and Mitigations

### The Root Cause: The Product Chain
The local error $\delta^{(l)}$ is a product of weights and derivatives: $\delta^{(l)} \propto \prod \mathbf{W} \cdot \sigma'$.

**The Tension:** When you multiply many numbers together, the result is extremely sensitive to the magnitude of those numbers. If the average value is $0.9$, after 100 layers, the signal is $0.9^{100} \approx 0.000026$. If it is $1.1$, the signal is $1.1^{100} \approx 13,780$.

1. **Vanishing Gradients:** If weights are small or $\sigma'$ is small (e.g., sigmoid saturation where $\sigma' \approx 0$), the product shrinks exponentially. Early layers receive negligible updates and stop learning.
2. **Exploding Gradients:** If weights are large, the product grows exponentially, leading to numerical overflow ($\text{NaN}$ values).

### Mitigation Matrix
| Problem | Solution | Mechanism |
| :--- | :--- | :--- |
| Vanishing $\sigma'$ | **ReLU Activation** | $\sigma'(z)=1$ for $z>0$; eliminates decay in the activation term. |
| Weight Variance | **He/Xavier Init** | Initializes $\mathbf{W}$ such that signal variance remains constant across layers. |
| Saturation | **Batch Normalization** | Keeps $\mathbf{z}^{(l)}$ within the steep, active region of the activation function. |
| Exploding $\mathbf{W}$ | **Gradient Clipping** | Caps the maximum norm of the gradient to prevent divergent updates. |

---

## 6. Advanced Training Techniques

### Beyond First-Order Gradients
Backpropagation computes the **Jacobian** (first derivative). Second-order methods, such as Newton's Method, use the **Hessian** $\mathbf{H}$ (curvature) to accelerate convergence:
$$\theta_{t+1} = \theta_t - \mathbf{H}^{-1} \nabla_\theta J$$
These are rarely used in deep learning because storing $\mathbf{H}$ requires $\mathcal{O}(W^2)$ space and inverting it requires $\mathcal{O}(W^3)$ time, where $W$ is the number of parameters.

### Industry-Standard Optimizers
- **Momentum:** Uses a moving average of gradients to dampen oscillations and accelerate through local minima.
- **Adam:** Implements adaptive learning rates per parameter based on the first and second moments of the gradients.
- **Mini-batch SGD:** Introduces stochastic noise into the gradient estimate, helping the model escape sharp local minima to improve generalization.

### Architectural Innovation: Residual Connections
In very deep networks, gradients can vanish even when using ReLU. **Residual Connections** modify the output to:
$$\mathbf{a}^{(l)} = \sigma(\mathbf{z}^{(l)}) + \mathbf{a}^{(l-1)}$$

**Mathematical Impact:** 
The derivative of the addition $\frac{\partial}{\partial \mathbf{a}^{(l-1)}}(\dots + \mathbf{a}^{(l-1)})$ is $1$. 

**Analogy:** If a standard network is a series of filters that each potentially block some of the signal, a Residual Connection is a **"bypass valve."** It creates a **"gradient highway,"** allowing the error signal to flow backward to early layers without being attenuated by small weights or derivatives. This allows us to train networks with thousands of layers that would otherwise be mathematically untrainable.