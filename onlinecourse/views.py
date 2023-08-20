from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(
            user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# Create a submit view to create an exam submission record for a course enrollment
def submit_exam(request, course_id):
    # Get the user and course object
    user = request.user
    course = get_object_or_404(Course, pk=course_id)

    # Get the associated enrollment object created when the user enrolled in the course
    enrollment = course.enrollment_set.get(user=user)

    if request.method == 'POST':
        # Create a submission object referring to the enrollment
        submission = Submission(enrollment=enrollment)
        submission.save()

        # Collect the selected choices from the exam form
        submitted_answers = extract_answers(request)

        # Add each selected choice object to the submission object
        for choice_id in submitted_answers:
            submission.choices.add(choice_id)

        # Redirect to show_exam_result with the submission id
        return redirect('show_exam_result', course_id=course_id, submission_id=submission.id)

    # Handle GET request (if needed)
    # Render your exam form here for GET requests

    # ...

# A helper method to collect the selected choices from the exam form


def extract_answers(request):
    submitted_answers = []
    for key in request.POST:
        if key.startswith('choice_'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_answers.append(choice_id)
    return submitted_answers

# Create an exam result view to check if the learner passed the exam
# and show their question results and result for each question


def show_exam_result(request, course_id, submission_id):
    # Get the course and submission based on their ids
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)

    # Get the selected choice ids from the submission record
    selected_choice_ids = submission.choices.all().values_list('id', flat=True)

    # Calculate the total score based on your scoring logic
    total_score = calculate_total_score(selected_choice_ids)

    # Render the exam result page with course, submission, and total score
    return render(request, 'exam_result.html', {
        'course': course,
        'submission': submission,
        'total_score': total_score,
    })

# Implement your scoring logic here


def calculate_total_score(selected_choice_ids):
    # Calculate the total score based on your scoring logic
    # For example, you can count the correct choices selected by the user
    total_score = 0
    # Iterate through selected_choice_ids and calculate the score
    # based on your scoring criteria
    # ...

    return total_score
