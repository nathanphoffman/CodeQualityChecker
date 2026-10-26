from dataclasses import dataclass

@dataclass
class Type_Info:
    name: str
    line_number: int
    fields: int  # struct and class fields, enum variants and component props
    methods: int
