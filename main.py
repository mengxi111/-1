def add(a: int, b: int) -> int:
    return a + b


result = add(1, 2)
print(result)

from typing import List, Dict

def process_messages(messages: List[str]) -> Dict[str, int]:
    return {
        "count": len(messages)
    }

print(process_messages(["hi", "hello"]))

from typing import Optional

def greet(name: Optional[str] = None) -> str:
    if name is None:
        return "hello stranger"
    return f"hello {name}"

print(greet())