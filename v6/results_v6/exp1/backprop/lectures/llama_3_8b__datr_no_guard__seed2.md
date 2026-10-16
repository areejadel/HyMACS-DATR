**Backpropagation in Neural Networks**

**Learning Objectives:**
By the end of this chapter, students will be able to:
1. Define and explain the concept of back-propagation in neural networks, using the analogy of a bungee jumper to illustrate how errors propagate backwards.
2. Describe the role of back-propagation in the training of neural networks, drawing a connection to the process of editing a manuscript by tracing back changes.
3. Illustrate the application of back-propagation in computing the gradient of the cost function with respect to the model's parameters, using the "try this yourself" prompt to encourage hands-on experimentation.

Backpropagation is a fundamental concept in deep learning, enabling the computation of the gradient of the cost function with respect to the model's parameters. This algorithm is often referred to as back-propagation or backprop (Rumelhart et al., 1986a). During training, forward propagation can continue onward until it produces a scalar cost J(θ). But what if we could turn back the clock and retrace our steps to correct mistakes? This is where backpropagation comes in, allowing the information from the cost to flow backwards through the network, computing the gradient (Goodfellow et al., 2016).

To illustrate the practical relevance of backpropagation, let's consider a real-world scenario: natural language processing with recurrent neural networks (RNNs). In this context, backpropagation is used to optimize the model's parameters, allowing the network to learn the most relevant features for language modeling. For example, in a study by Graves et al. (2013), the authors used backpropagation to train an RNN for language modeling, achieving state-of-the-art results on the Penn Treebank dataset. This application of backpropagation demonstrates its effectiveness in practical scenarios.

The back-propagation algorithm allows us to do just that, by filling in a table with intermediate results. Each node in the graph has a corresponding slot in a table to store the gradient for that node. By filling in these table entries in order, back-propagation avoids repeating many common subexpressions (Goodfellow et al., 2016). It's like solving a puzzle, where each piece fits together to reveal the complete picture.

Imagine a game of chess, where each piece represents a node in the neural network. As the game progresses, each piece moves, influencing the next one to move. In backpropagation, we play this game in reverse, starting with the final piece and working our way back to the first. This algorithm is particularly useful in computing the gradient of the cost function, as it allows us to do so efficiently, without having to recompute intermediate results. We can also think of it as a game of "undo" – we're essentially undoing the forward pass to compute the gradient.

Backpropagation is closely related to the concept of dynamic programming, where we break down a complex problem into smaller sub-problems and solve them iteratively. In backpropagation, we are essentially doing the same thing, but instead of solving sub-problems, we are solving sub-gradients. This connection highlights the importance of backpropagation in machine learning, as it allows us to efficiently compute the gradient of complex cost functions.

**The Backpropagation Algorithm**

The backpropagation algorithm can be summarized as follows:

1. Compute the output of the neural network for a given input.
2. Compute the error between the predicted output and the actual output.
3. Compute the gradient of the error with respect to the output of each node in the network.
4. Compute the gradient of the error with respect to the weights and biases of each node in the network.
5. Update the weights and biases of each node in the network using the gradient descent algorithm.

**Example: Back-Propagation for MLP Training**

Let's walk through the back-propagation algorithm as it is used to train a multilayer perceptron. We'll develop a simple multilayer perception with a single hidden layer. To train this model, we'll use minibatch stochastic gradient descent. The back-propagation algorithm is used to compute the gradient of the cost on a single minibatch (Goodfellow et al., 2016). Try using this algorithm to train a simple neural network, and see how it can help you optimize your model's performance.

**Minibatch Stochastic Gradient Descent**

We'll use a minibatch of examples from the training set, formatted as [4]. This minibatch is used to update the model's parameters, and the process is repeated for each iteration until convergence is reached.