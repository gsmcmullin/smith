
# Electromagnetic transformations
def z_to_gamma(z):
    return (z - 1) / (z + 1)

def gamma_to_z(gamma):
    return -(gamma + 1) / (gamma - 1)

def gamma_to_swr(gamma):
    return (1 + abs(gamma)) / (1 - abs(gamma))

