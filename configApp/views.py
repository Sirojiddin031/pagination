import random
from configApp.models import Student
from configApp.serializers import StudentSerializer
from configApp.pagination import StudentPagination
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.generics import ListAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.module_loading import import_string
from rest_framework.request import Request
from rest_framework.serializers import Serializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import *
from .serializers import *
from django.contrib.auth.hashers import make_password
from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets
from django.db.models import Count
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, action
from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model
from django.core.cache import cache
import random

class Pagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
    
#User
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer
    pagination_class = Pagination
    permission_classes = [IsAuthenticated]

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]    

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer

class UserUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]

class UserDeleteView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserAllSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]

class PhoneSendOTP(APIView):
    @swagger_auto_schema(request_body=SMSSerializer)
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        print(phone_number)
        if phone_number:
            phone = str(phone_number)
            user = User.objects.filter(phone__iexact=phone)
            if user.exists():
                return Response({
                    'status': False,
                    'detail': 'phone number already exist'
                })
            else:
                key = send_otp(phone)

                if key:
                    cache.set(phone_number, key, 600)

                    return Response({"message": "SMS sent successfully"}, status=status.HTTP_200_OK)

                return Response({"message": "Failed to send SMS"}, status=status.HTTP_400_BAD_REQUEST)

def send_otp(phone):
    if phone:
        key = 1212
        print(key)
        return key
    else:
        return False

class StatisticsView(APIView):
    def get(self, request):
        date1 = request.GET.get('date1')
        date2 = request.GET.get('date2')

        if not date1 or not date2:
            return Response({"error": "date1 va date2 parametrlari kerak"}, status=400)

        date1 = parse_date(date1)
        date2 = parse_date(date2)

        if not date1 or not date2:
            return Response({"error": "Noto‘g‘ri sana formati"}, status=400)

        data = {
            "registered": Enrollment.objects.filter(status='registered', date_joined__range=[date1, date2]).count(),
            "studying": Enrollment.objects.filter(status='studying', date_joined__range=[date1, date2]).count(),
            "graduated": Enrollment.objects.filter(status='graduated', date_joined__range=[date1, date2]).count(),
        }
        return Response(data)

class EnrollmentUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    
from rest_framework.permissions import AllowAny

class StudentListByIdsAPIView(APIView):
    permission_classes = [AllowAny]  # Auth talab qilinmaydi

    def post(self, request, *args, **kwargs):
        student_ids = request.data.get("student_ids", [])
        students = Student.objects.filter(id__in=student_ids)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentListView(ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    pagination_class = StudentPagination


class StudentUpdateView(UpdateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]

class StudentRetrieveAPIView(RetrieveAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]

class StudentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=UserAndStudentSerializer)
    def post(self, request):
        user_data = request.data.get('user', {})
        user_serializer = UserSerializer(data=user_data)

        if user_serializer.is_valid():
            user = user_serializer.save(is_student=True)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student_data = request.data.get('student', {})   
        student_serializer = StudentSerializer(data=student_data)

        if student_serializer.is_valid():
            student = student_serializer.save(user=user)
            return Response(StudentSerializer(student).data, status=status.HTTP_201_CREATED)
        else:
            user.delete()
            return Response(student_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentGroupsAPIView(APIView):
    def get(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
        except Teacher.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)

        groups = Group.objects.filter(g_student=student)
        serializer = GroupSerializer(groups, many=True)

        return Response(serializer.data, status=200)
    
class StudentGroupListView(APIView):
    def post(self, request, *args, **kwargs):
        student_ids = request.data.get("student_ids", [])
        group_ids = request.data.get("group_ids", [])

        students = Student.objects.filter(id__in=student_ids)
        groups = Group.objects.filter(id__in=group_ids)

        student_data = StudentSerializer(students, many=True).data
        group_data = GroupSerializer(groups, many=True).data

        return Response(
            {"students": student_data, "groups": group_data}, 
            status=status.HTTP_200_OK
        )

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

class VerifySms(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=VerifySMSSerializer)
    def post(self, request):
        serializer = VerifySMSSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            verification_code = serializer.validated_data['verification_code']
            cached_code = str(cache.get(phone_number))
            if verification_code == str(cached_code):
                return Response({
                    'status': True,
                    'detail': 'OTP matched. please proceed for registration'
                })
            else:
                return Response({
                    'status': False,
                    'detail': 'otp INCOORECT'
                })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterUserApi(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            password = serializer.validated_data.get('password')
            serializer.validated_data['password'] = make_password(password)
            serializer.save()
            return Response({
                'status': True,
                'datail': 'Account create'
            })

    def get(self, request):
        users = User.objects.all().order_by('-id')
        serializer = UserSerializer(users, many=True)
        return Response(data=serializer.data)

class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def patch(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(instance=self.request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DepartmentsApiView(ModelViewSet):
    queryset = Departments.objects.all().order_by('-id')
    serializer_class = DepartmentsSerializer
    pagination_class = PageNumberPagination

class DepartmentsViewSet(viewsets.ViewSet):
    permission_classes = [PageNumberPagination]

    def list(self, request):
        departments = Departments.objects.all()
        paginator = Pagination()
        result_page = paginator.paginate_queryset(departments, request)
        serializer = DepartmentsSerializer(result_page, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        department = get_object_or_404(Departments, pk=pk)
        serializer = DepartmentsSerializer(department)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='create/department')
    @swagger_auto_schema(request_body=DepartmentsSerializer)
    def create_department(self, request):
        serializer = DepartmentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'], url_path='update/department')
    def update_department(self, request, pk=None):
        department = get_object_or_404(Departments, pk=pk)
        serializer = DepartmentsSerializer(department, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='delete/department')
    def delete_department(self, request, pk=None):
        department = get_object_or_404(Departments, pk=pk)
        department.delete()
        return Response({'status':True,'detail': 'Department deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='add-worker')
    @swagger_auto_schema(request_body=DepartamentAddWorker)
    def add_worker(self, request, pk=None):
        department = get_object_or_404(Departments, pk=pk)
        serializer = DepartamentAddWorker(data=request.data)

        if serializer.is_valid():
            worker_id = serializer.validated_data['worker_id']
            worker = get_object_or_404(Worker, pk=worker_id)
            worker.department = department
            worker.save()

            return Response({'status':True,'detail': f'Worker {worker.user.phone} added to department {department.title}'},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CourseApiView(ModelViewSet):
    queryset = Course.objects.all().order_by('-id')
    serializer_class = CourseSerializer
    pagination_class = PageNumberPagination

class TeacherApiView(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=WorkerSerializer)
    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = str(serializer.validated_data.get('user'))
            try:
                user = User.objects.get(phone=user_id)
                user.is_teacher = True
                user.save()
                serializer.save()

            except Exception as e:
                print(e)
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        teacher = Worker.objects.filter(user__is_teacher=True).order_by('-id')
        serializer = WorkerSerializer(instance=teacher, many=True)
        return Response(data=serializer.data)

class TeacherListView(ListAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    pagination_class = Pagination

class TeacherUpdateView(UpdateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    lookup_field = 'id'

class TeacherRetrieveAPIView(RetrieveAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    lookup_field = 'id'

class TeacherCreateAPIView(APIView):

    @swagger_auto_schema(request_body=UserAndTeacherSerializer)
    def post(self, request):
        user_data = request.data.get('user', {})
        user_serializer = UserSerializer(data=user_data)

        if user_serializer.is_valid():
            user = user_serializer.save(is_worker=True)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        teacher_data = request.data.get('teacher', {})   
        teacher_serializer = TeacherSerializer(data=teacher_data)

        if teacher_serializer.is_valid():
            teacher = teacher_serializer.save(user=user)
            return Response(TeacherSerializer(teacher).data, status=status.HTTP_201_CREATED)
        else:
            user.delete()
            return Response(teacher_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherGroupsAPIView(APIView):
    def get(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher not found"}, status=404)

        groups = teacher.groups.all()
        serializer = GroupSerializer(groups, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class WorkerApiView(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = serializer.validated_data.get('user')

            user = User.objects.get(phone=f"{user_id}")
            user.is_staff = True
            user.save()
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):

        worker = Worker.objects.filter(user__is_staff=True).order_by('-id')
        serializer = WorkerSerializer(worker, many=True)
        return Response(data=serializer.data)

class WorkerApiViewId(APIView):
    def get(self, request, pk):
        try:
            worker = Worker.objects.get(pk=pk)
            serializer = WorkerSerializer(worker)
            return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

    def put(self, request, pk):
        try:
            teacher = Worker.objects.get(id=pk)
            serializer = WorkerSerializer(teacher, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

    def patch(self, request, pk):
        try:
            teacher = Worker.objects.get(pk=pk)
            serializer = WorkerSerializer(teacher, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

class WorkerApiView(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=WorkerSerializer)
    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = serializer.validated_data.get('user')
            user = User.objects.get(phone=user_id)
            user.is_staff = True
            user.save()
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        worker = Worker.objects.filter(user__is_staff=True).order_by('-id')
        serializer = WorkerSerializer(worker, many=True)
        return Response(data=serializer.data)

class RoomAPIView(ModelViewSet):
    queryset = Rooms.objects.all().order_by('-id')
    serializer_class = RoomSerializer
    pagination_class = PageNumberPagination

class DayAPIView(ModelViewSet):
    queryset = Day.objects.all().order_by('-id')
    serializer_class = DaySerializer
    pagination_class = PageNumberPagination

class WorkerApiView(APIView):
    pagination_class = PageNumberPagination

    @swagger_auto_schema(request_body=WorkerSerializer)
    def post(self, request):
        serializer = WorkerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = serializer.validated_data.get('user')
            user = User.objects.get(phone=user_id)
            user.is_staff = True
            user.save()
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        worker = Worker.objects.filter(user__is_staff=True).order_by('-id')
        serializer = WorkerSerializer(worker, many=True)
        return Response(data=serializer.data)


class StudentApiView(APIView):
    pagination_class = PageNumberPagination
    @swagger_auto_schema(request_body=StudentSerializer)
    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_id = serializer.validated_data.get('user')
            user = User.objects.get(phone=user_id)
            user.is_student = True
            user.save()
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        student = Student.objects.filter(user__is_student=True).order_by('-id')
        group = Group.objects.all().order_by('-id')
        course = Course.objects.all().order_by('-id')
        serializer_student = StudentSerializer(student, many=True)
        serializer_group = GroupSerializer(group, many=True)
        serializer_course = CourseSerializer(course, many=True)
        data = {
            "students": serializer_student.data,
            "groups": serializer_group.data,
            "courses": serializer_course.data
        }
        return Response(data=data)

class StudentApiViewId(APIView):
    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
            serializer = StudentSerializer(student)
            return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

    def put(self, request, pk):
        try:
            student = Student.objects.get(id=pk)
            serializer = StudentSerializer(student, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})

    def patch(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
            serializer = StudentSerializer(student, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(data=serializer.data)
        except Exception as e:
            return Response(data={'error': e})
        
from rest_framework import generics
from configApp.models import Group
from configApp.serializers import GroupSerializer

class GroupListCreateView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class GroupRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class GroupApiView(ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = Group.objects.all().order_by('-id')
    serializer_class = GroupSerializer

class GroupApi(APIView):
    pagination_class = PageNumberPagination
    def get(self, request):
        teachers = Worker.objects.filter(user__is_teacher=True).order_by('-id')
        courses = Course.objects.all().order_by('-id')
        tables = Table.objects.all().order_by('-id')
        serializer_teachers = WorkerSerializer(teachers, many=True)
        serializer_courses = CourseSerializer(courses, many=True)
        serializer_table = TableSerializer(tables, many=True)

        datas = {
            "teachers": serializer_teachers.data,
            "courses": serializer_courses.data,
            "tables": serializer_table.data
        }
        return Response(data=datas)

class GroupListByIdsAPIView(APIView):
    def post(self, request, *args, **kwargs):
        group_ids = request.data.get("group_ids", [])  # JSON dan group ID larini olish
        groups = Group.objects.filter(id__in=group_ids)  # Shu ID dagi grouplarni olish
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TableTypeApi(ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = TableType.objects.all().order_by('-id')
    serializer_class = TableTypeSerializer

class TableApi(ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = Table.objects.all().order_by('-id')
    serializer_class = TableSerializer

class TopicsApi(ModelViewSet):
    queryset = Topics.objects.all().order_by('-id')
    serializer_class = TopicsSerializer
    pagination_class = PageNumberPagination

class AttendanceLevelApi(ModelViewSet):
    queryset = AttendanceLevel.objects.all().order_by('-id')
    serializer_class = AttendanceLevelSerializer
    pagination_class = PageNumberPagination
    
class GroupHomeWorkApi(ModelViewSet):
    pagination_class = PageNumberPagination
    queryset = GroupHomeWork.objects.all().order_by('-id')
    serializer_class = GroupHomeWorkSerializer

class HomeWorkApi(ModelViewSet):
    queryset = HomeWork.objects.all().order_by('-id')
    serializer_class = HomeWorkSerializer
    pagination_class = PageNumberPagination


class ParentsViewSet(viewsets.ViewSet):
    permission_classes = [PageNumberPagination]

    def list(self, request):
        parents = Parents.objects.all()
        paginator = Pagination()
        result_page = paginator.paginate_queryset(parents, request)
        serializer = ParentsSerializer(result_page, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        parent = get_object_or_404(Parents, pk=pk)
        serializer = ParentsSerializer(parent)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='create/parent')
    @swagger_auto_schema(request_body=ParentsSerializer)
    def create_parent(self, request):
        serializer = ParentsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'], url_path='update/parent')
    def update_parent(self, request, pk=None):
        parent = get_object_or_404(Parents, pk=pk)
        serializer = ParentsSerializer(parent, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='delete/parent')
    def delete_parent(self, request, pk=None):
        parent = get_object_or_404(Parents, pk=pk)
        parent.delete()
        return Response({'status':True,'detail': 'Parent muaffaqiatli uchirildi'}, status=status.HTTP_204_NO_CONTENT)


User = get_user_model()

class RegisterView(APIView):
    """
    Telefon raqam orqali foydalanuvchini ro'yxatdan o'tkazish va OTP yuborish
    """

    def post(self, request):
        phone = request.data.get("phone")
        if not phone:
            return Response({"error": "Telefon raqami talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 4 xonali tasodifiy OTP yaratish
        otp_code = random.randint(1000, 9999)
        
        # OTP ni vaqtinchalik saqlash (30 daqiqa)
        cache.set(phone, otp_code, timeout=1800)

        return Response({"message": "OTP kod yuborildi", "otp": otp_code}, status=status.HTTP_201_CREATED)

class VerifyOTPView(APIView):
    """
    OTP orqali foydalanuvchini tasdiqlash va akkaunt yaratish
    """

    def post(self, request):
        phone = request.data.get("phone")
        otp_code = request.data.get("otp")

        if not phone or not otp_code:
            return Response({"error": "Telefon raqam va OTP kod talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)

        stored_otp = cache.get(phone)

        if not stored_otp or str(stored_otp) != str(otp_code):
            return Response({"error": "Noto‘g‘ri yoki eskirgan OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # OTP to‘g‘ri bo‘lsa, foydalanuvchini ro‘yxatdan o‘tkazamiz
        user, created = User.objects.get_or_create(phone=phone)
        
        if created:
            user.set_password(str(otp_code))  # Parol sifatida vaqtinchalik OTP
            user.save()

        # OTP ni cache dan o‘chirish
        cache.delete(phone)

        return Response({"message": "Ro'yxatdan o‘tish muvaffaqiyatli yakunlandi"}, status=status.HTTP_200_OK)

