from django import forms
from .models import Job, JobPosting

# --- This is your Tailwind class ---
TAILWIND_INPUT_CLASS = (
    "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 "
    "rounded-md text-sm shadow-sm placeholder-slate-400 "
    "focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
)


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title',
            'description',
            'client_pay_per_worker',
            'workers_needed',
            'location_address',
            'location_latitude',
            'location_longitude'
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'placeholder': 'e.g., Catering for Wedding Event'
            }),
            'description': forms.Textarea(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'rows': 4,
                'placeholder': 'Describe the job details...'
            }),

            # --- THIS IS THE FIX ---
            'client_pay_per_worker': forms.NumberInput(attrs={
                # We remove 'px-3' from the class and add our own 'pl-7 pr-3'
                'class': TAILWIND_INPUT_CLASS.replace("px-3", "") + " pl-7 pr-3",
                'placeholder': '500'
            }),
            # --- END FIX ---

            'workers_needed': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'placeholder': '10'
            }),
            'location_address': forms.HiddenInput(),
            'location_latitude': forms.HiddenInput(),
            'location_longitude': forms.HiddenInput(),
        }


class JobPostingForm(forms.ModelForm):
    """
    This form is for the Agent. It does NOT need to be changed.
    """

    class Meta:
        model = JobPosting
        fields = ['title', 'description', 'worker_pay_rate']

        widgets = {
            'title': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'placeholder': 'e.g., Catering for Wedding Event'
            }),
            'description': forms.Textarea(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'rows': 4,
                'placeholder': 'Describe the job details for the worker...'
            }),
            'worker_pay_rate': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'placeholder': '450'
            }),
        }