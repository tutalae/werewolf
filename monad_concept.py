from pymonad.maybe import Maybe, Just, Nothing
from pymonad.either import Left, Right
from pymonad.tools import curry

@curry(2)
def add(x, y):
    return x + y

@curry(2)
def div(y, x):
    return Nothing if y == 0 else Just(x / y)

# Example usage
print(add(2, 3))  # Prints '5'

add2 = add(2)
print(add2(3))  # Prints '5'

m = (Maybe.insert(2)
     .then(add(2))
     .then(div(4))
)

print(m)  # Just 1.0

a = Right(2)
b = Left('Invalid')

print(a.either(lambda x: f'Sorry, {x}', lambda x: x))  # Prints 2
print(b.either(lambda x: f'Sorry, {x}', lambda x: x))  # Prints 'Sorry, Invalid'
