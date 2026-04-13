import codecs
import json
from lark import Lark, Transformer, v_args
import logging

logger = logging.getLogger(__name__)

# Define the PNQL grammar using Lark
pnql_grammar = """
    ?start: query

    ?query: "SELECT" "*" "FROM" service_name [WHERE_CLAUSE] -> select_all
          | "SELECT" field_list "FROM" service_name [WHERE_CLAUSE] -> select_fields
          | "SCAN" target_spec "USING" tool_list [WITH_CLAUSE] -> scan_command
          | "SHOW" target_spec [WHERE_CLAUSE] -> show_command

    field_list: field ("," field)*
    field: CNAME

    service_name: CNAME

    WHERE_CLAUSE: "WHERE" condition
    condition: CNAME "=" ESCAPED_STRING        -> equals_condition
             | CNAME "CONTAINS" ESCAPED_STRING -> contains_condition
             | CNAME comparison_op NUMBER      -> numeric_condition
             | "(" condition ")"
             | condition "AND" condition       -> and_condition
             | condition "OR" condition        -> or_condition
             | "NOT" condition                 -> not_condition

    comparison_op: ">" | "<" | ">=" | "<=" | "==" | "!="

    target_spec: CNAME | ESCAPED_STRING

    tool_list: CNAME ("," CNAME)*

    WITH_CLAUSE: "WITH" option_list
    option_list: option ("," option)*
    option: CNAME "=" ESCAPED_STRING


    %import common.CNAME
    %import common.NUMBER
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""


@v_args(inline=True)  # Affects the signatures of the methods in the transformer
class PNQLTransformer(Transformer):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def select_all(self, service):
        return {"command": "SELECT", "type": "all", "service": service}

    def select_fields(self, fields, service):
        return {
            "command": "SELECT",
            "type": "fields",
            "fields": list(fields),
            "service": service,
        }

    def scan_command(self, target, tools, options=None):
        return {
            "command": "SCAN",
            "target": target,
            "tools": list(tools),
            "options": options if options else {},
        }

    def show_command(self, target, condition=None):
        return {"command": "SHOW", "target": target, "condition": condition}

    def field_list(self, *items):
        return list(items)

    def tool_list(self, *items):
        return list(items)

    def option_list(self, *items):
        return dict(items)

    def option(self, key, value):
        return key, self._unescape_string(value)

    def equals_condition(self, field, value):
        return {"field": field, "operator": "=", "value": self._unescape_string(value)}

    def contains_condition(self, field, value):
        return {
            "field": field,
            "operator": "CONTAINS",
            "value": self._unescape_string(value),
        }

    def numeric_condition(self, field, op, value):
        return {
            "field": field,
            "operator": op,
            "value": float(value),
        }  # Convert number to float

    def and_condition(self, left, right):
        return {"operator": "AND", "left": left, "right": right}

    def or_condition(self, left, right):
        return {"operator": "OR", "left": left, "right": right}

    def not_condition(self, condition):
        return {"operator": "NOT", "condition": condition}

    def service_name(self, name):
        return str(name)

    def field(self, name):
        return str(name)

    def target_spec(self, value):
        return self._unescape_string(value)

    def _unescape_string(self, s):
        """Removes quotes and unescapes standard string escapes."""
        if s.startswith('"') and s.endswith('"'):
            return codecs.decode(s[1:-1], "unicode_escape")
        return s


pnql_parser = Lark(pnql_grammar, parser="lalr", transformer=PNQLTransformer())


def parse_query(query_string: str) -> dict:
    """
    Parses a PNQL query string into a structured dictionary.
    """
    try:
        parsed_ast = pnql_parser.parse(query_string)
        logger.info(f"Successfully parsed query: {query_string}")
        return parsed_ast
    except Exception as e:
        logger.error(f"Failed to parse PNQL query '{query_string}': {e}", exc_info=True)
        raise ValueError(f"Invalid PNQL query: {e}")


if __name__ == "__main__":
    # Test cases
    queries = [
        'SELECT * FROM logs WHERE severity = "HIGH"',
        'SELECT timestamp, source FROM alerts WHERE type CONTAINS "malware"',
        'SCAN domain("example.com") USING nmap, nuclei WITH port="80,443", rate="5"',
        'SHOW processes WHERE parent="cmd.exe" AND NOT (user = "SYSTEM" OR process_name = "svchost.exe")',
    ]

    for q in queries:
        try:
            result = parse_query(q)
            print(f"\nQuery: {q}\nParsed: {json.dumps(result, indent=2)}")
        except ValueError as e:
            print(f"\nQuery: {q}\nError: {e}")
