# from aiohttp_apispec import request_schema, response_schema
# from aiohttp_session import new_session
#
# from app.admin.schemes import AdminSchema
# from app.web.app import View
# from aiohttp.web import HTTPForbidden, HTTPUnauthorized
#
# from app.web.utils import json_response
#
#
# class AdminLoginView(View):
#     @request_schema(AdminSchema)
#     @response_schema(AdminSchema, 200)
#     async def post(self):
#         email, password = self.data["email"], self.data["password"]
#         admin = await self.store.admins.get_by_email(email)
#         if not admin or not admin.is_password_valid(password):
#             raise HTTPForbidden
#         admin_data = AdminSchema().dump(admin)
#         response = json_response(data=admin_data)
#         session = await new_session(request=self.request)
#         session["admin"] = admin_data
#         return response
#
#
# class AdminCurrentView(View):
#     @response_schema(AdminSchema, 200)
#     async def get(self):
#         if self.request.admin:
#             return json_response(data=AdminSchema().dump(self.request.admin))
#         raise HTTPUnauthorized