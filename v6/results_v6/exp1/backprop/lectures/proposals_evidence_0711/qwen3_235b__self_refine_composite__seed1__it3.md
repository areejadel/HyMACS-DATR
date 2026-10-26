Why

Now

But

---

### Section 1: Forward Pass — A Concrete Example

Consider a small feedforward neural network with the following specification:

- Input: $\mathbf{x} = [1, 2]^\top$
- One hidden layer with a single neuron using $\tanh$ activation
- One output neuron with identity (linear) activation
- Target output: $y = 1$
- Loss function: Mean squared error $C = \frac{1}{2}(a^{(2)} - y)^2$

Parameters:
- $\mathbf{W}^{(1)} = [0.5, -0.3]^\top$, $b_1 = 0.1$
- $w_2 = 0.4$, $b_2 = 0.2$

We compute the forward pass step by step.

1. **Hidden layer pre-activation**:
   $$
   z^{(1)} = \mathbf{W}^{(1)\top} \mathbf{x} + b_1 = 0.5(1) + (-0.3)(2) + 0.1 = 0.0
   $$

2. **Hidden activation**:
   $$
   a^{(1)} = \tanh(z^{(1)}) = \tanh(0.0) = 0.0
   $$

3. **Output pre-activation**:
   $$
   z^{(2)} = w_2 a^{(1)} + b_2 = 0.4(0.0) + 0.2 = 0.2
   $$

4. **Final output**:
   $$
   a^{(2)} = z^{(2)} \quad \text{(since activation is identity)}
   $$

5. **Loss**:
   $$
   C = \frac{1}{2}(a^{(2)} - y)^2 = \frac{1}{2}(0.2 - 1)^2 = \frac{1}{2}(0.64) = 0.32
   $$

✅ **Try This Yourself**: What is $a^{(1)}$ if $z^{(1)} = 1$?  
Answer: $\tanh(1) \approx 0.7616$. This illustrates the role of activation functions in introducing nonlinearity.

⚠️ **Common Misconception Alert**: The output of a neuron is the activation function applied to the pre-activation. Always compute $a^{(l)} = \sigma^{(l)}(z^{(l)})$, not just $z^{(l)}$.

Having established a concrete forward computation, we now generalize the process.

---

### Section 2: General Forward Pass

Let the network have $L$ layers. For each layer $l = 1, 2, \dots, L$, define:

- $\mathbf{a}^{(l)} \in \mathbb{R}^{n_l}$: post-activation vector
- $\mathbf{W}^{(l)} \in \mathbb{R}^{n_l \times n_{l-1}}$: weight matrix
- $\mathbf{b}^{(l)} \in \mathbb{R}^{n_l}$: bias vector
- $\sigma^{(l)}$: element-wise differentiable activation function
- $\mathbf{z}^{(l)} = \mathbf{W}^{(l)} \mathbf{a}^{(l-1)} + \mathbf{b}^{(l)}$: pre-activation
- $\mathbf{a}^{(l)} = \sigma^{(l)}(\mathbf{z}^{(l)})$: post-activation

Set $\mathbf{a}^{(0)} = \mathbf{x}$. The forward pass proceeds sequentially from $l = 1$ to $L$. The final output $\mathbf{a}^{(L)}$ is compared to target $\mathbf{y}$ via a differentiable cost function $C(\mathbf{a}^{(L)}, \mathbf{y})$. Our goal is to minimize $C$ by adjusting parameters.

---

### Section 3: Gradient-Based Learning

To minimize the loss, we compute partial derivatives of $C$ with respect to each parameter: $\partial C / \partial \mathbf{W}^{(l)}$ and $\partial C / \partial \mathbf{b}^{(l)}$. These gradients indicate how to adjust parameters to reduce $C$.

Computing gradients by finite differences—perturbing each parameter individually—would require $O(N)$ forward passes for $N$ parameters, which is infeasible for large networks.

Backpropagation computes all gradients efficiently in a single backward pass using the **chain rule of calculus**, leveraging the computational graph structure of the forward pass.

The key idea: propagate error signals backward through the network, reusing intermediate derivatives to avoid redundant computation.

---

### Section 4: Error Signals and the Backward Pass

Define the **error signal** (or sensitivity) at layer $l$ as:
$$
\boldsymbol{\delta}^{(l)} = \frac{\partial C}{\partial \mathbf{z}^{(l)}}
$$
This vector measures how a change in pre-activation $\mathbf{z}^{(l)}$ affects the loss $C$. It is central to backpropagation.

We compute $\boldsymbol{\delta}^{(l)}$ recursively, starting from the output layer and proceeding backward. This reverse traversal gives the algorithm its name: *backpropagation*.

Because parameters $\mathbf{W}^{(l)}$ and $\mathbf{b}^{(l)}$ directly influence $C$ only through $\mathbf{z}^{(l)}$, gradients with respect to them depend directly on $\boldsymbol{\delta}^{(l)}$.

We now compute these signals step by step using our earlier example.

---

### Section 5: Output Layer Gradient

From the forward pass:
- $a^{(2)} = 0.2$, $y = 1$, $C = 0.32$

Compute the derivative of the loss:
$$
\frac{\partial C}{\partial a^{(2)}} = a^{(2)} - y = 0.2 - 1 = -0.8
$$

Since the output activation is identity, $a^{(2)} = z^{(2)}$, so:
$$
\frac{\partial a^{(2)}}{\partial z^{(2)}} = 1
$$

Thus:
$$
\delta^{(2)} = \frac{\partial C}{\partial z^{(2)}} = \frac{\partial C}{\partial a^{(2)}} \cdot \frac{\partial a^{(2)}}{\partial z^{(2)}} = (-0.8)(1) = -0.8
$$

In general, for any differentiable output activation $\sigma^{(L)}$:
$$
\boldsymbol{\delta}^{(L)} = \frac{\partial C}{\partial \mathbf{a}^{(L)}} \odot \sigma^{(L)'}(\mathbf{z}^{(L)})
$$
where $\odot$ denotes element-wise multiplication.

✅ **Try This Yourself**: If the output used sigmoid and $z^{(2)} = 0$, what is $\sigma'(z^{(2)})$?  
Answer: $\sigma'(0) = \sigma(0)(1 - \sigma(0)) = 0.5(1 - 0.5) = 0.25$

⚠️ **Common Misconception Alert**: The derivative $\sigma'(z)$ must be included. For linear units, it is 1; for sigmoid or tanh, it varies with $z$. Omitting it leads to incorrect gradients.

---

### Section 6: Hidden Layer Gradient

We now compute $\delta^{(1)} = \partial C / \partial z^{(1)}$. By the chain rule:
$$
\delta^{(1)} = \frac{\partial C}{\partial z^{(2)}} \cdot \frac{\partial z^{(2)}}{\partial a^{(1)}} \cdot \frac{\partial a^{(1)}}{\partial z^{(1)}}
= \delta^{(2)} \cdot w_2 \cdot \tanh'(z^{(1)})
$$

From earlier:
- $\delta^{(2)} = -0.8$
- $w_2 = 0.4$
- $z^{(1)} = 0.0$ → $\tanh'(0) = 1 - \tanh^2(0) = 1 - 0 = 1$

So:
$$
\delta^{(1)} = (-0.8)(0.4)(1) = -0.32
$$

This matches the general formula:
$$
\boldsymbol{\delta}^{(l)} = \left( (\mathbf{W}^{(l+1)})^\top \boldsymbol{\delta}^{(l+1)} \right) \odot \sigma^{(l)'}(\mathbf{z}^{(l)})
$$

In the scalar case: $\delta^{(1)} = w_2 \delta^{(2)} \cdot \sigma'(z^{(1)})$

✅ **Try This Yourself**: What if $w_2 = -0.4$?  
Answer: $\delta^{(1)} = (-0.8)(-0.4)(1) = 0.32$. The sign flip shows how weight signs influence gradient direction.

---

### Section 7: Parameter Gradients

Using $\boldsymbol{\delta}^{(l)}$, we compute gradients for parameters:

$$
\frac{\partial C}{\partial \mathbf{W}^{(l)}} = \boldsymbol{\delta}^{(l)} (\mathbf{a}^{(l-1)})^\top, \quad
\frac{\partial C}{\partial \mathbf{b}^{(l)}} = \boldsymbol{\delta}^{(l)}
$$

**Output layer ($l=2$)**:
- $\frac{\partial C}{\partial w_2} = \delta^{(2)} a^{(1)} = (-0.8)(0.0) = 0$
- $\frac{\partial C}{\partial b_2} = \delta^{(2)} = -0.8$

**Hidden layer ($l=1$)**:
- $\frac{\partial C}{\partial w_{11}} = \delta^{(1)} x_1 = (-0.32)(1) = -0.32$
- $\frac{\partial C}{\partial w_{12}} = (-0.32)(2) = -0.64$
- $\frac{\partial C}{\partial b_1} = \delta^{(1)} = -0.32$

Note: Although $\partial C / \partial w_2 = 0$ (due to $a^{(1)} = 0$), gradients for earlier layers are non-zero. Learning can still occur upstream.

✅ **Try This Yourself**: What if $a^{(1)} = 0.5$? Then $\partial C / \partial w_2 = (-0.8)(0.5) = -0.4$, which is non-zero.

---

### Section 8: Full Backpropagation Algorithm

The backpropagation algorithm proceeds in two phases.

**Forward Pass**:
1. Set $\mathbf{a}^{(0)} = \mathbf{x}$
2. For $l = 1$ to $L$:
   - $\mathbf{z}^{(l)} = \mathbf{W}^{(l)} \mathbf{a}^{(l-1)} + \mathbf{b}^{(l)}$
   - $\mathbf{a}^{(l)} = \sigma^{(l)}(\mathbf{z}^{(l)})$
3. Compute loss $C(\mathbf{a}^{(L)}, \mathbf{y})$

**Backward Pass**:
1. $\boldsymbol{\delta}^{(L)} = \frac{\partial C}{\partial \mathbf{a}^{(L)}} \odot \sigma^{(L)'}(\mathbf{z}^{(L)})$
2. For $l = L-1$ down to $1$:
   - $\boldsymbol{\delta}^{(l)} = \left( (\mathbf{W}^{(l+1)})^\top \boldsymbol{\delta}^{(l+1)} \right) \odot \sigma^{(l)'}(\mathbf{z}^{(l)})$
3. For each $l$:
   - $\frac{\partial C}{\partial \mathbf{W}^{(l)}} = \boldsymbol{\delta}^{(l)} (\mathbf{a}^{(l-1)})^\top$
   - $\frac{\partial C}{\partial \mathbf{b}^{(l)}} = \boldsymbol{\delta}^{(l)}$

This computes all gradients in one backward sweep, reusing activations from the forward pass.

⚠️ **Common Misconception Alert**: The transpose $(\mathbf{W}^{(l+1)})^\top$ is essential. It reverses the direction of gradient flow. Omitting it breaks the algorithm.

---

### Section 9: Computational Efficiency

Without backpropagation, computing gradients via finite differences would require $O(N)$ forward passes for $N$ parameters.

Backpropagation computes all gradients in **one forward pass** and **one backward pass**, with total computation proportional to the forward pass. This yields $O(N)$ time complexity per gradient computation, making deep learning feasible.

This efficiency arises from reverse-mode automatic differentiation: backpropagation is a special case of this general method, applied to computational graphs.

---

### Section 10: Practical Challenges and Mitigations

Despite correct gradients, training deep networks presents challenges:

1. **Vanishing or Exploding Gradients**  
   Long chains of Jacobians can cause gradients to shrink or grow exponentially.  
   ✅ *Mitigation*: Use ReLU activations, Xavier or He initialization, or skip connections (e.g., ResNet).

2. **Saturating Activations**  
   Sigmoid or tanh in saturated regions have near-zero derivatives, halting learning.  
   ✅ *Mitigation*: Prefer ReLU or Leaky ReLU.

3. **Memory Usage**  
   Backpropagation requires storing all activations $\mathbf{a}^{(l)}$ for the backward pass.  
   ✅ *Mitigation*: Use checkpointing—recompute activations during backward pass to reduce memory.

4. **Non-Differentiable Operations**  
   Operations like argmax, sorting, or hard attention break differentiability.  
   ✅ *Mitigation*: Use differentiable approximations (e.g., softmax, Gumbel-Softmax, soft sorting).

5. **Noisy Gradients**  
   Mini-batch gradients are stochastic, leading to high variance.  
   ✅ *Mitigation*: Use adaptive optimizers (e.g., Adam, RMSProp).

---

### Section 11: Limitations and Broader Context

Backpropagation assumes:
- Differentiable operations
- Continuous parameters
- Exact gradient computation

It fails for:
- Discrete decisions (e.g., symbolic reasoning)
- Non-differentiable layers (e.g., sorting in ranking)
- Models with conditional branching

However, backpropagation is not merely an engineering trick. It is a discrete realization of the **adjoint method** from optimal control theory. The forward pass evolves the state; the backward pass computes the co-state (adjoint variable). The transpose $(\mathbf{W}^{(l+1)})^\top$ reflects the dual nature of forward and backward dynamics.

When you call `loss.backward()` in PyTorch or TensorFlow, you invoke a highly optimized implementation of reverse-mode automatic differentiation—assigning credit or blame across millions of parameters with numerical precision.

---

### Section 12: Summary

🔁 **Quick Review**:
1. What is $\boldsymbol{\delta}^{(l)}$?  
   → $\partial C / \partial \mathbf{z}^{(l)}$, the sensitivity of the loss to pre-activations.

2. Why include $\sigma'(z^{(l)})$ in backpropagation?  
   → By the chain rule, gradients must pass through the derivative of the activation function.

3. Why use $(\mathbf{W}^{(l+1)})^\top$?  
   → To reverse the direction of information flow; gradients propagate backward through transposed weights.

4. What is the main advantage of backpropagation?  
   → It computes all gradients in time proportional to the forward pass—$O(N)$ for $N$ parameters.

5. Name one solution to vanishing gradients.  
   → Use ReLU, skip connections, or proper weight initialization.

You now understand not only *how* backpropagation works—from concrete example to formal algorithm—but also *why* it works, and how to avoid common pitfalls in practice.