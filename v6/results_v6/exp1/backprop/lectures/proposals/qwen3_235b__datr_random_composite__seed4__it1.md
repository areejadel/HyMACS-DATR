- Compute partial derivatives of the loss with respect to weights, biases, and pre-activations in a multi-layer neural network using the chain rule.
- Explain how gradients propagate backward through activation functions and linear transformations, and interpret the meaning of the error signal $\delta^{(l)}$.
- Apply the backpropagation algorithm to a concrete two-layer network, computing all gradients step by step.
- Analyze how network architecture (e.g., activation function choice, residual connections) affects gradient flow and training dynamics.
- Predict and diagnose common training issues (e.g., vanishing gradients) based on backpropagation mechanics.

---

### Prerequisites

Before we begin, ensure you are comfortable with:

- Matrix-vector multiplication and transpose.
- Basic calculus: derivatives, chain rule.
- The structure of a feedforward neural network: layers, weights, biases, activations, and loss.

We’ll build on these to understand how neural networks "learn" by adjusting parameters to reduce error.

> **Quick Check (Prerequisites)**  
> Compute $\frac{d}{dx}(2x + 1)^2$ using the chain rule.  
> *(Answer: $2(2x+1) \cdot 2 = 8x + 4$)*

---

### Intuition First: A Concrete Example

Let’s start with a real scenario before introducing formalism.

Imagine you're training a small neural network to predict house prices. Your model has two layers:

- Input: size and number of bedrooms.
- Hidden layer with $\tanh$ activation.
- Output: predicted price (linear).
- Loss: squared difference from true price.

After one forward pass, the model predicts \$300k, but the true price is \$250k — it’s off by \$50k. The loss is high.

Now, you want to **adjust the weights** so the next prediction is better. But which weights are most responsible? The ones in the first layer? The second? And by how much should each be changed?

Backpropagation answers this by:

1. **Tracing backward** from the loss, through each layer,
2. **Quantifying contribution** using derivatives,
3. **Assigning blame** via the chain rule.

Just like figuring out which mechanic made a mistake in building a car by starting at the broken car and working backward.

Let’s walk through this step by step.

---

### Step 1: Forward Pass and the Computational Graph

We define a two-layer network:

- Input: $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $
- Hidden layer:
  $$
  z^{(1)} = W^{(1)}x + b^{(1)}, \quad a^{(1)} = \tanh(z^{(1)})
  $$
- Output layer:
  $$
  z^{(2)} = W^{(2)}a^{(1)} + b^{(2)}, \quad \hat{y} = z^{(2)}
  $$
- Loss:
  $$
  J = \frac{1}{2}(y - \hat{y})^2
  $$

During the forward pass, we compute and **cache** intermediate values: $z^{(1)}, a^{(1)}, z^{(2)}$. Why? Because derivatives depend on them — for example, $\frac{d}{dz}\tanh(z) = 1 - \tanh^2(z)$, which requires the value of $z$.

This is the **memory-speed tradeoff**: store intermediates to avoid recomputing them during backprop.

> **Worked Example (Forward Pass)**  
> Given:
> - $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $
> - $ W^{(1)} = \begin{bmatrix}1 & 1 \\ -1 & 1\end{bmatrix} $
> - $ b^{(1)} = \begin{bmatrix}0 \\ 0\end{bmatrix} $
>
> Compute:
> $$
> z^{(1)} = W^{(1)}x = \begin{bmatrix}1\cdot1 + 1\cdot0 \\ -1\cdot1 + 1\cdot0\end{bmatrix} = \begin{bmatrix}1 \\ -1\end{bmatrix}
> $$
> $$
> a^{(1)} = \tanh(z^{(1)}) = \begin{bmatrix}\tanh(1) \\ \tanh(-1)\end{bmatrix} \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix}
> $$

> **Formative Check (Forward Pass)**  
> Now suppose $W^{(2)} = \begin{bmatrix}2 & -1\end{bmatrix}, b^{(2)} = 0$. Compute $z^{(2)}$ and $\hat{y}$.  
> *(Answer: $z^{(2)} = 2(0.762) + (-1)(-0.762) = 1.524 + 0.762 = 2.286$, $\hat{y} = 2.286$)*

> **Misconception Alert**  
> *“The forward pass only matters for prediction.”*  
> No — it’s essential for backprop. Without caching $z^{(1)}$, we cannot compute $\tanh'(z^{(1)})$. The forward pass prepares the data needed to assign credit or blame.

---

### Step 2: Backward Pass — Gradient Computation via Chain Rule

Now we go backward, layer by layer, computing gradients.

We define the **error signal** at layer $l$:
$$
\delta^{(l)} = \frac{\partial J}{\partial z^{(l)}}
$$
This tells us how sensitive the loss is to the pre-activation $z^{(l)}$. It’s the core of backprop.

We compute $\delta^{(l)}$ recursively, from output to input.

#### Output Layer ($l = 2$)

We start here because $J$ depends directly on $\hat{y} = z^{(2)}$.

Given $J = \frac{1}{2}(y - \hat{y})^2$, we compute:
$$
\delta^{(2)} = \frac{\partial J}{\partial z^{(2)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} = -(y - \hat{y}) \cdot 1 = \hat{y} - y
$$

Now compute gradients for output parameters:
$$
\frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} (a^{(1)})^\top, \quad \frac{\partial J}{\partial b^{(2)}} = \delta^{(2)}
$$

> **Why the transpose?**  
> Each weight $W^{(2)}_{ij}$ connects neuron $j$ in layer 1 to neuron $i$ in layer 2. The gradient $\frac{\partial J}{\partial W^{(2)}_{ij}} = \delta^{(2)}_i \cdot a^{(1)}_j$, so the full matrix is the outer product.

> **Worked Example (Output Gradients)**  
> Let $y = 1$, $\hat{y} = 2.286$ → $\delta^{(2)} = 2.286 - 1 = 1.286$  
> $a^{(1)} \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix}$  
> So:
> $$
> \frac{\partial J}{\partial W^{(2)}} = 1.286 \cdot \begin{bmatrix}0.762 & -0.762\end{bmatrix} \approx \begin{bmatrix}0.980 & -0.980\end{bmatrix}
> $$
> $$
> \frac{\partial J}{\partial b^{(2)}} = 1.286
> $$

> **Formative Check (Output Layer)**  
> If $\hat{y} = 0.5$, $y = 0.8$, what is $\delta^{(2)}$?  
> *(Answer: $0.5 - 0.8 = -0.3$)*

> **Misconception Alert**  
> *“Gradients flow backward, so we need to reverse the network structure.”*  
> No — the network stays the same. We just traverse it in reverse order, reusing cached forward values. It’s a *computation order*, not a structural change.

---

#### Hidden Layer ($l = 1$)

Now we go deeper. $z^{(1)}$ doesn’t affect $J$ directly — it affects $a^{(1)}$, which affects $z^{(2)}$, which affects $J$.

So we chain:
$$
\delta^{(1)} = \frac{\partial J}{\partial z^{(1)}} = \frac{\partial J}{\partial a^{(1)}} \cdot \frac{\partial a^{(1)}}{\partial z^{(1)}}
$$

- $\frac{\partial a^{(1)}}{\partial z^{(1)}} = \text{diag}(1 - \tanh^2(z^{(1)}))$ — element-wise derivative.
- $\frac{\partial J}{\partial a^{(1)}} = (W^{(2)})^\top \delta^{(2)}$ — because $a^{(1)}$ influences $z^{(2)}$ through $W^{(2)}$.

So:
$$
\delta^{(1)} = \left( (W^{(2)})^\top \delta^{(2)} \right) \odot f^{(1)'}(z^{(1)})
$$

This is the **heart of backpropagation**.

> **Worked Example (Hidden Layer)**  
> $W^{(2)} = \begin{bmatrix}2 & -1\end{bmatrix}$, $\delta^{(2)} = 1.286$  
> $$
> (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix}2 \\ -1\end{bmatrix} \cdot 1.286 = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix}
> $$
> $z^{(1)} = \begin{bmatrix}1 \\ -1\end{bmatrix}$ → $f^{(1)'}(z^{(1)}) = 1 - \tanh^2(z^{(1)}) \approx \begin{bmatrix}0.420 \\ 0.420\end{bmatrix}$  
> So:
> $$
> \delta^{(1)} = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix} \odot \begin{bmatrix}0.420 \\ 0.420\end{bmatrix} \approx \begin{bmatrix}1.080 \\ -0.540\end{bmatrix}
> $$

Now compute gradients:
$$
\frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix}1.080 \\ -0.540\end{bmatrix} \begin{bmatrix}1 & 0\end{bmatrix} = \begin{bmatrix}1.080 & 0 \\ -0.540 & 0\end{bmatrix}
$$
$$
\frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} \approx \begin{bmatrix}1.080 \\ -0.540\end{bmatrix}
$$

> **Formative Check (Hidden Layer)**  
> If $z^{(1)}_1 = 5$, what is $\tanh'(z^{(1)}_1)$? What does this imply for gradient flow?  
> *(Answer: $\tanh'(5) \approx 1 - \tanh^2(5) \approx 0.004$ — very small. So gradient signal is blocked — vanishing gradient.)*

> **Misconception Alert**  
> *“The derivative of tanh is always positive, so gradients always flow.”*  
> No — in saturated regions ($|z|$ large), $\tanh'(z) \approx 0$, so gradients vanish. This is why deep tanh networks struggle to train.

---

### Complete Worked Example: Forward and Backward Pass

Let’s now run the full sequence.

**Given:**
- $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $, $ y = 1 $
- $ W^{(1)} = \begin{bmatrix}1 & 1 \\ -1 & 1\end{bmatrix} $, $ b^{(1)} = \begin{bmatrix}0 \\ 0\end{bmatrix} $
- $ W^{(2)} = \begin{bmatrix}2 & -1\end{bmatrix} $, $ b^{(2)} = 0 $
- $ f^{(1)} = \tanh $, $ f^{(2)} = \text{linear} $
- $ J = \frac{1}{2}(y - \hat{y})^2 $

#### Forward Pass

1. $ z^{(1)} = W^{(1)}x = \begin{bmatrix}1 \\ -1\end{bmatrix} $
2. $ a^{(1)} = \tanh(z^{(1)}) \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix} $
3. $ z^{(2)} = W^{(2)}a^{(1)} + b^{(2)} = 2(0.762) + (-1)(-0.762) = 2.286 $
4. $ \hat{y} = 2.286 $
5. $ J = \frac{1}{2}(1 - 2.286)^2 \approx 0.825 $

#### Backward Pass

1. $ \delta^{(2)} = \hat{y} - y = 1.286 $
2. $ \frac{\partial J}{\partial W^{(2)}} = 1.286 \cdot \begin{bmatrix}0.762 & -0.762\end{bmatrix} \approx \begin{bmatrix}0.980 & -0.980\end{bmatrix} $
3. $ \frac{\partial J}{\partial b^{(2)}} = 1.286 $
4. $ (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix} $
5. $ f^{(1)'}(z^{(1)}) \approx \begin{bmatrix}0.420 \\ 0.420\end{bmatrix} $
6. $ \delta^{(1)} = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix} \odot \begin{bmatrix}0.420 \\ 0.420\end{bmatrix} \approx \begin{bmatrix}1.080 \\ -0.540\end{bmatrix} $
7. $ \frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix}1.080 & 0 \\ -0.540 & 0\end{bmatrix} $
8. $ \frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} $

All gradients are now computed and ready for optimization (e.g., SGD).

> **Insight**  
> Notice that only the first column of $W^{(1)}$ gets updated, because $x_2 = 0$. Inputs that are zero don’t contribute — this is **selective credit assignment**.

---

### Beyond Mechanics: Architecture and Gradient Flow

Backpropagation isn’t just a computation — it shapes how we design networks.

#### Vanishing Gradients

In deep networks with sigmoid or tanh, gradients can vanish because:
- $f'(z)$ is small in saturated regions ($|z|$ large).
- Each layer multiplies gradients by $f'(z)$ and $W^\top$.
- Deep chains → exponential decay.

> **Try this yourself**: In a 10-layer linear network with weights = 0.5, how does gradient scale?  
> *(Answer: Each layer attenuates by 0.5 → total attenuation $0.5^{10} \approx 0.001$ — signal vanishes.)*

#### Residual Connections

ResNet uses:
$$
a^{(l+1)} = a^{(l)} + F(a^{(l)})
$$
In backprop, the error splits:
- One path through $F$,
- One direct path backward.

This is like a **short-circuit wire** — it ensures some gradient always flows, even if $F$’s path vanishes.

#### Batch Normalization

It stabilizes $z^{(l)}$ in the linear region of $f'$, where gradients are strong. No more saturation.

#### ReLU

Its derivative is 1 for $z > 0$ — like a wide-open valve. No vanishing gradient — but if $z < 0$, derivative is 0 → **dying ReLU**.

> **Final Prompt**  
> Design a 3-layer sigmoid network with large initial weights. Predict what happens in backprop.  
> *(Answer: large weights → large $z$ → sigmoid saturates → $f'(z) \approx 0$ → gradients vanish → no learning.)*  
> How to fix? Use smaller weights, batch norm, or switch to ReLU.

---

Backpropagation is not just calculus — it’s the **physics of learning**.  
Every gradient tells a story of cause and effect, traced backward through space and time.  
And now, you can read that story — one derivative at a time.