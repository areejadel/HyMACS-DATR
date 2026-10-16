# Backpropagation in Neural Networks

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember:** State the two phases of backpropagation and the purpose of each.
2. **Understand:** Explain why naive gradient computation repeats work and how backpropagation avoids it by reusing stored intermediate values.
3. **Apply:** Compute all partial derivatives for a single-hidden-layer network given a specific loss function and activation.
4. **Analyze:** Trace gradient flow through a computational graph, identifying which nodes contribute to the gradient of a given parameter.
5. **Create:** Construct the backpropagation rules for a novel network architecture by decomposing it into its computational graph.

---

## 1. Prerequisites

We assume you are comfortable with:

- **Matrix multiplication and broadcasting:** Multiplying a weight matrix by an input vector, adding a bias vector, and understanding the shapes involved.
- **The chain rule from calculus:** If \( y = g(u) \) and \( u = f(x) \), then \( \frac{dy}{dx} = \frac{dy}{du} \cdot \frac{du}{dx} \). For multivariate functions, the chain rule sums over all intermediate paths.
- **Elementary partial derivatives:** The identity \( \frac{\partial}{\partial \mathbf{W}} (\mathbf{W}\mathbf{x}) = \mathbf{x}^\top \) for a vector input, and the ability to differentiate common activation functions such as sigmoid, ReLU, or softmax.
- **The forward pass of a neural network:** Given an input, the network computes layer outputs sequentially to produce a prediction.

If any of these topics feel shaky, pause here and review them — they are the building blocks for everything that follows.

---

## 2. Motivation: The Gradient Computation Bottleneck

### 2.1 The Problem That Would Kill Deep Learning

In 1986, a paper by Rumelhart, Hinton, and Williams did something extraordinary: it resurrected neural networks from a decade of academic exile. The AI winter of the 1970s had frozen research after Marvin Minsky and Seymour Papert proved that single-layer perceptrons couldn't learn even the XOR function. The problem wasn't that multi-layer networks lacked expressive power — it was that no one knew how to train them efficiently. The gradient computation bottleneck had convinced the field that neural networks were a dead end.

**A puzzle to start with:** You're handed a black box with one million dials on its surface and a single display showing a number between 0 and 1. Your job: adjust all one million dials so that the display reads exactly 0.5. You can turn any dial by a tiny amount and watch the number change, but you must return each dial to its original position before testing the next one. How long will this take you? If each test takes one second, you'll need about 11.5 days of nonstop work — and that's for just *one* round of adjustments. If you need a thousand rounds to reach 0.5, you'll be there for over 31 years.

This is exactly the predicament of training a neural network without a smarter gradient algorithm. Training a neural network means adjusting its parameters \( \boldsymbol{\theta} \) to minimize a scalar cost function \( J(\boldsymbol{\theta}) \). The cost measures how wrong our predictions are. To improve, we need to know how each parameter influences the cost — that is, we need the gradient \( \nabla_{\boldsymbol{\theta}} J \).

Modern networks can have millions or billions of parameters. Computing each partial derivative individually by evaluating the network twice (once with a slightly perturbed parameter) is hopelessly slow. If the black box takes an hour per test, the one-dial-at-a-time approach stretches across millennia. We need an algorithm that computes the entire gradient in roughly the same time it takes to compute the cost itself.

**Try this yourself:** Before reading further, estimate how long a billion-parameter network would take to train using the "perturb one parameter at a time" method, assuming a single forward pass takes 10 milliseconds. What about 100 billion parameters? The numbers should make the necessity of backpropagation visceral.

### 2.2 The Core Intuition: Don't Repeat Yourself

Consider evaluating a deeply nested mathematical expression:

\[
z = \bigl( f(w) \bigr)^2
\]

You want \( \frac{dz}{dw} \). The chain rule gives:

\[
\frac{dz}{dw} = 2 f(w) \cdot f'(w)
\]

The quantity \( f(w) \) appears in two places: as the factor \( 2f(w) \) and inside \( f'(w) \). If you compute \( f(w) \) from scratch each time it appears, you do redundant work. The same redundancy explodes in a deep network: a single early parameter influences many downstream nodes, and each of those nodes recomputes the same intermediate values when we apply the chain rule naively.

**An analogy from city planning:** Imagine a city where every neighborhood independently computes the distance from City Hall to itself, each time tracing the entire road network from scratch. The result is millions of redundant calculations of the same arterial roads. A smarter approach: precompute the distance along each road segment once, then let every neighborhood sum the segments along its unique path. This is backpropagation's strategy — compute each road segment once, store it, reuse it.

**Backpropagation eliminates this redundancy** by computing every intermediate value once during the forward pass, storing it, and then reusing those stored values during the backward pass. The runtime becomes proportional to one forward pass plus one backward pass — a small constant factor overhead.

### 2.3 A Detailed Application: Training a Spam Classifier

To make the motivation concrete, consider training a logistic regression model — the simplest neural network — to classify emails as spam (\(y=1\)) or not spam (\(y=0\)). You have a dataset of 10,000 emails, each represented by a 1,000-dimensional feature vector \(\mathbf{x}^{(i)}\) (word frequencies, presence of suspicious headers, etc.). The model is:

\[
\hat{y}^{(i)} = \sigma(\mathbf{w}^\top \mathbf{x}^{(i)} + b), \quad \sigma(z) = \frac{1}{1+e^{-z}}
\]

The cross-entropy loss over the dataset is:

\[
J(\mathbf{w}, b) = -\frac{1}{N}\sum_{i=1}^{N} \left[ y^{(i)} \log \hat{y}^{(i)} + (1-y^{(i)}) \log(1-\hat{y}^{(i)}) \right]
\]

To update \(\mathbf{w} \in \mathbb{R}^{1000}\) and \(b \in \mathbb{R}\), you need \(\nabla_{\mathbf{w}} J\) and \(\frac{\partial J}{\partial b}\) — a total of 1,001 partial derivatives. Using the perturb-one-parameter method, each partial derivative requires two forward passes over the entire dataset of 10,000 examples. That is:

\[
1{,}001 \text{ parameters} \times 2 \text{ passes} \times 10{,}000 \text{ examples} = 20{,}020{,}000 \text{ forward passes per gradient evaluation}
\]

If each forward pass takes 1 millisecond, one gradient evaluation takes over 5.5 hours. Training typically requires hundreds or thousands of gradient steps — making this approach utterly infeasible.

**Before we see the solution, pause and predict:** We have 1,001 parameters and 10,000 examples. The naive method does 20 million forward passes. What would a "smart" method need to achieve to be practical? What is the theoretical minimum number of forward passes required to get all 1,001 partial derivatives? (Hint: each example must be processed at least once to contribute to the gradient.) Keep your answer in mind as we proceed.

Now apply backpropagation. The forward pass computes all \(\hat{y}^{(i)}\) and stores them. The backward pass computes:

\[
\frac{\partial J}{\partial \hat{y}^{(i)}} = \frac{1}{N}\left(\frac{\hat{y}^{(i)} - y^{(i)}}{\hat{y}^{(i)}(1-\hat{y}^{(i)})}\right)
\]

Then, for each example \(i\):

\[
\frac{\partial \hat{y}^{(i)}}{\partial z^{(i)}} = \sigma(z^{(i)})(1-\sigma(z^{(i)})) = \hat{y}^{(i)}(1-\hat{y}^{(i)}), \quad z^{(i)} = \mathbf{w}^\top \mathbf{x}^{(i)} + b
\]

The chain rule gives:

\[
\frac{\partial J}{\partial z^{(i)}} = \frac{\partial J}{\partial \hat{y}^{(i)}} \cdot \frac{\partial \hat{y}^{(i)}}{\partial z^{(i)}} = \frac{1}{N}(\hat{y}^{(i)} - y^{(i)})
\]

Notice how the \(\hat{y}^{(i)}(1-\hat{y}^{(i)})\) terms cancel elegantly — a property specific to the sigmoid–cross-entropy pair that backpropagation exploits automatically. The parameter gradients are then:

\[
\nabla_{\mathbf{w}} J = \sum_{i=1}^{N} \frac{\partial J}{\partial z^{(i)}} \mathbf{x}^{(i)}, \quad \frac{\partial J}{\partial b} = \sum_{i=1}^{N} \frac{\partial J}{\partial z^{(i)}}
\]

The entire gradient over all 1,001 parameters is computed in one forward pass (10,000 examples) and one backward pass (reusing stored \(\hat{y}^{(i)}\)). Total time: roughly 20 seconds instead of 5.5 hours — a speedup factor of approximately 1,000×. This is not an asymptotic curiosity; it is the difference between a model that trains during a coffee break and one that never finishes.

**Pause and reflect:** The cancellation we just witnessed — where the sigmoid derivative terms vanished — is not a coincidence. It's a deliberate design choice called a "canonical link function" in statistics. The sigmoid–cross-entropy pairing is the classification analog of linear–Gaussian models in regression. When you later design custom loss functions, ask yourself: can I pair my activation and loss so that the gradient simplifies? This principle — matching activation to loss for gradient cleanliness — shows up repeatedly, from softmax–cross-entropy to the reparameterization trick in variational autoencoders.

**Try this yourself:** Take the mean squared error loss \(J = \frac{1}{2}(\hat{y} - y)^2\) paired with a sigmoid activation \(\hat{y} = \sigma(z)\). Compute \(\frac{\partial J}{\partial z}\). Do the \(\sigma'(z)\) terms cancel cleanly? What happens to the gradient when \(\hat{y}\) is very close to 0 or 1? This exercise reveals why cross-entropy is strongly preferred over MSE for classification — the gradient of MSE-with-sigmoid vanishes precisely when the prediction is most confident but wrong, a phenomenon known as the "saturation problem."

### 2.4 Real-World Application: Medical Image Segmentation with U-Net

Beyond the simple spam classifier, backpropagation is the engine behind far more complex and impactful applications. Consider **U-Net**, a convolutional neural network architecture widely deployed in medical imaging for tasks like tumor segmentation in MRI scans or organ delineation in CT volumes.

A typical U-Net for 3D medical image segmentation might contain 30 million parameters. The input is a 3D volume (e.g., \(256 \times 256 \times 64\) voxels), and the output is a per-voxel probability map indicating whether each voxel belongs to a tumor. The loss function is typically a combination of Dice loss and cross-entropy, computed over millions of output voxels.

**Why backpropagation is indispensable here:** The U-Net architecture includes a contracting path (downsampling through convolution and pooling) and an expansive path (upsampling with skip connections). The skip connections mean that gradients must flow along multiple parallel routes — from deep bottleneck layers all the way back to early encoder layers, *and* directly through the skip pathways. The computational graph for this network has thousands of nodes with complex, non-sequential dependency structures.

Without backpropagation, computing even a single gradient evaluation for 30 million parameters via finite differences would require 60 million forward passes. At approximately 50 milliseconds per forward pass on a modern GPU for a volume of this size, that amounts to roughly 35 days per gradient step. Training typically requires 50,000–100,000 steps, making this approach completely impossible.

With backpropagation, the forward pass computes all intermediate feature maps and stores them. The backward pass propagates gradients from the output segmentation map back through the expansive path, across the skip connections, and down through the contracting path — all in roughly the same time as the forward pass. Each training step takes approximately 100 milliseconds, and full training completes in hours or days rather than millennia. This capability has directly enabled the deployment of deep learning in clinical settings, where U-Net models now assist radiologists in detecting and measuring tumors with accuracy approaching that of human experts.

### 2.5 Real-World Application: Neural Machine Translation

Another domain where backpropagation's efficiency is non-negotiable is **neural machine translation (NMT)**. Consider the Transformer architecture, which powers systems like Google Translate and DeepL. A large Transformer model processes variable-length sequences through dozens of attention layers, each computing pairwise interactions between all tokens in the input and output sequences.

A single training example might involve a 50-token English sentence and its 60-token French translation. The self-attention mechanism computes \(O(L^2)\) interactions per layer, where \(L\) is the sequence length. The computational graph for a 12-layer Transformer contains attention weight matrices, feed-forward networks, layer normalization, and residual connections — all composed into a deep DAG with extensive parameter sharing through the token positions.

**The gradient computation challenge:** The attention weights in layer 1 influence every subsequent layer, and the final loss (typically cross-entropy over the target vocabulary) depends on predictions at every output position. Computing \(\frac{\partial J}{\partial \mathbf{W}_Q^{(1)}}\) — the gradient with respect to the query weight matrix in the first layer — requires summing gradient contributions through all 12 layers and across all attention heads and token positions. The chain rule's "sum over all paths" becomes a sum over an exponential number of paths through the attention and feed-forward sublayers.

Backpropagation handles this by computing gradients layer-by-layer backward, accumulating contributions from all paths in time proportional to one forward pass. This is what makes training Transformers feasible: a single gradient step for a billion-parameter model takes seconds rather than years. The practical impact is measured in the quality of machine translation available today — systems trained using backpropagation handle hundreds of language pairs and serve billions of translations daily.

**Try this yourself:** Pick a sentence in your native language and translate it to English using Google Translate. Now imagine that every weight in the Transformer behind that translation had to be tuned by finite differences. The model that produced your translation was trained on billions of sentence pairs — each gradient step would require twice that many forward passes. The fact that you got a translation in under a second is a direct consequence of backpropagation's \(O(1)\) factor overhead relative to the forward pass.

### 2.6 Real-World Application: Autonomous Driving Perception

Backpropagation also underpins the perception systems in autonomous vehicles. Consider a **multi-task network** that simultaneously performs object detection, lane segmentation, and depth estimation from a single camera image. Such a network might use a shared ResNet-152 backbone (approximately 60 million parameters) with task-specific heads.

The input is a high-resolution image (e.g., \(1920 \times 1200\) pixels), and the outputs include bounding boxes for vehicles, pedestrians, and cyclists; pixel-wise lane markings; and a dense depth map. The total loss is a weighted sum of detection loss (e.g., Smooth L1 for bounding box regression plus cross-entropy for classification), segmentation loss (per-pixel cross-entropy), and depth regression loss (L1 or L2).

**Why backpropagation is critical:** The shared backbone means that gradients from all three task heads flow back into the same early convolutional layers. These layers must learn features useful for edge detection (important for all tasks), texture analysis (depth), and semantic understanding (classification) simultaneously. The gradient contributions from the three tasks must be properly balanced — if the detection loss dominates, the network may ignore lane markings; if segmentation loss overwhelms, depth accuracy suffers.

Backpropagation computes all these gradient contributions in one backward pass, summing the signals from the three heads at each shared layer. This enables end-to-end training of the entire multi-task system. Without backpropagation, training such a network would be computationally intractable, and the alternative — training separate networks for each task — would multiply inference cost and miss the opportunity for shared representations. The practical result is that a single forward pass through a trained multi-task network can produce all the perceptual outputs needed for real-time autonomous driving decisions, running at 30+ frames per second on specialized hardware.

**A thought experiment to internalize the stakes:** Imagine you're designing the perception system for a self-driving car. Your network must detect a child running into the street within 100 milliseconds. You have two choices: (a) a multi-task network trained end-to-end with backpropagation, running one forward pass in 30ms, or (b) three separate networks trained independently (because joint training without backpropagation is infeasible), each taking 30ms, running sequentially for 90ms total. In scenario (a), you have 70ms of slack for decision-making. In scenario (b), you have 10ms. The difference between backpropagation-enabled joint training and the alternative is not merely computational convenience — it is, quite literally, braking distance.

---

## 3. Computational Graphs: A Visual Language for Function Composition

### 3.1 Intuition Before Formalism

A neural network is a composition of operations: matrix multiply, add bias, apply activation, repeat. We can represent this composition as a **directed acyclic graph** (DAG) where:

- **Nodes** are variables (inputs, intermediate results, parameters, and the final cost).
- **Edges** point from inputs to the operation that consumes them.

For a simple linear layer \( \mathbf{z} = \mathbf{W}\mathbf{x} + \mathbf{b} \), the graph looks like:

\[
\mathbf{x} \rightarrow [\text{matmul with } \mathbf{W}] \rightarrow \mathbf{W}\mathbf{x} \rightarrow [\text{add } \mathbf{b}] \rightarrow \mathbf{z}
\]

Here \( \mathbf{W}\mathbf{x} \) and \( \mathbf{z} \) are nodes; \( \mathbf{W} \) and \( \mathbf{b} \) are also nodes (parameters we will eventually differentiate with respect to). The operations live on the edges.

**Why this matters:** The graph makes explicit what depends on what. Once you can see the dependency structure, the chain rule's "sum over all paths" becomes a visual traversal problem rather than an algebraic nightmare.

**An analogy from electrical engineering:** If you've studied circuit analysis, you've seen Kirchhoff's Current Law: the sum of currents entering a node equals the sum leaving it. Backpropagation on a computational graph obeys an analogous conservation principle. The gradient arriving at a node (like current entering a junction) must equal the sum of gradients flowing out to its parents (like current splitting across incoming branches). This isn't a loose metaphor — it's a direct consequence of the multivariate chain rule's linearity. If you can trace current through a circuit, you can trace gradients through a computational graph.

### 3.2 Formal Definition

Let the graph have nodes \( \{u^{(1)}, u^{(2)}, \ldots, u^{(n)}\} \) sorted in **topological order**: every edge goes from an earlier node to a later node. The final node \( u^{(n)} \) is the scalar cost \( J \).

For any node \( u^{(i)} \), its value is computed by applying an operation to its **parents** — the nodes with edges pointing into it. We write:

\[
u^{(i)} = f^{(i)}\bigl(\text{Pa}(u^{(i)})\bigr)
\]

The gradient we ultimately want is \( \frac{\partial u^{(n)}}{\partial u^{(i)}} \) for every node that is a parameter.

### 3.3 The Chain Rule on the Graph

The chain rule tells us how a change in node \( u^{(i)} \) propagates to the final cost. It flows **forward through the children** of \( u^{(i)} \). Formally:

\[
\frac{\partial u^{(n)}}{\partial u^{(i)}} = \sum_{j: u^{(i)} \in \text{Pa}(u^{(j)})} \frac{\partial u^{(n)}}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

**Interpretation:** The gradient of the final cost