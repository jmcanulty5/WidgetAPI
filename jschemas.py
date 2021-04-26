widget_schema = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "maxLength": 64,
        },
        "num_of_parts": {
            "type": "integer"
        },
        "created_date": {
            "type": "string",
            "format": "date"
        },
        "updated_date": {
            "type": "string",
            "format": "date"
        }
    },
    "required": [
        "name",
        "num_of_parts",
        "created_date",
        "updated_date"
    ]
}

cond_spec_schema = {
        "type": "array",
        "items": {
            "oneOf": [
                {  # universal unary predicates (just use variable. no constant)
                    "type": "object",
                    "properties": {
                        "predicate": {
                            "enum": [
                                "isnull",
                                "not isnull"
                            ]
                        },
                        "variable": {
                            "enum": [
                                'name',
                                'num_of_parts',
                                'created_date',
                                'updated_date'
                            ]
                        },
                        "constants": {
                            "type": "array",
                            "minItems": 0,
                            "maxItems": 0
                        }
                    },
                    "required": [
                        "predicate",
                        "variable",
                        "constants"
                    ]
                },
                {  # universal binary predicates (left arg will be variable, right a constant)
                    "type": "object",
                    "properties": {
                        "predicate": {
                            "enum": [
                                "eq",
                                "ne",
                                "lt",
                                "gt",
                                "ge",
                                "le",
                                "like",
                                "not like"
                            ]
                        },
                        "variable": {
                            "enum": [
                                'name',
                                'num_of_parts',
                                'created_date',
                                'updated_date'
                            ]
                        },
                        "constants": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 1
                        }
                    },
                    "required": [
                        "predicate",
                        "variable",
                        "constants"
                    ]
                },
                {  # universal ternary predicates (leftmost arg is variable, others are constants)
                    "type": "object",
                    "properties": {
                        "predicate": {
                            "enum": [
                                "between",
                                "not between"
                            ]
                        },
                        "variable": {
                            "enum": [
                                'name',
                                'num_of_parts',
                                'created_date',
                                'updated_date'
                            ]
                        },
                        "constants": {
                            "oneOf": [
                                {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 2,
                                    "maxItems": 2
                                },
                                {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "minItems": 2,
                                    "maxItems": 2
                                }
                            ]
                        },
                    },
                    "required": [
                        "predicate",
                        "variable",
                        "constants"
                    ]
                }
            ]
        },
        "maxItems": 15
    }
