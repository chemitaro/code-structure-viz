class Safe:
    pass


__import__("private.module")
load = __import__
load("another.module")


def wrapper(name):
    return __import__(name)


wrapper("third.module")
