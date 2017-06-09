import ast

__all__ = ['safe_eval']


def safe_eval(literal):
    """
    Evaluate a literal value or fall back to string

    Safely performs the evaluation of a literal. If the literal is not valid,
    it is assumed to be a regular string and returned unchanged.

    :param literal: literal to evaluate, e.g. `"1.0"` or `"{'foo': 3}"`
    :type literal: str
    :return: evaluated or original literal
    """
    try:
        return ast.literal_eval(literal)
    except (ValueError, SyntaxError):
        return literal
