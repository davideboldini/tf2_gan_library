'''
    Improved Training of Wasserstein GANs
    Ref:
        https://arxiv.org/abs/1704.00028
'''

import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Conv2D, GlobalAveragePooling2D, LeakyReLU, Conv2DTranspose
from tensorflow.keras.optimizers import Adam

def build_generator(input_shape):
    x = Input(input_shape)

    y = Conv2DTranspose(512, (3, 3), strides=(2,2), padding="same")(x)
    y = LeakyReLU(0.2)(y)

    y = Conv2DTranspose(256, (3, 3), strides=(2,2), padding="same")(y)
    y = LeakyReLU(0.2)(y)

    y = Conv2DTranspose(128, (3, 3), strides=(2,2), padding="same")(y)
    y = LeakyReLU(0.2)(y)

    y = Conv2DTranspose(64, (3, 3), strides=(2,2), padding="same")(y)
    y = LeakyReLU(0.2)(y)

    y = Conv2D(3, (3, 3), padding="same", activation="tanh")(y)
    return Model(x, y)

def build_discriminator(input_shape):
    x = Input(input_shape)

    y = Conv2D(64, (3, 3), strides=(2,2), padding="same")(x)
    y = LeakyReLU(0.2)(y)

    y = Conv2D(128, (3, 3), strides=(2,2), padding="same")(y)
    y = LeakyReLU(0.2)(y)

    y = Conv2D(256, (3, 3), strides=(2,2), padding="same")(y)
    y = LeakyReLU(0.2)(y)

    y = Conv2D(512, (3, 3), strides=(2,2), padding="same")(y)
    y = LeakyReLU(0.2)(y)

    y = GlobalAveragePooling2D()(y)
    y = Dense(1)(y)
    return Model(x, y)


def build_train_step(generator, discriminator):
    d_optimizer = Adam(learning_rate=0.0001, beta_1=0.0, beta_2=0.9)
    g_optimizer = Adam(learning_rate=0.0001, beta_1=0.0, beta_2=0.9)

    @tf.function
    def train_step(real_image, noise):

        fake_image = generator(noise)
        pred_real, pred_fake = tf.split(discriminator(tf.concat([real_image, fake_image], axis=0)), num_or_size_splits=2, axis=0)


        alpha = tf.random.uniform((tf.shape(real_image)[0],1,1,1), 0.0, 1.0)
        interpolates = (1 - alpha) * real_image + alpha * fake_image
        grad = tf.gradients(discriminator(interpolates), [interpolates])[0]
        norm_grad = tf.sqrt(tf.reduce_sum(tf.square(grad), axis=[1, 2, 3]) + 1e-8)
        grad_penalty = tf.reduce_mean(tf.square(norm_grad - 1))


        LAMBA = 10
        d_loss = tf.reduce_mean(pred_fake) - tf.reduce_mean(pred_real) + LAMBA * grad_penalty
        g_loss = -tf.reduce_mean(pred_fake)

        d_gradients = tf.gradients(d_loss, discriminator.trainable_variables)
        g_gradients = tf.gradients(g_loss, generator.trainable_variables)

        d_optimizer.apply_gradients(zip(d_gradients, discriminator.trainable_variables))
        g_optimizer.apply_gradients(zip(g_gradients, generator.trainable_variables))

        return d_loss, g_loss

    return train_step
