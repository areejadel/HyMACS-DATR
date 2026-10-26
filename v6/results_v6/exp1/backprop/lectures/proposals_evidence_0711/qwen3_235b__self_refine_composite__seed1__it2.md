But

Now

Imagine

Let

---

### Forward Pass

Start

---

### Backward Pass

Here

#### Output Layer ($ \ell = L $)

At

$$
\delta^{(L)} = \frac{\partial C}{\partial a^{(L)}} \odot \sigma'^{(L)}(z^{(L)})
$$

This

$$
\frac{\partial C}{\partial W^{(L)}} = \delta^{(L)} (a^{(L-1)})^T, \quad \frac{\partial C}{\partial b^{(L)}} = \delta^{(L)}
$$

> **Try this yourself**: Compute $ \delta^{(L)} $ for a squared loss and sigmoid output. What happens if $ a^{(L)} $ is very close to 0 or 1? Why does this matter?

#### Hidden Layers ($ \ell = L-1, \dots, 1 $)

Now

$$
\delta^{(\ell)} = \left( W^{(\ell+1)} \right)^T \delta^{(\ell+1)} \odot \sigma'^{(\ell)}(z^{(\ell)})
$$

Think

Then

$$
\frac{\partial C}{\partial W^{(\ell)}} = \delta^{(\ell)} (a^{(\ell-1)})^T, \quad \frac{\partial C}{\partial b^{(\ell)}} = \delta^{(\ell)}
$$

> **Try this yourself**: Suppose $ W^{(\ell+1)} $ is nearly orthogonal and $ \sigma' $ is bounded. What does this imply for $ \|\delta^{(\ell)}\| $? Try estimating it numerically in a two-layer network.

---

### Worked Example

Consider

#### Network Setup

- Input: $ x = [1, 0]^T $, so $ d_0 = 2 $
- Hidden layer: $ d_1 = 1 $, weights $ W^{(1)} = [0.5, -0.5] $, no bias
- Output layer: $ d_2 = 1 $, weight $ W^{(2)} = [2] $, no bias
- Activation: $ \sigma(z) = (1 + e^{-z})^{-1} $
- Cost: $ C = \frac{1}{2}(a^{(2)} - 1)^2 $, target $ y = 1 $
- Approximations: $ \sigma(0.5) \approx 0.6225 $, $ \sigma(1.245) \approx 0.777 $

---

#### Step 1: Forward Pass

Compute

**Layer 1:**
- $ z^{(1)} = W^{(1)} x = 0.5 \cdot 1 + (-0.5) \cdot 0 = 0.5 $
- $ a^{(1)} = \sigma(0.5) \approx 0.6225 $

**Layer 2:**
- $ z^{(2)} = W^{(2)} a^{(1)} = 2 \cdot 0.6225 = 1.245 $
- $ a^{(2)} = \sigma(1.245) \approx 0.777 $

**Cost:**
- $ C = \frac{1}{2}(0.777 - 1)^2 \approx 0.0248 $

Store $ z^{(1)}, a^{(1)}, z^{(2)}, a^{(2)} $ — not because we're sentimental, but because gradients depend on them.

---

#### Step 2: Backward Pass

Start

**Output Layer ($ \ell = 2 $):**

- $ \frac{\partial C}{\partial a^{(2)}} = a^{(2)} - y = 0.777 - 1 = -0.223 $
- $ \sigma'(z^{(2)}) = a^{(2)}(1 - a^{(2)}) = 0.777 \cdot 0.223 \approx 0.173 $
- $ \delta^{(2)} = (-0.223) \cdot 0.173 \approx -0.0386 $
- $ \frac{\partial C}{\partial W^{(2)}} = \delta^{(2)} \cdot a^{(1)} = -0.0386 \cdot 0.6225 \approx -0.0240 $

**Hidden Layer ($ \ell = 1 $):**

- $ (W^{(2)})^T \delta^{(2)} = 2 \cdot (-0.0386) = -0.0772 $
- $ \sigma'(z^{(1)}) = a^{(1)}(1 - a^{(1)}) = 0.6225 \cdot 0.3775 \approx 0.235 $
- $ \delta^{(1)} = -0.0772 \cdot 0.235 \approx -0.0181 $
- $ \frac{\partial C}{\partial W^{(1)}} = \delta^{(1)} \cdot x^T = -0.0181 \cdot [1, 0] = [-0.0181, 0] $

Notice: only the first input neuron contributes to the gradient — a direct consequence of $ x_2 = 0 $. The network "sees" only the first feature.

---

### Gradient Summary

| Parameter | Gradient |
|---------|----------|
| $ W^{(1)} $ | $ [-0.0181, 0] $ |
| $ W^{(2)} $ | $ -0.0240 $ |

Update: $ W \leftarrow W - \eta \frac{\partial C}{\partial W} $

---

### Vanishing and Exploding Gradients

In

But

Now

In

To

> **Try this yourself**: Scale $ W^{(2)} $ to 10. Re-run the backward pass. What happens to $ \delta^{(1)} $? Now set $ W^{(2)} = 0.1 $. What changes?

---

### Gradient Stabilization Strategies

| Problem | Solution |
|--------|--------|
| Vanishing gradients | ReLU, skip connections, proper initialization |
| Exploding gradients | Gradient clipping, reduced learning rate |
| Unstable variance | Batch normalization |
| Non-differentiable ops | Gumbel-Softmax, straight-through estimator |

#### Xavier (Glorot) Initialization

Set

$$
\mathrm{Var}(W_{ij}) = \frac{2}{d_{\ell-1} + d_\ell}
$$

This

Think

---

### Implementation: Memory and Stability

Backprop

#### Checkpointing (Rematerialization)

- Store activations at selected layers.
- Recompute others during backward pass.
- Trade memory $ O(L/k) $ for computation $ O(k) $.

This

#### Sigmoid Gradient Stability

Avoid

```python
def sigmoid_grad_stable(a):
    return a * (1 - a)
```

For

```python
def relu_grad_stable(z):
    return (z > 0).astype(float)
```

> **Try this yourself**: Compute $ \sigma'(z) $ for $ z = 10 $. Now compute it using $ a(1-a) $. What do you get? Now try $ z = -10 $. Why is this a problem?

---

### Theoretical Connection: Adjoint Method

Backprop

For

$$
z_{t+1} = f_t(z_t, \theta_t), \quad C = C(z_T)
$$

Define

$$
\lambda_t = \left( \frac{\partial f_t}{\partial z_t} \right)^T \lambda_{t+1}
$$

This

It

This

---

### Non-Differentiable Operations

Backprop

But

#### Workarounds

1. **Straight-Through Estimator (STE)**  
   Forward: $ y = \mathrm{argmax}(x) $  
   Backward: $ \frac{\partial y}{\partial x} = I $

   Like pretending a brick wall is glass — only works if you don’t look too closely.

2. **Gumbel-Softmax**  
   Replace $ \mathrm{argmax} $ with softmax using Gumbel noise.

   Think of it as voting with weighted dice instead of a single winner.

3. **REINFORCE**  
   $ \nabla_\theta \mathbb{E}[C] = \mathbb{E}[C \nabla_\theta \log p_\theta] $

   A policy gradient method — slower, noisier, but works where gradients can’t go.

> Never assume gradients pass through non-differentiable operations.

---

### Best Practices in Frameworks

PyTorch

#### Key Features

- Dynamic computation graphs (PyTorch)
- Gradient accumulation for large batches
- Mixed precision with loss scaling

#### Common Pitfalls

- ❌ In-place operations: `x += y` breaks autograd — the graph is watching.
- ❌ Accidental detachment: `with torch.no_grad():` — useful, but dangerous if forgotten.

#### Verification

Use `torch.autograd.gradcheck()` to validate custom layers. Try it on a small input — it computes numerical gradients and compares.

> **Try this yourself**: Write a custom sigmoid layer. Run `gradcheck`. Now modify it to be numerically unstable — what happens?

---

### Final Summary

Backpropagation

- The **chain rule** applied recursively,
- Efficient via **error signals** $ \delta^{(\ell)} = \partial C / \partial z^{(\ell)} $,
- Implemented with care for **memory**, **stability**, and **architecture**.

Its

With