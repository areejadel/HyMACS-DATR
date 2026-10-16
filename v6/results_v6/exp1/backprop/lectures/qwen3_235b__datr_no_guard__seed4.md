**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. Recall the forward and backward pass equations in a feedforward neural network.  
2. Understand how the chain rule propagates gradients through a computational graph.  
3. Apply the backpropagation algorithm to compute gradients in a multilayer perceptron.  
4. Analyze common issues such as vanishing gradients and numerical instability, and explain how architectural choices affect them.  
5. Construct a step-by-step backward pass for a given network by combining local derivatives and error signals.

---

### Prerequisites

Before proceeding, ensure familiarity with the following concepts:  
- **Partial derivatives and the chain rule**: For a composite function $ z = f(g(x)) $, the derivative is $ \frac{dz}{dx} = \frac{dz}{dg} \cdot \frac{dg}{dx} $.  
- **Vector calculus**: The gradient of a scalar loss $ J $ with respect to a vector $ w $ is denoted $ \nabla_w J $, and contains partial derivatives $ \frac{\partial J}{\partial w_i} $.  
- **Matrix operations**: Matrix multiplication and transposition, particularly how $ W^\top $ enables backward gradient routing.  
- **Element-wise operations**: The Hadamard (element-wise) product $ \odot $, used when applying activation function derivatives.

These tools form the foundation for deriving gradient flow in neural networks.

> **Formative Check (Prerequisites)**  
> Let $ a = \tanh(z) $, $ z = Wx + b $, and $ J = a^2 $. Compute $ \frac{\partial J}{\partial z} $ using the chain rule.  
> *(Answer: $ \frac{\partial J}{\partial z} = 2a \cdot (1 - \tanh^2(z)) = 2\tanh(z)(1 - \tanh^2(z)) $.)*

---

### Intuition: The Purpose of Backpropagation

Imagine you're debugging a complex audio mixing board with 10,000 knobs. Each knob subtly affects the final sound, but you only hear the *total output*—a single number measuring how far it is from the ideal mix.  

You want to adjust the knobs so the music sounds perfect.  
But every time you twist one knob, you must restart the entire song to hear the result.  
And each playthrough takes a second.  

To test each knob individually? That’s 10,000 seconds—nearly three hours—for just *one* update cycle.  

Now imagine an alternative:  
You play the track once. You record every voltage, every signal path. Then, in silence, you *reverse the signal flow*: starting from the final distortion, you trace backward through each amplifier, filter, and mixer stage, asking:  
*Which knob, at which moment, pushed the signal toward this flaw?*  

Suddenly, from one forward pass, you get *all* the sensitivities at once.  
Not hours—**milliseconds**.

This is the power of **backpropagation**.

> **Try this yourself**: Suppose a neural network has 5 million parameters, and one forward pass takes 5 milliseconds. How long would it take to estimate gradients using finite differences (one parameter at a time)? How many updates could you afford per hour?  
> Now compare that to backpropagation, which computes all gradients in roughly *twice* the forward time (~10 ms). What changes in your training strategy?

Here’s the catch:  
There’s no omniscient observer tracking blame. No AI “understanding” the network.  
Just **calculus**—applied with surgical precision across a **computational graph**.

And yet, this method turns an intractable problem into a routine computation.  
> It reduces gradient evaluation from $ \mathcal{O}(n) $ forward passes to just **one forward, one backward**—independent of parameter count.

That efficiency isn’t incremental.  
It’s **existential**.  
Without backpropagation, deep networks wouldn’t learn. They’d stall in the dark, adjusting knobs at random.

But here’s a paradox:  
Why does *reversing* the computation work at all?

After all, information flows forward: data in, prediction out.  
Yet we send *sensitivity signals* backward—like playing a movie in reverse and still understanding cause and effect.

The answer lies in a deep symmetry:  
**Every computational step that can propagate values forward can also propagate derivatives backward**, provided we know how it distorts space locally.

Think of it like folding a map:  
- Forward: you unfold it step by step—each crease reveals new terrain.  
- Backward: you refold it, retracing the same creases in reverse, but now guided by where you ended up.

The path is deterministic in both directions—not because time reverses, but because each operation is **differentiable**, and hence **invertible in gradient space**.

This is not magic. It’s mechanics.  
And we’re about to build it, layer by layer.

---

### Step 1: Forward Pass and the Computational Graph

Consider a two-layer feedforward network:  
- Input: $ x \in \mathbb{R}^2 $  
- Hidden layer:  
  $$
  z^{(1)} = W^{(1)}x + b^{(1)}, \quad a^{(1)} = \tanh(z^{(1)})
  $$  
- Output layer:  
  $$
  z^{(2)} = W^{(2)}a^{(1)} + b^{(2)}, \quad \hat{y} = z^{(2)} \quad \text{(linear output)}
  $$  
- Loss:  
  $$
  J = \frac{1}{2}(y - \hat{y})^2
  $$

The forward pass is like a **pipeline for responsibility creation**:  
- Data enters.  
- Each layer transforms it, building a chain of causality.  
- The loss quantifies failure at the end.

But to fix the system, we need **responsibility assignment**—a way to ask:  
*Whose transformation most amplified the error?*

Backpropagation answers this by reversing the pipeline, not to undo the computation, but to **distribute blame**.

Each operation becomes a node in a **computational graph**, a dependency map where every value knows its parents.  
And we **cache** intermediate results: $ z^{(1)}, a^{(1)}, z^{(2)} $.  
Why? Because derivatives depend on context.  
Just as you can’t compute the slope of $ \tanh(z) $ without knowing $ z $, you can’t assign blame without knowing the state during the forward pass.

This is the **memory-speed tradeoff** in action: store more, compute less.

> **Formative Check (Forward Pass)**  
> Given $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $, $ W^{(1)} = \begin{bmatrix}1 & 1 \\ -1 & 1\end{bmatrix} $, $ b^{(1)} = \begin{bmatrix}0 \\ 0\end{bmatrix} $, compute $ z^{(1)} $ and $ a^{(1)} $.  
> *(Answer: $ z^{(1)} = \begin{bmatrix}1 \\ -1\end{bmatrix} $, $ a^{(1)} = \begin{bmatrix}\tanh(1) \\ \tanh(-1)\end{bmatrix} \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix} $.)*

---

### Step 2: Backward Pass — Gradient Computation via the Chain Rule

Now begins the audit.

We start at the loss and walk backward, asking at each node:  
*How much did your output influence the final error?*

We define the **error signal** at layer $ l $:  
$$
\delta^{(l)} = \frac{\partial J}{\partial z^{(l)}}
$$  
This is the **sensitivity of the loss to pre-activation inputs**.  
It answers: *If I nudged $ z^{(l)} $, how would the final error change?*

We compute $ \delta^{(l)} $ recursively—like tracing a pollutant upstream through a river network.

#### Output Layer ($ l = 2 $)

We begin with:  
$$
\delta^{(2)} = \frac{\partial J}{\partial z^{(2)}}
$$  
Since $ \hat{y} = z^{(2)} $ and $ J = \frac{1}{2}(y - \hat{y})^2 $,  
$$
\frac{\partial J}{\partial z^{(2)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} = (-(y - \hat{y})) \cdot 1 = \hat{y} - y
$$  
Thus,  
$$
\delta^{(2)} = \hat{y} - y
$$

Now compute gradients for output parameters:  
$$
\frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} (a^{(1)})^\top, \quad \frac{\partial J}{\partial b^{(2)}} = \delta^{(2)}
$$

> **Why $ (a^{(1)})^\top $?**  
> Think of it as **blame-by-contribution**: each weight $ W^{(2)}_{ij} $ links activation $ j $ to output $ i $. The gradient $ \frac{\partial J}{\partial W^{(2)}_{ij}} = \delta^{(2)}_i \cdot a^{(1)}_j $—so the full gradient is the outer product.  
> This is **credit assignment** in action: error is shared between *how wrong the output was* ($ \delta^{(2)} $) and *how much the input contributed* ($ a^{(1)} $).

**Real-World Application: Speech Recognition in Google Assistant**  
In automatic speech recognition (ASR) systems like Google Assistant, acoustic features (e.g., mel-frequency cepstral coefficients) are fed into deep neural networks to predict phonemes. The output layer computes logits over phoneme classes, and the loss (e.g., cross-entropy) measures prediction error. Backpropagation computes gradients efficiently across millions of weights, enabling real-time adaptation to speaker variability. For instance, during training on the LibriSpeech dataset, backpropagation allows the model to adjust output layer weights so that misclassified phonemes (e.g., "s" vs "sh") are corrected by amplifying discriminative features in the hidden representations.

---

#### Hidden Layer ($ l = 1 $)

Now the real challenge: propagate error *through* the activation function and *back through* the linear layer.

We want $ \delta^{(1)} = \frac{\partial J}{\partial z^{(1)}} $.  
But $ z^{(1)} $ doesn’t directly affect $ J $. It affects $ a^{(1)} $, which affects $ z^{(2)} $, which affects $ J $.

So we chain:  
$$
\frac{\partial J}{\partial z^{(1)}} = \frac{\partial J}{\partial a^{(1)}} \cdot \frac{\partial a^{(1)}}{\partial z^{(1)}}
$$

First, $ \frac{\partial a^{(1)}}{\partial z^{(1)}} $ is diagonal: $ \text{diag}(1 - \tanh^2(z^{(1)})) $.  
Second, $ \frac{\partial J}{\partial a^{(1)}} = (W^{(2)})^\top \delta^{(2)} $—because $ z^{(2)} = W^{(2)}a^{(1)} + b^{(2)} $, so each component of $ a^{(1)} $ influences $ J $ through all outputs via the weights.

Putting it together:  
$$
\delta^{(1)} = \left( (W^{(2)})^\top \delta^{(2)} \right) \odot f^{(1)'}(z^{(1)})
$$

This equation is the **heartbeat of backpropagation**.  
Let’s dissect it with a new analogy:

> **Backpropagation is like a supply chain audit after a product recall**:  
> - The defective product (high loss) is traced back through distribution, manufacturing, and raw materials.  
> - At each stage, auditors ask: *Did you introduce or amplify the defect?*  
> - The activation derivative $ f'(z) $ acts like a **quality gate**: if a neuron is saturated ($ \tanh(z) \approx \pm1 $), its gate is nearly closed—no useful signal gets through.  
> - The weight transpose $ W^\top $ acts like a **reverse logistics map**, showing how outputs depend on inputs.  
> - If one factory (layer) has a broken sensor (zero gradient), the entire upstream chain loses feedback—this is **vanishing gradients**.

But here’s a twist:  
What if the supply chain *learns* from each audit?

Each time a defect is found, the factories don’t just fix the current batch—they **update their machinery**, retrain inspectors, and redesign processes.  
That’s what gradient descent does: backpropagation delivers the audit report, and optimization acts on it.

> **Try this yourself**: Suppose $ z^{(1)} = 4 $. What is $ \tanh'(z^{(1)}) $? What does this imply about the ability of the first layer to learn?  
> Now suppose you replace tanh with ReLU. Recompute $ f'(z) $ at the same $ z $. What changes in the backward flow?

Then compute:  
$$
\frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top, \quad \frac{\partial J}{\partial b^{(1)}} = \delta^{(1)}
$$

> **Clarification**: The transpose $ W^{(2)\top} $ ensures dimensional compatibility and reflects how each neuron in layer 1 influences all neurons in layer 2 through the weights.

> **Formative Check (Backward Pass)**  
> Given $ \delta^{(2)} = 0.5 $, $ W^{(2)} = \begin{bmatrix}2 & -1\end{bmatrix} $, $ z^{(1)} = \begin{bmatrix}0 \\ 1\end{bmatrix} $, compute $ \delta^{(1)} $.  
> *(Answer: $ (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix}1.0 \\ -0.5\end{bmatrix} $, $ f^{(1)'}(z^{(1)}) = \begin{bmatrix}1 \\ 1 - \tanh^2(1)\end{bmatrix} \approx \begin{bmatrix}1 \\ 0.42\end{bmatrix} $, so $ \delta^{(1)} \approx \begin{bmatrix}1.0 \\ -0.21\end{bmatrix} $.)*

**Real-World Application: Medical Image Segmentation with U-Net**  
In biomedical imaging, U-Net architectures are used to segment tumors in MRI scans. During training, the network processes patches of brain scans and predicts pixel-wise labels (tumor vs. healthy tissue). The loss (e.g., Dice loss) quantifies overlap between prediction and ground truth. Backpropagation enables precise gradient computation through both the contracting (downsampling) and expansive (upsampling) paths. Crucially, gradients from the final segmentation layer must propagate through multiple non-linearities and skip connections to update early convolutional filters. Without efficient backpropagation, the model could not learn to detect subtle tumor boundaries—critical for accurate diagnosis in clinical settings such as glioma segmentation in the BraTS challenge.

---

### Worked Example: Complete Forward and Backward Pass

We now execute a full forward and backward pass.

**Given:**  
- $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $, $ y = 1 $  
- $ W^{(1)} = \begin{bmatrix}1 & 1 \\ -1 & 1\end{bmatrix} $, $ b^{(1)} = \begin{bmatrix}0 \\ 0\end{bmatrix} $  
- $ W^{(2)} = \begin{bmatrix}2 & -1\end{bmatrix} $, $ b^{(2)} = 0 $  
- $ f^{(1)} = \tanh $, $ f^{(2)} = \text{linear} $, $ J = \frac{1}{2}(y - \hat{y})^2 $

#### Forward Pass

1. $ z^{(1)} = W^{(1)}x = \begin{bmatrix}1\cdot1 + 1\cdot0 \\ -1\cdot1 + 1\cdot0\end{bmatrix} = \begin{bmatrix}1 \\ -1\end{bmatrix} $  
2. $ a^{(1)} = \tanh(z^{(1)}) = \begin{bmatrix}\tanh(1) \\ \tanh(-1)\end{bmatrix} \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix} $  
3. $ z^{(2)} = W^{(2)}a^{(1)} + b^{(2)} = 2(0.762) + (-1)(-0.762) = 1.524 + 0.762 = 2.286 $  
4. $ \hat{y} = z^{(2)} = 2.286 $  
5. $ J = \frac{1}{2}(1 - 2.286)^2 = \frac{1}{2}(1.651)^2 \approx 0.825 $

#### Backward Pass

1. $ \delta^{(2)} = \hat{y} - y = 2.286 - 1 = 1.286 $  
2. $ \frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} (a^{(1)})^\top = 1.286 \cdot \begin{bmatrix}0.762 & -0.762\end{bmatrix} \approx \begin{bmatrix}0.980 & -0.980\end{bmatrix} $  
3. $ \frac{\partial J}{\partial b^{(2)}} = \delta^{(2)} = 1.286 $  
4. $ (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix}2 \\ -1\end{bmatrix} \cdot 1.286 = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix} $  
5. $ f^{(1)'}(z^{(1)}) = 1 - \tanh^2(z^{(1)}) = \begin{bmatrix}1 - \tanh^2(1) \\ 1 - \tanh^2(-1)\end{bmatrix} \approx \begin{bmatrix}0.420 \\ 0.420\end{bmatrix} $  
6. $ \delta^{(1)} = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix} \odot \begin{bmatrix}0.420 \\ 0.420\end{bmatrix} \approx \begin{bmatrix}1.080 \\ -0.540\end{bmatrix} $  
7. $ \frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix}1.080 \\ -0.540\end{bmatrix} \begin{bmatrix}1 & 0\end{bmatrix} = \begin{bmatrix}1.080 & 0 \\ -0.540 & 0\end{bmatrix} $  
8. $ \frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} \approx \begin{bmatrix}1.080 \\ -0.54