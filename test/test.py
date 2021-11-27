# class Name:
#     def __init__(self, camera_id=1):
#         """
#         camera_id: 1: Apple (Basler pulse), 2: Human (regular camera)
#         """
#         self.camera_id = camera_id
#         self.camera = None
#         self.converter = None
#         self.b = [2] * (2 * 10 ** 7)
#         a = [4] * (2 * 10 ** 7)
#         a = [7] * (2 * 10 ** 7)
#         self.a = [6] * (2 * 10 ** 7)
#
# class Camera:
#     def __init__(self, camera_id=1):
#         """
#         camera_id: 1: Apple (Basler pulse), 2: Human (regular camera)
#         """
#         self.camera_id = camera_id
#         self.camera = Name()
#         self.converter = Name()
#
#     # def export(self):
#     #     # self.converter.get_a()
#     #     return self.camera
#
#     def __del__(self):
#         del self.camera
#         # del self.converter
#
#
# @profile
# def check():
#     t = Camera()
#     c = t
#     # from copy import copy, deepcopy
#     # d = deepcopy(t)
#     del c
#     del t
#     # del d
#     u = 0
#     u = u + 1
#
#
# check()
