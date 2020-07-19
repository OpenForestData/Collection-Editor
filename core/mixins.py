from rest_framework.serializers import Serializer


class MultiSerializerMixin:
    """
    Mixin allowing for different serializers for different ViewSet methods

    ViewSet using this mixin should implement special mapping under ``serializers`` variable.

    **Example mapping**

    .. sourcecode:: python

        serializers = {
            'default': DefaultSerializer,
            'list': ReadOnlySerializer,
            'create': CreateSerializer
        }
    """
    serializers = {
        'default': None,
    }

    def get_serializer_class(self) -> Serializer:
        """
        Gets serializer based on ViewSet method that called this function

        :return: serializer serving given action
        """
        return self.serializers.get(self.action, self.serializers['default'])
