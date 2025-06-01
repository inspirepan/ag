import asyncio
import inspect
import json
from typing import Annotated, Callable, Union, get_args, get_origin

from rich.live import Live
from rich.text import Text

from .stdout import console, print_message
from .utils import snake_to_pascal


class Tool:
    def __init__(self, name: str, description: str, parameters: dict, func: Callable):
        self.name = name
        self.nice_name = snake_to_pascal(name)
        self.description = description
        self.func = func
        self.parameters = parameters

    async def __call__(self, input: Union[str, dict]):
        return await self.invoke_async(input)

    async def invoke_async(self, input: Union[str, dict]):
        if isinstance(input, str):
            input_dict = json.loads(input)
        else:
            input_dict = input

        nice_print_input = next(iter(input_dict.values())) if len(input_dict) == 1 else ",".join([f"{k}: {v}" for k, v in input_dict.items()])
        print_message(f"[bold]{self.nice_name}[/bold]({nice_print_input})", mark_style="green", end_new_line=False)
        console.incr_indent()

        try:
            if inspect.iscoroutinefunction(self.func):
                result = await self.func(**input_dict)
            else:
                result = self.func(**input_dict)
        except Exception as e:
            result = f"Tool {self.name} failed: {e}"
        finally:
            print_message(f"{result}", mark="⎿", mark_style=None)
            console.decr_indent()
            return result

    def __str__(self) -> str:
        return self.json_schema()

    def __repr__(self) -> str:
        return self.json_schema()

    def schema(self):
        return {
            "type": "function",
            "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.parameters
            }
        }

    def json_schema(self):
        return json.dumps(self.schema())


def tool(description: str = ""):
    """@tool: support int, str, bool, list, dict, Annotated"""
    def decorator(func):
        final_description = description if description else func.__doc__
        properties = convert_func_parameters_to_json_schema(func.__annotations__)
        required = []
        for p in properties:
            if func.__defaults__ and p in func.__defaults__:
                properties[p]["default"] = func.__defaults__[p]
            else:
                required.append(p)
        parameters = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        tool = Tool(func.__name__, final_description, parameters, func)
        return tool
    return decorator


def convert_func_parameters_to_json_schema(annotation: dict) -> dict:

    def convert_type_to_json_schema(type_hint) -> dict:
        actual_type = type_hint
        description = ""

        # Handle Annotated types
        if get_origin(type_hint) is Annotated:
            actual_type, *metadata = get_args(type_hint)
            description = metadata[0] if metadata else ""

        # Get the origin type for generic types like list[str], dict[str, int]
        origin_type = get_origin(actual_type)
        type_args = get_args(actual_type)

        schema = {"description": description} if description else {}

        # Handle basic types
        if actual_type == int:
            schema["type"] = "integer"
        elif actual_type == str:
            schema["type"] = "string"
        elif actual_type == bool:
            schema["type"] = "boolean"
        elif actual_type == list or origin_type is list:
            schema["type"] = "array"
            # Handle typed lists like list[str], list[dict], etc.
            if type_args:
                item_type = type_args[0]
                schema["items"] = convert_type_to_json_schema(item_type)
        elif actual_type == dict or origin_type is dict:
            schema["type"] = "object"
            # Handle typed dicts like dict[str, int]
            if type_args and len(type_args) == 2:
                # For dict[str, ValueType], we set additionalProperties to the value type schema
                key_type, value_type = type_args
                if key_type == str:  # JSON only supports string keys
                    schema["additionalProperties"] = convert_type_to_json_schema(value_type)
                else:
                    # If key is not string, treat as generic object
                    schema["additionalProperties"] = True
            else:
                # Generic dict without type hints
                schema["additionalProperties"] = True
        else:
            # Fallback for unsupported types
            schema["type"] = "string"
            if not description:
                schema["description"] = f"Unsupported type: {actual_type}"

        return schema

    properties = {}
    for arg_name, arg_type in annotation.items():
        if arg_name == "return":
            continue
        properties[arg_name] = convert_type_to_json_schema(arg_type)

    return properties


# TEST
# ----------


def test_tool_decorator():
    @tool("A tool that help you compare numbers. Return True if x is greater than y, otherwise return False.")
    def compare_numbers(x: Annotated[int, "The first number to compare."], y: Annotated[int, "The second number to compare."]) -> bool:
        return x > y

    # Test basic types
    print("Basic types test:")
    print(compare_numbers.json_schema())
    print(json.dumps(compare_numbers))

    # Test nested types
    @tool("A tool that processes complex data structures.")
    def process_data(
        items: Annotated[list[str], "List of string items"],
        metadata: Annotated[dict[str, int], "Metadata with string keys and integer values"],
        nested_list: Annotated[list[dict[str, bool]], "List of dictionaries with string keys and boolean values"],
        simple_dict: dict,
        simple_list: list
    ) -> dict:
        pass

    print("\nNested types test:")
    print(process_data.json_schema())

    # Test the schema structure
    schema = process_data.schema()
    properties = schema["function"]["parameters"]["properties"]

    # Verify items (list[str])
    assert properties["items"]["type"] == "array"
    assert properties["items"]["items"]["type"] == "string"

    # Verify metadata (dict[str, int])
    assert properties["metadata"]["type"] == "object"
    assert properties["metadata"]["additionalProperties"]["type"] == "integer"

    # Verify nested_list (list[dict[str, bool]])
    assert properties["nested_list"]["type"] == "array"
    assert properties["nested_list"]["items"]["type"] == "object"
    assert properties["nested_list"]["items"]["additionalProperties"]["type"] == "boolean"

    # Verify simple types
    assert properties["simple_dict"]["type"] == "object"
    assert properties["simple_list"]["type"] == "array"

    print("All tests passed!")


if __name__ == "__main__":
    test_tool_decorator()
