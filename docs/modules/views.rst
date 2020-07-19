API Views
=======

Datatable
---------
.. autoclass:: core.views.datatable.DatatableViewSet
    :members:

    .. method:: list(self, request, *args, **kwargs)

        Returns list of all Datatables

        .. http:get:: /datatable/

            :query offset: offset number. default is 0
            :query limit: limit number. default is 100
            :reqheader Authorization: optional Bearer (JWT) token to authenticate
            :statuscode 200: no error
            :statuscode 401: user unauthorized
            :statuscode 403: user lacks permissions for this action

    .. method:: create(self, request, *args, **kwargs)

        Creates a Datatable

        .. http:post:: /datatable/

            :param title: Datatable title
            :param file: `csv` or `excel` tabular file
            :param optional collection_name: unique name of table to be created in DB to store Datatable rows,
                    if not supplied collection_name will be slugified title
            :reqheader Authorization: optional Bearer (JWT) token to authenticate
            :reqheader Content-Type: multipart/form-data
            :statuscode 200: no error
            :statuscode 400: collection_name isn't unique
            :statuscode 401: user unauthorized
            :statuscode 403: user lacks permissions for this action



DatatableAction
---------------
.. autoclass:: core.views.datatable_action.DatatableActionViewSet
    :members: revert

    .. method:: list(self, request, *args, **kwargs)

        Returns list of all DatatablesActions

        .. http:get:: /datatable/actions/

            :query offset: offset number. default is 0
            :query limit: limit number. default is 100
            :reqheader Authorization: optional Bearer (JWT) token to authenticate
            :statuscode 200: no error
            :statuscode 401: user unauthorized
            :statuscode 403: user lacks permissions for this action