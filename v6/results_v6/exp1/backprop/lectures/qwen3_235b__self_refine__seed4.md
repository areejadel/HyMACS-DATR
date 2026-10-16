By the end of this lecture, you will be able to:

1. Compute gradients in a computational graph using reverse-mode automatic differentiation, given a scalar loss and differentiable operations.
2. Trace forward and backward passes in a feedforward neural network, correctly applying the chain rule and storing intermediate values.
3. Apply the backpropagation recurrence to compute error signals $\delta^{(l)}$ and parameter gradients $\nabla_{W^{(l)}} J$, $\nabla_{b^{(l)}} J$ for fully connected layers.
4. Diagnose vanishing or exploding gradients in deep networks by analyzing activation functions, weight initialization, and depth.
5. Evaluate trade-offs between backpropagation and alternative gradient computation methods in terms of efficiency, memory, and biological plausibility.

---

### 1. Prerequisites: Multivariable Calculus and the Chain Rule

Imagine you're debugging a complex software system where a single output failure could stem from any of thousands of lines of code. You don’t want to re-run the entire program for each variable. What if you could trace the *sensitivity* of the final error back through every operation—just once—and pinpoint which inputs mattered most?

That’s the core idea behind **backpropagation**—but to build it, we start with a deeper truth: the **chain rule** of multivariable calculus.

Let $ J = f(g(x)) $. The derivative of $ J $ with respect to $ x $ is:
$$
\frac{dJ}{dx} = \frac{df}{dg} \cdot \frac{dg}{dx}.
$$
In higher dimensions, suppose $ J \in \mathbb{R} $ depends on $ \mathbf{u} \in \mathbb{R}^m $, and $ \mathbf{u} $ depends on $ \mathbf{v} \in \mathbb{R}^n $. Then:
$$
\frac{\partial J}{\partial \mathbf{v}} = \left( \frac{\partial \mathbf{u}}{\partial \mathbf{v}} \right)^\top \frac{\partial J}{\partial \mathbf{u}}.
$$
We define the **adjoint** of $ \mathbf{u} $ as $ \bar{\mathbf{u}} = \partial J / \partial \mathbf{u}} $, which quantifies the sensitivity of $ J $ to infinitesimal changes in $ \mathbf{u} $.

> **Analogy: Electrical Circuit Sensitivity**  
Think of $ J $ as voltage at the end of a circuit. Each component (resistor, amplifier) transforms signals. The chain rule computes how tweaking an input resistor affects the final voltage—by propagating the effect *backward* through each stage’s gain. Backpropagation is this same idea, but for computation instead of electricity.

> **Worked Example: Chain Rule in a Scalar Function**  
Let $ J = (w_1 + w_2)^2 $, with $ w_1 = 1 $, $ w_2 = 2 $. Define $ u = w_1 + w_2 = 3 $, so $ J = u^2 = 9 $.  
To compute $ \partial J / \partial w_1 $:  
- $ \partial J / \partial u = 2u = 6 $,  
- $ \partial u / \partial w_1 = 1 $,  
- Thus $ \partial J / \partial w_1 = 6 \cdot 1 = 6 $.  
Similarly, $ \partial J / \partial w_2 = 6 $.  

This illustrates reverse-mode automatic differentiation: a single backward pass computes gradients with respect to all inputs.

> **Try This Yourself**  
Let $ J = \sin(w_1 w_2^2) $, $ w_1 = 1 $, $ w_2 = 1 $.  
Define $ u = w_2^2 $, $ v = w_1 u $, $ J = \sin(v) $.  
Compute $ \partial J / \partial w_1 $ and $ \partial J / \partial w_2 $ step-by-step using the chain rule.  
*Hint: $ \partial J / \partial w_2 = \partial J / \partial v \cdot \partial v / \partial u \cdot \partial u / \partial w_2 $.*

> **Common Misconception**  
Gradients depend not only on the value of $ J $, but on the **computation path**. For example, $ J = w_1 w_2 $ and $ J = (w_1 + w_2)^2 $ may evaluate to the same number at a point, but their gradients differ due to distinct functional forms.

---

### 2. Computational Graphs and Reverse-Mode Automatic Differentiation

Now imagine you’re a detective reconstructing a crime. The final outcome—say, a corrupted file—is known. Your job is to trace backward through every logged operation: who accessed what, when, and how it changed. You don’t repeat the crime; you reverse-engineer its causes.

A **computational graph** is your logbook. It represents the evaluation of a scalar $ J $ from inputs and parameters. Nodes denote variables or operations; directed edges represent data flow.

Backpropagation implements **reverse-mode automatic differentiation (AD)**: after a forward pass computes $ J $, a backward pass propagates adjoints $ \bar{v} = \partial J / \partial v $ from output to inputs, applying the chain rule at each node.

Reverse mode is optimal for deep learning because it computes the gradient of one scalar output with respect to many inputs in time proportional to the forward pass—significantly faster than finite differences or forward-mode AD.

> **Analogy: Water Flow in a Drainage Network**  
Imagine rainfall ($ J $) collected from a vast watershed (input parameters). Streams (intermediate variables) merge into rivers. Reverse-mode AD is like measuring how much each tiny tributary contributed to the final flow—by reversing the water’s direction and seeing how much "pull" each upstream path exerts. The gradient is the contribution sensitivity.

> **Worked Example: $ J = \sin(w_1 w_2) $**  
Define:  
- $ u = w_1 w_2 $,  
- $ J = \sin(u) $.  
Forward pass: $ w_1 = 1, w_2 = 2 \Rightarrow u = 2, J = \sin(2) \approx 0.909 $.  
Backward pass (starting with $ \bar{J} = 1 $):  
- $ \bar{u} = \bar{J} \cdot \cos(u) = \cos(2) \approx -0.416 $,  
- $ \bar{w}_1 = \bar{u} \cdot \partial u / \partial w_1 = -0.416 \cdot w_2 = -0.832 $,  
- $ \bar{w}_2 = \bar{u} \cdot \partial u / \partial w_2 = -0.416 \cdot w_1 = -0.416 $.  

Although $ w_1 $ and $ w_2 $ appear symmetrically in $ u $, their gradients differ when $ w_1 \ne w_2 $—gradients depend on both structure and value.

> **Try This Yourself**  
Let $ J = \log(\exp(w_1) + \exp(w_2)) $, $ w_1 = 0 $, $ w_2 = 1 $.  
This is the log-sum-exp function—common in softmax.  
Compute $ \partial J / \partial w_1 $ and $ \partial J / \partial w_2 $ using a computational graph.  
*Observe: the gradients resemble probabilities. Why?*

> **Common Misconception**  
"Backpropagation is just calculus." In fact, it is **efficient gradient computation via dynamic programming**. Without caching intermediate values and reusing adjoints, reverse-mode AD would require redundant derivative evaluations.

> **Practical Relevance**  
In PyTorch, tensors with `requires_grad=True` record operations during the forward pass, building a dynamic computational graph. Calling `.backward()` initiates reverse traversal. Always call `optimizer.zero_grad()` before each backward pass to prevent gradient accumulation across batches.

---

### 3. Forward Pass: Computation and Intermediate Storage

In a feedforward neural network, the forward pass computes activations layer by layer. For layer $ l $:

- Pre-activation: $ z^{(l)} = W^{(l)} a^{(l-1)} + b^{(l)} $,
- Activation: $ a^{(l)} = f^{(l)}(z^{(l)}) $, where $ f^{(l)} $ is a differentiable nonlinearity (e.g., tanh, ReLU),
- Input: $ a^{(0)} = x $.

The loss $ J $, such as mean squared error or cross-entropy, measures discrepancy between output $ \hat{y} = a^{(L)} $ and target $ y $.

Crucially, we **store all $ z^{(l)} $ and $ a^{(l)} $** during the forward pass. These values are required in the backward pass to compute $ f^{(l)\prime}(z^{(l)}) $, which depends on the actual $ z^{(l)} $.

> **Analogy: Theater Production with Rehearsal Notes**  
A play’s final performance (output) depends on every actor’s delivery. To improve, the director reviews rehearsal footage (intermediate values): where did timing falter? Without those recordings, feedback is guesswork. Backpropagation needs the "footage" of $ z^{(l)} $ to assign credit or blame.

> **Worked Example: Two-Layer Network Forward Pass**  
Given:  
- $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $, $ y = 1 $,  
- $ W^{(1)} = \begin{bmatrix}1 & 1 \\ -1 & 1\end{bmatrix}, b^{(1)} = \begin{bmatrix}0 \\ 0\end{bmatrix} $,  
- $ W^{(2)} = \begin{bmatrix}2 & -1\end{bmatrix}, b^{(2)} = 0 $,  
- $ f^{(1)} = \tanh $, $ f^{(2)} = \text{identity} $.  

Forward computation:  
- $ z^{(1)} = W^{(1)}x = \begin{bmatrix}1 \\ -1\end{bmatrix} $,  
- $ a^{(1)} = \tanh(z^{(1)}) \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix} $,  
- $ z^{(2)} = W^{(2)}a^{(1)} = 2(0.762) + (-1)(-0.762) = 2.286 $,  
- $ \hat{y} = z^{(2)} = 2.286 $,  
- $ J = \frac{1}{2}(y - \hat{y})^2 = \frac{1}{2}(1 - 2.286)^2 \approx 0.825 $.  

Store $ z^{(1)}, a^{(1)}, z^{(2)} $ for use in backpropagation.

> **Try This Yourself**  
Suppose you only stored $ a^{(1)} $, not $ z^{(1)} $. Could you recover $ f^{(1)\prime}(z^{(1)}) $ for $ \tanh $? What if $ f^{(1)} = \text{ReLU} $?  
*This is why gradient checkpointing works for ReLU but not tanh—nonlinearities matter.*

> **Common Misconception**  
"We only need the final output." In reality, gradients require **intermediate values**. For ReLU, $ f'(z) = 1 $ if $ z > 0 $, else $ 0 $. Without $ z^{(l)} $, we cannot determine which neurons were active.

> **Practical Relevance**  
Large models like transformers use **gradient checkpointing**: instead of storing all $ z^{(l)} $, they recompute them during the backward pass. This reduces memory usage from $ O(L) $ to $ O(\sqrt{L}) $ at the cost of recomputation, enabling training of deeper networks.

---

### 4. Backward Pass: Error Signals and Gradient Recurrence

Now consider a symphony. The conductor hears a wrong note in the final chord. Who erred—the violinist, the cellist, or the composer’s orchestration? The sound traveled through layers of instruments; each contributed. How do you assign responsibility?

In neural networks, we use **error signals** $ \delta^{(l)} = \partial J / \partial z^{(l)} $, which measure the sensitivity of $ J $ to perturbations in pre-activations.

The backpropagation recurrence is:
$$
\delta^{(l)} = \left( (W^{(l+1)})^\top \delta^{(l+1)} \right) \odot f^{(l)\prime}(z^{(l)}),
$$
with base case $ \delta^{(L)} = \partial J / \partial z^{(L)} $. The Hadamard product $ \odot $ arises because activation functions are applied element-wise.

Parameter gradients follow directly:
- $ \nabla_{W^{(l)}} J = \delta^{(l)} (a^{(l-1)})^\top $,
- $ \nabla_{b^{(l)}} J = \delta^{(l)} $.

> **Analogy: Blame Propagation in a Supply Chain**  
A defective phone (high $ J $) is traced back: the assembler (last layer) checks components from the camera module supplier (previous layer). Each supplier asks their own suppliers, but only for parts used in *that* unit. The gradient is the audit trail—scaled by how sensitive each subcomponent was to change.

> **Worked Example: Backward Pass on Two-Layer Network**  
From forward pass: $ \hat{y} = 2.286 $, $ y = 1 $, $ J \approx 0.825 $.

**Output Layer ($ l = 2 $)**:  
- $ \partial J / \partial \hat{y} = \hat{y} - y = 1.286 $,  
- Since $ \hat{y} = z^{(2)} $, $ \partial \hat{y} / \partial z^{(2)} = 1 $, so $ \delta^{(2)} = 1.286 $,  
- $ \nabla_{W^{(2)}} J = \delta^{(2)} (a^{(1)})^\top = 1.286 \cdot \begin{bmatrix}0.762 & -0.762\end{bmatrix} = \begin{bmatrix}0.980 & -0.980\end{bmatrix} $,  
- $ \nabla_{b^{(2)}} J = \delta^{(2)} = 1.286 $.

**Hidden Layer ($ l = 1 $)**:  
- $ \partial J / \partial a^{(1)} = (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix}2 \\ -1\end{bmatrix} \cdot 1.286 = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix} $,  
- $ f^{(1)\prime}(z^{(1)}) = 1 - \tanh^2(z^{(1)}) \approx \begin{bmatrix}0.419 \\ 0.419\end{bmatrix} $,  
- $ \delta^{(1)} = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix} \odot \begin{bmatrix}0.419 \\ 0.419\end{bmatrix} \approx \begin{bmatrix}1.078 \\ -0.539\end{bmatrix} $,  
- $ \nabla_{W^{(1)}} J = \delta^{(1)} x^\top = \begin{bmatrix}1.078 \\ -0.539\end{bmatrix} \begin{bmatrix}1 & 0\end{bmatrix} = \begin{bmatrix}1.078 & 0 \\ -0.539 & 0\end{bmatrix} $,  
- $ \nabla_{b^{(1)}} J = \delta^{(1)} \approx \begin{bmatrix}1.078 \\ -0.539\end{bmatrix} $.

> **Try This Yourself**  
Suppose $ W^{(2)} $ were zero. What would $ \delta^{(1)} $ be? What does this imply about learning in early layers when later weights are small?

> **Common Misconception**  
"Gradient magnitude depends only on weights." In fact, the activation derivative $ f'(z) $ acts as a **gate**: if $ f'(z) = 0 $, gradient flow stops regardless of weight size.

> **Practical Relevance**  
In convolutional networks (CNNs), weight sharing implies gradients are summed over spatial positions. In recurrent networks (RNNs), backpropagation through time (BPTT) unrolls the network across timesteps and applies the same recurrence.

---

### 5. Vanishing and Exploding Gradients: Causes and Consequences

The recurrence $ \delta^{(l)} = (W^{(l+1)})^\top \delta^{(l+1)} \odot f^{(l)\prime}(z^{(l)}) $ can amplify or attenuate gradients across layers.

- **Vanishing gradients**: $ \|\delta^{(l)}\| \ll \|\delta^{(L)}\| $—early layers receive negligible updates, slowing learning.
- **Exploding gradients**: $ \|\delta^{(l)}\| \gg \|\delta^{(L)}\| $—updates become unstable, causing divergence.

> **Analogy: Whispering Down the Lane—With Amplifiers**  
Now imagine each person in the game doesn’t just whisper, but uses a microphone with gain. If each gain is 0.5, the message fades fast. If it’s 2.0, feedback howls. The network’s depth turns small per-layer changes into exponential effects.

> **Worked Example: Vanishing Gradient with Sigmoid**  
In a 10-layer network with $ f = \sigma(z) $, $ \sigma'(z) \leq 0.25 $. If each layer attenuates gradients by ~0.25, after 10 layers: $ (0.25)^{10} \approx 10^{-6} $. Early layers receive almost no learning signal.

> **Worked Example: Dying ReLU**  
If $ z^{(l)} < 0 $ for a ReLU neuron, then $ f'(z) = 0 $, so $ \delta^{(l)} = 0 $. No gradient flows—neuron remains inactive and cannot recover.

> **Try This Yourself**  
Simulate gradient norm decay: assume $ \| \delta^{(l)} \| = \gamma \| \delta^{(l+1)} \| $, $ \gamma = 0.8 $. After how many layers is the gradient less than 1% of the output?  
*Answer: $ l > \log(0.01)/\log(0.8) \approx 21 $ layers.*

> **Common Misconception**  
"ReLU eliminates vanishing gradients." While ReLU mitigates saturation for positive inputs, **dying ReLU**—where neurons stay inactive—causes permanent gradient blockage. Solution: Leaky ReLU, with $ f'(z) = \alpha $ for $ z < 0 $, $ \alpha > 0 $.

---

### 6. Activation Functions and Initialization: Preserving Gradient Scale

To enable stable training, activation functions and initialization schemes must preserve signal magnitude across layers.

| Activation   | Derivative Range       | Gradient Risk                        |
|--------------|------------------------|