from django.db import models

# Create your models here.
class Token(models.Model):
	token=models.CharField(max_length=64)
	issued_to=models.CharField(max_length=120)
	issued_on=models.DateField(auto_now_add=True)
	def __str__(self):
		ret = self.issued_to
		return ret