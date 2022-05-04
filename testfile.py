import BillSplitterApp.backend.mongodb as backendService
import random, string


def create_group():
        randomcode = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        return randomcode

print(create_group())