from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import Client, Worker, Agent, Application, JobPosting
from functools import wraps
from decimal import Decimal, InvalidOperation
from django.db.models import F, Count
from .models import Client, Worker, Agent, Application, JobPosting, Job, WorkProof
from django.db.models import Avg
import math
from django.http import JsonResponse

# ==================================
# ADMIN DECORATOR
# ==================================
# This decorator protects views so only a logged-in admin can access them
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_loggedin') or request.session.get('user_role') != 'admin':
            messages.error(request, "You must be an admin to view this page.")
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)

    return _wrapped_view


# ==================================
# GENERAL & CLIENT VIEWS
# ==================================

def index(request):
    return render(request, 'index.html')


def client_register(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        company_name = request.POST.get('company_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        profile_pic = request.FILES.get('profile_pic')

        context = {'values': request.POST}

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'client_register.html', context)

        if Client.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return render(request, 'client_register.html', context)

        Client.objects.create(
            name=name,
            email=email,
            phone=phone,
            company_name=company_name,
            password=make_password(password),
            profile_pic=profile_pic,
            status='pending'  # <-- Set status to pending
        )

        messages.success(request, "Client registered successfully! Please wait for admin approval.")
        return redirect('client_login')

    return render(request, 'client_register.html')


def client_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            client = Client.objects.get(email=email)

            # --- STATUS CHECK ---
            if client.status == 'pending':
                messages.warning(request, "Your account is still pending approval.")
                return redirect('client_login')

            if client.status == 'rejected':
                messages.error(request, "Your account has been rejected. Please contact support.")
                return redirect('client_login')
            # --- END STATUS CHECK ---

            if check_password(password, client.password) and client.status == 'approved':
                request.session['client_id'] = client.id
                request.session['client_name'] = client.name
                request.session['is_loggedin'] = True
                request.session['user_role'] = 'client'
                messages.success(request, f"Welcome back, {client.name}!")
                return redirect('client_home')
            else:
                messages.error(request, "Invalid credentials. Please try again.")
                return redirect('client_login')

        except Client.DoesNotExist:
            messages.error(request, "Invalid credentials. Please try again.")
            return redirect('client_login')

    return render(request, 'client_login.html')


# ... (add this view function to views.py) ...




# ==================================
# WORKER VIEWS
# ==================================

def worker_register(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        skills = request.POST.get('skills')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        profile_pic = request.FILES.get('profile_pic')

        context = {'values': request.POST}

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'worker_register.html', context)

        if Worker.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return render(request, 'worker_register.html', context)

        Worker.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address,
            skills=skills,
            password=make_password(password),
            profile_pic=profile_pic,
            status='pending'  # <-- Set status to pending
        )

        messages.success(request, "Worker registered successfully! Please wait for admin approval.")
        return redirect('worker_login')

    return render(request, 'worker_register.html')


def worker_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            worker = Worker.objects.get(email=email)

            # --- STATUS CHECK ---
            if worker.status == 'pending':
                messages.warning(request, "Your account is still pending approval.")
                return redirect('worker_login')

            if worker.status == 'rejected':
                messages.error(request, "Your account has been rejected. Please contact support.")
                return redirect('worker_login')
            # --- END STATUS CHECK ---

            if check_password(password, worker.password) and worker.status == 'approved':
                request.session['is_loggedin'] = True
                request.session['worker_id'] = worker.id
                request.session['user_role'] = 'worker'
                request.session['worker_name'] = worker.name
                messages.success(request, f"Welcome back, {worker.name}!")
                return redirect('worker_home')
            else:
                messages.error(request, "Invalid email or password.")
                return render(request, 'worker_login.html', {'email': email})

        except Worker.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, 'worker_login.html', {'email': email})

    return render(request, 'worker_login.html')





# ==================================
# AGENT VIEWS
# ==================================

def agent_register(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        agency_name = request.POST.get('agency_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        profile_pic = request.FILES.get('profile_pic')

        # --- ADDED ---
        address = request.POST.get('address')  # Get address from POST
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')

        # Convert empty strings to None for the database
        latitude = lat if lat else None
        longitude = lng if lng else None
        # --- END ADDED ---

        context = {'values': request.POST}

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'agent_register.html', context)

        # --- ADDED ---
        if not latitude or not longitude:
            messages.error(request, "Please select your agency location on the map.")
            return render(request, 'agent_register.html', context)
        # --- END ADDED ---

        if Agent.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered to an agent")
            return render(request, 'agent_register.html', context)

        Agent.objects.create(
            name=name,
            email=email,
            phone=phone,
            agency_name=agency_name,
            password=make_password(password),
            profile_pic=profile_pic,
            address=address,  # <-- Save the address
            latitude=latitude,  # <-- Save the latitude
            longitude=longitude,  # <-- Save the longitude
            status='pending'
        )

        messages.success(request, "Agent registered successfully! Please wait for admin approval.")
        return redirect('agent_login')

    return render(request, 'agent_register.html')

def agent_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            agent = Agent.objects.get(email=email)

            # --- STATUS CHECK ---
            if agent.status == 'pending':
                messages.warning(request, "Your account is still pending approval.")
                return redirect('agent_login')

            if agent.status == 'rejected':
                messages.error(request, "Your account has been rejected. Please contact support.")
                return redirect('agent_login')
            # --- END STATUS CHECK ---

            if check_password(password, agent.password) and agent.status == 'approved':
                request.session['is_loggedin'] = True

                # --- THIS IS THE FIX ---
                # Changed 'user_id' to 'agent_id' to match the profile view
                request.session['agent_id'] = agent.id
                # --- END FIX ---

                request.session['user_role'] = 'agent'
                request.session['agent_name'] = agent.name
                messages.success(request, f"Welcome back, {agent.name}!")
                return redirect('agent_home')
            else:
                messages.error(request, "Invalid email or password.")
                return render(request, 'agent_login.html', {'email': email})

        except Agent.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, 'agent_login.html', {'email': email})

    return render(request, 'agent_login.html')




def admin_login(request):
    ADMIN_EMAIL = "admin@sidecrew.com"
    ADMIN_PASSWORD = "Admin@123"

    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            request.session['is_loggedin'] = True
            request.session['user_role'] = 'admin'
            request.session['user_id'] = 'admin'
            messages.success(request, "Logged in as admin.")
            return redirect('admin_home')
        else:
            messages.error(request, "Invalid credentials. Please try again.")
            return redirect('admin_login')

    return render(request, 'admin_login.html')


@admin_required
def admin_home(request):
    context = {
        'client_count': Client.objects.count(),
        'worker_count': Worker.objects.count(),
        'agent_count': Agent.objects.count(),
        'pending_clients': Client.objects.filter(status='pending').count(),
        'pending_workers': Worker.objects.filter(status='pending').count(),
        'pending_agents': Agent.objects.filter(status='pending').count(),
        'total_jobs': Job.objects.count(),
    }
    return render(request, 'admin_home.html', context)


def user_logout(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('index')



@admin_required
def manage_clients(request):
    clients = Client.objects.all().order_by('status', 'name')
    return render(request, 'manage_clients.html', {'clients': clients})


@admin_required
def approve_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client.status = 'approved'
    client.save()
    messages.success(request, f"Client '{client.name}' has been approved.")
    return redirect('manage_clients')


@admin_required
def reject_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client.status = 'rejected'
    client.save()
    messages.warning(request, f"Client '{client.name}' has been rejected.")
    return redirect('manage_clients')


@admin_required
def delete_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    name = client.name
    client.delete()
    messages.error(request, f"Client '{name}' has been deleted.")
    return redirect('manage_clients')


# --- Worker Management ---
@admin_required
def manage_workers(request):
    workers = Worker.objects.all().order_by('status', 'name')
    return render(request, 'manage_workers.html', {'workers': workers})


@admin_required
def approve_worker(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    worker.status = 'approved'
    worker.save()
    messages.success(request, f"Worker '{worker.name}' has been approved.")
    return redirect('manage_workers')


@admin_required
def reject_worker(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    worker.status = 'rejected'
    worker.save()
    messages.warning(request, f"Worker '{worker.name}' has been rejected.")
    return redirect('manage_workers')


@admin_required
def delete_worker(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    name = worker.name
    worker.delete()
    messages.error(request, f"Worker '{name}' has been deleted.")
    return redirect('manage_workers')


# --- Agent Management ---
@admin_required
def manage_agents(request):
    agents = Agent.objects.all().order_by('status', 'name')
    return render(request, 'manage_agent.html', {'agents': agents})


@admin_required
def approve_agent(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    agent.status = 'approved'
    agent.save()
    messages.success(request, f"Agent '{agent.name}' has been approved.")
    return redirect('manage_agents')


@admin_required
def reject_agent(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    agent.status = 'rejected'
    agent.save()
    messages.warning(request, f"Agent '{agent.name}' has been rejected.")
    return redirect('manage_agents')


@admin_required
def delete_agent(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    name = agent.name
    agent.delete()
    messages.error(request, f"Agent '{name}' has been deleted.")
    return redirect('manage_agents')


def agent_required(view_func):

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_loggedin') or request.session.get('user_role') != 'agent':
            messages.error(request, "You must be logged in as an agent to view this page.")
            return redirect('agent_login')

        if 'agent_id' not in request.session:
            messages.error(request, "Your session is invalid. Please log in again.")
            return redirect('agent_login')

        return view_func(request, *args, **kwargs)

    return _wrapped_view




@agent_required
def agent_home(request):
    try:
        agent_id = request.session['agent_id']
        agent = Agent.objects.get(id=agent_id)
    except (KeyError, Agent.DoesNotExist):
        return redirect('agent_login')

    direct_invites = Job.objects.filter(
        agent=agent,
        status='PENDING_AGENT'
    ).order_by('-created_at')

    public_invites = Job.objects.filter(
        agent__isnull=True,
        status='SEEKING_AGENT'
    ).order_by('-created_at')

    unposted_jobs = Job.objects.filter(
        agent=agent,
        status='OPEN',
        postings__isnull=True
    ).order_by('-created_at')

    active_postings = Job.objects.filter(
        agent=agent,
        status__in=['OPEN', 'FILLED'],
        postings__isnull=False
    ).prefetch_related(
        'postings__applications__worker'
    ).order_by('-created_at')

    completed_jobs = Job.objects.filter(
        agent=agent,
        status='COMPLETED',
        postings__isnull=False
    ).prefetch_related(
        'postings__applications__worker'
    ).order_by('-created_at')

    pending_applications = Application.objects.filter(
        job_posting__agent=agent,
        status='PENDING'
    ).order_by('applied_at')

    pending_proofs = WorkProof.objects.filter(
        application__job_posting__agent=agent,
        status='PENDING'
    )

    context = {
        'agent': agent,
        'direct_invites': direct_invites,
        'new_invites': public_invites,
        'active_jobs': unposted_jobs,
        'active_postings': active_postings,
        'completed_jobs': completed_jobs,
        'pending_applications': pending_applications,
        'pending_proofs': pending_proofs,
    }
    return render(request, 'agent_home.html', context)




@agent_required
def accept_direct_invite(request, job_id):
    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
    except (KeyError, Agent.DoesNotExist):
        return redirect('agent_login')

    job = get_object_or_404(Job, id=job_id, agent=agent, status='PENDING_AGENT')

    job.status = 'OPEN'
    job.save()

    messages.success(request, f"You have accepted the invitation for '{job.title}'. You can now post it to workers.")
    return redirect('agent_home')


@agent_required
def reject_direct_invite(request, job_id):
    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
    except (KeyError, Agent.DoesNotExist):
        return redirect('agent_login')

    job = get_object_or_404(Job, id=job_id, agent=agent, status='PENDING_AGENT')


    job.agent = None
    job.status = 'SEEKING_AGENT'
    job.save()

    messages.warning(request, f"You have rejected the invitation for '{job.title}'. It is now on the public board.")
    return redirect('agent_home')

@agent_required
def accept_application(request, application_id):
    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
    except Agent.DoesNotExist:
        messages.error(request, "Please log in.")
        return redirect('agent_login')

    application = get_object_or_404(Application, id=application_id, job_posting__agent=agent, status='PENDING')
    job_posting = application.job_posting
    original_job = job_posting.job

    application.status = 'ACCEPTED'
    application.save()


    accepted_count = Application.objects.filter(
        job_posting=job_posting,
        status='ACCEPTED'
    ).count()

    if accepted_count >= original_job.workers_needed:
        job_posting.is_active = False
        job_posting.save()

        original_job.status = 'FILLED'
        original_job.save()
        messages.success(request,
                         f"Worker {application.worker.name} accepted. This job is now full and has been closed.")
    else:
        messages.success(request, f"Worker {application.worker.name} accepted for {job_posting.title}.")

    return redirect('agent_home')


@agent_required
def reject_application(request, application_id):
    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
    except Agent.DoesNotExist:
        messages.error(request, "Please log in.")
        return redirect('agent_login')

    application = get_object_or_404(Application, id=application_id, job_posting__agent=agent, status='PENDING')

    application.status = 'REJECTED'
    application.save()

    messages.warning(request, f"Application from {application.worker.name} has been rejected.")
    return redirect('agent_home')

@agent_required
def agent_profile(request):

    try:
        agent = Agent.objects.get(pk=request.session['agent_id'])
    except Agent.DoesNotExist:
        request.session.flush()
        messages.error(request, "Could not find your profile. Please log in again.")
        return redirect('agent_login')

    if request.method == 'POST':
        new_name = request.POST.get('name')
        new_agency_name = request.POST.get('agency_name')
        new_email = request.POST.get('email')
        new_phone = request.POST.get('phone')
        new_address = request.POST.get('address')

        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')

        new_latitude = lat if lat else None
        new_longitude = lng if lng else None

        if new_email != agent.email:
            if Agent.objects.filter(email=new_email).exclude(pk=agent.pk).exists():
                messages.error(request, "This email address is already in use by another account.")
                return render(request, 'agent_profile.html', {'agent': agent})
            else:
                agent.email = new_email

        agent.name = new_name
        agent.agency_name = new_agency_name
        agent.phone = new_phone
        agent.address = new_address

        agent.latitude = new_latitude
        agent.longitude = new_longitude

        if 'profile_pic' in request.FILES:
            agent.profile_pic = request.FILES['profile_pic']

        try:
            agent.save()
            messages.success(request, "Your profile has been updated successfully!")
        except Exception as e:
            messages.error(request, f"An error occurred while saving: {e}")

        return redirect('agent_profile')

    context = {
        'agent': agent
    }
    return render(request, 'agent_profile.html', context)



@agent_required
def delete_agent_profile(request):

    try:
        agent = Agent.objects.get(pk=request.session['agent_id'])

        agent_name = agent.name


        agent.delete()

        request.session.flush()

        messages.success(request, f"Your account '{agent_name}' has been permanently deleted.")
        return redirect('index')

    except Agent.DoesNotExist:
        request.session.flush()
        messages.error(request, "Could not find your profile. You have been logged out.")
        return redirect('agent_login')


def client_required(view_func):

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_loggedin') or request.session.get('user_role') != 'client':
            messages.error(request, "You must be logged in as a client to view this page.")
            return redirect('client_login')

        if 'client_id' not in request.session:
            messages.error(request, "Your session is invalid. Please log in again.")
            return redirect('client_login')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

@client_required
def client_home(request):
    try:
        client = Client.objects.get(id=request.session['client_id'])
    except (KeyError, Client.DoesNotExist):
        messages.error(request, "Session expired. Please log in.")
        return redirect('client_login')

    # This query now fetches the workers assigned to each job
    my_jobs = Job.objects.filter(client=client).order_by('-created_at').prefetch_related(
        'postings__applications__worker'
    )

    context = {
        'client': client,
        'jobs': my_jobs,
    }
    return render(request, 'client_home.html', context)
# --- 2. Client Profile View (View and Edit) ---

@client_required
def client_profile(request):
    """
    Allows a client to view and update their profile.
    """
    try:
        client = Client.objects.get(pk=request.session['client_id'])
    except Client.DoesNotExist:
        request.session.flush()
        messages.error(request, "Could not find your profile. Please log in again.")
        return redirect('client_login')

    if request.method == 'POST':
        # --- This block handles the "Save Changes" form submission ---

        # Get the form data
        new_name = request.POST.get('name')
        new_email = request.POST.get('email')
        new_phone = request.POST.get('phone')
        new_company_name = request.POST.get('company_name') # --- ADDED THIS LINE ---
        # new_address = request.POST.get('address') # --- REMOVED THIS LINE ---

        # Check if the email is being changed and if it's already taken
        if new_email != client.email:
            if Client.objects.filter(email=new_email).exclude(pk=client.pk).exists():
                messages.error(request, "This email address is already in use by another account.")
                return render(request, 'client_profile.html', {'client': client})
            else:
                client.email = new_email

        # Update the client object
        client.name = new_name
        client.phone = new_phone
        client.company_name = new_company_name # --- ADDED THIS LINE ---
        # client.address = new_address # --- REMOVED THIS LINE ---

        # Handle the profile picture file upload
        if 'profile_pic' in request.FILES:
            client.profile_pic = request.FILES['profile_pic']

        try:
            client.save()
            request.session['client_name'] = client.name
            messages.success(request, "Your profile has been updated successfully!")
        except Exception as e:
            messages.error(request, f"An error occurred while saving: {e}")

        return redirect('client_profile')

    # --- This block handles the GET request (just viewing the page) ---
    context = {
        'client': client
    }
    return render(request, 'client_profile.html', context)


# --- 3. Delete Client Profile View ---

@client_required
def delete_client_profile(request):
    """
    Handles the permanent deletion of a client's own profile.
    """
    try:
        client = Client.objects.get(pk=request.session['client_id'])
        client_name = client.name # Get name for success message

        # Delete the client object
        client.delete()

        # Log the user out by clearing their session
        request.session.flush()

        messages.success(request, f"Your account '{client_name}' has been permanently deleted.")
        # Redirect to the main homepage
        return redirect('index')  # Assumes you have a homepage URL named 'index'

    except Client.DoesNotExist:
        request.session.flush()
        messages.error(request, "Could not find your profile. You have been logged out.")
        return redirect('client_login')


from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Client, Agent, Worker  # <-- Make sure to import Worker


# --- 1. Worker Required Decorator ---

def worker_required(view_func):
    """
    Decorator to ensure a user is logged in as a worker.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_loggedin') or request.session.get('user_role') != 'worker':
            messages.error(request, "You must be logged in as a worker to view this page.")
            return redirect('worker_login')  # Assumes you have a 'worker_login' URL

        if 'worker_id' not in request.session:
            messages.error(request, "Your session is invalid. Please log in again.")
            return redirect('worker_login')  # Assumes you have a 'worker_login' URL

        return view_func(request, *args, **kwargs)

    return _wrapped_view


# In views.py, find your existing worker_home and REPLACE it with this:

@worker_required
def worker_home(request):
    try:
        worker = Worker.objects.get(id=request.session['worker_id'])
    except Worker.DoesNotExist:
        messages.error(request, "Please log in.")
        return redirect('worker_login')

    # 1. Get IDs of jobs this worker has already applied for
    applied_job_ids = Application.objects.filter(worker=worker).values_list('job_posting_id', flat=True)

    # 2. Get all available jobs (active) that this worker has NOT applied for
    available_jobs = JobPosting.objects.filter(
        is_active=True
    ).exclude(
        id__in=applied_job_ids
    ).order_by('-created_at')

    # 3. Get all of this worker's existing applications
    my_applications = Application.objects.filter(
        worker=worker
    ).order_by('-applied_at')

    context = {
        'available_jobs': available_jobs,
        'my_applications': my_applications,
    }
    return render(request, 'worker_home.html', context)


# --- ADD THIS NEW FUNCTION (in the "WORKER VIEWS" section) ---

@worker_required
def apply_for_job(request, posting_id):
    try:
        worker = Worker.objects.get(id=request.session['worker_id'])
    except Worker.DoesNotExist:
        messages.error(request, "Please log in.")
        return redirect('worker_login')

    # Get the job posting, but only if it's still active
    job_posting = get_object_or_404(JobPosting, id=posting_id, is_active=True)

    # Check if the worker has already applied (prevents double-applying)
    already_applied = Application.objects.filter(job_posting=job_posting, worker=worker).exists()

    if already_applied:
        messages.warning(request, "You have already applied for this job.")
        return redirect('worker_home')

    # --- This is the "Booking" / "Applying" logic ---
    Application.objects.create(
        job_posting=job_posting,
        worker=worker,
        status='PENDING'  # The agent will have to approve this
    )

    messages.success(request, f"You have successfully applied for '{job_posting.title}'!")
    return redirect('worker_home')
# --- 2. Worker Profile View (View and Edit) ---

@worker_required
def worker_profile(request):
    """
    Allows a worker to view and update their profile.
    """
    try:
        # Get the worker object based on the ID stored in the session
        worker = Worker.objects.get(pk=request.session['worker_id'])
    except Worker.DoesNotExist:
        # This handles a bad session (e.g., worker was deleted)
        request.session.flush()  # Clear the bad session
        messages.error(request, "Could not find your profile. Please log in again.")
        return redirect('worker_login')

    if request.method == 'POST':
        # --- This block handles the "Save Changes" form submission ---

        # Get the form data
        new_name = request.POST.get('name')
        new_email = request.POST.get('email')
        new_phone = request.POST.get('phone')
        new_address = request.POST.get('address')
        new_skills = request.POST.get('skills')

        # Handle the checkbox for availability. If it's not checked, 'availability'
        # will not be in request.POST, so .get() will return None.
        new_availability = request.POST.get('availability') == 'on'

        # Check if the email is being changed and if it's already taken
        if new_email != worker.email:
            if Worker.objects.filter(email=new_email).exclude(pk=worker.pk).exists():
                # This email is taken by *another* user
                messages.error(request, "This email address is already in use by another account.")
                return render(request, 'worker_profile.html', {'worker': worker})
            else:
                worker.email = new_email

        # Update the worker object
        worker.name = new_name
        worker.phone = new_phone
        worker.address = new_address
        worker.skills = new_skills
        worker.availability = new_availability

        # Handle the profile picture file upload
        if 'profile_pic' in request.FILES:
            worker.profile_pic = request.FILES['profile_pic']

        try:
            worker.save()
            # IMPORTANT: Update the session name if it changed
            request.session['worker_name'] = worker.name
            messages.success(request, "Your profile has been updated successfully!")
        except Exception as e:
            messages.error(request, f"An error occurred while saving: {e}")

        # Redirect back to the same page to show the new data
        return redirect('worker_profile')

    # --- This block handles the GET request (just viewing the page) ---
    context = {
        'worker': worker
    }
    return render(request, 'worker_profile.html', context)


# --- 3. Delete Worker Profile View ---

@worker_required
def delete_worker_profile(request):
    """
    Handles the permanent deletion of a worker's own profile.
    """
    try:
        worker = Worker.objects.get(pk=request.session['worker_id'])
        worker_name = worker.name  # Get name for success message

        # Delete the worker object
        worker.delete()

        # Log the user out by clearing their session
        request.session.flush()

        messages.success(request, f"Your account '{worker_name}' has been permanently deleted.")
        # Redirect to the main homepage
        return redirect('index')  # Assumes you have a homepage URL named 'index'

    except Worker.DoesNotExist:
        request.session.flush()
        messages.error(request, "Could not find your profile. You have been logged out.")
        return redirect('worker_login')


from django.shortcuts import render, redirect
from .models import Client, Job  # Import your models
from .forms import JobForm, JobPostingForm  # Import your new form



@client_required
def create_job(request):
    try:
        client = Client.objects.get(id=request.session['client_id'])
    except (KeyError, Client.DoesNotExist):
        messages.error(request, "You must be logged in to post a job.")
        return redirect('client_login')

    if request.method == 'POST':
        form = JobForm(request.POST)
        agent_selection = request.POST.get('agent_selection')


        if form.is_valid():
            job = form.save(commit=False)
            job.client = client

            if agent_selection and agent_selection != 'public_board':
                try:
                    invited_agent = Agent.objects.get(id=agent_selection)
                    job.agent = invited_agent
                    job.status = 'PENDING_AGENT'
                    job.save()
                    messages.success(request,
                                     f"Job has been created and sent directly to {invited_agent.agency_name} for approval.")
                except Agent.DoesNotExist:
                    messages.error(request, "Selected agent not found. Posting to public board.")
                    job.status = 'SEEKING_AGENT'
                    job.save()
            else:
                job.status = 'SEEKING_AGENT'
                job.save()
                messages.success(request, "Job posted successfully! It is now visible to all agents.")

            return redirect('client_home')
        else:
            messages.error(request, "Please correct the errors in the form.")

    else:
        form = JobForm()

    return render(request, 'create_job.html', {
        'form': form,
    })





from django.shortcuts import render, redirect, get_object_or_404
from .models import Agent, Job  # Make sure Agent and Job are imported




# --- ADD THIS FUNCTION ---
# In views.py, find accept_job and REPLACE it with this:

@agent_required
def accept_job(request, job_id):
    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
    except (KeyError, Agent.DoesNotExist):
        return redirect('agent_login')

    # --- THIS IS THE CHANGE ---
    # Get the job, but ONLY if it has no agent and is seeking one
    job = get_object_or_404(Job, id=job_id, agent__isnull=True, status='SEEKING_AGENT')

    # --- This is the core logic: Claim the job ---
    job.agent = agent  # Assign the agent who clicked
    job.status = 'OPEN'  # Set it to 'OPEN' so they can post it
    job.save()
    # --- END CHANGE ---

    messages.success(request, f"Job '{job.title}' has been claimed! You can now post it to workers.")
    return redirect('agent_home')





# Add this view in the "AGENT VIEWS" section of views.py

@agent_required
def create_job_posting(request, job_id):
    """
    Allows an Agent to create a JobPosting (for workers) based on
    an accepted client Job.
    """
    try:
        agent_obj = Agent.objects.get(id=request.session['agent_id'])
    except Agent.DoesNotExist:
        messages.error(request, "Agent not found. Please log in.")
        return redirect('agent_login')

    original_job = get_object_or_404(Job, id=job_id, agent=agent_obj, status='OPEN')

    initial_data = {
        'title': original_job.title,
        'description': original_job.description,

        # --- THIS IS THE FIX ---
        'worker_pay_rate': original_job.client_pay_per_worker * Decimal('0.90')
        # --- END FIX ---
    }

    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job_post = form.save(commit=False)
            job_post.agent = agent_obj
            job_post.job = original_job
            job_post.save()

            messages.success(request, f"New job '{job_post.title}' has been posted for workers.")
            return redirect('agent_home')
        else:
            messages.error(request, "Please correct the errors below.")

    else:  # GET request
        form = JobPostingForm(initial=initial_data)

    context = {
        'form': form,
        'original_job': original_job
    }
    return render(request, 'create_job_posting.html', context)


# --- ADD TO YOUR "WORKER VIEWS" SECTION ---

@worker_required
def worker_upload_proof(request, application_id):
    try:
        worker = Worker.objects.get(id=request.session['worker_id'])
    except Worker.DoesNotExist:
        messages.error(request, "Please log in.")
        return redirect('worker_login')

    application = get_object_or_404(Application, id=application_id)

    # SECURITY CHECK: Is this the correct worker?
    if application.worker != worker:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('worker_home')

    # LOGIC CHECK: Only allow upload if status is 'ACCEPTED' or 'PROOF_REJECTED'
    if application.status not in ['ACCEPTED', 'PROOF_REJECTED']:
        messages.warning(request, "You cannot submit proof for this application at this time.")
        return redirect('worker_home')

    # Get existing proof if it was rejected, to show remarks
    existing_proof = WorkProof.objects.filter(application=application).first()

    if request.method == 'POST':
        image = request.FILES.get('image')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if not all([image, latitude, longitude]):
            messages.error(request, "Missing location or image. Please enable location and try again.")
            return render(request, 'upload_proof.html', {
                'application': application,
                'proof': existing_proof
            })

        # Use update_or_create to handle both new uploads and resubmissions
        proof, created = WorkProof.objects.update_or_create(
            application=application,
            defaults={
                'image': image,
                'latitude': latitude,
                'longitude': longitude,
                'status': 'PENDING',
                'agent_remarks': None # Clear old remarks on resubmission
            }
        )

        # Update the application status
        application.status = 'PROOF_SUBMITTED'
        application.save()

        messages.success(request, "Proof uploaded successfully! Waiting for agent approval.")
        return redirect('worker_home')

    return render(request, 'upload_proofs.html', {
        'application': application,
        'proof': existing_proof # Pass existing proof to show rejection remarks
    })


# --- ADD TO YOUR "AGENT VIEWS" SECTION ---

@agent_required
def agent_review_dashboard(request):
    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
    except Agent.DoesNotExist:
        messages.error(request, "Please log in.")
        return redirect('agent_login')

    # Get all pending proofs for jobs managed by this agent
    pending_proofs = WorkProof.objects.filter(
        status='PENDING',
        application__job_posting__agent=agent
    ).order_by('uploaded_at')

    return render(request, 'agent_review_dashboard.html', {'proofs': pending_proofs})


# In views.py

@agent_required
def agent_approve_proof(request, proof_id):
    if request.method != 'POST':
        return redirect('agent_review_dashboard')

    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
    except Agent.DoesNotExist:
        messages.error(request, "Please log in.")
        return redirect('agent_login')

    proof = get_object_or_404(WorkProof, id=proof_id)

    # SECURITY CHECK
    if proof.application.job_posting.agent != agent:
        messages.error(request, "You do not have permission to review this proof.")
        return redirect('agent_review_dashboard')

    # 1. Approve the Proof
    proof.status = 'APPROVED'
    proof.save()

    # 2. Update the Application status to final
    application = proof.application
    application.status = 'COMPLETED'
    application.save()

    # --- NEW LOGIC: CHECK IF THE WHOLE JOB IS COMPLETE ---

    # Get the original job this application belongs to
    original_job = application.job_posting.job

    # Count how many applications for this *entire job* are now 'COMPLETED'
    completed_app_count = Application.objects.filter(
        job_posting__job=original_job,
        status='COMPLETED'
    ).count()

    # Check if all needed workers have completed the job
    if completed_app_count >= original_job.workers_needed:
        original_job.status = 'COMPLETED'
        original_job.save()
        messages.success(request,
                         f"Proof from {application.worker.name} approved. This was the final worker, so the job '{original_job.title}' is now marked as COMPLETED.")
    else:
        # Not the last worker, just give a standard message
        remaining = original_job.workers_needed - completed_app_count
        messages.success(request,
                         f"Proof from {application.worker.name} approved. Still waiting on {remaining} more worker(s).")

    # --- END NEW LOGIC ---

    return redirect('agent_review_dashboard')


@agent_required
def agent_reject_proof(request, proof_id):
    if request.method != 'POST':
        return redirect('agent_review_dashboard')

    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
    except Agent.DoesNotExist:
        messages.error(request, "Please log in.")
        return redirect('agent_login')

    proof = get_object_or_404(WorkProof, id=proof_id)
    remarks = request.POST.get('remarks')

    if not remarks:
        messages.error(request, "A reason is required for rejection.")
        return redirect('agent_review_dashboard')

    # SECURITY CHECK
    if proof.application.job_posting.agent != agent:
        messages.error(request, "You do not have permission to review this proof.")
        return redirect('agent_review_dashboard')

    # 1. Reject the Proof
    proof.status = 'REJECTED'
    proof.agent_remarks = remarks
    proof.save()

    # 2. Update the Application, setting it back so the worker can re-submit
    application = proof.application
    application.status = 'PROOF_REJECTED'
    application.save()

    messages.warning(request, f"Proof from {application.worker.name} rejected. Worker has been notified to resubmit.")
    return redirect('agent_review_dashboard')


@client_required
def delete_job(request, job_id):
    """
    Allows a client to delete a job they posted.
    """
    try:
        # Get the logged-in client
        client = Client.objects.get(id=request.session['client_id'])
    except (KeyError, Client.DoesNotExist):
        messages.error(request, "Session expired. Please log in.")
        return redirect('client_login')

    # Get the job, ensuring it exists AND belongs to this client
    job = get_object_or_404(Job, id=job_id, client=client)

    # --- Business Logic Check ---
    # We'll prevent deletion if the job is already completed.
    if job.status == 'COMPLETED':
        messages.error(request, f"Cannot delete '{job.title}' as it is already completed.")
        return redirect('client_home')

    # If an agent is already working on it ('OPEN' or 'FILLED'),
    # deleting it will cascade and remove all postings and applications.
    # We will allow this, but a confirmation is essential.

    job_title = job.title
    job.delete()

    messages.success(request, f"Job '{job_title}' and all related postings have been deleted.")
    return redirect('client_home')


# In views.py, under the CLIENT VIEWS section

@client_required
def client_pay_for_job(request, job_id):
    """
    Simulates a client paying an agent for a job.
    """
    try:
        client = Client.objects.get(id=request.session['client_id'])
    except (KeyError, Client.DoesNotExist):
        messages.error(request, "Session expired. Please log in.")
        return redirect('client_login')

    job = get_object_or_404(Job, id=job_id, client=client)

    # --- PAYMENT GATEWAY LOGIC ---
    # In a real app, you would redirect to Stripe, Razorpay, etc.
    # After a successful callback from the gateway, you'd set the status.
    # For now, we'll just simulate success.

    job.client_payment_status = 'paid'
    job.save()

    messages.success(request, f"Payment for '{job.title}' was successful! The agent has been notified.")
    return redirect('client_home')

# In views.py, under the AGENT VIEWS section

@agent_required
def agent_mark_worker_paid(request, application_id):
    """
    Allows an agent to mark a worker as paid for a completed application.
    """
    if request.method != 'POST':
        return redirect('agent_home')

    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
    except Agent.DoesNotExist:
        messages.error(request, "Please log in.")
        return redirect('agent_login')

    # Get the application, ensuring it belongs to this agent and is 'COMPLETED'
    application = get_object_or_404(
        Application,
        id=application_id,
        job_posting__agent=agent,
        status='COMPLETED'
    )

    application.worker_payment_status = 'paid'
    application.save()

    messages.success(request, f"Worker {application.worker.name} has been marked as paid.")
    return redirect('agent_home')


@client_required
def client_rate_agent(request, job_id):
    if request.method == 'POST':
        try:
            client = Client.objects.get(id=request.session['client_id'])
        except (KeyError, Client.DoesNotExist):
            return redirect('client_login')

        # Get the job, ensure it belongs to this client and is completed
        job = get_object_or_404(Job, id=job_id, client=client, status='COMPLETED')

        # Ensure it hasn't been rated yet
        if job.client_rating_for_agent is not None:
            messages.error(request, "You have already rated this agent for this job.")
            return redirect('client_home')

        rating = request.POST.get('rating')
        if not rating:
            messages.error(request, "Please select a rating.")
            return redirect('client_home')

        # 1. Save the rating on the job
        job.client_rating_for_agent = int(rating)
        job.save()

        # 2. Recalculate the agent's average rating
        agent = job.agent
        all_agent_ratings = Job.objects.filter(agent=agent, client_rating_for_agent__isnull=False).aggregate(
            avg_rating=Avg('client_rating_for_agent')
        )

        agent.rating = all_agent_ratings['avg_rating'] or 0.0
        agent.save()

        messages.success(request, f"You have successfully rated {agent.name} {rating} stars.")

    return redirect('client_home')


@agent_required
def agent_rate_worker(request, application_id):
    if request.method == 'POST':
        try:
            agent = Agent.objects.get(id=request.session['agent_id'])
        except (KeyError, Agent.DoesNotExist):
            return redirect('agent_login')

        # Get the application, ensure it belongs to this agent and is completed
        application = get_object_or_404(
            Application,
            id=application_id,
            job_posting__agent=agent,
            status='COMPLETED'
        )

        # Ensure it hasn't been rated yet
        if application.agent_rating_for_worker is not None:
            messages.error(request, "You have already rated this worker for this job.")
            return redirect('agent_home')

        rating = request.POST.get('rating')
        if not rating:
            messages.error(request, "Please select a rating.")
            return redirect('agent_home')

        # 1. Save the rating on the application
        application.agent_rating_for_worker = int(rating)
        application.save()

        # 2. Recalculate the worker's average rating
        worker = application.worker
        all_worker_ratings = Application.objects.filter(worker=worker, agent_rating_for_worker__isnull=False).aggregate(
            avg_rating=Avg('agent_rating_for_worker')
        )

        worker.rating = all_worker_ratings['avg_rating'] or 0.0
        worker.save()

        messages.success(request, f"You have successfully rated {worker.name} {rating} stars.")

    return redirect('agent_home')


# In views.py, add these two new views to your "NEW ADMIN MANAGEMENT VIEWS" section

@admin_required
def admin_manage_jobs(request):
    """
    Shows a new admin page to list all jobs in the system.
    """
    # Get all jobs, ordered by most recent, with client and agent info
    all_jobs = Job.objects.select_related('client', 'agent').all().order_by('-created_at')

    return render(request, 'admin_manage_jobs.html', {
        'jobs': all_jobs
    })


@admin_required
def admin_delete_job(request, job_id):
    """
    Allows admin to delete any job.
    """
    # Admins can delete any job, so we just get it by ID
    job = get_object_or_404(Job, id=job_id)
    job_title = job.title

    if request.method == 'POST':
        job.delete()
        messages.error(request, f"Job '{job_title}' and all related data have been permanently deleted.")
        return redirect('admin_manage_jobs')

    # If GET, just redirect back
    return redirect('admin_manage_jobs')


# In views.py, in the "ADMIN MANAGEMENT VIEWS" section
# Make sure to import Application: from .models import ... Application

@admin_required
def admin_job_detail(request, job_id):
    """
    Shows a detailed read-only view of a job and all its related
    workers and applications for the admin.
    """
    job = get_object_or_404(Job.objects.select_related('client', 'agent'), id=job_id)

    # Get all applications related to this job, regardless of which posting
    applications = Application.objects.filter(job_posting__job=job).select_related('worker').order_by('applied_at')

    context = {
        'job': job,
        'applications': applications
    }
    return render(request, 'admin_job_detail.html', context)




def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    a = math.sin(dLat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dLon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


def get_agents_near(request):

    try:
        job_lat = Decimal(request.GET.get('lat'))
        job_lng = Decimal(request.GET.get('lng'))
    except (TypeError, ValueError, InvalidOperation):
        return JsonResponse({'error': 'Invalid location data'}, status=400)

    SEARCH_RADIUS_KM = 50

    all_agents = Agent.objects.filter(
        status='approved',
        latitude__isnull=False,
        longitude__isnull=False
    )

    nearby_agents = []
    for agent in all_agents:
        distance = haversine(job_lat, job_lng, agent.latitude, agent.longitude)

        if distance <= SEARCH_RADIUS_KM:
            nearby_agents.append({
                'id': agent.id,
                'name': agent.name,
                'agency_name': agent.agency_name,
                'rating': agent.rating,
                'distance': f"{distance:.1f}"
            })

    nearby_agents.sort(key=lambda x: float(x['distance']))

    return JsonResponse({'agents': nearby_agents})
