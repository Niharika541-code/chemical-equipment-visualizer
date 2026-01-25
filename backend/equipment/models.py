from django.db import models

# Create your models here.
class UploadHistory(models.Model):
    total_equipment = models.IntegerField() # stored whole number
    avg_flowrate = models.FloatField() #stored decimal numbers
    avg_pressure = models.FloatField()
    avg_temperature = models.FloatField()
    type_distribution = models.TextField() #Databases cannot store dictionary directly so we store as text
    created_at = models.DateTimeField(auto_now_add=True) #stores date and time in auto mdoe
    