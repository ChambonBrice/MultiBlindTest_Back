caracspe = "&~¨£%µ§/.?^$*ù!:;,-*/+"

def motdepassesecu(mdp):

    if len(mdp) < 10:
        raise ValueError("Mot de passe trop court")

    elif not any(c in caracspe for c in mdp):
        raise ValueError("Pas de caractère spécial")

    elif not any(c.isdigit() for c in mdp):
        raise ValueError("Pas de chiffre")

    elif not any(c.isupper() for c in mdp):
        raise ValueError("Pas de majuscule dans le mot de passe")

    else:
        return True