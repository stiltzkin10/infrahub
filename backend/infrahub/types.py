import graphene
from graphene.types.generic import GenericScalar

from infrahub.core import registry


class InfrahubDataType:
    label: str
    graphql_query: str
    graphql_input: str
    graphql_filter: type
    graphql: type
    infrahub: str

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        registry.data_type[cls.label] = cls

    def __str__(self):
        return self.label

    @classmethod
    def get_infrahub_class(cls):
        return registry.attribute[cls.infrahub]

    @classmethod
    def get_graphql_input(cls):
        return registry.input_type[cls.graphql_input]

    @classmethod
    def get_graphql_type(cls):
        return registry.default_graphql_type[cls.graphql_input]

    @classmethod
    def get_graphql_type_name(cls):
        return registry.default_graphql_type[cls.graphql_input].__name__


class ID(InfrahubDataType):
    label: str = "ID"
    graphql = graphene.ID
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class Text(InfrahubDataType):
    label: str = "Text"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class TextArea(Text):
    label: str = "TextArea"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class DateTime(InfrahubDataType):
    label: str = "DateTime"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class Email(InfrahubDataType):
    label: str = "Email"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class Password(InfrahubDataType):
    label: str = "Password"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class URL(InfrahubDataType):
    label: str = "URL"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class File(InfrahubDataType):
    label: str = "File"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class MacAddress(InfrahubDataType):
    label: str = "MacAddress"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class Color(InfrahubDataType):
    label: str = "Color"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class Number(InfrahubDataType):
    label: str = "Number"
    graphql = graphene.Int
    graphql_query = "NumberAttributeType"
    graphql_input = "NumberAttributeInput"
    graphql_filter = graphene.Int
    infrahub = "Integer"


class Bandwidth(InfrahubDataType):
    label: str = "Bandwidth"
    graphql = graphene.Int
    graphql_query = "NumberAttributeType"
    graphql_input = "NumberAttributeInput"
    graphql_filter = graphene.Int
    infrahub = "Integer"


class IPHost(InfrahubDataType):
    label: str = "IPHost"
    graphql = graphene.Int
    graphql_query = "NumberAttributeType"
    graphql_input = "NumberAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class IPNetwork(InfrahubDataType):
    label: str = "IPNetwork"
    graphql = graphene.Int
    graphql_query = "NumberAttributeType"
    graphql_input = "NumberAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class Checkbox(InfrahubDataType):
    label: str = "Checkbox"
    graphql = graphene.Boolean
    graphql_query = "CheckboxAttributeType"
    graphql_input = "CheckboxAttributeInput"
    graphql_filter = graphene.Boolean
    infrahub = "String"


class List(InfrahubDataType):
    label: str = "List"
    graphql = GenericScalar
    graphql_query = "ListAttributeType"
    graphql_input = "ListAttributeInput"
    graphql_filter = GenericScalar
    infrahub = "ListAttribute"


class Any(InfrahubDataType):
    label: str = "Any"
    graphql = GenericScalar
    graphql_query = "AnyAttributeType"
    graphql_input = "AnyAttributeInput"
    graphql_filter = GenericScalar
    infrahub = "AnyAttribute"


# ------------------------------------------
# Deprecated
# ------------------------------------------
class String(InfrahubDataType):
    label: str = "String"
    graphql = graphene.String
    graphql_query = "TextAttributeType"
    graphql_input = "TextAttributeInput"
    graphql_filter = graphene.String
    infrahub = "String"


class Integer(InfrahubDataType):
    label: str = "Integer"
    graphql = graphene.Int
    graphql_query = "NumberAttributeType"
    graphql_input = "NumberAttributeInput"
    graphql_filter = graphene.Int
    infrahub = "Integer"


class Boolean(InfrahubDataType):
    label: str = "Boolean"
    graphql = graphene.Boolean
    graphql_query = "CheckboxAttributeType"
    graphql_input = "CheckboxAttributeInput"
    graphql_filter = graphene.Boolean
    infrahub = "Boolean"
