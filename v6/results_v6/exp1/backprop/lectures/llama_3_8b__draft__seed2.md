**Backpropagation in Neural Networks**

**Learning Objectives:**
By the end of this chapter, students will be able to:
1. Define and explain the concept of back-propagation in neural networks, using the analogy of a bungee jumper to illustrate how errors propagate backwards.
2. Describe the role of back-propagation in the training of neural networks, drawing a connection to the process of editing a manuscript by tracing back changes.
3. Illustrate the application of back-propagation in computing the gradient of the cost function with respect to the model's parameters, using the "try this yourself" prompt to encourage hands-on experimentation.

Backpropagation is a fundamental concept in deep learning, enabling the computation of the gradient of the cost function with respect to the model's parameters. This algorithm is often referred to as back-propagation or backprop (Rumelhart et al., 1986a). During training, forward propagation can continue onward until it produces a scalar cost J(θ). But what if we could turn back the clock and retrace our steps to correct mistakes? This is where backpropagation comes in, allowing the information from the cost to flow backwards through the network, computing the gradient (Goodfellow et al., 2016).

The back-propagation algorithm allows us to do just that, by filling in a table with intermediate results. Each node in the graph has a corresponding slot in a table to store the gradient for that node. By filling in these table entries in order, back-propagation avoids repeating many common subexpressions (Goodfellow et al., 2016). It's like solving a puzzle, where each piece fits together to reveal the complete picture.

**The Backpropagation Algorithm**

Imagine a game of dominoes, where each domino represents a node in the neural network. As the game progresses, each domino falls, influencing the next one to fall. In backpropagation, we play this game in reverse, starting with the final domino and working our way back to the first. This algorithm is particularly useful in computing the gradient of the cost function, as it allows us to do so efficiently, without having to recompute intermediate results.

**Example: Back-Propagation for MLP Training**

Let's walk through the back-propagation algorithm as it is used to train a multilayer perceptron. We'll develop a simple multilayer perception with a single hidden layer. To train this model, we'll use minibatch stochastic gradient descent. The back-propagation algorithm is used to compute the gradient of the cost on a single minibatch (Goodfellow et al., 2016). Try using this algorithm to train a simple neural network, and see how it can help you optimize your model's performance.

**Minibatch Stochastic Gradient Descent**

We'll use a minibatch of examples from the training set, formatted as [4]. This minibatch is used to compute the gradient of the cost on a single minibatch. We'll then use this gradient to update the model's parameters. Think of it like editing a manuscript by tracing back changes – we're making adjustments to the model's parameters based on the feedback from the cost function.

**Conclusion**

Backpropagation is a fundamental concept in deep learning, enabling the computation of the gradient of the cost function with respect to the model's parameters. This algorithm is particularly useful in computing the gradient of the cost function, as it allows us to do so efficiently, without having to recompute intermediate results. By understanding how backpropagation works, you'll be better equipped to train your own neural networks and optimize their performance. So go ahead, try it out for yourself, and see the magic of backpropagation in action!