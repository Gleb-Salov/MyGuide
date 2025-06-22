from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


if __name__ == '__main__':

    test_password = "<PASSWORD>"
    hashed_test_password = hash_password(test_password)
    print(hashed_test_password)

    if verify_password(test_password, hashed_test_password):
        print("Password verified")