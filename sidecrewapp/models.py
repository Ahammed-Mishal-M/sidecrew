from django.db import models
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Client(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    profile_pic = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    phone = models.CharField(max_length=15)
    company_name = models.CharField(max_length=100, blank=True, null=True)

    # --- ADD THIS ---
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # --- END ADD ---

    def __str__(self):
        return self.name


class Worker(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    profile_pic = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    address = models.TextField()
    skills = models.TextField()
    availability = models.BooleanField(default=True)
    rating = models.FloatField(default=0)

    # --- ADD THIS ---
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # --- END ADD ---

    def __str__(self):
        return self.name


class Agent(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    profile_pic = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    address = models.TextField()
    agency_name = models.CharField(max_length=100)
    rating = models.FloatField(default=0.0)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # --- ADD THIS ---
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # --- END ADD ---

    def __str__(self):
        return self.name




# --- ADD THE FOLLOWING MODELS ---

# Model 1: The private contract between Client and Agent
class Job(models.Model):
    JOB_STATUS_CHOICES = [
        ('PENDING_AGENT', 'Pending Agent Approval'),
        ('OPEN', 'Open (Awaiting Posts)'),
        ('FILLED', 'Filled'),
        ('COMPLETED', 'Completed'),
    ]

    # --- MODIFIED ---
    # Links to your Client model
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="posted_jobs")
    # Links to your Agent model
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_jobs")
    # --- END MODIFIED ---

    title = models.CharField(max_length=255)
    description = models.TextField()
    location_address = models.TextField(blank=True, null=True, help_text="Auto-filled by map")
    location_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    client_pay_per_worker = models.DecimalField(max_digits=10, decimal_places=2)
    workers_needed = models.PositiveIntegerField(default=1)

    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='SEEKING_AGENT')
    # --- ADD THIS SECTION ---
    CLIENT_PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    client_payment_status = models.CharField(
        max_length=10,
        choices=CLIENT_PAYMENT_CHOICES,
        default='pending'
    )
    # --- END ADD ---
    client_rating_for_agent = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (Client: {self.client.name})"


# Model 2: The public post from the Agent to the Workers
class JobPosting(models.Model):
    # This links the posting to the main Client-Agent contract
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="postings")

    # --- MODIFIED ---
    # Links to your Agent model
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="job_postings")
    # --- END MODIFIED ---

    title = models.CharField(max_length=255)
    description = models.TextField()

    worker_pay_rate = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)  # Workers see this if True
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (Posted by Agent: {self.agent.name})"


# Model 3: The Worker's application to the Agent's post
class Application(models.Model):
    APPLICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),  # Worker applied, agent hasn't seen
        ('ACCEPTED', 'Accepted'),  # Agent accepted, worker must now upload proof
        ('REJECTED', 'Rejected'),  # Agent rejected application
        ('PROOF_SUBMITTED', 'Proof Submitted'),  # Worker uploaded, agent must review
        ('COMPLETED', 'Completed'),  # Agent approved proof, worker gets paid
        ('PROOF_REJECTED', 'Proof Rejected')  # Agent rejected proof, worker must resubmit
    ]

    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name="applications")

    # --- MODIFIED ---
    # Links to your Worker model
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name="applications")
    # --- END MODIFIED ---

    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='PENDING')

    applied_at = models.DateTimeField(auto_now_add=True)
    agent_rating_for_worker = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    # --- ADD THIS SECTION ---
    WORKER_PAYMENT_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]
    worker_payment_status = models.CharField(
        max_length=10,
        choices=WORKER_PAYMENT_CHOICES,
        default='unpaid'
    )

    # --- END ADD ---

    def __str__(self):
        return f"Application by {self.worker.name} for {self.job_posting.title}"

class WorkProof(models.Model):
    """
    Stores the photo and location proof uploaded by a worker
    for a specific job application.
    """
    # Links this proof to the specific application
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='work_proof'
    )

    # The uploaded image
    image = models.ImageField(upload_to='work_proofs/')

    # Geolocation data
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)

    # Status fields (for the agent's review)
    status = models.CharField(max_length=10, choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # A field for the agent to explain a rejection
    agent_remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Proof for Application {self.application.id} - {self.status}"