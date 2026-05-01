from django.db import models
from django.template.loader import render_to_string, get_template
from django.conf import settings
from pathlib import Path
from apps.common.models import BaseModel


class MailTemplates(BaseModel):
    """
    Model to store and manage HTML email/notification templates.
    
    Stores template metadata including the file path and default input variables.
    """
    
    template_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique identifier for the template"
    )
    
    template_path = models.CharField(
        max_length=500,
        help_text="File path to the HTML template file (relative to templates directory)"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of what this template is used for"
    )
    
    input_variable_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="Default/example dictionary of input variables for template rendering"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template is active and available for use"
    )
    
    class Meta:
        verbose_name = "HTML Template"
        verbose_name_plural = "HTML Templates"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template_name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.template_name
    
    def get_required_variables(self):
        """
        Get list of required variable keys from input_variable_values.
        
        Returns:
            list: Keys from the input_variable_values dictionary
        """
        return list(self.input_variable_values.keys()) if self.input_variable_values else []
    
    def get_template_string(self):
        """
        Read and return the HTML template file as a string.
        
        Uses Django's template loader to safely load the template file
        from the configured template directories.
        
        Returns:
            str: The raw HTML template content as a string

        Raises:
            FileNotFoundError: If the template file doesn't exist
            IOError: If there's an error reading the template file

        Example:
            template = MailTemplates.objects.get(template_name='welcome')
            html_string = template.get_template_string()
        """
        try:
            template = get_template(self.template_path)
            return template.template.source
        except Exception as e:
            # Fallback: Try reading directly from templates directory
            try:
                for template_dir in settings.TEMPLATES[0]['DIRS']:
                    template_file_path = Path(template_dir) / self.template_path
                    if template_file_path.exists():
                        with open(template_file_path, 'r', encoding='utf-8') as f:
                            return f.read()
                raise FileNotFoundError(f"Template not found: {self.template_path}")
            except FileNotFoundError as fnf:
                raise FileNotFoundError(f"Template file not found at path: {self.template_path}") from fnf
            except IOError as io_err:
                raise IOError(f"Error reading template file: {self.template_path}") from io_err


class OutBounds(BaseModel):
    mail_template = models.ForeignKey(MailTemplates, on_delete=models.CASCADE)
    to_mail = models.EmailField()
    is_sent = models.BooleanField(default=False)
    body = models.TextField()

    def __str__(self):
        return self.mail_template.template_name