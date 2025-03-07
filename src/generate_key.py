from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(f'ENCRYPTION_KEY="{key.decode()}"')