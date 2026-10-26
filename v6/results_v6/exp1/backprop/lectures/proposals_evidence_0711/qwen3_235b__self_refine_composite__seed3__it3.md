The

Now

You

But

Let’s

---

### Section 2: Intuition First — Why Backward?

Imagine you're debugging a complex pipeline where each stage depends on the previous one. If the final output is incorrect, how do you determine which stage contributed most to the error?

Backpropagation answers this question for neural networks by propagating the error backward through the network, assigning responsibility to each layer.

**Concrete Example: Baking a Cake (Intuition)**

Suppose a cake turned out too salty. The process was:

- Flour → Batter → Baking → Final Cake

Who is to blame?

- The oven (last step)? Unlikely — it only baked what it received.
- The batter (added salt)? Plausible.
- The flour (already salty)? Also possible.

To fix the recipe, you must trace the error backward from the final product to earlier ingredients. Similarly, in a neural network, an incorrect prediction means poor feature extraction somewhere in the pipeline. We cannot fix only the last layer — we must propagate the error backward to update all relevant parameters.

Backpropagation is this process: computing how much each parameter contributed to the final loss via the chain rule.

This backward flow is efficient because it reuses intermediate computations, avoiding redundant derivatives.

✅ **Formative Check (Intuition)**  
Suppose a neural network misclassifies an image. Why can’t we just adjust the last layer?  
→ Because earlier layers may have extracted poor features. We need to trace error backward to fix all layers.

But here’s the puzzle: *Why go backward at all?* Why not compute gradients layer by layer from input to output?

Try this:  
👉 **Pause and sketch the computational graph of a three-layer network. Trace how the loss depends on the first-layer weights. How many paths do you find?**

You’ll see that the influence of early parameters fans out through many nonlinear transformations. Computing gradients forward would require recomputing the same derivatives repeatedly — a combinatorial explosion.

Backward mode automatic differentiation — which backprop implements — avoids this by traversing once from output to input, reusing intermediate gradients. It’s not just intuitive; it’s computationally optimal.

This is no accident: **backpropagation is the adjoint method applied to neural networks**, a concept from optimal control theory used to optimize aircraft trajectories and climate models. The same mathematics that guides rockets also trains ResNets.

---

### Section 3: Formal Setup — Forward Pass

Let us consider a feedforward neural network with $ L $ layers. Each layer $ l $ performs an affine transformation followed by a nonlinear activation:

$$
\mathbf{z}^{(l)} = \mathbf{W}^{(l)} \mathbf{a}^{(l-1)} + \mathbf{b}^{(l)}, \quad \mathbf{a}^{(l)} = \sigma^{(l)}(\mathbf{z}^{(l)})
$$

We define:
- $ \mathbf{z}^{(l)} $: pre-activation (weighted input) at layer $ l $
- $ \mathbf{a}^{(l)} $: post-activation (output) at layer $ l $
- $ \mathbf{W}^{(l)} $: weight matrix mapping from layer $ l-1 $ to $ l $
- $ \mathbf{b}^{(l)} $: bias vector at layer $ l $
- $ \sigma^{(l)} $: activation function (applied element-wise)
- $ \mathcal{L} $: scalar loss function, typically $ \mathcal{L}(\mathbf{a}^{(L)}, \mathbf{t}) $, where $ \mathbf{t} $ is the target

We assume $ \mathbf{a}^{(0)} = \mathbf{x} $, the input.

The goal of backpropagation is to compute gradients of $ \mathcal{L} $ with respect to all trainable parameters: $ \partial \mathcal{L} / \partial \mathbf{W}^{(l)} $ and $ \partial \mathcal{L} / \partial \mathbf{b}^{(l)} $ for each $ l $.

📌 **Common Misconception Alert**  
"Gradients are computed with respect to activations $ \mathbf{a}^{(l)} $."  
→ No! We compute gradients with respect to **parameters** ($ \mathbf{W}, \mathbf{b} $) via the **pre-activations** $ \mathbf{z}^{(l)} $. The chain rule flows through $ \mathbf{z}^{(l)} $, not $ \mathbf{a}^{(l)} $, because $ \mathbf{z}^{(l)} $ is where parameters enter.

✅ **Formative Check (Setup)**  
In a 3-layer network, what is the dimension of $ \mathbf{W}^{(2)} $ if layer 1 has 10 units and layer 2 has 5?  
→ $ \mathbf{W}^{(2)} \in \mathbb{R}^{5 \times 10} $

With the forward pass defined, we now derive the backward pass.

---

### Section 4: Backpropagation — Step-by-Step Derivation

We now derive backpropagation using the chain rule. The key idea is to compute gradients layer by layer, starting from the output and moving backward.

#### Step 1: Define the Error Signal

We define the **error signal** at layer $ l $ as:

$$
\boldsymbol{\delta}^{(l)} = \frac{\partial \mathcal{L}}{\partial \mathbf{z}^{(l)}}
$$

Why $ \mathbf{z}^{(l)} $? Because it is the point where parameters $ \mathbf{W}^{(l)} $ and $ \mathbf{b}^{(l)} $ directly influence the network. The chain rule will flow through $ \mathbf{z}^{(l)} $ to reach them.

This definition allows us to express gradients compactly:
$$
\frac{\partial \mathcal{L}}{\partial \mathbf{W}^{(l)}} = \boldsymbol{\delta}^{(l)} (\mathbf{a}^{(l-1)})^T, \quad \frac{\partial \mathcal{L}}{\partial \mathbf{b}^{(l)}} = \boldsymbol{\delta}^{(l)}
$$

We now compute $ \boldsymbol{\delta}^{(l)} $ recursively, starting from the output.

**Here’s the tension**: We know $ \partial \mathcal{L}/\partial \mathbf{a}^{(L)} $, but we need $ \partial \mathcal{L}/\partial \mathbf{z}^{(L)} $. How do we connect them?

👉 **Try this yourself**: Write the chain rule from $ \mathcal{L} $ to $ \mathbf{z}^{(L)} $ via $ \mathbf{a}^{(L)} $. What derivative appears?

You get:
$$
\frac{\partial \mathcal{L}}{\partial \mathbf{z}^{(L)}} = \frac{\partial \mathcal{L}}{\partial \mathbf{a}^{(L)}} \odot \frac{\partial \mathbf{a}^{(L)}}{\partial \mathbf{z}^{(L)}}
$$

But $ \mathbf{a}^{(L)} = \sigma^{(L)}(\mathbf{z}^{(L)}) $, so $ \partial \mathbf{a}^{(L)}/\partial \mathbf{z}^{(L)} = \sigma^{(L)\prime}(\mathbf{z}^{(L)}) $.

Thus:

#### Step 2: Output Layer Gradient (Base Case)

$$
\boldsymbol{\delta}^{(L)} = \frac{\partial \mathcal{L}}{\partial \mathbf{a}^{(L)}} \odot \sigma^{(L)\prime}(\mathbf{z}^{(L)})
$$

Let us interpret this:
- $ \frac{\partial \mathcal{L}}{\partial \mathbf{a}^{(L)}} $: How does the loss change with output?
- $ \sigma^{(L)\prime}(\mathbf{z}^{(L)}) $: How does activation change with input?

Now, combining these gives $ \boldsymbol{\delta}^{(L)} $, the sensitivity of the loss to pre-activations.

💡 **Intuition**: The error splits into two parts:
- How much the loss changes with output ($ \partial \mathcal{L}/\partial \mathbf{a}^{(L)} $).
- How much the activation changes with input ($ \sigma'(\mathbf{z}^{(L)}) $).

Their element-wise product gives the total effect: $ \boldsymbol{\delta}^{(L)} $.

Then, gradients for the last layer are:
$$
\frac{\partial \mathcal{L}}{\partial \mathbf{W}^{(L)}} = \boldsymbol{\delta}^{(L)} (\mathbf{a}^{(L-1)})^T, \quad \frac{\partial \mathcal{L}}{\partial \mathbf{b}^{(L)}} = \boldsymbol{\delta}^{(L)}
$$

These update rules show that gradients depend on both error and input magnitude.

📌 **Common Misconception Alert**  
"Gradient of loss w.r.t. weights is $ \boldsymbol{\delta}^{(l)} $ alone."  
→ No! It’s $ \boldsymbol{\delta}^{(l)} $ times the input from the previous layer: $ \mathbf{a}^{(l-1)} $. This is critical — gradients depend on both error and input magnitude.

---

### Section 5: Worked Example — Two-Layer Network (Full Step-by-Step)

Let us apply backpropagation to a two-layer network with scalar inputs and outputs.

**Network Setup**:
- Input: $ x = 2 $
- True label: $ t = 1 $
- Activation: $ \sigma(z) = \frac{1}{1 + e^{-z}} $, derivative $ \sigma'(z) = \sigma(z)(1 - \sigma(z)) $
- Loss: $ \mathcal{L} = \frac{1}{2}(a^{(2)} - t)^2 $
- Parameters: $ W^{(1)} = 1, b^{(1)} = 0, W^{(2)} = 1, b^{(2)} = 0 $

#### Forward Pass

We compute activations layer by layer:

1. $ z^{(1)} = W^{(1)}x + b^{(1)} = (1)(2) + 0 = 2 $
2. $ a^{(1)} = \sigma(2) = \frac{1}{1 + e^{-2}} \approx 0.8808 $
3. $ z^{(2)} = W^{(2)}a^{(1)} + b^{(2)} = (1)(0.8808) + 0 \approx 0.8808 $
4. $ a^{(2)} = \sigma(0.8808) \approx 0.7071 $
5. $ \mathcal{L} = \frac{1}{2}(0.7071 - 1)^2 \approx \frac{1}{2}(0.2929)^2 \approx 0.0429 $

#### Backward Pass

**Step 1: Output Layer ($ l = 2 $)**

- $ \frac{\partial \mathcal{L}}{\partial a^{(2)}} = a^{(2)} - t = 0.7071 - 1 = -0.2929 $
- $ \sigma'(z^{(2)}) = \sigma(0.8808)(1 - \sigma(0.8808)) \approx (0.7071)(1 - 0.7071) \approx 0.2090 $
- $ \delta^{(2)} = \left( \frac{\partial \mathcal{L}}{\partial a^{(2)}} \right) \odot \sigma'(z^{(2)}) = (-0.2929)(0.2090) \approx -0.0612 $

Now compute gradients:
- $ \frac{\partial \mathcal{L}}{\partial W^{(2)}} = \delta^{(2)} \cdot a^{(1)} = (-0.0612)(0.8808) \approx -0.0539 $
- $ \frac{\partial \mathcal{L}}{\partial b^{(2)}} = \delta^{(2)} \approx -0.0612 $

**Step 2: Hidden Layer ($ l = 1 $)**

Now propagate error backward:

- $ \frac{\partial \mathcal{L}}{\partial z^{(2)}} = \delta^{(2)} \approx -0.0612 $
- $ \frac{\partial z^{(2)}}{\partial a^{(1)}} = W^{(2)} = 1 $
- So $ \frac{\partial \mathcal{L}}{\partial a^{(1)}} = (W^{(2)})^T \delta^{(2)} = (1)(-0.0612) = -0.0612 $
- $ \sigma'(z^{(1)}) = \sigma(2)(1 - \sigma(2)) \approx (0.8808)(1 - 0.8808) \approx 0.1050 $
- $ \delta^{(1)} = \left( \frac{\partial \mathcal{L}}{\partial a^{(1)}} \right) \odot \sigma'(z^{(1)}) = (-0.0612)(0.1050) \approx -0.00642 $

Now compute gradients:
- $ \frac{\partial \mathcal{L}}{\partial W^{(1)}} = \delta^{(1)} \cdot x = (-0.00642)(2) = -0.0128 $
- $ \frac{\partial \mathcal{L}}{\partial b^{(1)}} = \delta^{(1)} \approx -0.00642 $

✅ **Formative Check (Worked Example)**  
Why is $ \frac{\partial \mathcal{L}}{\partial W^{(1)}} $ smaller than $ \frac{\partial \mathcal{L}}{\partial W^{(2)}} $?  
→ Because gradients diminish through layers (vanishing signal), and earlier inputs affect the loss through more transformations.

---

### Section 6: General Backpropagation Algorithm

Now that we have seen a concrete example, we present the general algorithm.

Given a network with $ L $ layers:

1. **Forward Pass**: Compute $ \mathbf{a}^{(l)} $ for all $ l = 1, \dots, L $.
2. **Initialize Output Error**:  
   $ \boldsymbol{\delta}^{(L)} = \frac{\partial \mathcal{L}}{\partial \mathbf{a}^{(L)}} \odot \sigma^{(L)\prime}(\mathbf{z}^{(L)}) $
3. **Backward Pass**: For $ l = L-1 $ down to $ 1 $:  
   $$
   \boldsymbol{\delta}^{(l)} = \left( (\mathbf{W}^{(l+1)})^T \boldsymbol{\delta}^{(l+1)} \right) \odot \sigma^{(l)\prime}(\mathbf{z}^{(l)})
   $$
4. **Compute Gradients**:  
   $$
   \frac{\partial \mathcal{L}}{\partial \mathbf{W}^{(l)}} = \boldsymbol{\delta}^{(l)} (\mathbf{a}^{(l-1)})^T, \quad \frac{\partial \mathcal{L}}{\partial \mathbf{b}^{(l)}} = \boldsymbol{\delta}^{(l)}
   $$

This algorithm efficiently computes all gradients in $ O(N) $ time, where $ N $ is the number of parameters.

📌 **Common Misconception Alert**  
"Backpropagation is only for sigmoid networks."  
→ No! It works for any differentiable function: ReLU, tanh, softmax, etc. Just plug in the correct derivative.

---

### Section 7: Gradient Pathologies and Mitigations

Even with correct gradients, training deep networks faces challenges.

#### 1. Vanishing Gradients

If activation derivatives $ |\sigma'(z)| < 1 $ (e.g., sigmoid), repeated multiplication across layers causes $ \boldsymbol{\delta}^{(l)} $ to shrink exponentially as $ l $ decreases.

💡 **Intuition**: Each layer multiplies gradients by $ |\sigma'(z)| < 1 $. After many layers, $ \delta^{(1)} \propto \prod_{l=1}^L |\sigma'(z^{(l)})| \to 0 $.

But here’s a non-obvious insight: **vanishing gradients are not just about activation functions — they’re about the entire signal path**. Even with ReLU, if weight matrices contract signals (e.g., small singular values), gradients still vanish.

✅ **Fix**: Use ReLU ($ \sigma'(z) = 1 $ for $ z > 0 $) or better initialization (Xavier, He).

#### 2. Exploding Gradients

If weight matrices amplify signals (e.g., large $ \mathbf{W} $), gradients can grow exponentially during backprop.

💡 **Analogy**: Think of a microphone too close to a speaker — a small sound becomes a deafening feedback loop. In deep networks, large weights + repeated multiplication = gradient explosion.

✅ **Fix**: Gradient clipping — scale down large gradients:  
$$
\nabla \mathcal{L} \leftarrow \nabla \mathcal{L} \cdot \min\left(1, \frac{c}{\|\nabla \mathcal{L}\|}\right)
$$

#### 3. Dead Neurons (ReLU)

If ReLU units receive negative inputs, they output zero and derivative is zero — no gradient flows.

👉 **Try this yourself**: Design a tiny network with ReLU where one neuron dies during training. What happens to gradients through that unit?

You’ll see: **zero gradient forever** — the neuron is frozen.

✅ **Fix**: Use Leaky ReLU ($ \sigma(z) = \max(\alpha z, z), \alpha > 0 $), PReLU, or reduce learning rate.

✅ **Formative Check (Pathologies)**  
Why does ReLU help with vanishing gradients?  
→ Because its derivative is 1 for positive inputs, so gradients don’t shrink layer-by-layer.

---

### Section 8: Practical Training and Variants

Backpropagation provides gradients; optimization algorithms use them to update parameters.

#### Stochastic Gradient Descent (SGD)  
Update rule:
$$
\mathbf{w} \leftarrow \mathbf{w} - \eta \nabla \mathcal{L}
$$

#### Momentum  
Introduce velocity to accelerate convergence:
$$
\mathbf{v} \leftarrow \gamma \mathbf{v} + \eta \nabla \mathcal{L}, \quad \mathbf{w} \leftarrow \mathbf{w} - \mathbf{v}
$$

💡 **Analogy**: Momentum is like a ball rolling downhill — it builds speed through valleys, helping escape shallow minima.

#### Adam  
Adapts learning rate per parameter using moving averages of gradient and squared gradient.

All these methods rely on gradients computed via backpropagation.

📌 **Common Misconception Alert**  
"Adam doesn’t use backpropagation."  
→ False! Adam uses the same gradients from backprop — it just changes how they’re used.

---

### Section 9: Summary and Reflection

We have now seen that:

- **Remember**: Backprop computes $ \partial \mathcal{L}/\partial \mathbf{w} $ via reverse chain rule.
- **Understand**: Error signals $ \boldsymbol{\delta}^{(l)} $ flow backward, combining downstream error and local derivative.
- **Apply**: You can now compute gradients manually in small networks.
- **Analyze**: Gradient magnitude reveals which layers