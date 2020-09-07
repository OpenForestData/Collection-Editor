from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from core.serializers.user import MinimalUserSerializer


@api_view(['GET'])
def get_current_user(request: Request):
    """
    Returns current User data

    .. http:get:: /user/me

        :reqheader Authorization: optional Bearer (JWT) token to authenticate
        :statuscode 200: returns serialized data of current `User`
        :statuscode 401: user unauthorized
    """

    user = request.user
    serializer = MinimalUserSerializer(user)
    return Response(serializer.data)
