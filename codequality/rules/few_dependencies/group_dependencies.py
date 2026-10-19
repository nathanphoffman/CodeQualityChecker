from .limits import FAMILY_SIZE_EXPONENT, RELATED_NAME_SHARE


def name_words(name):
    return set("".join(character if character.isalnum() else " " for character in name).split())


def are_related(first, second):
    """True when the names share at least RELATED_NAME_SHARE of all the words used in either name."""
    first_words, second_words = name_words(first), name_words(second)
    return len(first_words & second_words) / len(first_words | second_words) >= RELATED_NAME_SHARE


def find_families(names):
    """Groups of related names. If A is related to B and B to C, all three are one family."""
    families = []
    for name in sorted(names):
        related = [family for family in families if any(are_related(name, member) for member in family)]
        families = [family for family in families if family not in related]
        families.append([name, *[member for family in related for member in family]])
    return families


def effective_count(dependencies):
    """Dependencies as {(where from, name)}, counting each family of related names as the square root of its size."""
    total = 0.0
    for ecosystem in {ecosystem for ecosystem, _ in dependencies}:
        names = [name for where, name in dependencies if where == ecosystem]
        total += sum(len(family) ** FAMILY_SIZE_EXPONENT for family in find_families(names))
    return total
